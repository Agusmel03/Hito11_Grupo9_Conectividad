import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"


@pytest.fixture(scope="module")
def cliente():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


def test_liveness(cliente):
    respuesta = cliente.get("/health/live")
    assert respuesta.status_code == 200


def test_salud_seis_motores(cliente):
    respuesta = cliente.get("/api/v1/salud")
    assert respuesta.status_code == 200

    datos = respuesta.json()["data"]
    assert datos["estado"] == "ok"

    motores = {
        "mongodb", "neo4j", "cassandra",
        "redis", "influxdb", "iris"
    }

    assert motores == set(datos["dependencias"])

    for motor in motores:
        assert datos["dependencias"][motor]["estado"] == "ok"


@pytest.mark.parametrize(
    "ruta",
    [
        "/api/v1/equipos",
        "/api/v1/grafo",
        "/api/v1/objetos/partidos/P001",
    ],
)
def test_consultas_funcionales(cliente, ruta):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    assert "data" in respuesta.json()


def test_cassandra_comentarios(cliente):
    respuesta = cliente.get(
        "/api/v1/partidos/P001/comentarios",
        params={
            "bucket_10m": "2030-06-10T18:00:00Z",
            "shard": 0,
            "limite": 10,
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["partido_id"] == "P001"


def test_influxdb_estadisticas(cliente):
    respuesta = cliente.get(
        "/api/v1/partidos/P001/estadisticas",
        params={
            "desde": "2030-06-08T19:00:00Z",
            "hasta": "2030-06-08T20:00:00Z",
            "resolucion": "5m",
        },
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()["data"]
    assert datos["partido_id"] == "P001"
    assert len(datos["items"]) > 0
    assert all(item["tiempo"].endswith("Z") for item in datos["items"])


def test_redis_sesion_inexistente(cliente):
    respuesta = cliente.get("/api/v1/sesiones/SESION_INEXISTENTE")
    assert respuesta.status_code == 404


def test_cassandra_parametro_obligatorio(cliente):
    respuesta = cliente.get("/api/v1/partidos/P001/comentarios")
    assert respuesta.status_code == 422
    assert "query.bucket_10m" in respuesta.json()["error"]["fields"]
