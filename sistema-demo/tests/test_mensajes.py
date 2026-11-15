"""Bandeja de mensajes (WhatsApp simulado): qué se envió, a quién y con qué link."""

import pytest

from delivery import db, pedidos
from delivery.config import Config
from delivery.estados import Estado, TransicionInvalida


def test_bandeja_filtra_por_pedido(cliente):
    a = cliente.post("/pedidos", json={"telefono": "1111111111"}).json()
    b = cliente.post("/pedidos", json={"telefono": "2222222222"}).json()
    msgs = cliente.get("/mensajes", params={"pedido_id": b["id"]}).json()
    assert [m["pedido_id"] for m in msgs] == [b["id"]]
    assert len(cliente.get("/mensajes").json()) == 2
    assert a["id"] != b["id"]


def test_bandeja_filtra_por_destino(cliente):
    cliente.post("/pedidos", json={"telefono": "1111111111"})
    assert len(cliente.get("/mensajes", params={"destino": "cliente"}).json()) == 1
    assert cliente.get("/mensajes", params={"destino": "delivery"}).json() == []


def test_mensaje_al_cliente_menciona_el_link(cliente):
    p = cliente.post("/pedidos", json={"telefono": "1111111111"}).json()
    m = cliente.get("/mensajes", params={"pedido_id": p["id"]}).json()[0]
    assert set(m) == {"id", "pedido_id", "destino", "telefono", "canal", "texto", "link", "creado_en"}
    assert m["destino"] == "cliente"
    assert m["link"] in m["texto"]
    assert m["creado_en"].endswith("Z")


def test_destino_desconocido_da_422(cliente):
    assert cliente.get("/mensajes", params={"destino": "cocina"}).status_code == 422


def test_avanzar_valida_la_transicion(tmp_path):
    """Toda mutación de estado pasa por _avanzar: un salto se rechaza y no deja rastro."""
    cfg = Config(db_path=tmp_path / "t.db")
    db.inicializar(cfg.db_path)
    ctx = db.Ctx(con=db.conectar(cfg.db_path), cfg=cfg)
    pid = pedidos.crear_pedido(ctx, "1122334455")
    with pytest.raises(TransicionInvalida):
        pedidos._avanzar(ctx, pid, Estado.PAGADO, "servicio")
    p = pedidos.obtener_pedido(ctx, pid)
    assert p["estado"] == "LINK_ENVIADO"
    assert len(p["eventos"]) == 2
    ctx.con.close()
