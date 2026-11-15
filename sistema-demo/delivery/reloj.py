"""Reloj del sistema: una sola fuente de "ahora" y el formato de las marcas de tiempo.

Cada actor vive en una zona horaria distinta (ZONAS). Sin el defecto sembrado,
todas las marcas se guardan en UTC con sufijo "Z", así se ordenan bien como texto.
El defecto de zona horaria se agrega en la Task 8.
"""

from datetime import UTC, datetime

from delivery.config import Config

ZONAS = {
    "cliente": "America/Mexico_City",
    "servicio": "America/New_York",
    "delivery": "America/Argentina/Buenos_Aires",
}

FORMATO_UTC = "%Y-%m-%dT%H:%M:%S.%fZ"


def ahora_utc() -> datetime:
    """Hora actual con zona (UTC). Los tests la reemplazan con monkeypatch."""
    return datetime.now(UTC)


def marca_tiempo(actor: str, cfg: Config) -> str:
    return ahora_utc().strftime(FORMATO_UTC)
