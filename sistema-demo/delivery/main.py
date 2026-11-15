"""Punto de entrada de la API del sistema demo de delivery."""

from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from delivery import catalogo, db, rutas_pedidos
from delivery.config import Config
from delivery.estados import TransicionInvalida
from delivery.pedidos import DatosInvalidos, FirmaRequerida, NoCancelable, PedidoNoEncontrado

PAGINAS = Path(__file__).parent / "paginas"

def crear_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or Config.desde_entorno()
    db.inicializar(cfg.db_path)
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

    @app.get("/platos", tags=["catálogo"])
    def platos(ctx: db.Ctx = Depends(db.obtener_ctx)) -> list[dict]:
        return catalogo.listar_platos(ctx)

    app.include_router(rutas_pedidos.router)

    # Páginas: HTML + JS plano. Son cascarones: el id del pedido lo lee el JS de la
    # URL y los datos (y los 404) llegan por la API, igual que en una app real.
    app.mount("/estaticos", StaticFiles(directory=PAGINAS), name="estaticos")

    @app.get("/", include_in_schema=False)
    def inicio() -> FileResponse:
        return FileResponse(PAGINAS / "inicio.html")

    @app.get("/cliente/pedido/{pedido_id}", include_in_schema=False)
    def pagina_cliente(pedido_id: int) -> FileResponse:
        return FileResponse(PAGINAS / "cliente.html")

    @app.get("/delivery/pedido/{pedido_id}", include_in_schema=False)
    def pagina_delivery(pedido_id: int) -> FileResponse:
        return FileResponse(PAGINAS / "delivery.html")

    @app.get("/panel", include_in_schema=False)
    def pagina_panel() -> FileResponse:
        return FileResponse(PAGINAS / "panel.html")

    # Las excepciones de dominio se traducen a HTTP en un solo lugar.
    @app.exception_handler(PedidoNoEncontrado)
    def _404(request: Request, exc: PedidoNoEncontrado) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": {"error": "pedido_no_encontrado"}})

    @app.exception_handler(DatosInvalidos)
    def _422(request: Request, exc: DatosInvalidos) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": {"error": exc.error}})

    @app.exception_handler(FirmaRequerida)
    def _409_firma(request: Request, exc: FirmaRequerida) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": {"error": "firma_requerida"}})

    @app.exception_handler(NoCancelable)
    def _409_cancelar(request: Request, exc: NoCancelable) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "error": "no_cancelable",
                    "estado_actual": exc.actual,
                    "mensaje": exc.mensaje,
                }
            },
        )

    @app.exception_handler(TransicionInvalida)
    def _409(request: Request, exc: TransicionInvalida) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "detail": {
                    "error": "transicion_invalida",
                    "estado_actual": exc.actual,
                    "destino": exc.destino,
                }
            },
        )

    return app


app = crear_app()
