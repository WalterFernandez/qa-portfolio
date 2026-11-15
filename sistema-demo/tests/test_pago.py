"""Pasos 6-7 del flujo: el cliente firma y paga; el servicio asigna el delivery.

Técnicas ISTQB: transición de estados COTIZADO -> PAGADO -> ASIGNADO y los intentos
inválidos (firmar o pagar fuera de COTIZADO) (CTFL v4.0 §4.2.4); partición de
equivalencia y valores límite sobre la imagen de la firma (§4.2.1 y §4.2.2);
tabla de decisión estado x firma para el pago (§4.2.3). La idempotencia del pago
cubre el "doble clic en Pagar" (Review Focus #1).
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from conftest import DATOS_OK, FIRMA_OK
from delivery.config import Config
from delivery.main import crear_app

PREFIJO = "data:image/png;base64,"
MAX_FIRMA = 200_000


def _firmar(cliente, pedido_id, imagen=FIRMA_OK):
    return cliente.post(f"/pedidos/{pedido_id}/firma", json={"imagen": imagen})


def _pagar(cliente, pedido_id):
    return cliente.post(f"/pedidos/{pedido_id}/pago")


def _base(tmp_path):
    con = sqlite3.connect(tmp_path / "t.db")
    con.row_factory = sqlite3.Row
    return con


def _forzar_estado(tmp_path, pedido_id, estado):
    """Prepara el pedido en un estado al que todavía no se llega por la API (Task 7)."""
    con = _base(tmp_path)
    with con:
        con.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (estado, pedido_id))
    con.close()


def _mensajes_delivery(cliente, pedido_id):
    return cliente.get("/mensajes", params={"destino": "delivery", "pedido_id": pedido_id}).json()


# --- Firma (Paso 6) ---------------------------------------------------------


def test_firmar_marca_el_pedido_sin_cambiar_de_estado(cliente, pedido_cotizado):
    r = _firmar(cliente, pedido_cotizado)
    assert r.status_code == 200
    p = r.json()
    assert p["firmado"] is True
    assert p["estado"] == "COTIZADO"
    assert "firma" not in p  # la imagen no viaja en el JSON del pedido
    assert [e["estado"] for e in p["eventos"]][-1] == "COTIZADO"


def test_volver_a_firmar_antes_de_pagar_reemplaza_la_firma(cliente, pedido_cotizado, tmp_path):
    _firmar(cliente, pedido_cotizado)
    otra = PREFIJO + "QUJD"
    assert _firmar(cliente, pedido_cotizado, otra).status_code == 200
    con = _base(tmp_path)
    guardada = con.execute("SELECT firma FROM pedidos WHERE id = ?", (pedido_cotizado,)).fetchone()
    con.close()
    assert guardada["firma"] == otra


@pytest.mark.parametrize(
    "imagen,esperado",
    [
        pytest.param(FIRMA_OK, 200, id="png-valido"),
        pytest.param("data:image/jpeg;base64,/9j/4AAQ", 422, id="jpeg"),
        pytest.param("iVBORw0KGgo=", 422, id="sin-prefijo"),
        pytest.param(PREFIJO, 422, id="solo-prefijo-vacio"),
        pytest.param(PREFIJO + "no es base64!", 422, id="caracteres-fuera-de-base64"),
        pytest.param(" " + FIRMA_OK, 422, id="espacio-adelante"),
        pytest.param(PREFIJO + "A" * (MAX_FIRMA - len(PREFIJO)), 200, id="justo-200000"),
        pytest.param(PREFIJO + "A" * (MAX_FIRMA - len(PREFIJO) + 1), 422, id="200001"),
    ],
)
def test_formato_y_largo_de_la_firma(cliente, pedido_cotizado, imagen, esperado):
    assert _firmar(cliente, pedido_cotizado, imagen).status_code == esperado


@pytest.mark.parametrize("body", [{}, {"imagen": FIRMA_OK, "firmado": True}, {"imagen": None}])
def test_body_de_firma_invalido_da_422(cliente, pedido_cotizado, body):
    assert cliente.post(f"/pedidos/{pedido_cotizado}/firma", json=body).status_code == 422


def test_firma_rechazada_no_marca_el_pedido(cliente, pedido_cotizado):
    _firmar(cliente, pedido_cotizado, "data:image/jpeg;base64,/9j/4AAQ")
    assert cliente.get(f"/pedidos/{pedido_cotizado}").json()["firmado"] is False


def test_firmar_antes_de_cotizar_da_409(cliente, pedido_nuevo):
    r = _firmar(cliente, pedido_nuevo)
    assert r.status_code == 409
    assert r.json()["detail"]["error"] == "transicion_invalida"
    assert r.json()["detail"]["estado_actual"] == "LINK_ENVIADO"
    assert cliente.get(f"/pedidos/{pedido_nuevo}").json()["firmado"] is False


def test_firmar_despues_de_pagar_da_409(cliente, pedido_cotizado):
    _firmar(cliente, pedido_cotizado)
    _pagar(cliente, pedido_cotizado)
    r = _firmar(cliente, pedido_cotizado, PREFIJO + "QUJD")
    assert r.status_code == 409
    assert r.json()["detail"]["estado_actual"] == "ASIGNADO"


# --- Pago (Paso 6) y asignación (Paso 7) ------------------------------------


def test_pagar_sin_firma_da_409_y_no_avanza(cliente, pedido_cotizado):
    r = _pagar(cliente, pedido_cotizado)
    assert r.status_code == 409
    assert r.json()["detail"]["error"] == "firma_requerida"
    p = cliente.get(f"/pedidos/{pedido_cotizado}").json()
    assert p["estado"] == "COTIZADO"
    assert [e["estado"] for e in p["eventos"]].count("PAGADO") == 0
    assert _mensajes_delivery(cliente, pedido_cotizado) == []


def test_pagar_antes_de_cotizar_da_409_transicion(cliente, pedido_nuevo):
    # Sin firma y en LINK_ENVIADO: manda el estado, no la firma.
    r = _pagar(cliente, pedido_nuevo)
    assert r.status_code == 409
    assert r.json()["detail"]["error"] == "transicion_invalida"
    assert r.json()["detail"]["estado_actual"] == "LINK_ENVIADO"


def test_pago_asigna_delivery_y_le_manda_whatsapp(cliente, pedido_cotizado):
    _firmar(cliente, pedido_cotizado)
    r = _pagar(cliente, pedido_cotizado)
    assert r.status_code == 200
    p = r.json()
    assert p["estado"] == "ASIGNADO"
    assert [(e["estado"], e["actor"]) for e in p["eventos"]][-2:] == [
        ("PAGADO", "cliente"),
        ("ASIGNADO", "servicio"),
    ]
    msgs = _mensajes_delivery(cliente, pedido_cotizado)
    assert len(msgs) == 1
    assert msgs[0]["link"] == f"/delivery/pedido/{pedido_cotizado}"
    assert msgs[0]["telefono"] == Config().delivery_telefono
    assert msgs[0]["canal"] == "whatsapp"
    assert "Av. Siempre Viva 742" in msgs[0]["texto"]


def test_pago_doble_no_duplica(cliente, pedido_cotizado):
    _firmar(cliente, pedido_cotizado)
    primero = _pagar(cliente, pedido_cotizado).json()
    r = _pagar(cliente, pedido_cotizado)
    assert r.status_code == 200
    assert r.json() == primero
    assert [e["estado"] for e in r.json()["eventos"]].count("PAGADO") == 1
    assert len(_mensajes_delivery(cliente, pedido_cotizado)) == 1


@pytest.mark.parametrize(
    "estado",
    ["PAGADO", "ASIGNADO", "RETIRADO", "EN_CAMINO", "EN_PUERTA", "RECIBIDO", "ENTREGADO", "CERRADO"],
)
def test_pagar_en_estado_pagado_o_posterior_no_hace_nada(cliente, pedido_cotizado, tmp_path, estado):
    _firmar(cliente, pedido_cotizado)
    _forzar_estado(tmp_path, pedido_cotizado, estado)
    antes = cliente.get(f"/pedidos/{pedido_cotizado}").json()
    r = _pagar(cliente, pedido_cotizado)
    assert r.status_code == 200
    assert r.json() == antes
    assert _mensajes_delivery(cliente, pedido_cotizado) == []


def test_pagar_pedido_cancelado_da_409(cliente, pedido_cotizado, tmp_path):
    _firmar(cliente, pedido_cotizado)
    _forzar_estado(tmp_path, pedido_cotizado, "CANCELADO")
    r = _pagar(cliente, pedido_cotizado)
    assert r.status_code == 409
    assert r.json()["detail"] == {
        "error": "transicion_invalida", "estado_actual": "CANCELADO", "destino": "PAGADO"}


@pytest.mark.parametrize("ruta", ["firma", "pago"])
def test_pedido_inexistente_da_404(cliente, ruta):
    body = {"imagen": FIRMA_OK} if ruta == "firma" else None
    r = cliente.post(f"/pedidos/999/{ruta}", json=body)
    assert r.status_code == 404
    assert r.json() == {"detail": {"error": "pedido_no_encontrado"}}


# --- Base existente ---------------------------------------------------------


def test_base_anterior_sin_columna_firma_se_actualiza_al_arrancar(tmp_path):
    """Una base creada antes de la Task 6 no tiene `firma`: arrancar la app la agrega."""
    cfg = Config(db_path=tmp_path / "t.db")
    TestClient(crear_app(cfg))
    con = _base(tmp_path)
    with con:
        con.execute("ALTER TABLE pedidos DROP COLUMN firma")
    con.close()
    cliente = TestClient(crear_app(cfg))
    pid = cliente.post("/pedidos", json={"telefono": "1122334455"}).json()["id"]
    cliente.put(f"/pedidos/{pid}", json=DATOS_OK)
    assert _firmar(cliente, pid).status_code == 200
