"""Todas las rutas de un pedido responden igual cuando el pedido no existe.

Review Focus #2: el 404 sale de un solo lugar (el manejador de `PedidoNoEncontrado`),
pero cada ruta tiene que pedir el pedido antes de hacer nada. Los bodies son válidos
para que el 404 no quede tapado por un 422 de validación.
"""

import pytest

from conftest import DATOS_OK, FIRMA_OK

RUTAS = [
    ("GET", "", None),
    ("PUT", "", DATOS_OK),
    ("POST", "/firma", {"imagen": FIRMA_OK}),
    ("POST", "/pago", None),
    ("POST", "/retirado", None),
    ("POST", "/en-puerta", None),
    ("POST", "/recibido", None),
    ("POST", "/entregado", None),
    ("POST", "/cancelar", {"por": "cliente"}),
]


@pytest.mark.parametrize(
    "metodo,sufijo,body", RUTAS, ids=[f"{m} {s or '/'}" for m, s, _ in RUTAS]
)
def test_pedido_inexistente_da_404(cliente, metodo, sufijo, body):
    r = cliente.request(metodo, f"/pedidos/999{sufijo}", json=body)
    assert r.status_code == 404
    assert r.json() == {"detail": {"error": "pedido_no_encontrado"}}
