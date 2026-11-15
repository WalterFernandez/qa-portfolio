import pytest
from fastapi.testclient import TestClient

from delivery.config import Config
from delivery.main import crear_app


@pytest.fixture
def crear_cliente(tmp_path):
    """Devuelve una función que arma un TestClient con base temporal y los flags pedidos."""

    def _crear(**flags) -> TestClient:
        return TestClient(crear_app(Config(db_path=tmp_path / "t.db", **flags)))

    return _crear


@pytest.fixture
def cliente(crear_cliente):
    return crear_cliente()


# Datos válidos para cargar un pedido (Paso 4): 2 docenas de empanadas + 1 flan.
DATOS_OK = {
    "items": [{"plato_id": 1, "cantidad": 2}, {"plato_id": 4, "cantidad": 1}],
    "direccion": "Av. Siempre Viva 742",
    "lat": -34.6,
    "lng": -58.4,
}


@pytest.fixture
def pedido_nuevo(cliente) -> int:
    """Id de un pedido recién creado, en LINK_ENVIADO (listo para cargar datos)."""
    return cliente.post("/pedidos", json={"telefono": "1122334455"}).json()["id"]


# Firma mínima válida (Paso 6): un PNG en data URL. El contenido no importa.
FIRMA_OK = "data:image/png;base64,iVBORw0KGgo="


@pytest.fixture
def pedido_cotizado(cliente, pedido_nuevo) -> int:
    """Id de un pedido en COTIZADO (listo para firmar y pagar)."""
    cliente.put(f"/pedidos/{pedido_nuevo}", json=DATOS_OK)
    return pedido_nuevo
