"""Punto de entrada de la API del sistema demo de delivery."""

from fastapi import FastAPI, Request

from delivery.config import Config


def crear_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or Config.desde_entorno()
    app = FastAPI(
        title="Sistema demo: delivery de comidas",
        description="Sistema ficticio bajo prueba del QA Portfolio.",
        version="0.1.0",
    )
    app.state.cfg = cfg

    @app.get("/salud", tags=["sistema"])
    def salud(request: Request) -> dict:
        c: Config = request.app.state.cfg
        return {
            "estado": "ok",
            "defectos": {"zona_horaria": c.defecto_zona_horaria, "contrato": c.defecto_contrato},
        }

    return app


app = crear_app()
