"""Acceso a SQLite (librería estándar, sin ORM): esquema, siembra y conexión por request."""

import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from fastapi import Request

from delivery.config import Config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS platos (
    id      INTEGER PRIMARY KEY,
    nombre  TEXT    NOT NULL UNIQUE,
    precio  INTEGER NOT NULL CHECK (precio > 0)
);

CREATE TABLE IF NOT EXISTS pedidos (
    id                  INTEGER PRIMARY KEY,
    telefono            TEXT    NOT NULL,
    estado              TEXT    NOT NULL,
    direccion           TEXT,
    lat                 REAL,
    lng                 REAL,
    total               INTEGER,
    demora_min          INTEGER,
    firmado             INTEGER NOT NULL DEFAULT 0,
    firma               TEXT,
    recibido_cliente    INTEGER NOT NULL DEFAULT 0,
    entregado_delivery  INTEGER NOT NULL DEFAULT 0,
    cancelado_por       TEXT,
    creado_en           TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS pedido_items (
    pedido_id        INTEGER NOT NULL REFERENCES pedidos(id),
    plato_id         INTEGER NOT NULL REFERENCES platos(id),
    cantidad         INTEGER NOT NULL,
    precio_unitario  INTEGER NOT NULL,
    PRIMARY KEY (pedido_id, plato_id)
);

CREATE TABLE IF NOT EXISTS eventos (
    id           INTEGER PRIMARY KEY,
    pedido_id    INTEGER NOT NULL REFERENCES pedidos(id),
    estado       TEXT    NOT NULL,
    actor        TEXT    NOT NULL,
    ocurrido_en  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS mensajes (
    id         INTEGER PRIMARY KEY,
    pedido_id  INTEGER NOT NULL REFERENCES pedidos(id),
    destino    TEXT    NOT NULL,
    telefono   TEXT    NOT NULL,
    canal      TEXT    NOT NULL,
    texto      TEXT    NOT NULL,
    link       TEXT,
    creado_en  TEXT    NOT NULL
);
"""

# Columnas agregadas después de la primera versión del esquema. `CREATE TABLE IF NOT
# EXISTS` no toca una tabla que ya existe, así que una base vieja se completa acá.
COLUMNAS_NUEVAS = [
    ("pedidos", "firma", "TEXT"),
]

# Precios en pesos enteros. Datos ficticios.
PLATOS_SEMILLA = [
    ("Empanadas (docena)", 9000),
    ("Milanesa con papas", 12500),
    ("Pizza muzzarella", 11000),
    ("Flan casero", 4500),
]


@dataclass
class Ctx:
    con: sqlite3.Connection
    cfg: Config


def conectar(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def inicializar(db_path: Path) -> None:
    """Crea la carpeta y las tablas si no existen; siembra los platos solo si la tabla está vacía."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = conectar(db_path)
    try:
        with con:
            con.executescript(ESQUEMA)
            _agregar_columnas_nuevas(con)
            if con.execute("SELECT COUNT(*) FROM platos").fetchone()[0] == 0:
                con.executemany("INSERT INTO platos (nombre, precio) VALUES (?, ?)", PLATOS_SEMILLA)
    finally:
        con.close()


def _agregar_columnas_nuevas(con: sqlite3.Connection) -> None:
    for tabla, columna, tipo in COLUMNAS_NUEVAS:
        existentes = {f["name"] for f in con.execute(f"PRAGMA table_info({tabla})")}
        if columna not in existentes:
            con.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")


def obtener_ctx(request: Request) -> Iterator[Ctx]:
    """Dependencia FastAPI: una conexión por request, commit si todo salió bien, rollback si no."""
    cfg: Config = request.app.state.cfg
    con = conectar(cfg.db_path)
    try:
        yield Ctx(con=con, cfg=cfg)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
