"""Recoge evidencia en Docker existente; no instala, crea ni detiene servicios."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]


def ejecutar(comando, entrada=None, timeout=180):
    return subprocess.run(comando, input=entrada, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout, cwd=ROOT)


def huella(contenido):
    return hashlib.sha256(contenido.decode("utf-8-sig").replace("\r\n", "\n").encode("utf-8")).hexdigest()


def manifiesto():
    base = ROOT / "api_hito11"
    paths = sorted((base / "app").rglob("*.py"))
    paths += [base / "validar_conectividad.py", base / "tests/test_integracion_hito11.py"]
    return {p.relative_to(base).as_posix(): huella(p.read_bytes()) for p in paths}


def comprobar_codigo(exec_api):
    esperado = manifiesto()
    script = """import hashlib, json
from pathlib import Path
esperado = json.loads(%r)
distintos, ausentes = [], []
for nombre, sha in esperado.items():
    p = Path(nombre)
    if not p.is_file():
        ausentes.append(nombre)
        continue
    contenido = p.read_text(encoding='utf-8-sig').replace('\\r\\n', '\\n')
    if hashlib.sha256(contenido.encode('utf-8')).hexdigest() != sha:
        distintos.append(nombre)
print(json.dumps({'estado': 'ok' if not distintos and not ausentes else 'error',
                  'archivos_distintos': distintos, 'archivos_ausentes': ausentes}))
""" % json.dumps(esperado)
    result = ejecutar([*exec_api, "python", "-"], script)
    if result.returncode:
        return {"estado": "no_probado", "motivo": "no_se_pudo_leer_codigo_del_contenedor"}
    return json.loads(result.stdout)


def inventario(contenedor):
    # Se seleccionan campos: nunca Config.Env ni inspect completo.
    formato = '{"id":{{json .Id}},"imagen":{{json .Config.Image}},"imagen_id":{{json .Image}},"activo":{{json .State.Running}},"inicio":{{json .State.StartedAt}},"montajes":{{json .Mounts}}}'
    result = ejecutar(["docker", "inspect", "--format", formato, contenedor], timeout=20)
    if result.returncode:
        return {"estado": "no_probado", "motivo": "contenedor_no_accesible"}
    data = json.loads(result.stdout)
    data["montajes"] = [{"tipo": m["Type"], "destino": m["Destination"],
                         "origen_sha256": hashlib.sha256(m.get("Source", "").encode()).hexdigest(),
                         "lectura_escritura": m.get("RW")} for m in data["montajes"]]
    data["estado"] = "ok" if data["activo"] else "no_probado"
    return data


def salida_json(exec_api, script, argumentos):
    result = ejecutar([*exec_api, "python", "-", *argumentos], script.read_text(encoding="utf-8-sig"))
    try:
        return {"codigo_salida": result.returncode, "informe": json.loads(result.stdout)}
    except (ValueError, TypeError):
        return {"codigo_salida": result.returncode, "estado": "error", "motivo": "salida_no_json"}


def verificar(args):
    report = {"fecha_utc": datetime.now(timezone.utc).isoformat(), "origen": "host_con_docker_exec",
              "estado": "no_probado", "pendientes_manuales": [
                  "Cotejar versiones y procedencia de las seis instancias con H4-H9",
                  "RF21: detencion temporal y recuperacion en ventana coordinada",
                  "Revisar permisos y errores de contexto por motor; adjuntar logs correlacionados"],
              "limites": "No cambia datos ni servicios. Codigo cotejado en disco; la API debe haberse recargado con ese codigo."}
    revision = ejecutar(["git", "rev-parse", "HEAD"], timeout=10)
    report["revision"] = revision.stdout.strip() if revision.returncode == 0 else "desconocida"
    cambios = ejecutar(["git", "status", "--porcelain", "--", "api_hito11", "scripts"], timeout=10)
    report["codigo_sin_commit"] = bool(cambios.returncode or cambios.stdout.strip())
    if shutil.which("docker") is None:
        report["motivo"] = "docker_no_instalado"
        return report
    if report["codigo_sin_commit"]:
        report["motivo"] = "confirmar_cambios_en_git_para_identificar_la_revision_probada"
        return report
    result = ejecutar(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=20)
    if result.returncode:
        report["motivo"] = "docker_no_accesible"
        return report
    report["contenedores"] = {c: inventario(c) for c in dict.fromkeys([args.contenedor_api, *args.motores])}
    if report["contenedores"][args.contenedor_api]["estado"] != "ok":
        report["motivo"] = "api_no_disponible"
        return report
    exec_api = ["docker", "exec", "-i", "-w", args.ruta_api, args.contenedor_api]
    report["codigo_contenedor"] = comprobar_codigo(exec_api)
    if report["codigo_contenedor"]["estado"] != "ok":
        report["motivo"] = "actualizar_solo_codigo_api_con_mecanismo_de_despliegue_existente"
        return report
    report["conectividad"] = salida_json(exec_api, ROOT / "api_hito11/validar_conectividad.py",
        ["--mode", "all", "--producto", "todos", "--origen", "contenedor-api", "--revision", report["revision"], "--json"])
    result = ejecutar([*exec_api, "python", "-m", "pytest", "tests/test_integracion_hito11.py",
                       "-q", "--tb=no", "-p", "no:cacheprovider"], timeout=360)
    # Guardar solo contadores, no errores arbitrarios ni logs sin redactar.
    cantidades = {nombre: sum(int(n) for n in re.findall(r"(\d+) " + nombre + r"\b", result.stdout))
                  for nombre in ("passed", "failed", "skipped", "error", "errors")}
    report["tests_originales"] = {"codigo_salida": result.returncode, **cantidades}
    report["influx3"] = salida_json(exec_api, ROOT / "api_hito11/verificar_agregaciones.py", [])
    report["estado"] = "comprobaciones_automaticas_ok" if (
        report["conectividad"]["codigo_salida"] == 0
        and result.returncode == 0 and cantidades["passed"] == 9
        and report["influx3"]["codigo_salida"] == 0
        and all(c["estado"] == "ok" for c in report["contenedores"].values())
    ) else "incompleto"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contenedor-api", default="fixture2030-hito11-api")
    parser.add_argument("--ruta-api", default="/app")
    parser.add_argument("--motores", nargs="+", default=["fixture2030-mongodb", "fixture2030-neo4j",
        "baseDeDatosIICassandra", "baseDeDatosIIRedis", "fixture2030-influxdb3", "baseDeDatosIIIRIS"])
    parser.add_argument("--salida", type=Path, help="Archivo JSON nuevo; nunca sobrescribe evidencia")
    args = parser.parse_args()
    destino = args.salida or ROOT / "docs/evidencia" / ("validacion_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8] + ".json")
    if destino.exists():
        parser.error("La salida ya existe; elegir un archivo nuevo")
    try:
        report = verificar(args)
    except Exception as error:
        report = {"estado": "incompleto", "tipo_error": type(error).__name__,
                  "fecha_utc": datetime.now(timezone.utc).isoformat(),
                  "limite": "Ejecucion interrumpida; no certifica las pruebas restantes"}
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as archivo:
        json.dump(report, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")
    print(f"Estado: {report['estado']}. Informe: {destino}")
    return 0 if report["estado"] == "comprobaciones_automaticas_ok" else 2


if __name__ == "__main__":
    sys.exit(main())
