# Etapa 1: Sistema demo "delivery de comidas" — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir el sistema demo (API + estados + bandeja de WhatsApp simulado + páginas cliente/delivery/panel + 2 defectos sembrados) que será el objetivo de todas las pruebas del portfolio.

**Architecture:** App FastAPI única (`crear_app(cfg)`) sobre SQLite con `sqlite3` de la librería estándar, sin ORM. La lógica de negocio vive en funciones de servicio que reciben un `Ctx` (conexión + configuración) y lanzan excepciones de dominio, que `main.py` traduce a 404/409. Los pasos automáticos del "servicio" (3, 5, 7, 9, 13) ocurren dentro de la misma llamada que los dispara. Las páginas son HTML + JS plano servidos por la misma app.

**Tech Stack:** Python 3.12, FastAPI 0.115.5, uvicorn 0.32.1, httpx 0.27.2 (TestClient), pytest 8.3.3, tzdata 2024.2 (zonas horarias en Windows), Leaflet 1.9.4 por CDN (mapa sin claves).

**Spec:** `docs/superpowers/specs/2026-11-10-qa-portfolio-design.md` (§4 sistema demo, §6 mapa ISTQB/ISO, §7 vistas). Leer §4 completo antes de empezar.

## Global Constraints

- Todo el código vive en `sistema-demo/`; el paquete Python se llama `delivery`. Nombres de dominio en español.
- **Nada de información real de la empresa del usuario**: ni nombres, ni endpoints, ni rubro, ni la herramienta interna. Los datos de ejemplo son ficticios.
- Git **solo local**: sin remoto, sin push. Identidad del repo = nombre y mail **personales** del usuario (`git config --local`); el `--global` actual es el del trabajo y no se usa.
- No se versionan: `thoughts/`, `Notas_Porfolio.txt`, `qa-portfolio-plan.md`, `.superpowers/`, `.venv/`, `*.db`, `.env`, `__pycache__/`.
- Liviano: sin Docker, sin emulador, sin servicios externos. El servidor se levanta solo para probar a mano y se apaga.
- Estados (exactos): `INICIADO, LINK_ENVIADO, DATOS_CARGADOS, COTIZADO, PAGADO, ASIGNADO, RETIRADO, EN_CAMINO, EN_PUERTA, RECIBIDO, ENTREGADO, CERRADO, CANCELADO`.
- Transición inválida o salto/retroceso → **409**. Pedido inexistente → **404**. Body inválido o con campos de más → **422**.
- Montos en **pesos enteros** (`int`), nunca `float`.
- Cada elemento interactivo de las páginas lleva `data-testid` (lo usan Playwright y Appium en etapas 3–4).
- Comandos desde `sistema-demo/`: tests con `.venv/Scripts/python -m pytest -q`.

## Review Focus

1. **Doble clic en "Pagar"**: el segundo `POST /pago` responde 200 con el mismo pedido y no duplica el evento `PAGADO` (Task 6).
2. **Id inexistente en cualquier ruta de pedido**: 404 con `{"detail": {"error": "pedido_no_encontrado"}}`, nunca 500 (Task 4, test parametrizado sobre todas las rutas en Task 7).
3. **Cliente que manda `total` o campos inventados**: 422, y el total sigue siendo el del servidor (Task 5).
4. **El mismo plato dos veces en `items`**: 422 `plato_repetido`, no se suman en silencio (Task 5).
5. **Reiniciar el servidor**: los pedidos siguen ahí (el archivo SQLite persiste; Task 4 crea la app dos veces sobre la misma base).

---

### Task 1: Esqueleto del proyecto, git local y `/salud`

**Files:**
- Create: `.gitignore` (en la raíz `Portfolio/`)
- Create: `sistema-demo/requirements.txt`, `sistema-demo/pytest.ini`
- Create: `sistema-demo/delivery/__init__.py`, `sistema-demo/delivery/config.py`, `sistema-demo/delivery/main.py`
- Test: `sistema-demo/tests/conftest.py`, `sistema-demo/tests/test_salud.py`

**Interfaces:**
- Produces:
  - `config.Config` (dataclass frozen): `db_path: Path = Path("data/demo.db")`, `defecto_zona_horaria: bool = False`, `defecto_contrato: bool = False`, `delivery_telefono: str = "+5491100000000"`; `Config.desde_entorno() -> Config` lee `DEMO_DB_PATH`, `DEMO_DEFECTO_ZONA_HORARIA`, `DEMO_DEFECTO_CONTRATO` (`"1"` = encendido).
  - `main.crear_app(cfg: Config | None = None) -> FastAPI` (guarda `cfg` en `app.state.cfg`); `main.app = crear_app()` para uvicorn.
  - Fixture `cliente(tmp_path)` → `TestClient(crear_app(Config(db_path=tmp_path / "t.db")))`; fixture `crear_cliente(tmp_path)` → función `(**flags) -> TestClient` para tests con defectos.

- [x] **Step 1:** Pedirle al usuario su nombre y mail **personales**. En `Portfolio/`: `git init`, `git config --local user.name "<nombre>"`, `git config --local user.email "<mail>"`. Escribir `.gitignore` con la lista de Global Constraints. Verificar: `git config user.email` muestra el mail personal y `git status` no lista `thoughts/`.
- [x] **Step 2:** `requirements.txt` con las versiones exactas del Tech Stack; `pytest.ini` con `testpaths = tests` y `pythonpath = .`. Crear el venv: `python -m venv .venv` y `.venv/Scripts/python -m pip install -r requirements.txt`.
- [x] **Step 3: Test que falla**

```python
def test_salud_informa_defectos_apagados(cliente):
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "defectos": {"zona_horaria": False, "contrato": False}}

def test_salud_refleja_defecto_encendido(crear_cliente):
    r = crear_cliente(defecto_contrato=True).get("/salud")
    assert r.json()["defectos"]["contrato"] is True
```

- [x] **Step 4:** Correr `.venv/Scripts/python -m pytest -q` → FAIL (no existe `delivery.main`).
- [x] **Step 5:** Implementar `Config`, `crear_app` y `GET /salud`.
- [x] **Step 6:** Correr los tests → PASS. Levantar `.venv/Scripts/python -m uvicorn delivery.main:app` y abrir `http://127.0.0.1:8000/docs` (OpenAPI visible). Apagar.
- [x] **Step 7: Commit** `git add .gitignore sistema-demo && git commit -m "feat(demo): esqueleto FastAPI con /salud"`

### Task 2: Base de datos y catálogo (`GET /platos`)

**Files:**
- Create: `sistema-demo/delivery/db.py`, `sistema-demo/delivery/catalogo.py`
- Modify: `sistema-demo/delivery/main.py`
- Test: `sistema-demo/tests/test_catalogo.py`

**Interfaces:**
- Consumes: `Config`, `crear_app`.
- Produces:
  - `db.Ctx` (dataclass): `con: sqlite3.Connection`, `cfg: Config`. `db.obtener_ctx(request) -> Iterator[Ctx]` (dependencia FastAPI; abre conexión con `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON`, commit al final, cierra).
  - `db.inicializar(db_path: Path) -> None`: crea carpeta y tablas (`platos`, `pedidos`, `pedido_items`, `eventos`, `mensajes`) si no existen y siembra los platos si `platos` está vacía. `crear_app` la llama al iniciar.
  - Tabla `eventos(id INTEGER PK, pedido_id, estado TEXT, actor TEXT, ocurrido_en TEXT)`; tabla `mensajes(id PK, pedido_id, destino TEXT, telefono TEXT, canal TEXT, texto TEXT, link TEXT, creado_en TEXT)`. Columnas de `pedidos`: ver el JSON de pedido en Task 4.
  - `catalogo.listar_platos(ctx) -> list[dict]` con `{"id", "nombre", "precio"}`; `catalogo.precios(ctx) -> dict[int, int]`.

- [x] **Step 1: Test que falla**

```python
def test_catalogo_tiene_los_4_platos_sembrados(cliente):
    platos = cliente.get("/platos").json()
    assert [(p["nombre"], p["precio"]) for p in platos] == [
        ("Empanadas (docena)", 9000),
        ("Milanesa con papas", 12500),
        ("Pizza muzzarella", 11000),
        ("Flan casero", 4500),
    ]
    assert all(isinstance(p["precio"], int) for p in platos)

def test_siembra_no_duplica_al_reiniciar(tmp_path):
    cfg = Config(db_path=tmp_path / "t.db")
    TestClient(crear_app(cfg)); c = TestClient(crear_app(cfg))
    assert len(c.get("/platos").json()) == 4
```

- [x] **Step 2:** Correr → FAIL (404 en `/platos`).
- [x] **Step 3:** Implementar `db.py`, `catalogo.py` y la ruta `GET /platos`.
- [x] **Step 4:** Correr → PASS.
- [x] **Step 5: Commit** `feat(demo): base SQLite y catálogo`

### Task 3: Máquina de estados (unitaria, sin HTTP)

**Files:**
- Create: `sistema-demo/delivery/estados.py`
- Test: `sistema-demo/tests/test_estados.py`

**Interfaces:**
- Produces:
  - `class Estado(StrEnum)` con los 13 estados de Global Constraints.
  - `TRANSICIONES: dict[Estado, set[Estado]]`: la cadena lineal `INICIADO→LINK_ENVIADO→DATOS_CARGADOS→COTIZADO→PAGADO→ASIGNADO→RETIRADO→EN_CAMINO→EN_PUERTA`, más `EN_PUERTA→{RECIBIDO, ENTREGADO}`, `RECIBIDO→{ENTREGADO}`, `ENTREGADO→{RECIBIDO}`, `RECIBIDO|ENTREGADO→CERRADO`, y `{INICIADO, LINK_ENVIADO, DATOS_CARGADOS, COTIZADO}→CANCELADO`. `CERRADO` y `CANCELADO` no tienen salidas.
  - `class TransicionInvalida(Exception)` con atributos `actual: Estado`, `destino: Estado`.
  - `validar_transicion(actual: Estado, destino: Estado) -> None` (lanza `TransicionInvalida`).
  - `CANCELABLES: frozenset[Estado]` = los 4 estados previos al pago.

- [ ] **Step 1: Test que falla** — parametrizar todas las transiciones válidas de `TRANSICIONES` (no lanzan) y estos casos inválidos (lanzan `TransicionInvalida`): `INICIADO→COTIZADO` (salto), `PAGADO→COTIZADO` (retroceso), `PAGADO→CANCELADO`, `CERRADO→CANCELADO`, `CANCELADO→LINK_ENVIADO`, `EN_PUERTA→CERRADO` (cerrar sin confirmaciones). Más: `assert CANCELABLES == {Estado.INICIADO, Estado.LINK_ENVIADO, Estado.DATOS_CARGADOS, Estado.COTIZADO}`.
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar `estados.py`.
- [ ] **Step 4:** Correr → PASS.
- [ ] **Step 5: Commit** `feat(demo): máquina de estados del pedido`

### Task 4: Crear pedido, reloj, eventos y bandeja de mensajes (pasos 1–3)

**Files:**
- Create: `sistema-demo/delivery/reloj.py`, `sistema-demo/delivery/mensajes.py`, `sistema-demo/delivery/pedidos.py`, `sistema-demo/delivery/rutas_pedidos.py`
- Modify: `sistema-demo/delivery/main.py` (routers + manejadores de excepciones)
- Test: `sistema-demo/tests/test_crear_pedido.py`, `sistema-demo/tests/test_mensajes.py`

**Interfaces:**
- Consumes: `Ctx`, `Estado`, `validar_transicion`, `TransicionInvalida`.
- Produces:
  - `reloj.ahora_utc() -> datetime` (tz-aware; los tests la reemplazan con `monkeypatch`). `reloj.ZONAS = {"cliente": "America/Mexico_City", "servicio": "America/New_York", "delivery": "America/Argentina/Buenos_Aires"}`. `reloj.marca_tiempo(actor: str, cfg: Config) -> str`: sin defecto devuelve UTC `"%Y-%m-%dT%H:%M:%S.%fZ"` (el defecto se agrega en Task 8).
  - `mensajes.enviar(ctx, pedido_id: int, destino: Literal["cliente","delivery"], telefono: str, texto: str, link: str | None) -> None` (canal fijo `"whatsapp"`); `mensajes.listar(ctx, destino: str | None, pedido_id: int | None) -> list[dict]`. Ruta `GET /mensajes?destino=&pedido_id=`.
  - `pedidos.PedidoNoEncontrado(Exception)`; `pedidos._avanzar(ctx, pedido_id, destino: Estado, actor: str) -> None` (valida transición, actualiza `estado`, inserta evento con `marca_tiempo`): **toda** mutación de estado pasa por acá.
  - `pedidos.crear_pedido(ctx, telefono: str) -> int`: inserta en `INICIADO` (actor `cliente`) y, en la misma llamada, el paso 3: mensaje al cliente con `link = f"/cliente/pedido/{id}"` y avance a `LINK_ENVIADO` (actor `servicio`).
  - `pedidos.obtener_pedido(ctx, pedido_id) -> dict` con este JSON (lo devuelven todas las rutas de pedido):
    `{"id", "telefono", "estado", "items": [{"plato_id","nombre","cantidad","precio_unitario","subtotal"}], "direccion", "lat", "lng", "total", "demora_min", "firmado", "recibido_cliente", "entregado_delivery", "cancelado_por", "eventos": [{"estado","actor","ocurrido_en"}]}`. Los eventos se ordenan con `ORDER BY ocurrido_en` **solamente** (sin desempate por id: así se ve el defecto de Task 8).
  - `pedidos.listar_pedidos(ctx) -> list[dict]` (mismo JSON sin `eventos`, más nuevo primero).
  - Rutas: `POST /pedidos` body `{"telefono": str}` → 201 + pedido; `GET /pedidos`; `GET /pedidos/{id}`.
  - Manejadores en `main.py`: `PedidoNoEncontrado` → 404 `{"detail": {"error": "pedido_no_encontrado"}}`; `TransicionInvalida` → 409 `{"detail": {"error": "transicion_invalida", "estado_actual": ..., "destino": ...}}`.
  - Todos los modelos Pydantic de entrada usan `model_config = ConfigDict(extra="forbid")`. Teléfono: regex `^\+?\d{8,15}$`.

- [ ] **Step 1: Tests que fallan**

```python
def test_crear_pedido_envia_link_por_whatsapp(cliente):
    r = cliente.post("/pedidos", json={"telefono": "+5215512345678"})
    assert r.status_code == 201
    p = r.json()
    assert p["estado"] == "LINK_ENVIADO"
    assert [e["estado"] for e in p["eventos"]] == ["INICIADO", "LINK_ENVIADO"]
    msgs = cliente.get("/mensajes", params={"destino": "cliente", "pedido_id": p["id"]}).json()
    assert msgs[0]["link"] == f"/cliente/pedido/{p['id']}"
    assert msgs[0]["canal"] == "whatsapp"

@pytest.mark.parametrize("tel", ["", "1234567", "+54911abc", "1" * 16])
def test_telefono_invalido_da_422(cliente, tel): ...

def test_pedido_inexistente_da_404(cliente):
    r = cliente.get("/pedidos/999")
    assert r.status_code == 404
    assert r.json()["detail"]["error"] == "pedido_no_encontrado"

def test_pedido_sobrevive_reinicio(tmp_path): ...  # crear con una app, leer con otra sobre el mismo db_path

def test_timestamps_en_utc_con_z(cliente):
    p = cliente.post("/pedidos", json={"telefono": "1122334455"}).json()
    assert all(e["ocurrido_en"].endswith("Z") for e in p["eventos"])
```

- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar `reloj.py`, `mensajes.py`, `pedidos.py` (crear/obtener/listar/`_avanzar`), `rutas_pedidos.py` y los manejadores.
- [ ] **Step 4:** Correr la suite completa → PASS.
- [ ] **Step 5: Commit** `feat(demo): crear pedido con link por WhatsApp simulado`

### Task 5: Cargar datos y cotización (pasos 4–5)

**Files:**
- Modify: `sistema-demo/delivery/pedidos.py`, `sistema-demo/delivery/rutas_pedidos.py`
- Test: `sistema-demo/tests/test_cotizacion.py`

**Interfaces:**
- Consumes: `catalogo.precios`, `_avanzar`, `mensajes.enviar`.
- Produces:
  - `pedidos.cargar_datos(ctx, pedido_id, items: list[tuple[int, int]], direccion: str, lat: float | None, lng: float | None) -> None`: valida, guarda los items con el **precio del catálogo**, avanza a `DATOS_CARGADOS` (actor `cliente`) y, en la misma llamada, paso 5: calcula `total`, `demora_min = min(60, 30 + 5 * max(0, unidades - 2))`, envía mensaje al cliente `f"Total ${total} - demora {demora_min} min"` y avanza a `COTIZADO` (actor `servicio`).
  - `PUT /pedidos/{id}` body `{"items": [{"plato_id": int, "cantidad": int}], "direccion": str, "lat": float | None, "lng": float | None}`.
  - Validación (422): `items` con 1 a 4 elementos; `cantidad` entre **1 y 10**; `plato_id` existente (`{"error": "plato_inexistente"}`); plato repetido (`{"error": "plato_repetido"}`); `direccion` sin espacios en los extremos de 1 a 200 caracteres; `lat` en [-90, 90] y `lng` en [-180, 180]; cualquier campo extra (por ejemplo `total`).

- [ ] **Step 1: Tests que fallan**

```python
def test_total_lo_calcula_el_servidor(cliente, pedido_nuevo):
    r = cliente.put(f"/pedidos/{pedido_nuevo}", json={
        "items": [{"plato_id": 1, "cantidad": 2}, {"plato_id": 4, "cantidad": 1}],
        "direccion": "Av. Siempre Viva 742", "lat": -34.6, "lng": -58.4})
    p = r.json()
    assert r.status_code == 200
    assert p["estado"] == "COTIZADO"
    assert p["total"] == 2 * 9000 + 4500
    assert p["demora_min"] == 35

def test_total_enviado_por_el_cliente_se_rechaza(cliente, pedido_nuevo):
    r = cliente.put(f"/pedidos/{pedido_nuevo}", json={**DATOS_OK, "total": 1})
    assert r.status_code == 422

@pytest.mark.parametrize("cantidad,esperado", [(0, 422), (1, 200), (10, 200), (11, 422)])
def test_valores_limite_de_cantidad(cliente, pedido_nuevo, cantidad, esperado): ...

def test_plato_repetido_da_422(cliente, pedido_nuevo): ...
def test_direccion_vacia_o_solo_espacios_da_422(cliente, pedido_nuevo): ...
def test_cargar_datos_dos_veces_da_409(cliente, pedido_nuevo): ...  # ya está COTIZADO
def test_demora_tiene_tope_de_60(cliente, pedido_nuevo): ...  # 4 platos x 10 unidades -> 60
```

  Agregar a `conftest.py` la fixture `pedido_nuevo` (id de un pedido en `LINK_ENVIADO`) y la constante `DATOS_OK`.
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar `cargar_datos` y la ruta `PUT`.
- [ ] **Step 4:** Correr la suite → PASS.
- [ ] **Step 5: Commit** `feat(demo): carga de datos y cotización calculada en el servidor`

### Task 6: Firma, pago idempotente y asignación al delivery (pasos 6–7)

**Files:**
- Modify: `sistema-demo/delivery/pedidos.py`, `sistema-demo/delivery/rutas_pedidos.py`, `sistema-demo/delivery/db.py` (columna `firma TEXT` en `pedidos`)
- Test: `sistema-demo/tests/test_pago.py`

**Interfaces:**
- Produces:
  - `pedidos.firmar(ctx, pedido_id, imagen: str) -> None`: solo en `COTIZADO` (si no, 409 `transicion_invalida`). Se puede volver a firmar antes de pagar (reemplaza). `imagen` debe empezar con `data:image/png;base64,` y medir como máximo 200 000 caracteres (si no, 422).
  - `pedidos.pagar(ctx, pedido_id) -> None`: en `COTIZADO` sin firma → 409 `{"error": "firma_requerida"}`; en `COTIZADO` con firma → avanza a `PAGADO` (actor `cliente`) y, en la misma llamada, paso 7: mensaje al delivery (`cfg.delivery_telefono`, texto con la dirección, `link = f"/delivery/pedido/{id}"`) y avanza a `ASIGNADO` (actor `servicio`). **Idempotencia:** si el pedido ya está en `PAGADO` o un estado posterior (excepto `CANCELADO`), no hace nada y la ruta responde 200 con el pedido.
  - `class FirmaRequerida(Exception)` → 409 en `main.py`.
  - Rutas: `POST /pedidos/{id}/firma` body `{"imagen": str}`; `POST /pedidos/{id}/pago` sin body.
  - Fixture `pedido_cotizado` en `conftest.py`.

- [ ] **Step 1: Tests que fallan**

```python
def test_pagar_sin_firma_da_409(cliente, pedido_cotizado):
    r = cliente.post(f"/pedidos/{pedido_cotizado}/pago")
    assert r.status_code == 409 and r.json()["detail"]["error"] == "firma_requerida"

def test_pago_asigna_delivery_y_le_manda_whatsapp(cliente, pedido_cotizado):
    cliente.post(f"/pedidos/{pedido_cotizado}/firma", json={"imagen": FIRMA_OK})
    p = cliente.post(f"/pedidos/{pedido_cotizado}/pago").json()
    assert p["estado"] == "ASIGNADO"
    msg = cliente.get("/mensajes", params={"destino": "delivery", "pedido_id": pedido_cotizado}).json()[0]
    assert msg["link"] == f"/delivery/pedido/{pedido_cotizado}"

def test_pago_doble_no_duplica(cliente, pedido_cotizado):
    cliente.post(f"/pedidos/{pedido_cotizado}/firma", json={"imagen": FIRMA_OK})
    cliente.post(f"/pedidos/{pedido_cotizado}/pago")
    r = cliente.post(f"/pedidos/{pedido_cotizado}/pago")
    assert r.status_code == 200
    assert [e["estado"] for e in r.json()["eventos"]].count("PAGADO") == 1

def test_firma_que_no_es_png_da_422(cliente, pedido_cotizado): ...
def test_firmar_antes_de_cotizar_da_409(cliente, pedido_nuevo): ...
```

  `FIRMA_OK = "data:image/png;base64,iVBORw0KGgo="` en `conftest.py`.
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** Correr la suite → PASS.
- [ ] **Step 5: Commit** `feat(demo): firma, pago idempotente y asignación al delivery`

### Task 7: Recorrido del delivery, confirmaciones, cierre y cancelación (pasos 8–13)

**Files:**
- Modify: `sistema-demo/delivery/pedidos.py`, `sistema-demo/delivery/rutas_pedidos.py`
- Test: `sistema-demo/tests/test_entrega.py`, `sistema-demo/tests/test_cancelacion.py`, `sistema-demo/tests/test_rutas_404.py`

**Interfaces:**
- Produces:
  - `pedidos.marcar_retirado(ctx, id)`: `ASIGNADO→RETIRADO` (actor `delivery`) y, en la misma llamada, paso 9: mensaje al cliente "Tu pedido está en camino" y `→EN_CAMINO` (actor `servicio`).
  - `pedidos.marcar_en_puerta(ctx, id)`: `EN_CAMINO→EN_PUERTA` (actor `delivery`).
  - `pedidos.confirmar_recibido(ctx, id)` (actor `cliente`) y `pedidos.confirmar_entregado(ctx, id)` (actor `delivery`): ponen su bandera en true y avanzan a `RECIBIDO` o `ENTREGADO`. Si la otra bandera ya estaba, en la misma llamada se hace el paso 13: `→CERRADO` (actor `servicio`). Repetir la misma confirmación → 409 `transicion_invalida`.
  - `pedidos.cancelar(ctx, id, por: Literal["cliente","servicio"]) -> None`: estado en `CANCELABLES` → `CANCELADO`, guarda `cancelado_por` (actor = `por`); si no → 409 `{"error": "no_cancelable", "estado_actual": ..., "mensaje": "No se puede cancelar un pedido que ya fue pagado"}` (para `CERRADO`/`CANCELADO` el mensaje es "El pedido ya está finalizado").
  - Rutas: `POST /pedidos/{id}/retirado`, `/en-puerta`, `/recibido`, `/entregado`, `/cancelar` (body `{"por": "cliente"|"servicio"}`).
  - Fixture `pedido_asignado`.

- [ ] **Step 1: Tests que fallan**
  - `test_flujo_completo_los_13_pasos`: desde `POST /pedidos` hasta `CERRADO`. Afirma la lista exacta de estados de `eventos` (12 eventos, de `INICIADO` a `CERRADO`, con `RECIBIDO` antes de `ENTREGADO`) y 4 mensajes en la bandeja (link al cliente, cotización, delivery, en camino).
  - `test_entregado_antes_que_recibido_tambien_cierra`: orden inverso → `CERRADO`.
  - `test_cerrar_requiere_las_dos_confirmaciones`: solo `recibido` → estado `RECIBIDO`, no `CERRADO`.
  - `test_confirmacion_repetida_da_409`.
  - `test_retirado_antes_de_pagar_da_409` (pedido en `COTIZADO`).
  - **Tabla de decisión de cancelación**, parametrizada con `(estado_de_partida, por, código_esperado)`: `LINK_ENVIADO/cliente → 200`, `COTIZADO/servicio → 200`, `ASIGNADO/cliente → 409 no_cancelable`, `CERRADO/servicio → 409`, `CANCELADO/cliente → 409`. Además: `por` inválido → 422.
  - `test_rutas_404`: parametrizar las 9 rutas de pedido (`GET`, `PUT`, `firma`, `pago`, `retirado`, `en-puerta`, `recibido`, `entregado`, `cancelar`) con id 999 → 404 `pedido_no_encontrado`.
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** Correr la suite → PASS.
- [ ] **Step 5: Commit** `feat(demo): entrega, cierre y cancelación`

### Task 8: Defectos sembrados (zona horaria y contrato)

**Files:**
- Modify: `sistema-demo/delivery/reloj.py`, `sistema-demo/delivery/catalogo.py`, `sistema-demo/delivery/pedidos.py`
- Create: `sistema-demo/delivery/formato.py`
- Test: `sistema-demo/tests/test_defectos.py`

**Interfaces:**
- Produces:
  - `reloj.marca_tiempo` con `cfg.defecto_zona_horaria=True`: hora **local del actor** según `ZONAS`, con formato `"%Y-%m-%dT%H:%M:%S.%f"` **sin offset ni Z** (no se normaliza a UTC).
  - `formato.pesos(n: int) -> str` → `"$ 9.000"` (separador de miles con punto).
  - Con `cfg.defecto_contrato=True`: `precio` en `/platos` y `precio_unitario`, `subtotal` y `total` en el pedido se serializan con `formato.pesos` (texto). La base sigue guardando enteros: el defecto está solo en el contrato de salida.

- [ ] **Step 1: Tests que fallan**

```python
def test_defecto_zona_horaria_desordena_la_linea_de_tiempo(crear_cliente, monkeypatch):
    c = crear_cliente(defecto_zona_horaria=True)
    instantes = iter([datetime(2026, 11, 14, 15, 0, s, tzinfo=UTC) for s in range(0, 60, 5)])
    monkeypatch.setattr("delivery.reloj.ahora_utc", lambda: next(instantes))
    estados = [e["estado"] for e in llevar_a_pagado(c)["eventos"]]  # helper local: crear, cargar datos, firmar, pagar
    assert estados.index("PAGADO") < estados.index("COTIZADO")   # el bug visible

def test_sin_defecto_la_linea_de_tiempo_esta_en_orden(crear_cliente, monkeypatch):
    ...  # mismos instantes, flag apagado -> orden de la tabla del spec

def test_defecto_contrato_precio_como_texto(crear_cliente):
    platos = crear_cliente(defecto_contrato=True).get("/platos").json()
    assert platos[0]["precio"] == "$ 9.000"

def test_defecto_contrato_total_como_texto(crear_cliente): ...  # total == "$ 22.500"
```

  (Con el defecto, los eventos del servicio quedan con hora de Nueva York (UTC-5, ~`10:00`) y los del cliente con hora de México (UTC-6, ~`09:00`). Al ordenar por texto, PAGADO (cliente) queda antes que COTIZADO (servicio), aunque ocurrió después.)
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar.
- [ ] **Step 4:** Correr la suite completa: los tests de Tasks 1–7 siguen en verde porque los defectos están apagados por defecto.
- [ ] **Step 5: Commit** `feat(demo): defectos sembrados activables por variable de entorno`

### Task 9: Páginas del cliente y del delivery

**Files:**
- Create: `sistema-demo/delivery/paginas/inicio.html`, `cliente.html`, `delivery.html`, `estilos.css`, `api.js`
- Modify: `sistema-demo/delivery/main.py` (rutas `GET /`, `GET /cliente/pedido/{id}`, `GET /delivery/pedido/{id}` con `FileResponse`; `StaticFiles` en `/estaticos`)
- Test: `sistema-demo/tests/test_paginas.py`

**Interfaces:**
- Consumes: todas las rutas de la API (llamadas con `fetch` desde `api.js`).
- Produces (`data-testid` exactos que usan las etapas 3–4):
  - `inicio.html` (pasos 1–2): `catalogo`, `plato-{id}`, `input-telefono`, `btn-pedir`, `msg-link-enviado`.
  - `cliente.html`: muestra la sección según `estado`. Carga de datos: `cantidad-{plato_id}`, `input-direccion`, `btn-ubicacion` (usa `navigator.geolocation`), `mapa` (Leaflet 1.9.4 por unpkg + teselas OSM: un clic fija lat/lng), `total-estimado` (se calcula en JS como `precio * cantidad` sumado desde `/platos`; con el defecto de contrato muestra `NaN`, y así el defecto es visible), `btn-confirmar-datos`. Cotización: `total`, `demora`, `canvas-firma`, `btn-limpiar-firma`, `btn-pagar`. Seguimiento: `estado-pedido`, `btn-recibido`, `btn-cancelar`. Errores de la API: `msg-error`.
  - `delivery.html`: `direccion-entrega`, `btn-retirado`, `btn-en-puerta`, `btn-entregado`, `estado-pedido`, `msg-error`.
  - Diseño mobile-first (ancho 360 px, el del A11), sin frameworks.

- [ ] **Step 1: Test que falla** (smoke): `GET /`, `/cliente/pedido/1` y `/delivery/pedido/1` → 200, `text/html`, y cada uno contiene sus `data-testid` principales (`btn-pedir`; `canvas-firma` y `btn-pagar`; `btn-entregado`).
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar las páginas.
- [ ] **Step 4:** Correr la suite → PASS.
- [ ] **Step 5: Prueba manual** (el usuario, en el navegador de la PC): levantar uvicorn y recorrer los 13 pasos haciendo clic, con la página del cliente y la del delivery en dos pestañas y los links sacados de `GET /mensajes`. Repetir con `DEMO_DEFECTO_CONTRATO=1` y verificar `NaN` en `total-estimado`. Anotar lo que no guste para la sección Mejoras.
- [ ] **Step 6: Commit** `feat(demo): páginas mobile del cliente y del delivery`

### Task 10: Panel central, README y vista HTML de la etapa

**Files:**
- Create: `sistema-demo/delivery/paginas/panel.html`; `sistema-demo/README.md`; `sistema-demo/docs/defectos/DEF-001-zona-horaria.md`, `DEF-002-contrato-precio.md`; `vistas/etapa-1-sistema-demo.html`
- Modify: `sistema-demo/delivery/main.py` (ruta `GET /panel`)
- Test: `sistema-demo/tests/test_paginas.py` (agregar el panel)

**Interfaces:**
- Produces:
  - `panel.html`: `tabla-pedidos` (fila `pedido-{id}` con estado, total y teléfono), `linea-de-tiempo` (los eventos en el orden en que llegan de la API, con actor y hora), `bandeja-mensajes`, `estado-defectos` (lee `/salud`), `btn-cancelar-servicio`.
  - `README.md`: cómo instalar y levantar el sistema, cómo correr los tests, cómo prender cada defecto, la tabla de estados y la de rutas, y la leyenda "Prácticas alineadas al syllabus ISTQB CTFL v4.0".
  - Informes de defecto (formato ISO/IEC/IEEE 29119-3): id, título, severidad y prioridad, pasos para reproducir (con la variable de entorno), resultado esperado y obtenido, evidencia (la captura del panel o del `NaN`), causa raíz y corrección propuesta.
  - `vistas/etapa-1-sistema-demo.html` (se abre con doble clic, sin servidor; mismo estilo que `mockups/portada-dashboard.html`): diagrama de estados, actores y rutas, con los recuadros **"En términos técnicos"** (máquina de estados, idempotencia, validación del lado servidor, bug seeding), **"Cómo se mide"** (cantidad de tests y de transiciones cubiertas: se cargan a mano en esta etapa, la automatización llega en la etapa 2), **"Norma / estándar"** (las filas del §6 del spec que aplican) y **"Mejoras"** (las notas de la prueba manual de Task 9).

- [ ] **Step 1: Test que falla:** `GET /panel` → 200 y contiene `linea-de-tiempo` y `estado-defectos`.
- [ ] **Step 2:** Correr → FAIL.
- [ ] **Step 3:** Implementar el panel, el README, los 2 informes de defecto y la vista.
- [ ] **Step 4:** Correr la suite completa → PASS. Abrir `/panel` con `DEMO_DEFECTO_ZONA_HORARIA=1`, completar un pedido hasta pago y ver PAGADO antes que COTIZADO en `linea-de-tiempo`.
- [ ] **Step 5:** Revisión de confidencialidad: `git grep -n -i` con las palabras de la lista privada del usuario (rubro, nombre de la empresa, herramienta interna) sobre todo lo versionado → sin resultados.
- [ ] **Step 6: Commit** `feat(demo): panel central, README y vista de la etapa 1`
