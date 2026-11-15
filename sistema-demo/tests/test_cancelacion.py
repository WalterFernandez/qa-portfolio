"""Cancelación del pedido: quién puede cancelar y hasta cuándo.

Técnica ISTQB: tabla de decisión (CTFL v4.0 §4.2.3). Condiciones: estado de partida
(antes del pago / después del pago / final) y quién cancela (cliente / servicio).
Acción: 200 y CANCELADO, o 409 `no_cancelable` con un mensaje para cada caso.
Partición de equivalencia sobre `por` (§4.2.1): valores válidos y uno inválido -> 422.

| Regla | Estado de partida | Por       | Resultado                                     |
|-------|-------------------|-----------|-----------------------------------------------|
| R1    | LINK_ENVIADO      | cliente   | 200, CANCELADO, cancelado_por = cliente       |
| R2    | COTIZADO          | servicio  | 200, CANCELADO, cancelado_por = servicio      |
| R3    | ASIGNADO          | cliente   | 409 no_cancelable "ya fue pagado"             |
| R4    | CERRADO           | servicio  | 409 no_cancelable "ya está finalizado"        |
| R5    | CANCELADO         | cliente   | 409 no_cancelable "ya está finalizado"        |
"""

import pytest

from conftest import DATOS_OK, FIRMA_OK, avanzar_hasta

YA_PAGADO = "No se puede cancelar un pedido que ya fue pagado"
FINALIZADO = "El pedido ya está finalizado"


def _cancelar(cliente, pedido_id, por):
    return cliente.post(f"/pedidos/{pedido_id}/cancelar", json={"por": por})


def _llevar_a(cliente, estado) -> int:
    """Pedido nuevo llevado por la API hasta `estado`."""
    pid = cliente.post("/pedidos", json={"telefono": "1122334455"}).json()["id"]
    if estado == "LINK_ENVIADO":
        return pid
    if estado == "CANCELADO":
        assert _cancelar(cliente, pid, "servicio").status_code == 200
        return pid
    cliente.put(f"/pedidos/{pid}", json=DATOS_OK)
    if estado == "COTIZADO":
        return pid
    cliente.post(f"/pedidos/{pid}/firma", json={"imagen": FIRMA_OK})
    cliente.post(f"/pedidos/{pid}/pago")
    if estado != "ASIGNADO":
        avanzar_hasta(cliente, pid, estado)
    return pid


@pytest.mark.parametrize(
    "estado,por",
    [
        pytest.param("LINK_ENVIADO", "cliente", id="R1"),
        pytest.param("COTIZADO", "servicio", id="R2"),
    ],
)
def test_cancelar_antes_del_pago(cliente, estado, por):
    pid = _llevar_a(cliente, estado)
    r = _cancelar(cliente, pid, por)
    assert r.status_code == 200
    p = r.json()
    assert p["estado"] == "CANCELADO"
    assert p["cancelado_por"] == por
    assert p["eventos"][-1]["estado"] == "CANCELADO"
    assert p["eventos"][-1]["actor"] == por


@pytest.mark.parametrize(
    "estado,por,mensaje",
    [
        pytest.param("ASIGNADO", "cliente", YA_PAGADO, id="R3"),
        pytest.param("CERRADO", "servicio", FINALIZADO, id="R4"),
        pytest.param("CANCELADO", "cliente", FINALIZADO, id="R5"),
    ],
)
def test_no_se_puede_cancelar(cliente, estado, por, mensaje):
    pid = _llevar_a(cliente, estado)
    antes = cliente.get(f"/pedidos/{pid}").json()
    r = _cancelar(cliente, pid, por)
    assert r.status_code == 409
    assert r.json()["detail"] == {
        "error": "no_cancelable", "estado_actual": estado, "mensaje": mensaje}
    assert cliente.get(f"/pedidos/{pid}").json() == antes  # no cambió nada


@pytest.mark.parametrize(
    "estado", ["PAGADO_Y_EN_CAMINO", "EN_PUERTA", "RECIBIDO"],
)
def test_despues_del_pago_siempre_dice_ya_pagado(cliente, estado):
    # Clases de equivalencia "pagado pero no finalizado": un representante de cada tramo.
    destino = "EN_CAMINO" if estado == "PAGADO_Y_EN_CAMINO" else estado
    pid = _llevar_a(cliente, destino)
    r = _cancelar(cliente, pid, "cliente")
    assert r.status_code == 409
    assert r.json()["detail"]["mensaje"] == YA_PAGADO


@pytest.mark.parametrize(
    "body",
    [
        pytest.param({"por": "delivery"}, id="delivery-no-cancela"),
        pytest.param({"por": "Cliente"}, id="mayuscula"),
        pytest.param({"por": ""}, id="vacio"),
        pytest.param({}, id="sin-por"),
        pytest.param({"por": "cliente", "motivo": "x"}, id="campo-de-mas"),
    ],
)
def test_por_invalido_da_422(cliente, pedido_nuevo, body):
    r = cliente.post(f"/pedidos/{pedido_nuevo}/cancelar", json=body)
    assert r.status_code == 422
    assert cliente.get(f"/pedidos/{pedido_nuevo}").json()["estado"] == "LINK_ENVIADO"


def test_cancelado_no_se_puede_pagar(cliente):
    pid = _llevar_a(cliente, "COTIZADO")
    cliente.post(f"/pedidos/{pid}/firma", json={"imagen": FIRMA_OK})
    _cancelar(cliente, pid, "cliente")
    r = cliente.post(f"/pedidos/{pid}/pago")
    assert r.status_code == 409
    assert r.json()["detail"]["estado_actual"] == "CANCELADO"
