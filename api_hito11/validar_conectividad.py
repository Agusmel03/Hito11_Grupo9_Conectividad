"""Diagnostico de solo lectura sobre las implementaciones existentes H4-H9."""
import argparse
from datetime import datetime, timezone
import json
import socket
import time
from urllib.parse import urlparse
from uuid import UUID

import httpx
from pydantic import TypeAdapter

from app.config.settings import Settings
from app.errors import ApiError
from app.schemas.models import (
    CommentQuery, Comments, Envelope, ErrorResponse, Events, Health,
    MatchID, MatchObject, Session, SessionID, Statistics, StatsQuery, Teams,
)

MOTORES = ("mongodb", "neo4j", "cassandra", "redis", "influxdb", "iris")
CONTRATOS = dict(zip(MOTORES, (Teams, Events, Comments, Session, Statistics, MatchObject)))


def destinos(settings, productos=MOTORES):
    def uri(value, port):
        parsed = urlparse(value)
        if parsed.scheme == "mongodb+srv":
            raise NotImplementedError("TCP requiere resolver registros SRV")
        return parsed.hostname, parsed.port or port

    factories = {
        "mongodb": lambda: uri(settings.mongo_uri.get_secret_value(), 27017),
        "neo4j": lambda: uri(settings.neo4j_uri, 7687),
        "cassandra": lambda: (settings.cassandra_host, settings.cassandra_port),
        "redis": lambda: uri(settings.redis_url.get_secret_value(), 6379),
        "influxdb": lambda: uri(settings.influx_url, 443 if settings.influx_url.startswith("https:") else 80),
        "iris": lambda: (settings.iris_host, settings.iris_port),
    }
    return {motor: factories[motor]() for motor in productos}


def medir(operacion):
    inicio = time.perf_counter()
    try:
        resultado = {"estado": "ok", "categoria": "success", **operacion()}
    except (ImportError, NotImplementedError) as error:
        resultado = {"estado": "skip", "categoria": "herramienta_no_disponible", "detalle": type(error).__name__}
    except Exception as error:
        categoria = "probe_failed"
        if isinstance(error, socket.gaierror):
            categoria = "dns_error"
        elif isinstance(error, ConnectionRefusedError):
            categoria = "connection_refused"
        elif isinstance(error, (TimeoutError, httpx.TimeoutException)):
            categoria = "timeout"
        elif isinstance(error, ApiError):
            categoria = "timeout" if error.code == "dependencia_timeout" else "dependencia_no_disponible"
        elif isinstance(error, httpx.ConnectError):
            categoria = "api_no_alcanzable"
        elif isinstance(error, ValueError):
            categoria = "configuracion_o_contrato_invalido"
        # str(error) puede contener URI, tokens o cuerpos HTTP.
        resultado = {"estado": "error", "categoria": categoria, "detalle": type(error).__name__}
    resultado["duracion_ms"] = round((time.perf_counter() - inicio) * 1000, 2)
    return resultado


def comprobar_tcp(host, puerto, timeout):
    def ejecutar():
        if not host or not 0 < puerto < 65536:
            raise ValueError("Destino invalido")
        socket.getaddrinfo(host, puerto)
        with socket.create_connection((host, puerto), timeout=timeout):
            pass
        return {"detalle": "DNS y TCP disponibles; no demuestra protocolo ni permisos"}
    return medir(ejecutar)


def comprobar_nativo(adaptador):
    def ejecutar():
        if adaptador.ping() is False:
            raise ValueError("Ping rechazado")
        return {"detalle": "Ping nativo correcto; no acredita procedencia de datos"}
    return medir(ejecutar)


def nativo_por_motor(settings, motor):
    def ejecutar():
        from app.main import build_adapters
        adaptadores = build_adapters(settings, (motor,))
        try:
            return comprobar_nativo(adaptadores[motor])
        finally:
            for adaptador in adaptadores.values():
                try:
                    adaptador.close()
                except Exception:
                    pass
    return medir(ejecutar)


def metadatos_http(respuesta):
    # No reflejar cabeceras arbitrarias en la evidencia.
    rid = str(UUID(respuesta.headers.get("X-Request-ID", "")))
    return {"http_status": respuesta.status_code, "request_id": rid}


def comprobar_api(cliente, motor, respuesta=None):
    def ejecutar():
        res = respuesta if respuesta is not None else cliente.get("/api/v1/salud")
        meta = metadatos_http(res)
        if res.status_code not in (200, 503):
            return {**meta, "estado": "error", "categoria": "http_inesperado"}
        salud = Envelope[Health].model_validate(res.json()).data
        todo_ok = all(item.estado == "ok" for item in salud.dependencias.values())
        if res.status_code != (200 if todo_ok else 503) or salud.estado != ("ok" if todo_ok else "degradado"):
            raise ValueError("Estado HTTP y salud inconsistentes")
        dependencia = salud.dependencias[motor]
        ok = dependencia.estado == "ok"
        return {**meta, "estado": "ok" if ok else "error",
                "categoria": "success" if ok else "dependencia_no_disponible",
                "detalle": "Salud por dependencia; no sustituye la lectura funcional"}
    return medir(ejecutar)


def rutas_funcionales(args):
    return {
        "mongodb": ("/api/v1/equipos", {"limite": 2}),
        "neo4j": (f"/api/v1/partidos/{args.partido}/eventos", {"limite": 2}),
        "cassandra": (f"/api/v1/partidos/{args.partido}/comentarios",
                      {"bucket_10m": args.bucket_10m, "shard": args.shard, "limite": 2}),
        "redis": (f"/api/v1/sesiones/{args.sesion}", None),
        "influxdb": (f"/api/v1/partidos/{args.partido}/estadisticas",
                     {"desde": args.desde, "hasta": args.hasta, "resolucion": args.resolucion}),
        "iris": (f"/api/v1/objetos/partidos/{args.partido}", {"limite_eventos": 2}),
    }


def comprobar_funcional(cliente, motor, ruta, parametros=None):
    def ejecutar():
        res = cliente.get(ruta, params=parametros)
        meta = metadatos_http(res)
        if res.status_code != 200:
            error = ErrorResponse.model_validate(res.json()).error
            if str(UUID(error.request_id)) != meta["request_id"]:
                raise ValueError("Correlacion inconsistente")
            if motor == "redis" and res.status_code == 404 and error.code == "recurso_inexistente":
                return {**meta, "categoria": "ausencia_valida",
                        "detalle": "Sesion ausente, expirada o sin vigencia; no prueba una sesion activa"}
            categorias = {404: "recurso_inexistente", 422: "validacion", 503: "dependencia_no_disponible", 500: "error_interno"}
            categoria = "timeout" if res.status_code == 503 and error.code == "dependencia_timeout" else categorias.get(res.status_code, "http_inesperado")
            return {**meta, "estado": "error", "categoria": categoria}
        datos = Envelope[CONTRATOS[motor]].model_validate(res.json()).data
        if motor in ("neo4j", "cassandra", "influxdb", "iris"):
            partes = ruta.split("/")
            if datos.partido_id != partes[partes.index("partidos") + 1]:
                raise ValueError("Identificador de partido inesperado")
        if motor == "redis" and datos.session_id != ruta.rsplit("/", 1)[1]:
            raise ValueError("Identificador de sesion inesperado")
        if motor == "redis" and datos.estado != "activa":
            raise ValueError("Sesion sin vigencia")
        if motor == "cassandra" and parametros is not None:
            consulta = CommentQuery(**parametros)
            if datos.bucket_10m != consulta.bucket_10m or datos.shard != consulta.shard:
                raise ValueError("Particion inesperada")
        if motor == "influxdb" and parametros is not None:
            consulta = StatsQuery(**parametros)
            if (datos.desde, datos.hasta, datos.resolucion) != (consulta.desde, consulta.hasta, consulta.resolucion):
                raise ValueError("Ventana inesperada")
        if hasattr(datos, "items"):
            cantidad = len(datos.items)
            return {**meta, "categoria": "lectura_con_datos" if cantidad else "vacio_valido", "filas": cantidad,
                    "detalle": "Contrato valido; no certifica origen ni completitud del dataset"}
        return {**meta, "categoria": "lectura_con_datos", "detalle": "Contrato e identificador validos"}
    return medir(ejecutar)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("tcp", "native", "api", "all"), default="all")
    parser.add_argument("--producto", choices=(*MOTORES, "todos"), default="todos")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--env-file", help="Archivo privado; variables del proceso tienen prioridad")
    parser.add_argument("--origen", choices=("contenedor-api", "host", "no-declarado"), default="no-declarado")
    parser.add_argument("--revision", default="no-declarada", help="Commit probado")
    parser.add_argument("--json", action="store_true", help="Informe JSON unico")
    parser.add_argument("--partido", default="P001")
    parser.add_argument("--sesion", default="SESION_INEXISTENTE")
    parser.add_argument("--bucket-10m", default="2030-06-10T18:00:00Z")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--desde", default="2030-06-08T19:00:00Z")
    parser.add_argument("--hasta", default="2030-06-08T20:00:00Z")
    parser.add_argument("--resolucion", choices=("1m", "5m", "15m", "1h"), default="5m")
    args = parser.parse_args()
    try:
        if args.env_file:
            from pathlib import Path
            if not Path(args.env_file).is_file():
                raise ValueError("Archivo de configuracion inexistente")
        settings = Settings(**({"_env_file": args.env_file} if args.env_file else {}))
        TypeAdapter(MatchID).validate_python(args.partido)
        TypeAdapter(SessionID).validate_python(args.sesion)
        CommentQuery(bucket_10m=args.bucket_10m, shard=args.shard)
        StatsQuery(desde=args.desde, hasta=args.hasta, resolucion=args.resolucion)
        if args.revision != "no-declarada" and (not 7 <= len(args.revision) <= 40 or any(c not in "0123456789abcdefABCDEF" for c in args.revision)):
            raise ValueError("Revision invalida")
        api_url = httpx.URL(args.api_url)
        if api_url.scheme not in ("http", "https") or not api_url.host or api_url.userinfo or api_url.query or api_url.fragment:
            raise ValueError("URL API invalida")
    except (ValueError, OSError, httpx.InvalidURL):
        print(json.dumps({"estado": "skip", "categoria": "configuracion_invalida",
                          "detalle": "Revisar configuracion y parametros sin publicar sus valores"}))
        raise SystemExit(2) from None

    elegidos = MOTORES if args.producto == "todos" else (args.producto,)
    rutas = rutas_funcionales(args)
    resultados = {}
    with httpx.Client(base_url=args.api_url, timeout=settings.timeout_seconds) as cliente:
        salud = None
        fallo_salud = None
        for motor in elegidos:
            resultado = {}
            if args.mode in ("tcp", "all"):
                def ejecutar_tcp():
                    host, puerto = destinos(settings, (motor,))[motor]
                    return comprobar_tcp(host, puerto, settings.timeout_seconds)
                resultado["tcp"] = medir(ejecutar_tcp)
            if args.mode in ("native", "all"):
                resultado["native"] = nativo_por_motor(settings, motor)
            if args.mode in ("api", "all"):
                if fallo_salud is None:
                    def consultar_salud():
                        nonlocal salud
                        salud = cliente.get("/api/v1/salud")
                        return {}
                    fallo_salud = medir(consultar_salud)
                resultado["api"] = comprobar_api(cliente, motor, salud) if salud is not None else fallo_salud.copy()
                resultado["api"]["duracion_ms"] = fallo_salud["duracion_ms"]
                ruta, parametros = rutas[motor]
                resultado["api_funcional"] = comprobar_funcional(cliente, motor, ruta, parametros)
            resultados[motor] = resultado
            if not args.json:
                print(motor, json.dumps(resultado, ensure_ascii=False))

    fallos = sum(v["estado"] == "error" for capas in resultados.values() for v in capas.values())
    omitidas = sum(v["estado"] == "skip" for capas in resultados.values() for v in capas.values())
    informe = {"fecha_utc": datetime.now(timezone.utc).isoformat(), "origen": args.origen,
               "revision": args.revision, "modo": args.mode, "resultados": resultados,
               "errores": fallos, "omitidas": omitidas,
               "caso": {"partido": args.partido, "bucket_10m": args.bucket_10m, "shard": args.shard,
                        "desde": args.desde, "hasta": args.hasta, "resolucion": args.resolucion},
               "limites": "No certifica versiones, permisos completos ni procedencia de volumenes. SKIP no significa motor caido."}
    if args.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    else:
        print("RESUMEN:", len(resultados), "motores;", fallos, "errores;", omitidas, "omitidas")
    raise SystemExit(1 if fallos else 2 if omitidas else 0)


if __name__ == "__main__":
    main()
