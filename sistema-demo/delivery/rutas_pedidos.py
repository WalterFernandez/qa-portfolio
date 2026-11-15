"""Rutas HTTP de pedidos y de la bandeja de mensajes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from delivery import mensajes, pedidos
from delivery.db import Ctx, obtener_ctx

router = APIRouter()

TELEFONO = r"^\+?\d{8,15}$"
# Sin espacios en los extremos: empieza y termina con un caracter visible.
SIN_ESPACIOS_EN_EXTREMOS = r"^\S(?:.*\S)?$"


class NuevoPedido(BaseModel):
    model_config = ConfigDict(extra="forbid")
    telefono: Annotated[str, Field(pattern=TELEFONO)]


class ItemPedido(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plato_id: int
    cantidad: Annotated[int, Field(ge=1, le=10)]


class DatosPedido(BaseModel):
    """Paso 4. No hay campo `total`: lo calcula el servidor y, por `extra="forbid"`, mandarlo da 422."""

    model_config = ConfigDict(extra="forbid")
    items: Annotated[list[ItemPedido], Field(min_length=1, max_length=4)]
    direccion: Annotated[
        str, Field(min_length=1, max_length=200, pattern=SIN_ESPACIOS_EN_EXTREMOS)
    ]
    lat: Annotated[float, Field(ge=-90, le=90)] | None = None
    lng: Annotated[float, Field(ge=-180, le=180)] | None = None


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


@router.put("/pedidos/{pedido_id}", tags=["pedidos"])
def cargar_datos(pedido_id: int, body: DatosPedido, ctx: Ctx = Depends(obtener_ctx)) -> dict:
    pedidos.cargar_datos(
        ctx,
        pedido_id,
        [(i.plato_id, i.cantidad) for i in body.items],
        body.direccion,
        body.lat,
        body.lng,
    )
    return pedidos.obtener_pedido(ctx, pedido_id)


@router.get("/mensajes", tags=["mensajes"])
def bandeja(
    destino: mensajes.Destino | None = None,
    pedido_id: int | None = None,
    ctx: Ctx = Depends(obtener_ctx),
) -> list[dict]:
    return mensajes.listar(ctx, destino, pedido_id)
