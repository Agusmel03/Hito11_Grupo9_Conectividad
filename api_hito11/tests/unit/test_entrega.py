"""Verificacion local del procedimiento; no requiere ni reemplaza Docker."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.schemas.models import StatsQuery
from verificar_agregaciones import comparar, referencia, verificar


spec = importlib.util.spec_from_file_location("entrega", Path(__file__).resolve().parents[3] / "scripts/verificar_entrega.py")
entrega = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entrega)


def consulta():
    return StatsQuery(desde="2030-06-08T19:00:00Z", hasta="2030-06-08T19:05:00Z")


def test_referencia_ultimo_valor_no_es_maximo_y_nulos():
    puntos = [
        {"time": "2030-06-08T19:00:00Z", "equipo_codigo": "AAA", "sede_id": "S001",
         "posesion_pct": 40, "pases_completados_total": 90, "tiros_intervalo": 1},
        {"time": "2030-06-08T19:04:59Z", "equipo_codigo": "AAA", "sede_id": "S001",
         "posesion_pct": 60, "pases_completados_total": 20, "tiros_intervalo": 2},
        {"time": "2030-06-08T19:05:00Z", "equipo_codigo": "AAA", "sede_id": "S001",
         "posesion_pct": 999, "pases_completados_total": 999, "tiros_intervalo": 999},
    ]
    esperado = referencia(puntos, consulta())
    fila = {"tiempo": "2030-06-08T19:05:00Z", "equipo_codigo": "AAA", "sede_id": "S001",
            "posesion_pct": 50, "pases_completados_total": 20, "tiros_intervalo": 3,
            "recuperaciones_intervalo": None}
    assert comparar(esperado, [fila]) == 0
    assert comparar(esperado, [fila, fila]) == 1
    assert comparar(esperado, [{**fila, "pases_completados_total": 90}]) == 1


@pytest.mark.parametrize("filas", [[], [{}] * 10001])
def test_sin_muestra_completa_no_declara_agregaciones_ok(filas):
    adapter = Mock()
    adapter.query_sql.return_value = filas
    assert verificar(adapter, "P001", consulta())["estado"] == "no_probado"
    adapter.statistics.assert_not_called()
    sql = adapter.query_sql.call_args.args[0]
    assert sql.lstrip().startswith("SELECT") and "LIMIT 10001" in sql


def test_docker_ausente_no_inventa_resultados(monkeypatch):
    command = Mock(return_value=SimpleNamespace(returncode=0, stdout=""))
    monkeypatch.setattr(entrega, "ejecutar", command)
    monkeypatch.setattr(entrega.shutil, "which", lambda _: None)
    result = entrega.verificar(SimpleNamespace())
    assert result["estado"] == "no_probado" and result["motivo"] == "docker_no_instalado"
    assert all(c.args[0][0] == "git" for c in command.call_args_list)


def test_codigo_viejo_impide_validar_otra_revision(monkeypatch):
    monkeypatch.setattr(entrega.shutil, "which", lambda _: "docker")
    monkeypatch.setattr(entrega, "ejecutar", Mock(return_value=SimpleNamespace(returncode=0, stdout="")))
    monkeypatch.setattr(entrega, "inventario", lambda _: {"estado": "ok"})
    monkeypatch.setattr(entrega, "comprobar_codigo", lambda _: {"estado": "error"})
    probe = Mock()
    monkeypatch.setattr(entrega, "salida_json", probe)
    result = entrega.verificar(SimpleNamespace(contenedor_api="api", motores=["redis"], ruta_api="/app"))
    assert result["estado"] == "no_probado"
    assert result["motivo"].startswith("actualizar_solo_codigo_api")
    probe.assert_not_called()


def test_huella_equivalente_con_crlf_y_bom():
    assert entrega.huella(b"print(1)\n") == entrega.huella(b"\xef\xbb\xbfprint(1)\r\n")
