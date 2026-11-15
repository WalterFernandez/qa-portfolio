"""Rutas HTTP de pedidos y de la bandeja de mensajes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from delivery import mensajes, pedidos
from delivery.db import Ctx, obtener_ctx

router = APIRouter()

TELEFONO = r"^\+?\d{8,15}$"


class NuevoPedido(BaseModel):
    model_config = ConfigDict(extra="forbid")
    telefono: Annotated[str, Field(pattern=TELEFONO)]


@router.post("/pedidos", status_code=201, tags=["pedidos"])
def crear(body: NuevoPedido, ctx: Ctx = Depends(obtener_ctx)) -> dict:
    pedido_id = pedidos.crear_pedido(ctx, body.telefono)
    return pedidos.obtener_pedido(ctx, pedido_id)


@router.get("/pedidos", tags=["pedidos"])
def listar(ctx: Ctx = Depends(obtener_ctx)) -> list[dict]:
    return pedidos.listar_pedidos(ctx)


@router.get("/pedidos/{pedido_id}", tags=["pedidos"])
def obtener(pedido_id: int, ctx: Ctx = Depends(obtener_ctx)) -> dict:
    return pedidos.obtener_pedido(ctx, pedido_id)


@router.get("/mensajes", tags=["mensajes"])
def bandeja(
    destino: mensajes.Destino | None = None,
    pedido_id: int | None = None,
    ctx: Ctx = Depends(obtener_ctx),
) -> list[dict]:
    return mensajes.listar(ctx, destino, pedido_id)
