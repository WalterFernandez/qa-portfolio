"""Máquina de estados del pedido: transiciones válidas e inválidas (prueba unitaria, sin HTTP).

Técnica ISTQB: prueba de transición de estados (CTFL v4.0 §4.2.4).
Cobertura: todas las transiciones válidas, 6 inválidas con nombre (salto, retroceso...)
y la tabla de estados completa (13 x 13 pares).
"""

import pytest

from delivery.estados import (
    CANCELABLES,
    TRANSICIONES,
    Estado,
    TransicionInvalida,
    validar_transicion,
)

E = Estado

VALIDAS = [(a, d) for a, destinos in TRANSICIONES.items() for d in sorted(destinos)]

INVALIDAS = [
    pytest.param(E.INICIADO, E.COTIZADO, id="salto"),
    pytest.param(E.PAGADO, E.COTIZADO, id="retroceso"),
    pytest.param(E.PAGADO, E.CANCELADO, id="cancelar-despues-de-pagar"),
    pytest.param(E.CERRADO, E.CANCELADO, id="salir-de-cerrado"),
    pytest.param(E.CANCELADO, E.LINK_ENVIADO, id="salir-de-cancelado"),
    pytest.param(E.EN_PUERTA, E.CERRADO, id="cerrar-sin-confirmaciones"),
]


def test_hay_13_estados():
    assert len(Estado) == 13
    assert set(TRANSICIONES) == set(Estado)


def test_hay_exactamente_18_transiciones_validas():
    """8 de la cadena + 4 cancelaciones + 2 desde EN_PUERTA + 2 cruzadas + 2 a CERRADO.
    Si alguien agrega una transición por error, este test lo detecta."""
    assert len(VALIDAS) == 18


@pytest.mark.parametrize(("actual", "destino"), VALIDAS, ids=lambda e: e.value)
def test_transicion_valida_no_lanza(actual, destino):
    validar_transicion(actual, destino)


@pytest.mark.parametrize(("actual", "destino"), INVALIDAS)
def test_transicion_invalida_lanza(actual, destino):
    with pytest.raises(TransicionInvalida) as exc:
        validar_transicion(actual, destino)
    assert exc.value.actual == actual
    assert exc.value.destino == destino


def test_tabla_de_estados_completa():
    """Los 13 x 13 pares: todo lo que no está en TRANSICIONES es inválido."""
    invalidas = 0
    for actual in Estado:
        for destino in Estado:
            if destino in TRANSICIONES[actual]:
                continue
            with pytest.raises(TransicionInvalida):
                validar_transicion(actual, destino)
            invalidas += 1
    assert invalidas == 13 * 13 - len(VALIDAS)


def test_estados_finales_no_tienen_salidas():
    assert TRANSICIONES[E.CERRADO] == set()
    assert TRANSICIONES[E.CANCELADO] == set()


def test_cancelables_son_los_4_previos_al_pago():
    assert CANCELABLES == {E.INICIADO, E.LINK_ENVIADO, E.DATOS_CARGADOS, E.COTIZADO}
