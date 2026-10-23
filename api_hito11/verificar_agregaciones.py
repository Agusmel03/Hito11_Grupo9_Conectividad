"""Contrasta SQL Core con calculos sobre puntos existentes; nunca escribe datos."""
import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
import re

import httpx
from pydantic import TypeAdapter

from app.adapters.influx3 import Influx3Adapter
from app.config.settings import Settings
from app.schemas.models import MatchID, StatsQuery


CAMPOS = ("posesion_pct", "pases_completados_total", "tiros_intervalo", "recuperaciones_intervalo")
RESOLUCIONES = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}


def instante(value):
    result = datetime.fromisoformat(value) if isinstance(value, str) else value
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


def referencia(puntos, consulta):
    """Referencia independiente de SQL; solo calcula sobre lecturas reales."""
    grupos = defaultdict(list)
    segundos = RESOLUCIONES[consulta.resolucion]
    for punto in puntos:
        tiempo = instante(punto["time"])
        if not consulta.desde <= tiempo < consulta.hasta:
            continue
        fin = datetime.fromtimestamp((int(tiempo.timestamp()) // segundos + 1) * segundos, timezone.utc)
        grupos[(fin, punto["equipo_codigo"], punto["sede_id"])].append(punto)
    resultado = {}
    for clave, filas in grupos.items():
        filas.sort(key=lambda fila: instante(fila["time"]))
        valores = {campo: [f[campo] for f in filas if f.get(campo) is not None] for campo in CAMPOS}
        resultado[clave] = {
            "posesion_pct": sum(valores["posesion_pct"]) / len(valores["posesion_pct"]) if valores["posesion_pct"] else None,
            "pases_completados_total": valores["pases_completados_total"][-1] if valores["pases_completados_total"] else None,
            **{campo: sum(valores[campo]) if valores[campo] else None for campo in CAMPOS[2:]},
        }
    return resultado


def comparar(esperado, filas):
    observado = {(instante(f["tiempo"]), f["equipo_codigo"], f["sede_id"]): f for f in filas}
    diferencias = len(set(esperado) ^ set(observado))
    diferencias += len(filas) - len(observado)  # No ocultar duplicados.
    for clave in esperado.keys() & observado.keys():
        for campo in CAMPOS:
            a, b = esperado[clave][campo], observado[clave].get(campo)
            igual = a == b
            if campo == "posesion_pct" and a is not None and b is not None:
                igual = math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
            diferencias += not igual
    return diferencias


def verificar(adapter, partido, consulta):
    # MatchID validado incluso al invocar esta funcion directamente.
    TypeAdapter(MatchID).validate_python(partido)
    sql = f"""SELECT time, equipo_codigo, sede_id, {', '.join(CAMPOS)}
        FROM estadisticas_equipo WHERE partido_id = '{partido}'
        AND time >= TIMESTAMP '{consulta.desde.isoformat()}'
        AND time < TIMESTAMP '{consulta.hasta.isoformat()}'
        ORDER BY time, equipo_codigo, sede_id LIMIT 10001"""
    puntos = adapter.query_sql(sql)
    if not puntos or len(puntos) >= 10001:
        return {"estado": "no_probado", "motivo": "sin_puntos" if not puntos else "muestra_truncada",
                "filas_leidas": len(puntos)}
    pruebas = []
    ventanas = [("completa", consulta.desde, consulta.hasta)]
    if consulta.hasta - consulta.desde > timedelta(seconds=2):
        ventanas.append(("parcial", consulta.desde + timedelta(seconds=1), consulta.hasta - timedelta(seconds=1)))
    for tipo, desde, hasta in ventanas:
        for resolucion in RESOLUCIONES:
            query = StatsQuery(desde=desde, hasta=hasta, resolucion=resolucion)
            esperado = referencia(puntos, query)
            if not esperado or len(esperado) > 1000:
                pruebas.append({"ventana": tipo, "resolucion": resolucion, "estado": "no_probado",
                                "motivo": "sin_ventanas_o_limite_de_api"})
                continue
            try:
                filas = adapter.statistics(partido, query)
                diferencias = comparar(esperado, filas)
                pruebas.append({"ventana": tipo, "resolucion": resolucion,
                                "estado": "ok" if diferencias == 0 else "error",
                                "ventanas": len(esperado), "diferencias": diferencias})
            except Exception as error:
                pruebas.append({"ventana": tipo, "resolucion": resolucion, "estado": "error",
                                "tipo_error": type(error).__name__})
    return {"estado": "ok" if all(p["estado"] == "ok" for p in pruebas) else "incompleto",
            "filas_leidas": len(puntos), "comparaciones": pruebas,
            "nulos_observados": sum(p.get(c) is None for p in puntos for c in CAMPOS),
            "limite": "Valida solo la muestra leida; no certifica equivalencia universal ni origen del volumen"}


def informacion_servidor(adapter):
    resultados = {}
    for path in ("health", "ping"):
        try:
            res = httpx.get(f"{adapter.url}/{path}", timeout=adapter.timeout,
                            headers={"Authorization": f"Bearer {adapter.token}"})
            datos = {"http_status": res.status_code, "estado": "ok" if res.status_code == 200 else "error"}
            if path == "ping" and res.status_code == 200:
                version = res.headers.get("x-influxdb-version", "")
                build = res.headers.get("x-influxdb-build", "")
                if re.fullmatch(r"3\.\d+\.\d+(?:[-+.][A-Za-z0-9.-]+)?", version) and build.lower() == "core":
                    datos.update(version=version, producto="Core")
                else:
                    datos.update(estado="no_probado", motivo="no_se_identifico_core_3_en_cabeceras")
            resultados[path] = datos
        except Exception as error:
            resultados[path] = {"estado": "error", "tipo_error": type(error).__name__}
    return resultados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partido", default="P001")
    parser.add_argument("--desde", default="2030-06-08T19:00:00Z")
    parser.add_argument("--hasta", default="2030-06-08T20:00:00Z")
    args = parser.parse_args()
    report = {"fecha_utc": datetime.now(timezone.utc).isoformat()}
    try:
        TypeAdapter(MatchID).validate_python(args.partido)
        consulta = StatsQuery(desde=args.desde, hasta=args.hasta)
        adapter = Influx3Adapter(Settings())
        try:
            report["servidor"] = informacion_servidor(adapter)
            report["agregaciones"] = verificar(adapter, args.partido, consulta)
            report["caso"] = {"partido": args.partido, "desde": consulta.desde.isoformat(), "hasta": consulta.hasta.isoformat()}
            report["estado"] = "ok" if report["agregaciones"]["estado"] == "ok" and all(
                r["estado"] == "ok" for r in report["servidor"].values()) else "incompleto"
        finally:
            adapter.close()
    except Exception as error:
        report.update(estado="error", tipo_error=type(error).__name__)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    raise SystemExit(0 if report["estado"] == "ok" else 1)


if __name__ == "__main__":
    main()
