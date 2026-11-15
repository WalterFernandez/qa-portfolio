"""Reloj del sistema: una sola fuente de "ahora" y el formato de las marcas de tiempo.

Cada actor vive en una zona horaria distinta (ZONAS). Sin el defecto sembrado,
todas las marcas se guardan en UTC con sufijo "Z", así se ordenan bien como texto.

Defecto sembrado (cfg.defecto_zona_horaria): cada actor guarda su hora LOCAL y sin
offset. Las marcas ya no se pueden comparar entre actores y la línea de tiempo,
que se ordena por texto, queda desordenada.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from delivery.config import Config

ZONAS = {
    "cliente": "America/Mexico_City",
    "servicio": "America/New_York",
    "delivery": "America/Argentina/Buenos_Aires",
}

FORMATO_UTC = "%Y-%m-%dT%H:%M:%S.%fZ"
FORMATO_LOCAL_SIN_OFFSET = "%Y-%m-%dT%H:%M:%S.%f"


def ahora_utc() -> datetime:
    """Hora actual con zona (UTC). Los tests la reemplazan con monkeypatch."""
    return datetime.now(UTC)


def marca_tiempo(actor: str, cfg: Config) -> str:
    ahora = ahora_utc()
    if cfg.defecto_zona_horaria:
        return ahora.astimezone(ZoneInfo(ZONAS[actor])).strftime(FORMATO_LOCAL_SIN_OFFSET)
    return ahora.strftime(FORMATO_UTC)
