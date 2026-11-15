# Sistema demo: delivery de comidas

Sistema **ficticio** bajo prueba del QA Portfolio. Un cliente pide comida desde la web móvil, el servicio cotiza y asigna, y un delivery la lleva. Todo pasa por una **máquina de estados**, los mensajes de WhatsApp se simulan en una bandeja y hay **dos defectos sembrados** que se prenden con variables de entorno, para que las pruebas de las etapas siguientes tengan algo real que encontrar.

> Prácticas alineadas al syllabus ISTQB CTFL v4.0.

**Stack:** Python 3.12 · FastAPI · SQLite · HTML + JS plano (sin build). Se corre en una PC modesta y sin servidor externo.

**Cómo se construyó, paso a paso:** [`../pasos/README.md`](../pasos/README.md) (versión visual: `../pasos/pasos.html`).
**Vista de la etapa:** [`../vistas/etapa-1-sistema-demo.html`](../vistas/etapa-1-sistema-demo.html) (se abre con doble clic).

## 1. Instalar

Desde esta carpeta (`sistema-demo/`), con Git Bash en Windows:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

En Linux o macOS, cambiar `.venv/Scripts/python` por `.venv/bin/python`.

## 2. Levantar

```bash
.venv/Scripts/python -m uvicorn delivery.main:app
```

| Página | URL | Para quién |
|---|---|---|
| Inicio (catálogo y teléfono) | http://localhost:8000/ | Cliente |
| Pedido del cliente | http://localhost:8000/cliente/pedido/1 | Cliente (llega por el link del mensaje) |
| Pedido del delivery | http://localhost:8000/delivery/pedido/1 | Delivery (llega por el link del mensaje) |
| Panel central | http://localhost:8000/panel | Servicio: todos los pedidos, su línea de tiempo y la bandeja |
| Documentación de la API | http://localhost:8000/docs | OpenAPI que genera FastAPI |

La base se crea sola en `data/demo.db`. Para usar otra (por ejemplo, para no mezclar pruebas): `DEMO_DB_PATH=data/otra.db`.

## 3. Correr los tests

```bash
.venv/Scripts/python -m pytest -q          # 196 tests
.venv/Scripts/python -m pytest -q tests/test_defectos.py -v
```

| Archivo | Tests | Qué cubre |
|---|---:|---|
| `test_estados.py` | 29 | Las 18 transiciones válidas, las inválidas con nombre y los 13 × 13 pares |
| `test_cotizacion.py` | 42 | Cantidades y dirección (valores límite y particiones), total del servidor |
| `test_pago.py` | 32 | Firma, pago idempotente, asignación al delivery |
| `test_defectos.py` | 18 | Cada defecto prendido y su par apagado |
| `test_crear_pedido.py` | 14 | Teléfono, estado inicial y mensaje con link |
| `test_cancelacion.py` | 14 | Cancelar antes del pago (cliente o servicio) y `409` después |
| `test_entrega.py` | 14 | Retiro, en puerta, confirmaciones en cualquier orden y cierre |
| `test_rutas_404.py` | 9 | Pedido inexistente en cada ruta |
| `test_concurrencia.py` | 8 | Carreras de pago y cancelación, conexión usada desde otro hilo |
| `test_paginas.py` | 7 | Las 4 páginas con sus `data-testid` y los estáticos |
| `test_mensajes.py` | 5 | Bandeja de WhatsApp simulado |
| `test_catalogo.py` | 2 | Catálogo de platos |
| `test_salud.py` | 2 | `/salud` y el estado de los defectos |
| **Total** | **196** | |

## 4. Defectos sembrados

Están **apagados por defecto**. Se prenden con una variable de entorno en `1` y `GET /salud` (y el panel central) informa cuáles están activos.

| Variable | Defecto | Qué se ve | Informe |
|---|---|---|---|
| `DEMO_DEFECTO_ZONA_HORARIA=1` | Cada actor guarda su hora local sin offset | La línea de tiempo queda desordenada: **PAGADO antes que COTIZADO** | [DEF-001](docs/defectos/DEF-001-zona-horaria.md) |
| `DEMO_DEFECTO_CONTRATO=1` | Los montos salen como texto (`"$ 9.000"`) | El total estimado del cliente muestra **`NaN`**; un contrato que espera `integer` falla | [DEF-002](docs/defectos/DEF-002-contrato-precio.md) |

```bash
DEMO_DB_PATH=data/defectos.db DEMO_DEFECTO_ZONA_HORARIA=1 DEMO_DEFECTO_CONTRATO=1 \
  .venv/Scripts/python -m uvicorn delivery.main:app
```

Además hubo un **defecto real**, no sembrado, que encontró el panel central y quedó corregido con su test de regresión: [DEF-003](docs/defectos/DEF-003-sqlite-entre-hilos.md) (`500` al azar con requests en paralelo).

## 5. Estados del pedido

| # | Actor | Acción | Estado | Ruta |
|---|---|---|---|---|
| 2 | Cliente | Deja su teléfono | `INICIADO` | `POST /pedidos` |
| 3 | Servicio | Envía el link por WhatsApp (simulado) | `LINK_ENVIADO` | automático |
| 4 | Cliente | Carga platos, cantidades y dirección | `DATOS_CARGADOS` | `PUT /pedidos/{id}` |
| 5 | Servicio | Calcula el total y la demora | `COTIZADO` | automático |
| 6 | Cliente | Firma y paga | `PAGADO` | `POST /pedidos/{id}/firma` y `/pago` |
| 7 | Servicio | Envía la dirección al delivery | `ASIGNADO` | automático |
| 8 | Delivery | Retira el pedido | `RETIRADO` | `POST /pedidos/{id}/retirado` |
| 9 | Servicio | Avisa al cliente que va en camino | `EN_CAMINO` | automático |
| 10 | Delivery | Llega a la dirección | `EN_PUERTA` | `POST /pedidos/{id}/en-puerta` |
| 11 | Cliente | Confirma que recibió | `RECIBIDO` | `POST /pedidos/{id}/recibido` |
| 12 | Delivery | Confirma que entregó | `ENTREGADO` | `POST /pedidos/{id}/entregado` |
| 13 | Servicio | Cierra cuando confirmaron los dos | `CERRADO` | automático |
| — | Cliente o servicio | Cancela **antes del pago** | `CANCELADO` | `POST /pedidos/{id}/cancelar` |

Reglas:

- Las transiciones solo avanzan en este orden: cualquier salto o retroceso responde **`409`** `transicion_invalida`. Son **18 transiciones válidas** en total.
- Los pasos 11 y 12 van en cualquier orden; el pedido se cierra cuando están los dos.
- Se puede cancelar de `INICIADO` a `COTIZADO`. Después del pago responde **`409`** `no_cancelable`.
- **El total lo calcula el servidor.** Si el cliente manda un `total`, la API responde `422`.
- **El pago es idempotente:** pagar dos veces responde `200` con el mismo pedido y no cobra de nuevo.
- `CERRADO` y `CANCELADO` son finales.

## 6. Rutas de la API

| Método | Ruta | Qué hace | Errores |
|---|---|---|---|
| `GET` | `/salud` | Estado del sistema y defectos prendidos | — |
| `GET` | `/platos` | Catálogo (3 a 4 platos) | — |
| `POST` | `/pedidos` | Crea el pedido con el teléfono | `422` |
| `GET` | `/pedidos` | Lista todos los pedidos | — |
| `GET` | `/pedidos/{id}` | Pedido con ítems, total y eventos | `404` |
| `PUT` | `/pedidos/{id}` | Carga ítems (1 a 4, cantidad 1 a 10), dirección y ubicación opcional | `404`, `409`, `422` |
| `POST` | `/pedidos/{id}/firma` | Firma en PNG (data URL) | `404`, `409`, `422` |
| `POST` | `/pedidos/{id}/pago` | Paga (idempotente; exige firma) | `404`, `409` |
| `POST` | `/pedidos/{id}/retirado` | El delivery retiró | `404`, `409` |
| `POST` | `/pedidos/{id}/en-puerta` | El delivery llegó | `404`, `409` |
| `POST` | `/pedidos/{id}/recibido` | El cliente confirma | `404`, `409` |
| `POST` | `/pedidos/{id}/entregado` | El delivery confirma | `404`, `409` |
| `POST` | `/pedidos/{id}/cancelar` | `{"por": "cliente" \| "servicio"}` | `404`, `409`, `422` |
| `GET` | `/mensajes` | Bandeja de WhatsApp simulado; filtros `destino` y `pedido_id` | `422` |

Los errores de dominio salen como `{"detail": {"error": "<código>"}}`: `pedido_no_encontrado`, `transicion_invalida`, `firma_requerida`, `no_cancelable`, `plato_repetido`, `plato_inexistente`.

## 7. Estructura

```
sistema-demo/
├── delivery/           # la app
│   ├── main.py         # crear_app, rutas de páginas y manejo de errores
│   ├── rutas_pedidos.py
│   ├── estados.py      # máquina de estados (única fuente de verdad)
│   ├── pedidos.py · catalogo.py · mensajes.py
│   ├── reloj.py        # "ahora" reemplazable; defecto de zona horaria
│   ├── formato.py      # pesos(); defecto de contrato
│   ├── db.py · config.py
│   └── paginas/        # inicio, cliente, delivery y panel (HTML + JS)
├── docs/defectos/      # informes DEF-001 a DEF-003 (ISO/IEC/IEEE 29119-3)
└── tests/              # 196 tests con pytest
```

Todos los datos son ficticios: teléfonos, direcciones, platos y nombres.
