"""Bandeja de mensajes: WhatsApp simulado.

No se envía nada de verdad: cada mensaje queda guardado en la tabla `mensajes`
y se puede leer con `GET /mensajes`, como si fuera el celular del destinatario.
"""

from typing import Literal

from delivery import reloj
from delivery.db import Ctx

Destino = Literal["cliente", "delivery"]

CANAL = "whatsapp"


def enviar(
    ctx: Ctx,
    pedido_id: int,
    destino: Destino,
    telefono: str,
    texto: str,
    link: str | None,
) -> None:
    ctx.con.execute(
        "INSERT INTO mensajes (pedido_id, destino, telefono, canal, texto, link, creado_en)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (pedido_id, destino, telefono, CANAL, texto, link, reloj.marca_tiempo("servicio", ctx.cfg)),
    )


def listar(ctx: Ctx, destino: str | None = None, pedido_id: int | None = None) -> list[dict]:
    condiciones, params = [], []
    if destino is not None:
        condiciones.append("destino = ?")
        params.append(destino)
    if pedido_id is not None:
        condiciones.append("pedido_id = ?")
        params.append(pedido_id)
    where = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
    filas = ctx.con.execute(
        "SELECT id, pedido_id, destino, telefono, canal, texto, link, creado_en"
        f" FROM mensajes{where} ORDER BY id",
        params,
    ).fetchall()
    return [dict(f) for f in filas]
