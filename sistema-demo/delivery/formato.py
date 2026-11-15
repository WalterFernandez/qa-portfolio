"""Formato de montos para mostrar: 9000 -> "$ 9.000".

Lo usa el defecto sembrado de contrato (Task 8): la API devuelve este texto en vez
del entero. Para mostrar en pantalla está bien; como contrato de una API, no.
"""


def pesos(n: int) -> str:
    return "$ " + f"{n:,}".replace(",", ".")
