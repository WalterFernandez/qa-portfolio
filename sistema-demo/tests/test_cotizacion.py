"""Pasos 4-5 del flujo: el cliente carga sus datos y el servicio le manda la cotización.

Técnicas ISTQB: partición de equivalencia y valores límite sobre cantidad, cantidad
de items, dirección y coordenadas (CTFL v4.0 §4.2.1 y §4.2.2); tabla de decisión
para la demora (§4.2.3); transición de estados LINK_ENVIADO -> DATOS_CARGADOS ->
COTIZADO y el intento inválido de cargar dos veces (§4.2.4).
"""

import pytest

from conftest import DATOS_OK


def _cargar(cliente, pedido_id, **cambios):
    return cliente.put(f"/pedidos/{pedido_id}", json={**DATOS_OK, **cambios})


def _items(*pares):
    return [{"plato_id": p, "cantidad": c} for p, c in pares]


# --- Camino feliz -----------------------------------------------------------


def test_total_lo_calcula_el_servidor(cliente, pedido_nuevo):
    r = _cargar(cliente, pedido_nuevo)
    p = r.json()
    assert r.status_code == 200
    assert p["estado"] == "COTIZADO"
    assert p["total"] == 2 * 9000 + 4500
    assert p["demora_min"] == 35
    assert p["items"] == [
        {"plato_id": 1, "nombre": "Empanadas (docena)", "cantidad": 2,
         "precio_unitario": 9000, "subtotal": 18000},
        {"plato_id": 4, "nombre": "Flan casero", "cantidad": 1,
         "precio_unitario": 4500, "subtotal": 4500},
    ]
    assert (p["direccion"], p["lat"], p["lng"]) == ("Av. Siempre Viva 742", -34.6, -58.4)


def test_eventos_del_paso_4_y_5_en_orden_y_con_su_actor(cliente, pedido_nuevo):
    eventos = _cargar(cliente, pedido_nuevo).json()["eventos"]
    assert [(e["estado"], e["actor"]) for e in eventos] == [
        ("INICIADO", "cliente"),
        ("LINK_ENVIADO", "servicio"),
        ("DATOS_CARGADOS", "cliente"),
        ("COTIZADO", "servicio"),
    ]


def test_cotizacion_llega_al_cliente_por_whatsapp(cliente, pedido_nuevo):
    _cargar(cliente, pedido_nuevo)
    msgs = cliente.get("/mensajes", params={"destino": "cliente", "pedido_id": pedido_nuevo}).json()
    assert len(msgs) == 2  # el link del Paso 3 y la cotización
    assert msgs[1]["texto"] == "Total $22500 - demora 35 min"
    assert msgs[1]["link"] is None
    assert msgs[1]["telefono"] == "1122334455"


def test_coordenadas_son_opcionales(cliente, pedido_nuevo):
    r = cliente.put(f"/pedidos/{pedido_nuevo}", json={
        "items": DATOS_OK["items"], "direccion": "Calle 1"})
    assert r.status_code == 200
    assert (r.json()["lat"], r.json()["lng"]) == (None, None)


# --- Demora: tabla de decisión (unidades -> minutos) ------------------------


@pytest.mark.parametrize(
    "items,demora",
    [
        pytest.param(_items((1, 1)), 30, id="1-unidad"),
        pytest.param(_items((1, 2)), 30, id="2-unidades-sin-recargo"),
        pytest.param(_items((1, 3)), 35, id="3-unidades-primer-recargo"),
        pytest.param(_items((1, 7)), 55, id="7-unidades"),
        pytest.param(_items((1, 8)), 60, id="8-unidades-llega-al-tope"),
        pytest.param(_items((1, 9)), 60, id="9-unidades-pasa-el-tope"),
        pytest.param(_items((1, 10), (2, 10), (3, 10), (4, 10)), 60, id="40-unidades-tope"),
    ],
)
def test_demora_por_unidades_con_tope_de_60(cliente, pedido_nuevo, items, demora):
    p = _cargar(cliente, pedido_nuevo, items=items).json()
    assert p["demora_min"] == demora


# --- Contrato: el cliente no manda el total ni campos inventados -------------


@pytest.mark.parametrize("extra", [{"total": 1}, {"estado": "PAGADO"}, {"descuento": 50}])
def test_campo_de_mas_da_422_y_no_toca_el_pedido(cliente, pedido_nuevo, extra):
    r = _cargar(cliente, pedido_nuevo, **extra)
    assert r.status_code == 422
    p = cliente.get(f"/pedidos/{pedido_nuevo}").json()
    assert p["estado"] == "LINK_ENVIADO"
    assert p["total"] is None


# --- Valores límite ---------------------------------------------------------


@pytest.mark.parametrize("cantidad,esperado", [(0, 422), (1, 200), (10, 200), (11, 422)])
def test_valores_limite_de_cantidad(cliente, pedido_nuevo, cantidad, esperado):
    r = _cargar(cliente, pedido_nuevo, items=_items((1, cantidad)))
    assert r.status_code == esperado


@pytest.mark.parametrize(
    "items,esperado",
    [
        pytest.param([], 422, id="0-items"),
        pytest.param(_items((1, 1)), 200, id="1-item"),
        pytest.param(_items((1, 1), (2, 1), (3, 1), (4, 1)), 200, id="4-items"),
        pytest.param(_items((1, 1), (2, 1), (3, 1), (4, 1), (1, 1)), 422, id="5-items"),
    ],
)
def test_valores_limite_de_cantidad_de_items(cliente, pedido_nuevo, items, esperado):
    assert _cargar(cliente, pedido_nuevo, items=items).status_code == esperado


@pytest.mark.parametrize(
    "direccion,esperado",
    [
        pytest.param("", 422, id="vacia"),
        pytest.param("   ", 422, id="solo-espacios"),
        pytest.param(" Calle 1", 422, id="espacio-al-inicio"),
        pytest.param("Calle 1 ", 422, id="espacio-al-final"),
        pytest.param("x", 200, id="1-caracter"),
        pytest.param("x" * 200, 200, id="200-caracteres"),
        pytest.param("x" * 201, 422, id="201-caracteres"),
    ],
)
def test_direccion_vacia_espacios_y_largo(cliente, pedido_nuevo, direccion, esperado):
    assert _cargar(cliente, pedido_nuevo, direccion=direccion).status_code == esperado


@pytest.mark.parametrize(
    "campo,valor,esperado",
    [
        ("lat", -90, 200), ("lat", 90, 200), ("lat", -90.1, 422), ("lat", 90.1, 422),
        ("lng", -180, 200), ("lng", 180, 200), ("lng", -180.1, 422), ("lng", 180.1, 422),
    ],
)
def test_valores_limite_de_coordenadas(cliente, pedido_nuevo, campo, valor, esperado):
    assert _cargar(cliente, pedido_nuevo, **{campo: valor}).status_code == esperado


# --- Reglas de negocio contra el catálogo ------------------------------------


def test_plato_repetido_da_422(cliente, pedido_nuevo):
    r = _cargar(cliente, pedido_nuevo, items=_items((1, 2), (1, 3)))
    assert r.status_code == 422
    assert r.json() == {"detail": {"error": "plato_repetido"}}


def test_plato_inexistente_da_422_y_no_guarda_nada(cliente, pedido_nuevo):
    r = _cargar(cliente, pedido_nuevo, items=_items((1, 2), (99, 1)))
    assert r.status_code == 422
    assert r.json() == {"detail": {"error": "plato_inexistente"}}
    p = cliente.get(f"/pedidos/{pedido_nuevo}").json()
    assert p["items"] == []
    assert p["estado"] == "LINK_ENVIADO"


# --- Estados y existencia ---------------------------------------------------


@pytest.mark.parametrize(
    "items_segunda_vez",
    [
        pytest.param(DATOS_OK["items"], id="mismos-platos"),  # chocaría con la PK de pedido_items
        pytest.param(_items((2, 1)), id="otros-platos"),
    ],
)
def test_cargar_datos_dos_veces_da_409(cliente, pedido_nuevo, items_segunda_vez):
    assert _cargar(cliente, pedido_nuevo).status_code == 200
    r = _cargar(cliente, pedido_nuevo, items=items_segunda_vez)
    assert r.status_code == 409
    assert r.json()["detail"] == {
        "error": "transicion_invalida", "estado_actual": "COTIZADO", "destino": "DATOS_CARGADOS"}
    p = cliente.get(f"/pedidos/{pedido_nuevo}").json()
    assert p["total"] == 22500  # la primera cotización queda intacta
    assert [i["plato_id"] for i in p["items"]] == [1, 4]


def test_cargar_datos_de_pedido_inexistente_da_404(cliente):
    r = cliente.put("/pedidos/999", json=DATOS_OK)
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "pedido_no_encontrado"
