"""Servicio de pedidos: alta, lectura y avance de estado.

Toda mutación de estado pasa por `_avanzar`, que valida la transición contra la
máquina de estados y deja un evento con su marca de tiempo.

Concurrencia: entre leer el estado y escribirlo puede entrar otro request (TOCTOU).
Por eso toda escritura que depende del estado va con `AND estado = <el leído>`
(`_actualizar_si_sigue`): si otro se adelantó, no cambia ninguna fila y da 409.
"""

from delivery import catalogo, mensajes, reloj
from delivery.db import Ctx
from delivery.estados import CANCELABLES, Estado, TransicionInvalida, validar_transicion


class PedidoNoEncontrado(Exception):
    def __init__(self, pedido_id: int) -> None:
        super().__init__(f"No existe el pedido {pedido_id}")
        self.pedido_id = pedido_id


class DatosInvalidos(Exception):
    """Regla de negocio que Pydantic no puede chequear sola (necesita el catálogo)."""

    def __init__(self, error: str) -> None:
        super().__init__(error)
        self.error = error


class FirmaRequerida(Exception):
    """Pagar exige firma previa (Paso 6)."""


class NoCancelable(Exception):
    """El pedido ya fue pagado o ya terminó: no se puede cancelar."""

    def __init__(self, actual: Estado) -> None:
        self.actual = actual
        self.mensaje = (
            "El pedido ya está finalizado"
            if actual in FINALES
            else "No se puede cancelar un pedido que ya fue pagado"
        )
        super().__init__(self.mensaje)


# Estados en los que el pago ya ocurrió: pagar de nuevo no hace nada (idempotencia).
# Son todos menos los previos al pago y CANCELADO (un cancelado no se paga: 409).
YA_PAGADOS: frozenset[Estado] = frozenset(Estado) - CANCELABLES - {Estado.CANCELADO}

FINALES: frozenset[Estado] = frozenset({Estado.CERRADO, Estado.CANCELADO})

# Paso 11 y 12: cada confirmación es (estado al que lleva, su bandera, la bandera del otro).
CONFIRMACIONES = {
    "cliente": (Estado.RECIBIDO, "recibido_cliente", "entregado_delivery"),
    "delivery": (Estado.ENTREGADO, "entregado_delivery", "recibido_cliente"),
}


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


def _actualizar_si_sigue(
    ctx: Ctx, pedido_id: int, leido: Estado, destino: Estado, columnas: str, valores: tuple
) -> None:
    """UPDATE que solo se aplica si el pedido sigue en el estado `leido`.

    Si otro request lo cambió entre la lectura y esta escritura, no toca ninguna
    fila: se relee el estado real y se rechaza como transición inválida.
    """
    cur = ctx.con.execute(
        f"UPDATE pedidos SET {columnas} WHERE id = ? AND estado = ?",
        (*valores, pedido_id, leido),
    )
    if cur.rowcount == 0:
        raise TransicionInvalida(Estado(_fila(ctx, pedido_id)["estado"]), destino)


def _avanzar(ctx: Ctx, pedido_id: int, destino: Estado, actor: str) -> None:
    actual = Estado(_fila(ctx, pedido_id)["estado"])
    validar_transicion(actual, destino)
    _actualizar_si_sigue(ctx, pedido_id, actual, destino, "estado = ?", (destino,))
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

    # Primero se "toma" el pedido (UPDATE condicional): un segundo envío simultáneo
    # del formulario da 409 acá, antes de chocar con la clave de pedido_items.
    _avanzar(ctx, pedido_id, Estado.DATOS_CARGADOS, "cliente")
    ctx.con.executemany(
        "INSERT INTO pedido_items (pedido_id, plato_id, cantidad, precio_unitario)"
        " VALUES (?, ?, ?, ?)",
        [(pedido_id, plato_id, cantidad, precios[plato_id]) for plato_id, cantidad in items],
    )
    ctx.con.execute(
        "UPDATE pedidos SET direccion = ?, lat = ?, lng = ? WHERE id = ?",
        (direccion, lat, lng, pedido_id),
    )

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


def firmar(ctx: Ctx, pedido_id: int, imagen: str) -> None:
    """Paso 6, primera mitad: el cliente firma. No cambia de estado.

    Se puede firmar solo donde el próximo paso es pagar (COTIZADO); por eso se
    valida la transición a PAGADO. Volver a firmar antes de pagar reemplaza la firma.
    El formato de `imagen` ya lo validó la ruta.
    """
    actual = Estado(_fila(ctx, pedido_id)["estado"])
    validar_transicion(actual, Estado.PAGADO)
    _actualizar_si_sigue(
        ctx, pedido_id, actual, Estado.PAGADO, "firmado = 1, firma = ?", (imagen,)
    )


def pagar(ctx: Ctx, pedido_id: int) -> None:
    """Paso 6 (el cliente paga) y paso 7 (el servicio asigna el delivery), en la misma llamada.

    Idempotente: si el pedido ya está pagado (o más adelante), no hace nada. Así un
    doble clic en "Pagar" no duplica el evento PAGADO ni el mensaje al delivery.
    """
    fila = _fila(ctx, pedido_id)
    actual = Estado(fila["estado"])
    if actual in YA_PAGADOS:
        return
    validar_transicion(actual, Estado.PAGADO)  # primero el estado, después la firma
    if not fila["firmado"]:
        raise FirmaRequerida()

    try:
        _avanzar(ctx, pedido_id, Estado.PAGADO, "cliente")
    except TransicionInvalida:
        # Otro request pagó entre nuestra lectura y nuestra escritura: mismo caso
        # que el doble clic, no es un error.
        if Estado(_fila(ctx, pedido_id)["estado"]) in YA_PAGADOS:
            return
        raise
    link = f"/delivery/pedido/{pedido_id}"
    mensajes.enviar(
        ctx, pedido_id, "delivery", ctx.cfg.delivery_telefono,
        f"Nuevo pedido #{pedido_id}: retirar y entregar en {fila['direccion']}", link,
    )
    _avanzar(ctx, pedido_id, Estado.ASIGNADO, "servicio")


def marcar_retirado(ctx: Ctx, pedido_id: int) -> None:
    """Paso 8 (el delivery retira) y paso 9 (el servicio avisa al cliente), en la misma llamada.

    Primero se "toma" el pedido con el UPDATE condicional: un doble toque en
    "Retirado" da 409 antes de mandar un segundo aviso.
    """
    _avanzar(ctx, pedido_id, Estado.RETIRADO, "delivery")
    link = f"/cliente/pedido/{pedido_id}"
    telefono = _fila(ctx, pedido_id)["telefono"]
    mensajes.enviar(ctx, pedido_id, "cliente", telefono, "Tu pedido está en camino", link)
    _avanzar(ctx, pedido_id, Estado.EN_CAMINO, "servicio")


def marcar_en_puerta(ctx: Ctx, pedido_id: int) -> None:
    """Paso 10: el delivery llega a la puerta."""
    _avanzar(ctx, pedido_id, Estado.EN_PUERTA, "delivery")


def _confirmar(ctx: Ctx, pedido_id: int, quien: str) -> None:
    """Pasos 11 y 12: cada parte confirma por su lado; con las dos, paso 13: CERRADO.

    Estado y bandera se escriben en un solo UPDATE condicional. Si la otra parte
    confirmó entre nuestra lectura y nuestra escritura, el UPDATE no aplica: se
    relee y se reintenta una vez, porque esta confirmación sigue siendo válida.
    Si se repite la misma confirmación, el reintento da 409 (RECIBIDO -> RECIBIDO).
    """
    destino, propia, otra = CONFIRMACIONES[quien]
    for intento in range(2):
        fila = _fila(ctx, pedido_id)
        actual = Estado(fila["estado"])
        validar_transicion(actual, destino)
        try:
            _actualizar_si_sigue(
                ctx, pedido_id, actual, destino, f"estado = ?, {propia} = 1", (destino,)
            )
        except TransicionInvalida:
            if intento == 0:
                continue
            raise
        _registrar_evento(ctx, pedido_id, destino, quien)
        if fila[otra]:
            _avanzar(ctx, pedido_id, Estado.CERRADO, "servicio")
        return


def confirmar_recibido(ctx: Ctx, pedido_id: int) -> None:
    _confirmar(ctx, pedido_id, "cliente")


def confirmar_entregado(ctx: Ctx, pedido_id: int) -> None:
    _confirmar(ctx, pedido_id, "delivery")


def cancelar(ctx: Ctx, pedido_id: int, por: str) -> None:
    """Cancela un pedido que todavía no se pagó. Después del pago: 409 no_cancelable.

    Si un pago se adelanta entre la lectura y la escritura, el UPDATE condicional
    no aplica y la respuesta es la misma que si el pago hubiera llegado antes.
    """
    actual = Estado(_fila(ctx, pedido_id)["estado"])
    try:
        validar_transicion(actual, Estado.CANCELADO)
        _actualizar_si_sigue(
            ctx, pedido_id, actual, Estado.CANCELADO,
            "estado = ?, cancelado_por = ?", (Estado.CANCELADO, por),
        )
    except TransicionInvalida as exc:
        raise NoCancelable(exc.actual) from exc
    _registrar_evento(ctx, pedido_id, Estado.CANCELADO, por)


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
            "precio_unitario": catalogo.monto(ctx, f["precio_unitario"]),
            "subtotal": catalogo.monto(ctx, f["cantidad"] * f["precio_unitario"]),
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
        "total": catalogo.monto(ctx, fila["total"]),
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
