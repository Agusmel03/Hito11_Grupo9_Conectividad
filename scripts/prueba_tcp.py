import argparse
import json
import os
import socket
import time
from datetime import datetime, timezone
from pathlib import Path

SERVICIOS = {
    "mongodb": ("MONGO_HOST", "MONGO_PORT", "127.0.0.1", 27017),
    "neo4j": ("NEO4J_HOST", "NEO4J_PORT", "127.0.0.1", 7687),
    "cassandra": ("CASSANDRA_HOST", "CASSANDRA_PORT", "127.0.0.1", 9042),
    "redis": ("REDIS_HOST", "REDIS_PORT", "127.0.0.1", 6379),
    "influxdb": ("INFLUX_HOST", "INFLUX_PORT", "127.0.0.1", 8181),
    "iris": ("IRIS_HOST", "IRIS_PORT", "127.0.0.1", 1972),
}

def comprobar(nombre, configuracion, timeout):
    host_var, port_var, host_default, port_default = configuracion
    host = os.getenv(host_var, host_default)
    puerto = int(os.getenv(port_var, port_default))

    resultado = {
        "producto": nombre,
        "origen": "Windows - PowerShell / Python local",
        "host": host,
        "puerto": puerto,
        "capa": "TCP",
        "fecha": datetime.now(timezone.utc).isoformat(),
    }

    inicio = time.perf_counter()

    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            resultado["estado"] = "TCP_OK"
            resultado["detalle"] = "Puerto accesible; no verifica autenticacion ni consultas."

    except socket.gaierror:
        resultado["estado"] = "DNS_ERROR"
        resultado["detalle"] = "No se pudo resolver el host."

    except ConnectionRefusedError:
        resultado["estado"] = "CONNECTION_REFUSED"
        resultado["detalle"] = "No se acepta la conexion en este puerto."

    except socket.timeout:
        resultado["estado"] = "TIMEOUT"
        resultado["detalle"] = "No hubo respuesta dentro del timeout."

    except OSError as exc:
        resultado["estado"] = "TCP_ERROR"
        resultado["detalle"] = type(exc).__name__

    resultado["duracion_ms"] = round(
        (time.perf_counter() - inicio) * 1000, 2
    )

    return resultado

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producto", choices=[*SERVICIOS, "todos"], default="todos")
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()

    seleccion = SERVICIOS.keys() if args.producto == "todos" else [args.producto]

    resultados = [
        comprobar(nombre, SERVICIOS[nombre], args.timeout)
        for nombre in seleccion
    ]

    for resultado in resultados:
        print(
            f'{resultado["producto"]}: {resultado["estado"]} '
            f'({resultado["host"]}:{resultado["puerto"]}) '
            f'{resultado["duracion_ms"]} ms'
        )

    salida = Path("docs/evidencia/resultados_tcp.json")
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\nEvidencia guardada: {salida}")

if __name__ == "__main__":
    main()
