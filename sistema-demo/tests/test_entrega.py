"""Pasos 8-13 del flujo: el delivery retira, va en camino, llega, y las dos partes confirman.

Técnicas ISTQB: transición de estados ASIGNADO -> RETIRADO -> EN_CAMINO -> EN_PUERTA
-> RECIBIDO/ENTREGADO -> CERRADO, con las transiciones inválidas (retirar sin pagar,
confirmar dos veces) (CTFL v4.0 §4.2.4). Las dos confirmaciones en cualquier orden
son una cobertura de transiciones de a pares ("0-switch" sobre RECIBIDO y ENTREGADO).
El flujo completo es el caso de prueba de extremo a extremo de los 13 pasos.
"""

import pytest

from conftest import RECORRIDO, avanzar_hasta


def _post(cliente, pedido_id, ruta):
    return cliente.post(f"/pedidos/{pedido_id}/{ruta}")


def _estados(pedido):
    return [e["estado"] for e in pedido["eventos"]]


def _mensajes_cliente(cliente, pedido_id):
    return cliente.get("/mensajes", params={"destino": "cliente", "pedido_id": pedido_id}).json()


# --- Extremo a extremo ------------------------------------------------------


def test_flujo_completo_los_13_pasos(cliente, pedido_asignado):
    for ruta, _ in RECORRIDO:
        assert _post(cliente, pedido_asignado, ruta).status_code == 200

    p = cliente.get(f"/pedidos/{pedido_asignado}").json()
    assert p["estado"] == "CERRADO"
    assert p["recibido_cliente"] is True
    assert p["entregado_delivery"] is True
    assert [(e["estado"], e["actor"]) for e in p["eventos"]] == [
        ("INICIADO", "cliente"),
        ("LINK_ENVIADO", "servicio"),
        ("DATOS_CARGADOS", "cliente"),
        ("COTIZADO", "servicio"),
        ("PAGADO", "cliente"),
        ("ASIGNADO", "servicio"),
        ("RETIRADO", "delivery"),
        ("EN_CAMINO", "servicio"),
        ("EN_PUERTA", "delivery"),
        ("RECIBIDO", "cliente"),
        ("ENTREGADO", "delivery"),
        ("CERRADO", "servicio"),
    ]
    todos = cliente.get("/mensajes", params={"pedido_id": pedido_asignado}).json()
    assert [m["destino"] for m in todos] == ["cliente", "cliente", "delivery", "cliente"]
    assert todos[-1]["texto"] == "Tu pedido está en camino"


# --- Pasos 8-10: retiro, en camino, en la puerta ----------------------------


def test_retirar_avisa_al_cliente_y_queda_en_camino(cliente, pedido_asignado):
    r = _post(cliente, pedido_asignado, "retirado")
    assert r.status_code == 200
    p = r.json()
    assert p["estado"] == "EN_CAMINO"
    assert [(e["estado"], e["actor"]) for e in p["eventos"]][-2:] == [
        ("RETIRADO", "delivery"),
        ("EN_CAMINO", "servicio"),
    ]
    aviso = _mensajes_cliente(cliente, pedido_asignado)[-1]
    assert aviso["texto"] == "Tu pedido está en camino"
    assert aviso["link"] == f"/cliente/pedido/{pedido_asignado}"


def test_retirado_antes_de_pagar_da_409(cliente, pedido_cotizado):
    r = _post(cliente, pedido_cotizado, "retirado")
    assert r.status_code == 409
    assert r.json()["detail"] == {
        "error": "transicion_invalida", "estado_actual": "COTIZADO", "destino": "RETIRADO"}
    assert len(_mensajes_cliente(cliente, pedido_cotizado)) == 2  # sin aviso "en camino"


def test_retirar_dos_veces_da_409_y_no_repite_el_aviso(cliente, pedido_asignado):
    _post(cliente, pedido_asignado, "retirado")
    r = _post(cliente, pedido_asignado, "retirado")
    assert r.status_code == 409
    assert r.json()["detail"]["estado_actual"] == "EN_CAMINO"
    textos = [m["texto"] for m in _mensajes_cliente(cliente, pedido_asignado)]
    assert textos.count("Tu pedido está en camino") == 1


def test_en_puerta_antes_de_retirar_da_409(cliente, pedido_asignado):
    r = _post(cliente, pedido_asignado, "en-puerta")
    assert r.status_code == 409
    assert r.json()["detail"]["estado_actual"] == "ASIGNADO"


def test_en_puerta(cliente, pedido_asignado):
    avanzar_hasta(cliente, pedido_asignado, "EN_CAMINO")
    r = _post(cliente, pedido_asignado, "en-puerta")
    assert r.status_code == 200
    assert r.json()["estado"] == "EN_PUERTA"
    assert r.json()["eventos"][-1]["actor"] == "delivery"


# --- Pasos 11-13: confirmaciones y cierre -----------------------------------


@pytest.mark.parametrize("ruta", ["recibido", "entregado"])
def test_confirmar_antes_de_llegar_da_409(cliente, pedido_asignado, ruta):
    avanzar_hasta(cliente, pedido_asignado, "EN_CAMINO")
    r = _post(cliente, pedido_asignado, ruta)
    assert r.status_code == 409
    assert r.json()["detail"]["estado_actual"] == "EN_CAMINO"


def test_cerrar_requiere_las_dos_confirmaciones(cliente, pedido_asignado):
    avanzar_hasta(cliente, pedido_asignado, "EN_PUERTA")
    p = _post(cliente, pedido_asignado, "recibido").json()
    assert p["estado"] == "RECIBIDO"
    assert p["recibido_cliente"] is True
    assert p["entregado_delivery"] is False
    assert "CERRADO" not in _estados(p)


def test_entregado_antes_que_recibido_tambien_cierra(cliente, pedido_asignado):
    avanzar_hasta(cliente, pedido_asignado, "EN_PUERTA")
    p = _post(cliente, pedido_asignado, "entregado").json()
    assert p["estado"] == "ENTREGADO"
    assert (p["recibido_cliente"], p["entregado_delivery"]) == (False, True)

    p = _post(cliente, pedido_asignado, "recibido").json()
    assert p["estado"] == "CERRADO"
    assert [(e["estado"], e["actor"]) for e in p["eventos"]][-3:] == [
        ("ENTREGADO", "delivery"),
        ("RECIBIDO", "cliente"),
        ("CERRADO", "servicio"),
    ]


@pytest.mark.parametrize(
    "primera,repetida,estado",
    [
        pytest.param("recibido", "recibido", "RECIBIDO", id="cliente-dos-veces"),
        pytest.param("entregado", "entregado", "ENTREGADO", id="delivery-dos-veces"),
    ],
)
def test_confirmacion_repetida_da_409(cliente, pedido_asignado, primera, repetida, estado):
    avanzar_hasta(cliente, pedido_asignado, "EN_PUERTA")
    _post(cliente, pedido_asignado, primera)
    r = _post(cliente, pedido_asignado, repetida)
    assert r.status_code == 409
    assert r.json()["detail"]["error"] == "transicion_invalida"
    assert r.json()["detail"]["estado_actual"] == estado
    assert _estados(cliente.get(f"/pedidos/{pedido_asignado}").json()).count(estado) == 1


@pytest.mark.parametrize("ruta", ["recibido", "entregado"])
def test_confirmar_un_pedido_cerrado_da_409(cliente, pedido_asignado, ruta):
    avanzar_hasta(cliente, pedido_asignado, "CERRADO")
    r = _post(cliente, pedido_asignado, ruta)
    assert r.status_code == 409
    assert r.json()["detail"]["estado_actual"] == "CERRADO"
