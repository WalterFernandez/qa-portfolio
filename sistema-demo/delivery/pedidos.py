"""Servicio de pedidos: alta, lectura y avance de estado.

Toda mutación de estado pasa por `_avanzar`, que valida la transición contra la
máquina de estados y deja un evento con su marca de tiempo.
"""

from delivery import catalogo, mensajes, reloj
from delivery.db import Ctx
from delivery.estados import Estado, validar_transicion


class PedidoNoEncontrado(Exception):
    def __init__(self, pedido_id: int) -> None:
        super().__init__(f"No existe el pedido {pedido_id}")
        self.pedido_id = pedido_id


class DatosInvalidos(Exception):
    """Regla de negocio que Pydantic no puede chequear sola (necesita el catálogo)."""

    def __init__(self, error: str) -> None:
        super().__init__(error)
        self.error = error


DEMORA_BASE_MIN = 30
DEMORA_TOPE_MIN = 60
UNIDADES_SIN_RECARGO = 2
RECARGO_POR_UNIDAD_MIN = 5


def calcular_demora(unidades: int) -> int:
    recargo = RECARGO_POR_UNIDAD_MIN * max(0, unidades - UNIDADES_SIN_RECARGO)
    return min(DEMORA_TOPE_MIN, DEMORA_BASE_MIN + recargo)


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


def cargar_datos(
    ctx: Ctx,
    pedido_id: int,
    items: list[tuple[int, int]],
    direccion: str,
    lat: float | None,
    lng: float | None,
) -> None:
    """Paso 4 (el cliente carga sus datos) y paso 5 (el servicio cotiza), en la misma llamada.

    Todo se valida ANTES de escribir: si algo falla no queda nada a medias.
    El precio sale siempre del catálogo; el cliente nunca manda montos.
    """
    fila = _fila(ctx, pedido_id)
    validar_transicion(Estado(fila["estado"]), Estado.DATOS_CARGADOS)

    ids = [plato_id for plato_id, _ in items]
    if len(set(ids)) != len(ids):
        raise DatosInvalidos("plato_repetido")
    precios = catalogo.precios(ctx)
    if any(plato_id not in precios for plato_id in ids):
        raise DatosInvalidos("plato_inexistente")

    ctx.con.executemany(
        "INSERT INTO pedido_items (pedido_id, plato_id, cantidad, precio_unitario)"
        " VALUES (?, ?, ?, ?)",
        [(pedido_id, plato_id, cantidad, precios[plato_id]) for plato_id, cantidad in items],
    )
    ctx.con.execute(
        "UPDATE pedidos SET direccion = ?, lat = ?, lng = ? WHERE id = ?",
        (direccion, lat, lng, pedido_id),
    )
    _avanzar(ctx, pedido_id, Estado.DATOS_CARGADOS, "cliente")

    total = sum(cantidad * precios[plato_id] for plato_id, cantidad in items)
    demora_min = calcular_demora(sum(cantidad for _, cantidad in items))
    ctx.con.execute(
        "UPDATE pedidos SET total = ?, demora_min = ? WHERE id = ?",
        (total, demora_min, pedido_id),
    )
    mensajes.enviar(
        ctx, pedido_id, "cliente", fila["telefono"],
        f"Total ${total} - demora {demora_min} min", None,
    )
    _avanzar(ctx, pedido_id, Estado.COTIZADO, "servicio")


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
