"""Máquina de estados del pedido.

Única fuente de verdad sobre qué cambios de estado están permitidos.
Toda mutación de estado (Paso 4 en adelante) pasa por `validar_transicion`.
"""

from enum import StrEnum


class Estado(StrEnum):
    INICIADO = "INICIADO"
    LINK_ENVIADO = "LINK_ENVIADO"
    DATOS_CARGADOS = "DATOS_CARGADOS"
    COTIZADO = "COTIZADO"
    PAGADO = "PAGADO"
    ASIGNADO = "ASIGNADO"
    RETIRADO = "RETIRADO"
    EN_CAMINO = "EN_CAMINO"
    EN_PUERTA = "EN_PUERTA"
    RECIBIDO = "RECIBIDO"
    ENTREGADO = "ENTREGADO"
    CERRADO = "CERRADO"
    CANCELADO = "CANCELADO"


E = Estado

# Estados previos al pago: desde acá se puede cancelar.
CANCELABLES: frozenset[Estado] = frozenset(
    {E.INICIADO, E.LINK_ENVIADO, E.DATOS_CARGADOS, E.COTIZADO}
)

_CADENA = [
    E.INICIADO, E.LINK_ENVIADO, E.DATOS_CARGADOS, E.COTIZADO, E.PAGADO,
    E.ASIGNADO, E.RETIRADO, E.EN_CAMINO, E.EN_PUERTA,
]

TRANSICIONES: dict[Estado, set[Estado]] = {e: set() for e in Estado}
for _actual, _siguiente in zip(_CADENA, _CADENA[1:]):
    TRANSICIONES[_actual].add(_siguiente)
for _e in CANCELABLES:
    TRANSICIONES[_e].add(E.CANCELADO)
# En la puerta, cliente y delivery confirman cada uno por su lado, en cualquier orden.
TRANSICIONES[E.EN_PUERTA] |= {E.RECIBIDO, E.ENTREGADO}
TRANSICIONES[E.RECIBIDO] |= {E.ENTREGADO, E.CERRADO}
TRANSICIONES[E.ENTREGADO] |= {E.RECIBIDO, E.CERRADO}
# CERRADO y CANCELADO son finales: sin salidas.


class TransicionInvalida(Exception):
    def __init__(self, actual: Estado, destino: Estado) -> None:
        super().__init__(f"No se puede pasar de {actual} a {destino}")
        self.actual = actual
        self.destino = destino


def validar_transicion(actual: Estado, destino: Estado) -> None:
    if destino not in TRANSICIONES[actual]:
        raise TransicionInvalida(actual, destino)
