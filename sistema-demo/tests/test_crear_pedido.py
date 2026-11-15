"""Pasos 1-3 del flujo: crear el pedido y enviarle el link al cliente por WhatsApp simulado.

Técnicas ISTQB: partición de equivalencia y valores límite sobre el teléfono
(CTFL v4.0 §4.2.1 y §4.2.2), y prueba de transición de estados en el alta
(INICIADO -> LINK_ENVIADO, §4.2.4).
"""

import pytest
from fastapi.testclient import TestClient

from delivery.config import Config
from delivery.estados import Estado, TransicionInvalida
from delivery.main import crear_app


def test_crear_pedido_envia_link_por_whatsapp(cliente):
    r = cliente.post("/pedidos", json={"telefono": "+5215512345678"})
    assert r.status_code == 201
    p = r.json()
    assert p["estado"] == "LINK_ENVIADO"
    assert [e["estado"] for e in p["eventos"]] == ["INICIADO", "LINK_ENVIADO"]
    assert [e["actor"] for e in p["eventos"]] == ["cliente", "servicio"]
    msgs = cliente.get("/mensajes", params={"destino": "cliente", "pedido_id": p["id"]}).json()
    assert len(msgs) == 1
    assert msgs[0]["link"] == f"/cliente/pedido/{p['id']}"
    assert msgs[0]["canal"] == "whatsapp"
    assert msgs[0]["telefono"] == "+5215512345678"


def test_pedido_nuevo_tiene_el_json_completo_y_vacio(cliente):
    p = cliente.post("/pedidos", json={"telefono": "1122334455"}).json()
    assert set(p) == {
        "id", "telefono", "estado", "items", "direccion", "lat", "lng", "total",
        "demora_min", "firmado", "recibido_cliente", "entregado_delivery",
        "cancelado_por", "eventos",
    }
    assert p["items"] == []
    assert p["total"] is None
    assert p["firmado"] is False
    assert p["recibido_cliente"] is False
    assert p["entregado_delivery"] is False


@pytest.mark.parametrize(
    "tel",
    [
        pytest.param("12345678", id="limite-8-digitos"),
        pytest.param("+123456789012345", id="limite-15-digitos-con-mas"),
    ],
)
def test_telefono_en_el_limite_es_valido(cliente, tel):
    assert cliente.post("/pedidos", json={"telefono": tel}).status_code == 201


@pytest.mark.parametrize(
    "tel",
    [
        pytest.param("", id="vacio"),
        pytest.param("1234567", id="7-digitos"),
        pytest.param("+54911abc", id="con-letras"),
        pytest.param("1" * 16, id="16-digitos"),
    ],
)
def test_telefono_invalido_da_422(cliente, tel):
    assert cliente.post("/pedidos", json={"telefono": tel}).status_code == 422


def test_campo_de_mas_da_422(cliente):
    r = cliente.post("/pedidos", json={"telefono": "1122334455", "estado": "PAGADO"})
    assert r.status_code == 422


def test_pedido_inexistente_da_404(cliente):
    r = cliente.get("/pedidos/999")
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "pedido_no_encontrado"


def test_listar_pedidos_mas_nuevo_primero_y_sin_eventos(cliente):
    a = cliente.post("/pedidos", json={"telefono": "1111111111"}).json()
    b = cliente.post("/pedidos", json={"telefono": "2222222222"}).json()
    lista = cliente.get("/pedidos").json()
    assert [p["id"] for p in lista] == [b["id"], a["id"]]
    assert all("eventos" not in p for p in lista)


def test_pedido_sobrevive_reinicio(tmp_path):
    cfg = Config(db_path=tmp_path / "t.db")
    pid = TestClient(crear_app(cfg)).post("/pedidos", json={"telefono": "1122334455"}).json()["id"]
    otra = TestClient(crear_app(cfg))
    r = otra.get(f"/pedidos/{pid}")
    assert r.status_code == 200
    assert r.json()["estado"] == "LINK_ENVIADO"


def test_timestamps_en_utc_con_z(cliente):
    p = cliente.post("/pedidos", json={"telefono": "1122334455"}).json()
    assert all(e["ocurrido_en"].endswith("Z") for e in p["eventos"])


def test_transicion_invalida_se_traduce_a_409(tmp_path):
    """El manejador de main.py convierte TransicionInvalida en 409 con el detalle.

    Todavía no hay rutas que muevan el estado (llegan en la Task 5), así que se
    monta una ruta de prueba que lanza la excepción.
    """
    app = crear_app(Config(db_path=tmp_path / "t.db"))

    @app.get("/_forzar_409")
    def _forzar():
        raise TransicionInvalida(Estado.PAGADO, Estado.COTIZADO)

    r = TestClient(app).get("/_forzar_409")
    assert r.status_code == 409
    assert r.json() == {
        "detail": {"error": "transicion_invalida", "estado_actual": "PAGADO", "destino": "COTIZADO"}
    }
