"""Pruebas aisladas: dobles HTTP en memoria, sin escrituras a los motores."""
from datetime import datetime, timezone
import json
import socket
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.adapters.influx3 import Influx3Adapter
from app.config.settings import Settings
from app.errors import ApiError
from app.main import build_adapters, create_app
from app.schemas.models import StatsQuery
import validar_conectividad as diagnostico


def settings(**kwargs):
    return Settings(_env_file=None, **kwargs)


def response(status, body, rid=None):
    return httpx.Response(status, json=body, headers={"X-Request-ID": rid or str(uuid4())})


def client_for(res):
    return httpx.Client(base_url="http://api.test", transport=httpx.MockTransport(lambda _: res))


@pytest.mark.parametrize("status,code,expected", [
    (404, "recurso_inexistente", "ausencia_valida"),
    (404, "error_http", "recurso_inexistente"),
    (422, "entrada_invalida", "validacion"),
    (503, "dependencia_no_disponible", "dependencia_no_disponible"),
    (503, "dependencia_timeout", "timeout"),
    (500, "error_interno", "error_interno"),
])
def test_redis_exige_contrato_de_ausencia(status, code, expected):
    rid = str(uuid4())
    res = response(status, {"error": {"code": code, "message": "Detalle privado que no se imprime",
                                    "request_id": rid}}, rid)
    with client_for(res) as client:
        result = diagnostico.comprobar_funcional(client, "redis", "/api/v1/sesiones/SESION_INEXISTENTE")
    assert result["categoria"] == expected
    assert result["estado"] == ("ok" if expected == "ausencia_valida" else "error")
    assert result["request_id"] == rid
    assert "privado" not in json.dumps(result)


@pytest.mark.parametrize("body", [{"error": {}}, {"data": None}, {"data": {}}, {"detail": "Not Found"}])
def test_contrato_incompleto_no_es_exito(body):
    with client_for(response(200, body)) as client:
        assert diagnostico.comprobar_funcional(client, "mongodb", "/api/v1/equipos")["estado"] == "error"


def test_vacio_valido_se_distingue_de_datos():
    with client_for(response(200, {"data": {"items": [], "siguiente_codigo": None}})) as client:
        result = diagnostico.comprobar_funcional(client, "mongodb", "/api/v1/equipos")
    assert result["estado"] == "ok"
    assert result["categoria"] == "vacio_valido"
    assert result["filas"] == 0


@pytest.mark.parametrize("partido,expected", [("P001", "ok"), ("P002", "error")])
def test_iris_conserva_identificador(partido, expected):
    data = {"id": "1", "partido_id": partido, "equipo_local": "AAA", "equipo_visitante": "AAB",
            "fecha": "2030-06-08T19:00:00", "sede": "S001", "estado": "Programado",
            "eventos": [], "eventos_truncados": False}
    with client_for(response(200, {"data": data})) as client:
        assert diagnostico.comprobar_funcional(client, "iris", "/api/v1/objetos/partidos/P001")["estado"] == expected


def test_salud_degradada_no_impide_otro_motor():
    res = response(503, {"data": {"estado": "degradado", "dependencias": {
        "redis": {"estado": "no_disponible", "duracion_ms": 1},
        "mongodb": {"estado": "ok", "duracion_ms": 1},
    }}})
    with client_for(res) as client:
        assert diagnostico.comprobar_api(client, "mongodb")["estado"] == "ok"
        assert diagnostico.comprobar_api(client, "redis")["estado"] == "error"


@pytest.mark.parametrize("error,category", [
    (socket.gaierror("secreto"), "dns_error"),
    (ConnectionRefusedError("secreto"), "connection_refused"),
    (TimeoutError("secreto"), "timeout"),
    (httpx.ReadTimeout("secreto"), "timeout"),
    (ImportError("secreto"), "herramienta_no_disponible"),
])
def test_diagnostico_clasifica_sin_revelar_excepcion(error, category):
    def fail():
        raise error
    result = diagnostico.medir(fail)
    assert result["categoria"] == category
    assert "secreto" not in json.dumps(result)
    assert result["estado"] == ("skip" if isinstance(error, ImportError) else "error")


def test_construccion_independiente_y_cierre(monkeypatch):
    import app.main as main
    adapter = Mock()
    module = SimpleNamespace(Influx3Adapter=Mock(return_value=adapter))
    importer = Mock(return_value=module)
    monkeypatch.setattr(main, "import_module", importer)
    result = diagnostico.nativo_por_motor(settings(), "influxdb")
    assert result["estado"] == "ok"
    importer.assert_called_once_with("app.adapters.influx3")
    adapter.close.assert_called_once()


def test_factory_conserva_seis_adaptadores_y_limpia_fallo(monkeypatch):
    import app.main as main
    clients = []
    def factory(name):
        client = Mock()
        clients.append(client)
        return SimpleNamespace(**{n: Mock(return_value=client) for n in
                                  ("MongoAdapter", "Neo4jAdapter", "CassandraAdapter", "RedisAdapter", "Influx3Adapter", "IrisAdapter")})
    monkeypatch.setattr(main, "import_module", factory)
    assert set(build_adapters(settings())) == set(diagnostico.MOTORES)
    def failing_import(name):
        if name.endswith("iris"):
            raise ImportError("driver ausente")
        return factory(name)
    monkeypatch.setattr(main, "import_module", failing_import)
    with pytest.raises(ImportError):
        build_adapters(settings(), ("influxdb", "iris"))
    clients[-1].close.assert_called_once()


def test_configuracion_ejemplo_y_puertos():
    from pathlib import Path
    config = Path(__file__).resolve().parents[3] / "config/configuracion-ejemplo.env"
    conf = Settings(_env_file=config)
    assert conf.cassandra_keyspace == "fixture2030_comentarios"
    assert conf.influx_mode == "v3"
    assert diagnostico.destinos(conf)["influxdb"][1] == 8181
    assert settings().influx_url == "http://localhost:8181"
    with pytest.raises(ValidationError):
        settings(influx_mode="v2")
    assert diagnostico.destinos(settings(influx_url="https://influx.test"), ("influxdb",))["influxdb"][1] == 443
    assert diagnostico.destinos(settings(mongo_uri="mongodb://host:invalido"), ("influxdb",))["influxdb"][1] == 8181


@pytest.mark.parametrize("resolution,minutes", [("1m", 1), ("5m", 5), ("15m", 15), ("1h", 60)])
def test_sql_conserva_campos_ventana_y_ultimo_valor(monkeypatch, resolution, minutes):
    adapter = Influx3Adapter(settings())
    sql_query = Mock(return_value=[])
    monkeypatch.setattr(adapter, "query_sql", sql_query)
    query = StatsQuery(desde="2030-06-08T16:00:00.123456-03:00", hasta="2030-06-08T16:03:00-03:00",
                       equipo="AAA", resolucion=resolution)
    assert adapter.statistics("P001", query) == []
    sql = sql_query.call_args.args[0]
    assert "selector_last(pases_completados_total, time)['value']" in sql
    assert "MAX(pases_completados_total)" not in sql
    assert f") + INTERVAL '{minutes} minutes' AS tiempo" in sql
    assert "2030-06-08T19:00:00.123456+00:00" in sql
    assert "time < TIMESTAMP '2030-06-08T19:03:00+00:00'" in sql
    assert "equipo_codigo = 'AAA'" in sql and "partido_id = 'P001'" in sql
    assert "LIMIT 1001" in sql
    assert "AVG(posesion_pct)" in sql and "SUM(tiros_intervalo)" in sql


@pytest.mark.parametrize("status", [400, 401, 403, 404, 500, 503])
def test_influx_http_error_se_traduce_a_503(monkeypatch, status):
    res = httpx.Response(status, text="respuesta privada", request=httpx.Request("GET", "http://influx.test"))
    monkeypatch.setattr(httpx, "get", Mock(return_value=res))
    with pytest.raises(ApiError) as error:
        Influx3Adapter(settings()).ping()
    assert error.value.status == 503
    assert error.value.dependency == "influxdb"
    assert "privada" not in str(error.value)


def test_ruta_influx_timeout_recuperacion_y_error_interno(monkeypatch):
    adapter = Influx3Adapter(settings())
    with TestClient(create_app(settings(), {"influxdb": adapter})) as client:
        params = {"desde": "2030-06-08T19:00:00Z", "hasta": "2030-06-08T20:00:00Z"}
        monkeypatch.setattr(httpx, "get", Mock(side_effect=httpx.ReadTimeout("token privado")))
        res = client.get("/api/v1/partidos/P001/estadisticas", params=params)
        assert res.status_code == 503 and res.json()["error"]["code"] == "dependencia_timeout"
        assert res.json()["error"]["request_id"] == res.headers["X-Request-ID"]
        assert "privado" not in res.text
        monkeypatch.setattr(httpx, "get", Mock(return_value=httpx.Response(200, json=[], request=httpx.Request("GET", "http://influx.test"))))
        res = client.get("/api/v1/partidos/P001/estadisticas", params=params)
        assert res.status_code == 200 and res.json()["data"]["items"] == []
        monkeypatch.setattr(httpx, "get", Mock(side_effect=RuntimeError("token privado")))
        res = client.get("/api/v1/partidos/P001/estadisticas", params=params)
        assert res.status_code == 500 and res.json()["error"]["code"] == "error_interno"
        assert "privado" not in res.text


def test_validacion_no_consulta_adaptador_y_preserva_rutas():
    adapter = Mock()
    with TestClient(create_app(settings(), {"influxdb": adapter})) as client:
        assert client.get("/api/v1/partidos/P001/estadisticas").status_code == 422
        adapter.statistics.assert_not_called()
        paths = set(client.get("/openapi.json").json()["paths"])
        assert paths == {"/health/live", "/api/v1/salud", "/api/v1/grafo", "/api/v1/equipos",
                         "/api/v1/equipos/{codigo}", "/api/v1/partidos/{partido_id}/eventos",
                         "/api/v1/partidos/{partido_id}/comentarios", "/api/v1/sesiones/{session_id}",
                         "/api/v1/partidos/{partido_id}/estadisticas", "/api/v1/objetos/partidos/{partido_id}"}
        assert client.get("/").status_code == 200


def test_cli_continua_tras_driver_ausente(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["validar_conectividad", "--mode", "native", "--json", "--origen", "host"])
    def probe(conf, motor):
        return {"estado": "skip" if motor == "cassandra" else "ok"}
    monkeypatch.setattr(diagnostico, "nativo_por_motor", probe)
    with pytest.raises(SystemExit) as exit_code:
        diagnostico.main()
    assert exit_code.value.code == 2
    report = json.loads(capsys.readouterr().out)
    assert set(report["resultados"]) == set(diagnostico.MOTORES)
    assert report["errores"] == 0 and report["omitidas"] == 1
    assert report["origen"] == "host"
    assert datetime.fromisoformat(report["fecha_utc"]).tzinfo == timezone.utc


def test_cli_configuracion_invalida_sin_filtrar_valores(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["validar_conectividad", "--partido", "secreto"])
    with pytest.raises(SystemExit) as exit_code:
        diagnostico.main()
    assert exit_code.value.code == 2
    assert "secreto" not in capsys.readouterr().out


def test_cli_api_conserva_salud_y_funcional_con_una_sola_consulta_salud(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["validar_conectividad", "--mode", "api", "--json"])
    health = response(200, {"data": {"estado": "ok", "dependencias": {
        motor: {"estado": "ok", "duracion_ms": 1} for motor in diagnostico.MOTORES}}})
    mocked_client = Mock()
    mocked_client.__enter__ = Mock(return_value=mocked_client)
    mocked_client.__exit__ = Mock(return_value=False)
    mocked_client.get.return_value = health
    monkeypatch.setattr(diagnostico.httpx, "Client", Mock(return_value=mocked_client))
    functional = Mock(return_value={"estado": "ok"})
    monkeypatch.setattr(diagnostico, "comprobar_funcional", functional)
    with pytest.raises(SystemExit) as exit_code:
        diagnostico.main()
    assert exit_code.value.code == 0
    mocked_client.get.assert_called_once_with("/api/v1/salud")
    assert functional.call_count == 6
    report = json.loads(capsys.readouterr().out)
    assert all(set(layer) == {"api", "api_funcional"} for layer in report["resultados"].values())


def test_ventana_de_otro_contexto_no_se_acepta():
    params = {"desde": "2030-06-08T19:00:00Z", "hasta": "2030-06-08T20:00:00Z", "resolucion": "5m"}
    data = {"partido_id": "P001", **params, "resolucion": "1h", "items": [], "truncado": False}
    with client_for(response(200, {"data": data})) as client:
        result = diagnostico.comprobar_funcional(client, "influxdb", "/api/v1/partidos/P001/estadisticas", params)
    assert result["estado"] == "error"


def test_salud_http_y_cuerpo_inconsistentes_no_se_aceptan():
    res = response(200, {"data": {"estado": "degradado", "dependencias": {
        "redis": {"estado": "no_disponible", "duracion_ms": 1}}}})
    with client_for(res) as client:
        assert diagnostico.comprobar_api(client, "redis")["categoria"] == "configuracion_o_contrato_invalido"


def test_query_http_v3_no_publica_token_y_ping_limitado(monkeypatch, caplog):
    token = "MARCADOR_PRIVADO_DE_PRUEBA"
    request = httpx.Request("GET", "http://influx.test/api/v3/query_sql")
    get = Mock(return_value=httpx.Response(200, json=[], request=request))
    monkeypatch.setattr(httpx, "get", get)
    caplog.set_level("INFO", logger="fixture.api")
    adapter = Influx3Adapter(settings(influx_token=token))
    assert adapter.ping() is True
    assert get.call_args.args[0].endswith("/api/v3/query_sql")
    assert get.call_args.kwargs["params"]["q"] == "SELECT time FROM estadisticas_equipo LIMIT 1"
    assert get.call_args.kwargs["params"]["db"] == "fixture2030"
    assert get.call_args.kwargs["headers"]["Authorization"] == f"Bearer {token}"
    assert token not in caplog.text
