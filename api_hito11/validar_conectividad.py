import argparse
import json
import socket
import time
from urllib.parse import urlparse

import httpx

from app.config.settings import Settings
from app.main import build_adapters


MOTORES = (
    "mongodb", "neo4j", "cassandra",
    "redis", "influxdb", "iris"
)


def destinos(settings):
    mongo = urlparse(settings.mongo_uri.get_secret_value())
    neo = urlparse(settings.neo4j_uri)
    redis = urlparse(settings.redis_url.get_secret_value())
    influx = urlparse(settings.influx_url)

    return {
        "mongodb": (mongo.hostname, mongo.port or 27017),
        "neo4j": (neo.hostname, neo.port or 7687),
        "cassandra": (settings.cassandra_host, settings.cassandra_port),
        "redis": (redis.hostname, redis.port or 6379),
        "influxdb": (influx.hostname, influx.port or 8181),
        "iris": (settings.iris_host, settings.iris_port),
    }


def comprobar_tcp(host, puerto, timeout):
    inicio = time.perf_counter()
    try:
        socket.getaddrinfo(host, puerto)
        with socket.create_connection((host, puerto), timeout=timeout):
            estado = "ok"
            detalle = "DNS y TCP disponibles"
    except Exception as error:
        estado = "error"
        detalle = type(error).__name__

    return {
        "estado": estado,
        "detalle": detalle,
        "duracion_ms": round((time.perf_counter() - inicio) * 1000, 2),
    }


def comprobar_nativo(adaptador):
    inicio = time.perf_counter()
    try:
        adaptador.ping()
        estado = "ok"
        detalle = "Ping nativo correcto"
    except Exception as error:
        estado = "error"
        detalle = type(error).__name__

    return {
        "estado": estado,
        "detalle": detalle,
        "duracion_ms": round((time.perf_counter() - inicio) * 1000, 2),
    }


def comprobar_api(cliente, motor):
    inicio = time.perf_counter()
    try:
        respuesta = cliente.get("/api/v1/salud")
        datos = respuesta.json().get("data", {})
        dependencia = datos.get("dependencias", {}).get(motor, {})
        estado = dependencia.get("estado", "sin_datos")
        detalle = f"HTTP {respuesta.status_code}"
    except Exception as error:
        estado = "error"
        detalle = type(error).__name__

    return {
        "estado": estado,
        "detalle": detalle,
        "duracion_ms": round((time.perf_counter() - inicio) * 1000, 2),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("tcp", "native", "api", "all"), default="all")
    parser.add_argument("--producto", choices=(*MOTORES, "todos"), default="todos")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    settings = Settings()
    elegidos = MOTORES if args.producto == "todos" else (args.producto,)
    destinos_tcp = destinos(settings)

    resultados = {}
    adaptadores = {}

    try:
        if args.mode in ("native", "all"):
            adaptadores = build_adapters(settings)

        with httpx.Client(base_url=args.api_url, timeout=30.0) as cliente:
            for motor in elegidos:
                resultado = {}

                if args.mode in ("tcp", "all"):
                    host, puerto = destinos_tcp[motor]
                    resultado["tcp"] = comprobar_tcp(
                        host, puerto, settings.timeout_seconds
                    )

                if args.mode in ("native", "all"):
                    resultado["native"] = comprobar_nativo(adaptadores[motor])

                if args.mode in ("api", "all"):
                    resultado["api"] = comprobar_api(cliente, motor)

                resultados[motor] = resultado
                print(motor, json.dumps(resultado, ensure_ascii=False))

    finally:
        for adaptador in adaptadores.values():
            try:
                adaptador.close()
            except Exception:
                pass

    fallos = sum(
        valor["estado"] != "ok"
        for capas in resultados.values()
        for valor in capas.values()
    )

    print("RESUMEN:", len(resultados), "motores;", fallos, "comprobaciones no OK")
    raise SystemExit(1 if fallos else 0)


if __name__ == "__main__":
    main()
