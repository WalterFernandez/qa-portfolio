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
