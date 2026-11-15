"""Catálogo de platos (solo lectura)."""

from delivery.db import Ctx


def listar_platos(ctx: Ctx) -> list[dict]:
    filas = ctx.con.execute("SELECT id, nombre, precio FROM platos ORDER BY id").fetchall()
    return [{"id": f["id"], "nombre": f["nombre"], "precio": f["precio"]} for f in filas]


def precios(ctx: Ctx) -> dict[int, int]:
    return {f["id"]: f["precio"] for f in ctx.con.execute("SELECT id, precio FROM platos")}
