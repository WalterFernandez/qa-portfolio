"""Configuración del sistema demo. Los defectos sembrados se prenden con variables de entorno."""

import os
from dataclasses import dataclass
from pathlib import Path


def _flag(nombre: str) -> bool:
    return os.environ.get(nombre, "") == "1"


@dataclass(frozen=True)
class Config:
    db_path: Path = Path("data/demo.db")
    defecto_zona_horaria: bool = False
    defecto_contrato: bool = False
    delivery_telefono: str = "+5491100000000"  # ficticio

    @classmethod
    def desde_entorno(cls) -> "Config":
        return cls(
            db_path=Path(os.environ.get("DEMO_DB_PATH", "data/demo.db")),
            defecto_zona_horaria=_flag("DEMO_DEFECTO_ZONA_HORARIA"),
            defecto_contrato=_flag("DEMO_DEFECTO_CONTRATO"),
        )
