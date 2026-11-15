"""Defectos sembrados: dos errores a propósito, apagados por defecto.

Se prenden con DEMO_DEFECTO_ZONA_HORARIA=1 y DEMO_DEFECTO_CONTRATO=1 (o con los
flags de Config en los tests). Son el blanco de las etapas siguientes: las pruebas
de API, UI y mobile tienen que poder encontrarlos.

1. Zona horaria: cada actor guarda su hora LOCAL sin offset. Como la línea de
   tiempo se ordena por texto, los eventos quedan desordenados.
2. Contrato: los montos salen como texto ("$ 9.000") en vez de enteros. La base
   no cambia: el defecto está solo en la salida.

Técnicas ISTQB: prueba basada en defectos (defectos sembrados, "defect seeding",
CTFL v4.0 Glosario) y prueba de contrato de la API. Cada test que muestra el
defecto prendido tiene su par con el defecto apagado (oráculo: el orden de la
tabla del spec y los tipos del contrato).
"""

from datetime import UTC, datetime, timedelta
from itertools import count

import pytest

from conftest import DATOS_OK, FIRMA_OK, RECORRIDO
from delivery import formato

ORDEN_ESPERADO = [
    "INICIADO", "LINK_ENVIADO", "DATOS_CARGADOS", "COTIZADO", "PAGADO", "ASIGNADO",
]


@pytest.fixture
def reloj_fijo(monkeypatch):
    """Cada marca de tiempo avanza 5 segundos desde las 15:00 UTC."""
    inicio = datetime(2026, 11, 14, 15, 0, 0, tzinfo=UTC)
    pasos = count()
    monkeypatch.setattr(
        "delivery.reloj.ahora_utc", lambda: inicio + timedelta(seconds=5 * next(pasos))
    )


def llevar_a_pagado(c) -> dict:
    """Crear, cargar datos, firmar y pagar. Devuelve el pedido (queda en ASIGNADO)."""
    pedido_id = c.post("/pedidos", json={"telefono": "1122334455"}).json()["id"]
    c.put(f"/pedidos/{pedido_id}", json=DATOS_OK)
    c.post(f"/pedidos/{pedido_id}/firma", json={"imagen": FIRMA_OK})
    return c.post(f"/pedidos/{pedido_id}/pago").json()


def _estados(pedido: dict) -> list[str]:
    return [e["estado"] for e in pedido["eventos"]]


# --- Defecto 1: zona horaria ------------------------------------------------


def test_defecto_zona_horaria_desordena_la_linea_de_tiempo(crear_cliente, reloj_fijo):
    estados = _estados(llevar_a_pagado(crear_cliente(defecto_zona_horaria=True)))
    assert estados.index("PAGADO") < estados.index("COTIZADO")  # el bug visible
    assert estados == [
        # Cliente en México (UTC-6): ~09:00. Servicio en Nueva York (UTC-5): ~10:00.
        "INICIADO", "DATOS_CARGADOS", "PAGADO", "LINK_ENVIADO", "COTIZADO", "ASIGNADO",
    ]


def test_sin_defecto_la_linea_de_tiempo_esta_en_orden(crear_cliente, reloj_fijo):
    assert _estados(llevar_a_pagado(crear_cliente())) == ORDEN_ESPERADO


def test_defecto_zona_horaria_marca_sin_offset_y_en_hora_local(crear_cliente, reloj_fijo):
    eventos = llevar_a_pagado(crear_cliente(defecto_zona_horaria=True))["eventos"]
    marcas = {e["estado"]: e["ocurrido_en"] for e in eventos}
    # Instantes: 15:00:00 creado_en, :05 evento INICIADO (cliente),
    # :10 mensaje con el link, :15 evento LINK_ENVIADO (servicio).
    assert marcas["INICIADO"] == "2026-11-14T09:00:05.000000"
    assert marcas["LINK_ENVIADO"] == "2026-11-14T10:00:15.000000"
    assert not any(m.endswith("Z") or "+" in m for m in marcas.values())


def test_sin_defecto_las_marcas_son_utc_con_z(crear_cliente, reloj_fijo):
    eventos = llevar_a_pagado(crear_cliente())["eventos"]
    assert eventos[0]["ocurrido_en"] == "2026-11-14T15:00:05.000000Z"


def test_defecto_zona_horaria_en_el_flujo_completo(crear_cliente, reloj_fijo):
    """Los 13 pasos con el defecto prendido: el delivery (Buenos Aires, UTC-3) queda al final."""
    c = crear_cliente(defecto_zona_horaria=True)
    pedido_id = llevar_a_pagado(c)["id"]
    for ruta, _ in RECORRIDO:
        assert c.post(f"/pedidos/{pedido_id}/{ruta}").status_code == 200
    eventos = c.get(f"/pedidos/{pedido_id}").json()["eventos"]
    actores = [e["actor"] for e in eventos]
    # Agrupados por zona horaria en vez de por orden real: cliente, servicio, delivery.
    assert actores == sorted(actores, key=["cliente", "servicio", "delivery"].index)
    assert [e["estado"] for e in eventos] != ORDEN_ESPERADO + [
        "RETIRADO", "EN_CAMINO", "EN_PUERTA", "RECIBIDO", "ENTREGADO", "CERRADO",
    ]


# --- Defecto 2: contrato ----------------------------------------------------


@pytest.mark.parametrize(
    ("monto", "texto"),
    [(0, "$ 0"), (999, "$ 999"), (1000, "$ 1.000"), (9000, "$ 9.000"),
     (22500, "$ 22.500"), (1234567, "$ 1.234.567")],
)
def test_formato_pesos(monto, texto):
    assert formato.pesos(monto) == texto


def test_defecto_contrato_precio_como_texto(crear_cliente):
    platos = crear_cliente(defecto_contrato=True).get("/platos").json()
    assert platos[0]["precio"] == "$ 9.000"
    assert all(isinstance(p["precio"], str) for p in platos)


def test_defecto_contrato_total_como_texto(crear_cliente):
    p = llevar_a_pagado(crear_cliente(defecto_contrato=True))
    assert p["total"] == "$ 22.500"
    assert [(i["precio_unitario"], i["subtotal"]) for i in p["items"]] == [
        ("$ 9.000", "$ 18.000"),
        ("$ 4.500", "$ 4.500"),
    ]


def test_defecto_contrato_tambien_en_la_lista_de_pedidos(crear_cliente):
    c = crear_cliente(defecto_contrato=True)
    llevar_a_pagado(c)
    assert c.get("/pedidos").json()[0]["total"] == "$ 22.500"


def test_defecto_contrato_pedido_sin_cotizar_total_sigue_nulo(crear_cliente):
    p = crear_cliente(defecto_contrato=True).post("/pedidos", json={"telefono": "1122334455"})
    assert p.json()["total"] is None


def test_defecto_contrato_no_toca_la_base(crear_cliente):
    """Mismo archivo SQLite: con el defecto sale texto, sin el defecto vuelven los enteros."""
    con_defecto = crear_cliente(defecto_contrato=True)
    pedido_id = llevar_a_pagado(con_defecto)["id"]
    p = crear_cliente().get(f"/pedidos/{pedido_id}").json()
    assert p["total"] == 22500
    assert p["items"][0]["precio_unitario"] == 9000


def test_sin_defecto_los_montos_son_enteros(crear_cliente):
    c = crear_cliente()
    p = llevar_a_pagado(c)
    assert isinstance(p["total"], int)
    assert all(isinstance(x["precio"], int) for x in c.get("/platos").json())


def test_salud_informa_los_defectos_prendidos(crear_cliente):
    c = crear_cliente(defecto_zona_horaria=True, defecto_contrato=True)
    assert c.get("/salud").json()["defectos"] == {"zona_horaria": True, "contrato": True}
