"""Smoke test de las páginas: se sirven como HTML y traen los data-testid que usan las etapas 3-4.

No prueba el comportamiento en el navegador (eso es la prueba manual y, más adelante,
Playwright/Appium): solo que cada página existe y expone sus puntos de enganche.
"""

import pytest

PAGINAS = [
    ("/", ["catalogo", "input-telefono", "btn-pedir", "msg-link-enviado"]),
    (
        "/cliente/pedido/1",
        [
            "input-direccion", "btn-ubicacion", "mapa", "total-estimado",
            "btn-confirmar-datos", "total", "demora", "canvas-firma",
            "btn-limpiar-firma", "btn-pagar", "estado-pedido", "btn-recibido",
            "btn-cancelar", "msg-error", "linea-de-tiempo",
        ],
    ),
    (
        "/delivery/pedido/1",
        [
            "direccion-entrega", "btn-retirado", "btn-en-puerta", "btn-entregado",
            "estado-pedido", "msg-error",
        ],
    ),
]


@pytest.mark.parametrize("ruta,testids", PAGINAS, ids=["inicio", "cliente", "delivery"])
def test_pagina_se_sirve_con_sus_testids(cliente, ruta, testids):
    r = cliente.get(ruta)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    faltan = [t for t in testids if f'data-testid="{t}"' not in r.text]
    assert faltan == []


@pytest.mark.parametrize("archivo,tipo", [
    ("estilos.css", "text/css"),
    ("api.js", "javascript"),
])
def test_estaticos_se_sirven(cliente, archivo, tipo):
    r = cliente.get(f"/estaticos/{archivo}")
    assert r.status_code == 200
    assert tipo in r.headers["content-type"]


def test_la_pagina_no_valida_el_id_del_pedido(cliente):
    """La página es un cascarón: el 404 de un pedido inexistente lo muestra el JS al llamar a la API."""
    assert cliente.get("/cliente/pedido/999").status_code == 200
