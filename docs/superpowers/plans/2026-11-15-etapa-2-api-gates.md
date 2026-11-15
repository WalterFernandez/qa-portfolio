---
date: 2026-11-15
status: draft (esperando comentarios del usuario)
etapa: 2
spec: docs/superpowers/specs/2026-11-10-qa-portfolio-design.md (§5.1, §6, §7, §8, §10)
---

# Etapa 2: Suite de API de caja negra + gates en GitHub Actions + triage + portada — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (o desplega:implementing) para implementar este plan fase por fase. Los pasos usan checkboxes (`- [ ]`).

## Overview

La etapa 1 dejó el sistema demo funcionando, con 196 **tests de componente** que corren dentro del mismo proceso (`TestClient`). La etapa 2 construye la **suite de QA de caja negra**. Es la versión ficticia del logro del usuario: un flujo API encadenado que hace de **gate antes del deploy**, que **no bloquea en QA y bloquea en prod**, con **triage** de fallos.

La suite le pega por **HTTP real** a un servidor uvicorn. Ese servidor puede ser uno ya levantado (`BASE_URL`) o uno que la suite levanta sola en un puerto libre. Valida el **contrato con JSON Schema**, que tiene que atrapar DEF-002, y muestra las técnicas ISTQB de §5.1. Cada corrida genera **métricas reales**, que leen la portada y la vista de API, publicadas en **GitHub Pages** solo si el gate de prod pasa.

## Current State Analysis

- Sistema demo completo en `sistema-demo/`: FastAPI + SQLite, 13 estados, bandeja `/mensajes` y defectos DEF-001 y DEF-002 activables por variable de entorno (`sistema-demo/delivery/config.py:13-25`). `/salud` informa qué defectos están prendidos (`sistema-demo/delivery/main.py:26-32`).
- Los tests existentes (`sistema-demo/tests/`) usan `TestClient` y una base temporal (`tests/conftest.py:9-15`). **Nunca pasan por un servidor HTTP real.** DEF-003 (SQLite entre hilos) solo apareció con uvicorn: 194 de 200 requests en 500 antes del arreglo (`84b077f`).
- **El OpenAPI no tipa las respuestas.** Las rutas devuelven `dict`/`list[dict]` (`delivery/rutas_pedidos.py:56-137`, `delivery/main.py:34-36`), así que FastAPI publica `{"type":"object","additionalProperties":true}`. Un schema copiado del OpenAPI actual **no atrapa DEF-002**, y la frase de `docs/defectos/DEF-002-contrato-precio.md` que dice "como define el OpenAPI" no es exacta.
- Repo público `qa-portfolio` creado (remoto `origin`), con 7 commits locales sin push. No hay `.github/`, ni JSON Schema, ni reporte de tests, ni portada (`mockups/portada-dashboard.html` es el diseño aprobado).
- Pendientes del usuario de la etapa 1: prueba manual del Paso 9 con la captura del `NaN` para DEF-002, OK de las Tasks 9 y 10, y push.

## Desired End State

- `pruebas-api/` es una suite pytest + httpx + jsonschema que corre igual:
  - en local contra `BASE_URL=http://localhost:8001`;
  - en local sin `BASE_URL`: levanta uvicorn sola, en un puerto libre y con base temporal;
  - en GitHub Actions (ubuntu).
- Con los defectos apagados, todo en verde. Con `DEMO_DEFECTO_CONTRATO=1`, fallan los tests de contrato y el triage lo clasifica como **defecto de producto**, enlazando DEF-002. Con `DEMO_DEFECTO_ZONA_HORARIA=1`, falla el orden de la línea de tiempo (DEF-001).
- Cada corrida escribe `vistas/datos/resultados-api.js` y `reportes/api.html` (pytest-html).
- Tres workflows:
  - `qa.yml`: corre en cada push, no bloquea y deja el triage en el resumen.
  - `prod.yml`: en `main`, es bloqueante y publica en Pages.
  - `demo-defectos.yml`: se lanza a mano y muestra QA en rojo con triage y prod bloqueado.
- La portada (`vistas/index.html`) y la vista de API (`vistas/api.html`) se abren con doble clic y están publicadas en Pages.

### Key Discoveries:
- `GET /salud` devuelve `defectos: {zona_horaria, contrato}` (`delivery/main.py:28-32`). La suite lo usa para saber contra qué está corriendo (skip/xfail condicionado) cuando no controla el servidor.
- Errores de dominio uniformes: `404 {"detail":{"error":"pedido_no_encontrado"}}`, `409 transicion_invalida | no_cancelable | firma_requerida`, `422 {"detail":{"error":...}}` (`delivery/main.py:61-98`). Son la base de los schemas de error.
- La firma mínima válida y los datos válidos ya están definidos en `tests/conftest.py:23-38`. Se copian (no se importan) en la suite de caja negra, que no depende del código del demo.
- `_actualizar_si_sigue` (`delivery/pedidos.py:85`) es el control optimista que cubre la carrera. La prueba concurrente de la Fase 6 lo ejercita desde afuera.

## Quick Verification Reference

- Tests del demo (no se tienen que romper): `cd sistema-demo && .venv/Scripts/python -m pytest -q`
- Suite de caja negra, servidor propio: `cd pruebas-api && ../sistema-demo/.venv/Scripts/python -m pytest -q`
- Suite contra tu servidor: `BASE_URL=http://localhost:8001 ../sistema-demo/.venv/Scripts/python -m pytest -q` (desde `pruebas-api/`)
- Solo el gate: `... -m pytest -q -m gate`
- Grep de confidencialidad: `git grep -n -i -f thoughts/confidencial.txt` (la lista de términos privados vive en `thoughts/`, que no se versiona; nunca se escriben en el repo) y `git grep -n -i "certificad" -- ":!docs/superpowers"` (los dos tienen que salir vacíos)

Archivos clave: `pruebas-api/conftest.py`, `pruebas-api/soporte/`, `pruebas-api/contratos/*.json`, `.github/workflows/*.yml`, `vistas/index.html`, `vistas/api.html`.

## What We're NOT Doing

- No se hostea el sistema demo (spec §10). Pages publica solo vistas estáticas.
- No hay Postman/Newman: queda como "Mejora" en la vista de API.
- No hay Allure (decisión del usuario 2026-11-15: JSON propio + pytest-html).
- No se corrige DEF-001 ni DEF-002: siguen sembrados y apagados por defecto en `main` (spec §10).
- No se toca la lógica de negocio del demo. El único cambio en `sistema-demo/` es **documental**: se declaran los modelos de respuesta en el OpenAPI (Fase 2).
- Mobile, Web, Performance y Prime son etapas 3 a 6.

## Implementation Approach

**Decisiones (usuario, 2026-11-15):**
1. Suite de **caja negra por HTTP** en una carpeta aparte. Si no hay `BASE_URL`, levanta uvicorn sola.
2. El "deploy a prod" es **publicar en GitHub Pages**.
3. Reporte con **JSON propio + pytest-html**.

**Decisiones del constructor (se pueden cambiar):**
- **Dependencias:** `pruebas-api/requirements.txt` (`httpx`, `pytest`, `jsonschema`, `pytest-html`, con versiones fijas). En local se instala en el `.venv` existente de `sistema-demo` para no duplicar entornos en un equipo con pocos recursos. En CI se instalan los dos `requirements.txt`.
- **Contrato:** los schemas de `pruebas-api/contratos/` son del **consumidor**, escritos a mano en JSON Schema draft 2020-12 y versionados. En el demo se declaran los modelos de respuesta **solo como documentación** (`responses={200: {"model": ...}}`, **sin** `response_model`), para no cambiar el comportamiento. Con `response_model`, FastAPI validaría la salida y DEF-002 pasaría a ser un 500 en vez de `"$ 9.000"`. Un test de deriva compara los schemas del consumidor con el OpenAPI publicado. Así se muestran los dos lados del contrato, proveedor y consumidor.
- **Servidor propio:** `subprocess` con `sys.executable -m uvicorn delivery.main:app --app-dir ../sistema-demo --port <libre>` y `DEMO_DB_PATH` en `tmp_path_factory`. Espera hasta que `/salud` responda (timeout de 15 s) y se apaga con `proc.terminate()` **por PID** en el teardown.
- **Defectos:** con servidor propio, la opción `--defectos=contrato,zona_horaria` los prende en el subprocess. Con `BASE_URL`, se leen de `/salud`. Los tests que dependen de un defecto se marcan `@pytest.mark.defecto("contrato")` y verifican el comportamiento esperado **sin el defecto**. Si el defecto está prendido, fallan a propósito: esa es la demostración.
- **Etiquetas:** cada test lleva `@pytest.mark.tecnica("...")` con un valor de un catálogo cerrado (`transicion_estados`, `tabla_decision`, `valores_limite`, `particiones`, `contrato`, `riesgo`, `flujo_e2e_api`, `concurrencia`, `humo`). El plugin de reporte las agrupa.
- **Datos para la vista:** `.js` (`window.RESULTADOS_API = {...}`) en vez de `.json`, porque `fetch` no anda con `file://` y las vistas se abren con doble clic.
- **Numeración de pasos:** las fases 1 a 9 son los pasos 11 a 19 en `pasos/`.

**Cierre de cada fase** (el mismo modo de trabajo de la etapa 1, `thoughts/handoffs/completed/2026-11-15-etapa-1-task-10.md`):
- TDD (rojo → verde) más mutación manual donde aplique.
- `pasos/paso-NN-<tema>.md` + fila en `pasos/README.md` + diapositivas en `pasos.html` antes de `<!-- Cierre -->` + fichas en `terminos.json` (empalme con script que respete strings) + `generar_glosario.py` + "Dónde lo aplicamos".
- Etiquetas 📘 ISTQB / 📐 Norma / ✅ Buena práctica. Nunca escribir "certificado".
- Grep de confidencialidad. **Commit sin push.** Marcar los checkboxes. OK del usuario.

---

## Phase 1: Esqueleto de `pruebas-api/` y smoke (Paso 11)

### Overview
Arma la suite de caja negra con su fixture de servidor y dos tests de humo. Es la base de todas las fases siguientes.

### Changes Required:

#### 1. Proyecto de la suite
**Files:** `pruebas-api/requirements.txt`, `pruebas-api/pytest.ini`, `pruebas-api/README.md`
**Changes:**
- `pytest.ini`: `testpaths = tests`, registra los marcadores `gate`, `tecnica`, `defecto` y `lento`, y agrega `--strict-markers`.
- README: cómo correr la suite contra un servidor propio y contra `BASE_URL`, cómo prender defectos y qué la diferencia de `sistema-demo/tests` (componente contra sistema, dev contra QA).

#### 2. Fixtures
**File:** `pruebas-api/conftest.py`, `pruebas-api/soporte/servidor.py`, `pruebas-api/soporte/api.py`
**Changes:**
- `servidor` (scope session): devuelve la URL base. Usa `BASE_URL` si está; si no, levanta uvicorn como se describe en Implementation Approach. Si el puerto está ocupado o el servidor no responde, el error lo dice claro, porque después el triage lo clasifica como **ambiente**.
- `api`: un `httpx.Client(base_url=..., timeout=5)` con un *event hook* que registra método, ruta normalizada (`/pedidos/{id}`), status y duración. Lo consume la Fase 7.
- `defectos_activos`: lee `/salud`.
- Helpers en `soporte/api.py`: `crear_pedido()`, `cotizar()`, `pagar()` y `avanzar_hasta(estado)`, todos por HTTP.

#### 3. Humo
**File:** `pruebas-api/tests/test_humo.py`
**Changes:** `/salud` responde 200 con `estado == "ok"`; `/platos` devuelve entre 3 y 4 platos. Marcados `tecnica("humo")` y `gate`.

### Success Criteria:

#### Automated Verification:
- [ ] Suite con servidor propio en verde: `cd pruebas-api && ../sistema-demo/.venv/Scripts/python -m pytest -q`
- [ ] No quedan procesos uvicorn colgados después de la corrida: `powershell -c "Get-NetTCPConnection -State Listen | ? LocalPort -ge 49152 | Select OwningProcess"` (sin el PID que imprimió la suite)
- [ ] Tests del demo intactos: `cd sistema-demo && .venv/Scripts/python -m pytest -q` (196 passed)
- [ ] Marcador inventado rechazado: con `@pytest.mark.tecnicaa` en un test de prueba, la corrida falla por `--strict-markers`

#### Manual Verification:
- [ ] Con tu servidor prendido en :8001: `BASE_URL=http://localhost:8001 ... -m pytest -q` en verde, y en `/panel` no aparecen pedidos raros (los de humo no crean pedidos)
- [ ] Con :8001 apagado y `BASE_URL` apuntando ahí, el error dice "no responde el servidor en …" (no un stacktrace críptico)

**Implementation Note**: pausar para el OK antes de la Fase 2.

---

## Phase 2: Contrato con JSON Schema (Paso 12) — atrapa DEF-002

### Overview
Schemas del consumidor para todas las respuestas, más los modelos documentados en el OpenAPI del proveedor y un test de deriva entre los dos.

### Changes Required:

#### 1. Modelos documentales en el demo
**File:** `sistema-demo/delivery/modelos.py` (nuevo), `delivery/main.py`, `delivery/rutas_pedidos.py`
**Changes:** modelos Pydantic `Plato`, `Item`, `Evento`, `Pedido`, `PedidoDetalle`, `Mensaje` y `Error` con montos `int`. Se declaran con `responses={200: {"model": ...}, 404: {...}, 409: {...}, 422: {...}}` en cada ruta. **No** se usa `response_model`. Test en `sistema-demo/tests/test_openapi.py` que verifica que `precio`, `precio_unitario`, `subtotal` y `total` figuran como `integer` en el OpenAPI.

#### 2. Schemas del consumidor
**Files:** `pruebas-api/contratos/{plato,pedido,pedido-detalle,mensaje,error}.schema.json`
**Changes:** draft 2020-12, `additionalProperties: false` y montos `{"type":"integer","minimum":0}` (`total` acepta `null` antes de cotizar). Los estados van como `enum` con los 13 valores.

#### 3. Tests de contrato
**File:** `pruebas-api/tests/test_contrato.py`, `pruebas-api/soporte/contrato.py`
**Changes:**
- Valida cada respuesta del flujo (catálogo, crear, cotizar, pagar, detalle, mensajes, errores 404/409/422). Usa `jsonschema.Draft202012Validator` y, cuando falla, muestra **campo, valor y tipo esperado**.
- `test_deriva_openapi`: para cada schema del consumidor, los campos y tipos coinciden con el componente del `/openapi.json`. Si alguien cambia el proveedor, este test avisa: es el ejemplo de **test desactualizado** para el triage.
- Marcados `tecnica("contrato")` y `defecto("contrato")`.

#### 4. Corrección del informe
**File:** `sistema-demo/docs/defectos/DEF-002-contrato-precio.md`
**Changes:** "como define el OpenAPI" pasa a ser verdad, con una nota de que desde el Paso 12 los modelos están documentados. Se agrega la sección "Cómo lo atrapa la etapa 2" con la salida real del test.

### Success Criteria:

#### Automated Verification:
- [ ] Contrato en verde con defectos apagados: `... -m pytest -q tests/test_contrato.py`
- [ ] **Atrapa DEF-002**: `... -m pytest -q tests/test_contrato.py --defectos=contrato` falla, y el mensaje menciona `precio` con `'$ 9.000' is not of type 'integer'`
- [ ] Deriva: si en una copia se cambia `precio: int` por `str` en `modelos.py`, `test_deriva_openapi` falla (mutación manual, archivo restaurado en `finally`)
- [ ] Demo intacto y test nuevo de OpenAPI en verde: `cd sistema-demo && .venv/Scripts/python -m pytest -q`
- [ ] DEF-002 sigue reproduciéndose: `DEMO_DEFECTO_CONTRATO=1` hace que `/platos` devuelva `"precio": "$ 9.000"` con status 200 (no 500)

#### Manual Verification:
- [ ] En `http://localhost:8001/docs` los schemas de respuesta muestran los campos tipados
- [ ] El mensaje de fallo del contrato se entiende sin leer el código

### QA Spec (optional):
Con :8001 levantado con `DEMO_DEFECTO_CONTRATO=1` y `BASE_URL` apuntando ahí, la suite marca los tests de contrato en rojo y el resto en verde.

**Implementation Note**: pausar para el OK antes de la Fase 3.

---

## Phase 3: Flujo encadenado, el gate (Paso 13)

### Overview
La pieza STAR: un solo test que recorre los 13 pasos del pedido por API, sacando los links de la bandeja como en el trabajo real.

### Changes Required:

#### 1. Flujo
**File:** `pruebas-api/tests/test_flujo_gate.py`
**Changes:**
- Recorrido: catálogo → crear → link en `/mensajes?destino=<tel>` → cargar datos → cotización (total = Σ precio × cantidad calculado **por la suite** con el catálogo) → firma → pago → mensaje al delivery con su link → retirado → mensaje "en camino" al cliente → en puerta → recibido → entregado → `CERRADO`.
- Cada paso se valida contra su schema (reutiliza la Fase 2).
- Al final, la línea de tiempo `eventos` está en orden cronológico y en el orden de la tabla de la spec §4.2. Con DEF-001 prendido, este chequeo falla.
- Marcadores: `gate`, `tecnica("flujo_e2e_api")`, `defecto("zona_horaria")`.

### Success Criteria:

#### Automated Verification:
- [ ] Gate en verde: `... -m pytest -q -m gate`
- [ ] **Atrapa DEF-001**: `... -m pytest -q -m gate --defectos=zona_horaria` falla en el chequeo de orden de eventos
- [ ] Mutación: si el total esperado se calcula mal a propósito (por ejemplo, sumando 1), el test falla

#### Manual Verification:
- [ ] Contra :8001, el pedido que deja el gate aparece en `/panel` con la línea de tiempo completa y `CERRADO`
- [ ] El test se lee como la historia del pedido (nombres de pasos en español, sin magia)

**Implementation Note**: pausar para el OK antes de la Fase 4.

---

## Phase 4: Transición de estados y tabla de decisión (Paso 14)

### Overview
Las técnicas de caja negra sobre la máquina de estados, vistas desde afuera.

### Changes Required:

#### 1. Matriz de transiciones
**File:** `pruebas-api/tests/test_transiciones.py`, `pruebas-api/soporte/estados.py`
**Changes:**
- `soporte/estados.py` copia la tabla de la spec §4.2 como **oráculo independiente**: no se importa `delivery.estados`.
- Para cada estado alcanzable × cada acción de la API (cargar, firmar, pagar, retirado, en-puerta, recibido, entregado, cancelar): se espera 200 si la transición es válida, o 409 con `transicion_invalida` y `estado_actual` correcto si no. El caso de firma sin pagar da 409 `firma_requerida`.
- Se agrega **cobertura de transiciones 0-switch**: el test cuenta cuántas transiciones válidas e inválidas ejercitó y lo publica para la Fase 7.
- `tecnica("transicion_estados")`.

#### 2. Tabla de decisión de cancelación
**File:** `pruebas-api/tests/test_cancelacion.py`
**Changes:** tabla explícita {estado} × {por: cliente, servicio, delivery} → {200 `CANCELADO`, 409 `no_cancelable`, 422}. La tabla se escribe como datos en el test y también va al `.md` del paso. `tecnica("tabla_decision")`.

### Success Criteria:

#### Automated Verification:
- [ ] `... -m pytest -q tests/test_transiciones.py tests/test_cancelacion.py`
- [ ] Mutación: si en una copia del oráculo se marca `PAGADO → CANCELADO` como válida, el test falla (prueba que el oráculo realmente compara)
- [ ] Duración de la fase < 30 s con servidor propio (si no, agrupar los pedidos por estado con fixtures de scope module)

#### Manual Verification:
- [ ] La tabla de decisión del `.md` coincide fila por fila con los datos del test
- [ ] Revisar que no haya transiciones del oráculo copiadas del código del demo (independencia)

**Implementation Note**: pausar para el OK antes de la Fase 5.

---

## Phase 5: Valores límite, particiones y riesgo (Paso 15)

### Overview
Entradas y reglas de riesgo: lo que un usuario o un atacante puede mandar mal.

### Changes Required:

#### 1. Límites y particiones
**File:** `pruebas-api/tests/test_limites.py`
**Changes:**
- Cantidad: 0, 1, 10 y 11 (límites de `ge=1, le=10`).
- Items: 0, 1, 4 y 5.
- Dirección: vacía, de 1 y 200 caracteres, de 201 caracteres, y con espacios en los extremos.
- Teléfono: 7, 8, 15 y 16 dígitos, con y sin `+`.
- Lat y lng: ±90/±180 y fuera de rango.
- Plato inexistente y plato repetido.
- Cada caso inválido valida su schema de error. `tecnica("valores_limite")` / `tecnica("particiones")`.

#### 2. Riesgo
**File:** `pruebas-api/tests/test_riesgo.py`
**Changes:**
- Total manipulado (`total` en el body → 422, y el total del servidor no cambia).
- Campos inventados → 422.
- Pago repetido → 200 con el mismo pedido y un solo evento `PAGADO`.
- Ids inexistentes en todas las rutas → 404 (nunca 500).
- `tecnica("riesgo")`.

### Success Criteria:

#### Automated Verification:
- [ ] `... -m pytest -q tests/test_limites.py tests/test_riesgo.py`
- [ ] Ninguna respuesta de la suite es 5xx (aserción global en un hook de `conftest.py` que falla el test si ve un 5xx no esperado)

#### Manual Verification:
- [ ] Los casos se leen como tabla en el `.md` del paso (valor, partición, esperado)

**Implementation Note**: pausar para el OK antes de la Fase 6.

---

## Phase 6: Concurrencia contra el servidor real (Paso 16) — lección del DEF-003

### Overview
Lo que los tests de componente no ven. Ráfagas reales contra uvicorn.

### Changes Required:

#### 1. Ráfagas
**File:** `pruebas-api/tests/test_concurrencia_real.py`
**Changes:**
- **Ráfaga mixta:** 20 hilos × 10 requests (GET `/platos`, POST `/pedidos`, GET `/pedidos/{id}`) → 0 respuestas 5xx.
- **Pago simultáneo:** 10 hilos pagan el mismo pedido → todos 200 y un solo evento `PAGADO`.
- **Confirmaciones cruzadas:** cliente y delivery confirman a la vez → el pedido termina en `CERRADO` con los dos flags.
- Marcadores: `tecnica("concurrencia")` y `lento`. Corre por defecto. Se puede excluir con `-m "not lento"`.

#### 2. Demostración de que atrapa
Mutación manual: un script en el scratchpad revierte el arreglo de `84b077f` en `sistema-demo/delivery/db.py`, corre la ráfaga y restaura el archivo en un `finally`. Los números del antes y el después van al paso y a `DEF-003-sqlite-entre-hilos.md` ("Regresión cubierta por la etapa 2").

### Success Criteria:

#### Automated Verification:
- [ ] `... -m pytest -q tests/test_concurrencia_real.py` en verde 5 corridas seguidas (no es *flaky*): `for i in 1 2 3 4 5; do ... -m pytest -q tests/test_concurrencia_real.py || break; done`
- [ ] Con el arreglo revertido, la ráfaga mixta falla con 5xx > 0
- [ ] `git diff --exit-code sistema-demo/delivery/db.py` después de la mutación (archivo restaurado)

#### Manual Verification:
- [ ] Revisar que los números del antes y el después del `.md` coinciden con la salida del script

**Implementation Note**: pausar para el OK antes de la Fase 7.

---

## Phase 7: Reporte de resultados y triage (Paso 17)

### Overview
Convierte cada corrida en métricas reales y en una clasificación de fallos según las tres categorías de la spec.

### Changes Required:

#### 1. Plugin de resultados
**File:** `pruebas-api/soporte/plugin_resultados.py` (registrado en `conftest.py`)
**Changes:** al terminar la sesión escribe `vistas/datos/resultados-api.js` (ruta configurable con `--resultados`) con:
- Totales (passed, failed, skipped, duración), y totales por técnica y por archivo.
- Por endpoint: cantidad de llamadas, status, y p50/p95/máximo en ms (datos del hook de la Fase 1).
- Cobertura de transiciones (de la Fase 4).
- Defectos activos y **triage** de cada fallo.
- Fecha, commit (`git rev-parse --short HEAD`) y ambiente (`local`, `qa` o `prod`, desde `--ambiente`).

#### 2. Clasificación de triage
**File:** `pruebas-api/soporte/triage.py`, `pruebas-api/triage/README.md`, `pruebas-api/triage/plantilla.md`
**Changes:**
- Reglas, en orden:
  1. Error de conexión, timeout o servidor que no levanta → **ambiente**.
  2. `test_deriva_openapi` u otro test marcado `@pytest.mark.contrato_vivo` → **test desactualizado**.
  3. Test con `defecto(X)` y X prendido → **defecto de producto** (con link al DEF).
  4. Cualquier otro caso → **sin clasificar**, que exige triage humano.
- La plantilla tiene los campos de un informe de incidente 29119-3 y las tres categorías.
- `triage/ejemplos/` guarda un ejemplo real de cada categoría, sacado de corridas reales: DEF-002 (producto), mutación de `modelos.py` (test desactualizado) y `BASE_URL` a un puerto cerrado (ambiente).

#### 3. pytest-html
`--html=reportes/api.html --self-contained-html` por defecto en `pytest.ini`. `reportes/` se ignora en git (en CI se sube como artefacto).

### Success Criteria:

#### Automated Verification:
- [ ] Después de una corrida, `node -e "global.window={};require('./vistas/datos/resultados-api.js');console.log(Object.keys(window.RESULTADOS_API))"` imprime las claves esperadas
- [ ] Tests unitarios del clasificador: `... -m pytest -q tests/test_triage.py` (una regla por caso, más el orden de prioridad)
- [ ] Con `--defectos=contrato`, el JSON tiene fallos con `triage == "producto"` y `def == "DEF-002"`
- [ ] `ls pruebas-api/reportes/api.html`

#### Manual Verification:
- [ ] Abrir `reportes/api.html` con doble clic: se ve completo, sin red
- [ ] Los tres ejemplos de `triage/ejemplos/` salen de corridas reales (con fecha y commit)

**Implementation Note**: pausar para el OK antes de la Fase 8.

---

## Phase 8: Gates en GitHub Actions (Paso 18)

### Overview
QA no bloquea; prod bloquea y publica. Requiere que el usuario haya hecho push y activado Pages (Settings → Pages → Source: GitHub Actions).

### Changes Required:

#### 1. Acción compuesta
**File:** `.github/actions/suite-api/action.yml`
**Changes:** prepara Python 3.12 con cache de pip, instala los dos `requirements.txt` y corre la suite con `--ambiente` y `--defectos` como inputs. Sube `reportes/` y `resultados-api.js` como artefactos.

#### 2. Workflows
**Files:** `.github/workflows/qa.yml`, `.github/workflows/prod.yml`, `.github/workflows/demo-defectos.yml`
**Changes:**
- `qa.yml`: se dispara con `push` (todas las ramas) y `pull_request`. Corre los tests del demo y la suite con `continue-on-error: true`. Escribe el triage en `$GITHUB_STEP_SUMMARY` (tabla de fallos → categoría → acción). Si hay fallos "sin clasificar", deja un `::warning::`. **Nunca falla el workflow.**
- `prod.yml`: se dispara con `push` a `main`. El job `gate` corre la suite completa **sin** `continue-on-error`, con `environment: prod`. El job `deploy`, con `needs: gate`, arma `sitio/` (copia de `vistas/` + `resultados-api.js` recién generado + `reportes/api.html`) y publica con `actions/upload-pages-artifact` + `actions/deploy-pages`. Si el gate falla, deploy queda *skipped*: **ese es el bloqueo visible.**
- `demo-defectos.yml`: se dispara a mano (`workflow_dispatch`), con un input para elegir defectos. Corre QA (rojo, triage, no bloquea) y un gate de prod simulado que falla, y el deploy queda *skipped* **sin publicar nada**. El portfolio nunca se bloquea a sí mismo (spec §10).
- Versiones de acciones fijadas por tag mayor (`actions/checkout@v4`, `actions/setup-python@v5`, etc.).

### Success Criteria:

#### Automated Verification:
- [ ] YAML válido: `python -c "import yaml,glob;[yaml.safe_load(open(f)) for f in glob.glob('.github/**/*.yml',recursive=True)]"` (PyYAML solo para esta verificación, o `actionlint` si está disponible)
- [ ] Después del push: `gh run list --workflow qa.yml -L 1` → `completed success`
- [ ] `gh run list --workflow prod.yml -L 1` → `success` y Pages responde: `curl -sI https://walterfernandez.github.io/qa-portfolio/ | head -1` → 200
- [ ] `gh workflow run demo-defectos.yml` → en el run, gate `failure`, deploy `skipped`, QA `success` con warning

#### Manual Verification:
- [ ] El resumen del run de `demo-defectos` muestra la tabla de triage legible, con link a DEF-002
- [ ] Captura del run bloqueado guardada para la vista de API
- [ ] Revisar que ningún log del run tenga datos personales ni del trabajo

**Implementation Note**: el push y la activación de Pages los hace el usuario. Pausar hasta que estén.

---

## Phase 9: Portada, vista de API y README (Paso 19)

### Overview
El primer hito visible: lo que se enlaza desde LinkedIn.

### Changes Required:

#### 1. Portada
**File:** `vistas/index.html`
**Changes:**
- Sigue `mockups/portada-dashboard.html`: tarjetas de módulos arriba (API activo; Mobile, Web, Performance y Prime como "próximamente"). Debajo, el dashboard del módulo elegido.
- Lee `datos/resultados-api.js`. Incluye la leyenda "Prácticas alineadas al syllabus ISTQB CTFL v4.0".
- Enlaza `etapa-1-sistema-demo.html`.

#### 2. Vista de API
**File:** `vistas/api.html`
**Changes:**
- KPIs: tests, % de éxito, duración y cobertura de transiciones.
- Tabla de endpoints con p50/p95 y status, tabla por técnica ISTQB, e historia del gate (QA no bloquea / prod bloquea) con la captura de la Fase 8.
- Sección de triage con los 3 ejemplos.
- Recuadros "En términos técnicos", "Cómo se mide" y "Norma / estándar", más una sección "Mejoras" (Postman/Newman, Schemathesis, mutation testing con mutmut, contract testing con Pact).
- Si `resultados-api.js` no existe, muestra un aviso en vez de romperse.

#### 3. README de la raíz
**File:** `README.md`
**Changes:** qué es el portfolio, link a Pages, historia STAR (§9; la métrica del resultado queda como `<!-- completar -->` para el usuario), cómo correr todo y la leyenda ISTQB. Sin datos de la empresa.

### Success Criteria:

#### Automated Verification:
- [ ] Sintaxis del JS inline: `node -e` con `new Function` sobre cada `<script>` de `index.html` y `api.html`
- [ ] Leyenda presente y palabra prohibida ausente: `grep -c "alineadas al syllabus ISTQB CTFL v4.0" README.md vistas/index.html` ≥ 1 y `git grep -i certificad -- ":!docs/superpowers"` vacío
- [ ] Grep de confidencialidad vacío
- [ ] Después del push, `curl -s https://walterfernandez.github.io/qa-portfolio/api.html | grep -c RESULTADOS_API` ≥ 1

#### Manual Verification:
- [ ] `vistas/index.html` y `api.html` con doble clic: se ven bien en escritorio y a 375 px de ancho
- [ ] La misma vista en Pages muestra los números del último run de prod
- [ ] Leer el README como un reclutador: se entiende en 1 minuto qué hiciste y con qué técnicas

**Implementation Note**: cierre de la etapa. Handoff `thoughts/handoffs/` y vista `vistas/etapa-2-api.html` o sección equivalente.

---

## Testing Strategy

- **Dos niveles:** `sistema-demo/tests` (componente, dev, rápido) y `pruebas-api/tests` (sistema, caja negra, QA). Ninguno reemplaza al otro.
- **Oráculos independientes:** la suite no importa `delivery.*`. Estados, montos y tablas salen de la spec.
- **Demostración por defectos:** cada técnica nueva muestra que atrapa algo, con un defecto sembrado (DEF-001, DEF-002) o con mutación manual (DEF-003, oráculos).
- **Sin flakiness:** las ráfagas se repiten 5 veces en la Fase 6. Cada servidor propio usa una base temporal nueva.

## References

- Spec: `docs/superpowers/specs/2026-11-10-qa-portfolio-design.md`
- Plan de la etapa 1: `docs/superpowers/plans/2026-11-14-etapa-1-sistema-demo.md`
- Handoff: `thoughts/handoffs/2026-11-15-etapa-1-cierre.md`
- Defectos: `sistema-demo/docs/defectos/DEF-00{1,2,3}-*.md`
