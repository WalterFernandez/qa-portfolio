"""Catálogo de platos: siembra inicial, precios enteros y persistencia sin duplicados."""

from fastapi.testclient import TestClient

from delivery.config import Config
from delivery.main import crear_app


def test_catalogo_tiene_los_4_platos_sembrados(cliente):
    platos = cliente.get("/platos").json()
    assert [(p["nombre"], p["precio"]) for p in platos] == [
        ("Empanadas (docena)", 9000),
        ("Milanesa con papas", 12500),
        ("Pizza muzzarella", 11000),
        ("Flan casero", 4500),
    ]
    assert all(isinstance(p["precio"], int) for p in platos)


def test_siembra_no_duplica_al_reiniciar(tmp_path):
    cfg = Config(db_path=tmp_path / "t.db")
    TestClient(crear_app(cfg))
    c = TestClient(crear_app(cfg))
    assert len(c.get("/platos").json()) == 4
