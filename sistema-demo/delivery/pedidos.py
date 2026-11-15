"""Servicio de pedidos: alta, lectura y avance de estado.

Toda mutación de estado pasa por `_avanzar`, que valida la transición contra la
máquina de estados y deja un evento con su marca de tiempo.
"""

from delivery import mensajes, reloj
from delivery.db import Ctx
from delivery.estados import Estado, validar_transicion


class PedidoNoEncontrado(Exception):
    def __init__(self, pedido_id: int) -> None:
        super().__init__(f"No existe el pedido {pedido_id}")
        self.pedido_id = pedido_id


def _fila(ctx: Ctx, pedido_id: int):
    fila = ctx.con.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if fila is None:
        raise PedidoNoEncontrado(pedido_id)
    return fila


def _registrar_evento(ctx: Ctx, pedido_id: int, estado: Estado, actor: str) -> None:
    ctx.con.execute(
        "INSERT INTO eventos (pedido_id, estado, actor, ocurrido_en) VALUES (?, ?, ?, ?)",
        (pedido_id, estado, actor, reloj.marca_tiempo(actor, ctx.cfg)),
    )


def _avanzar(ctx: Ctx, pedido_id: int, destino: Estado, actor: str) -> None:
    actual = Estado(_fila(ctx, pedido_id)["estado"])
    validar_transicion(actual, destino)
    ctx.con.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (destino, pedido_id))
    _registrar_evento(ctx, pedido_id, destino, actor)


def crear_pedido(ctx: Ctx, telefono: str) -> int:
    """Paso 1 (el cliente escribe) y paso 3 (el servicio le manda el link), en la misma llamada."""
    cur = ctx.con.execute(
        "INSERT INTO pedidos (telefono, estado, creado_en) VALUES (?, ?, ?)",
        (telefono, Estado.INICIADO, reloj.marca_tiempo("cliente", ctx.cfg)),
    )
    pedido_id = cur.lastrowid
    _registrar_evento(ctx, pedido_id, Estado.INICIADO, "cliente")

    link = f"/cliente/pedido/{pedido_id}"
    mensajes.enviar(
        ctx, pedido_id, "cliente", telefono,
        f"¡Hola! Armá tu pedido acá: {link}", link,
    )
    _avanzar(ctx, pedido_id, Estado.LINK_ENVIADO, "servicio")
    return pedido_id


def _items(ctx: Ctx, pedido_id: int) -> list[dict]:
    filas = ctx.con.execute(
        "SELECT i.plato_id, p.nombre, i.cantidad, i.precio_unitario"
        " FROM pedido_items i JOIN platos p ON p.id = i.plato_id"
        " WHERE i.pedido_id = ? ORDER BY i.plato_id",
        (pedido_id,),
    ).fetchall()
    return [
        {
            "plato_id": f["plato_id"],
            "nombre": f["nombre"],
            "cantidad": f["cantidad"],
            "precio_unitario": f["precio_unitario"],
            "subtotal": f["cantidad"] * f["precio_unitario"],
        }
        for f in filas
    ]


def _eventos(ctx: Ctx, pedido_id: int) -> list[dict]:
    # Se ordena SOLO por ocurrido_en, sin desempate por id: así se ve el defecto
    # de zona horaria de la Task 8 (marcas en texto con distinto offset).
    filas = ctx.con.execute(
        "SELECT estado, actor, ocurrido_en FROM eventos WHERE pedido_id = ? ORDER BY ocurrido_en",
        (pedido_id,),
    ).fetchall()
    return [dict(f) for f in filas]


def _a_json(ctx: Ctx, fila) -> dict:
    return {
        "id": fila["id"],
        "telefono": fila["telefono"],
        "estado": fila["estado"],
        "items": _items(ctx, fila["id"]),
        "direccion": fila["direccion"],
        "lat": fila["lat"],
        "lng": fila["lng"],
        "total": fila["total"],
        "demora_min": fila["demora_min"],
        "firmado": bool(fila["firmado"]),
        "recibido_cliente": bool(fila["recibido_cliente"]),
        "entregado_delivery": bool(fila["entregado_delivery"]),
        "cancelado_por": fila["cancelado_por"],
    }


def obtener_pedido(ctx: Ctx, pedido_id: int) -> dict:
    pedido = _a_json(ctx, _fila(ctx, pedido_id))
    pedido["eventos"] = _eventos(ctx, pedido_id)
    return pedido


def listar_pedidos(ctx: Ctx) -> list[dict]:
    filas = ctx.con.execute("SELECT * FROM pedidos ORDER BY id DESC").fetchall()
    return [_a_json(ctx, f) for f in filas]
