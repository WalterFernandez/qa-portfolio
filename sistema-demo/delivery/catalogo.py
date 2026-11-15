"""Catálogo de platos (solo lectura)."""

from delivery import formato
from delivery.db import Ctx


def listar_platos(ctx: Ctx) -> list[dict]:
    filas = ctx.con.execute("SELECT id, nombre, precio FROM platos ORDER BY id").fetchall()
    return [
        {"id": f["id"], "nombre": f["nombre"], "precio": monto(ctx, f["precio"])} for f in filas
    ]


def monto(ctx: Ctx, n: int | None) -> int | str | None:
    """Monto tal como sale por la API.

    Defecto sembrado (cfg.defecto_contrato): sale como texto "$ 9.000" en vez del
    entero. La base sigue guardando enteros; el defecto está solo en la salida.
    """
    if n is None or not ctx.cfg.defecto_contrato:
        return n
    return formato.pesos(n)


def precios(ctx: Ctx) -> dict[int, int]:
    return {f["id"]: f["precio"] for f in ctx.con.execute("SELECT id, precio FROM platos")}
