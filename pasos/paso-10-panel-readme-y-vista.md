# Paso 10: Panel central, README, informes de defecto y vista de la etapa

**Objetivo:** cerrar la etapa 1 con lo que hace falta para **mostrar y usar** el sistema demo. Se suman el **panel central** del servicio (`/panel`), con todos los pedidos, su línea de tiempo, la bandeja de mensajes y qué defectos están prendidos. También el **README** del sistema, los **informes de defecto** en formato ISO/IEC/IEEE 29119-3 y la **vista HTML** que resume la etapa. Al probar el panel apareció un **defecto real** (`500` al azar con requests en paralelo): se reprodujo, se corrigió con su test de regresión y se documentó como DEF-003.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/paginas/panel.html` | Página de escritorio. **Defectos sembrados** (lee `GET /salud`): cada uno con PRENDIDO o apagado. **Pedidos**: tabla con id, estado, total y teléfono; el id es un botón que elige el pedido. **Pedido elegido**: estado, línea de tiempo (estado · actor y `ocurrido_en` tal cual) y "Cancelar pedido (servicio)", solo antes del pago. **Bandeja de mensajes**: todos los mensajes, con el link clickeable. El pedido elegido vive en la URL (`/panel#1`). Consulta cada 3 s: `/pedidos` y `/mensajes` en paralelo y después el pedido y `/salud`. |
| `sistema-demo/delivery/main.py` | Ruta `GET /panel` (`include_in_schema=False`). |
| `sistema-demo/delivery/paginas/estilos.css` | Bloque "Panel central": `body.ancho` (1100 px), dos columnas desde 860 px, tabla con scroll horizontal y botón con aspecto de enlace. |
| `sistema-demo/delivery/db.py` | **Arreglo del DEF-003:** `conectar` usa `check_same_thread=False`, con un comentario que explica por qué es seguro. |
| `sistema-demo/tests/test_paginas.py` | El panel se suma a la lista parametrizada de páginas, con sus 6 `data-testid`. |
| `sistema-demo/tests/test_concurrencia.py` | `test_la_conexion_se_puede_usar_desde_otro_hilo`: test de regresión del DEF-003. |
| `sistema-demo/README.md` | Instalar, levantar, correr los tests (tabla por archivo), prender cada defecto, tabla de estados, tabla de rutas y estructura. Con la leyenda "Prácticas alineadas al syllabus ISTQB CTFL v4.0". |
| `sistema-demo/docs/defectos/DEF-001-zona-horaria.md` · `DEF-002-contrato-precio.md` · `DEF-003-sqlite-entre-hilos.md` | Informes con los campos de ISO/IEC/IEEE 29119-3: id, tipo, entorno, severidad, prioridad, estado, pasos, resultado esperado y obtenido, evidencia, causa raíz y corrección. |
| `sistema-demo/docs/defectos/evidencia/panel-zona-horaria-y-500.jpg` | Captura del panel con PAGADO antes que COTIZADO (DEF-001) y el banner `[error_500]` (DEF-003). |
| `vistas/etapa-1-sistema-demo.html` | Vista de la etapa con el estilo del mockup aprobado: KPIs, máquina de estados coloreada por actor, actores y rutas, los tres defectos y los recuadros "En términos técnicos", "Cómo se mide", "Norma / estándar" y "Mejoras". Se abre con doble clic. |

**Los `data-testid` del panel:**

| Zona | `data-testid` |
|---|---|
| Defectos | `estado-defectos`, y adentro `defecto-zona_horaria` y `defecto-contrato` |
| Pedidos | `tabla-pedidos`, y una fila `pedido-{id}` por pedido |
| Pedido elegido | `linea-de-tiempo`, `btn-cancelar-servicio` |
| Bandeja | `bandeja-mensajes`, y un `mensaje-{id}` por mensaje |
| Errores | `msg-error` |

**El defecto real (DEF-003).** Con el panel abierto apareció `Algo salió mal. [error_500]` sin tocar nada. El log decía `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread`. FastAPI corre la dependencia `obtener_ctx` (que abre la conexión) en un hilo del *threadpool* y el endpoint en otro, y `sqlite3` por defecto no deja usar una conexión desde otro hilo. Con un request por vez casi nunca pasa; el panel pide dos rutas **en paralelo** y lo dispara. Medido contra uvicorn con 200 requests (20 en paralelo):

| | `200` | `500` |
|---|---:|---:|
| Sin el arreglo | 6 | **194** |
| Con el arreglo | **200** | 0 |

## 2. Por qué lo hicimos así

- **El panel es la vista del servicio**, el tercer actor: en el celular del cliente o del delivery se ve un pedido; acá se ven todos, con la bandeja que hace de WhatsApp. Es la pantalla donde mejor se nota el defecto de zona horaria, porque muestra los eventos de los tres actores juntos.
- **Los defectos se ven y se sabe cuáles están prendidos:** la línea de tiempo muestra `ocurrido_en` sin reformatear y el total con `pesos()`, que no esconde un texto. Arriba, "Defectos sembrados" dice qué interruptores están prendidos: quien prueba no tiene que adivinar en qué modo está el sistema.
- **El pedido elegido va en la URL** (`#1`): sobrevive a un F5 y se puede mandar el link exacto en un informe de defecto, como en el DEF-001.
- **Sin `confirm()` al cancelar**, igual que en el Paso 9: un diálogo nativo traba a Playwright.
- **El arreglo del DEF-003 es el mínimo:** `check_same_thread=False`. Es seguro porque cada conexión es de un solo request y se usa desde un hilo por vez, nunca desde dos a la vez. Volver `async` todas las rutas o sumar un *pool* de conexiones cambiaba mucho más código para un problema de configuración.
- **Primero el test, después el arreglo:** `test_la_conexion_se_puede_usar_desde_otro_hilo` usa la conexión desde otro hilo; falló (rojo) con el `ProgrammingError` y pasó (verde) con el arreglo. Ese test queda como **regresión**. La ráfaga contra uvicorn es la **prueba de confirmación** en el servidor real.
- **El DEF-003 se documenta aunque ya esté corregido:** un defecto real, encontrado por una pantalla nueva y no por la suite, es justo lo que el portfolio quiere mostrar. Los 195 tests de entonces no lo veían porque `TestClient` manda un request por vez.
- **Los informes siguen 29119-3:** los mismos campos en los tres, para que se comparen y para que la etapa 2 los complete con el triage automático.
- **La vista carga los números a mano en esta etapa:** desde la etapa 2 los va a generar la corrida de tests (§7 del spec). La sección "Mejoras" lo dice, junto con las notas de la prueba manual del Paso 9, que siguen pendientes.
- **Prueba de mutación manual: 7 de 7.** Sacar la ruta `/panel`, servir `cliente.html` en `/panel` y renombrar cada uno de los 5 `data-testid` del plan (`tabla-pedidos`, `linea-de-tiempo`, `bandeja-mensajes`, `estado-defectos`, `btn-cancelar-servicio`): todos rompieron el test.

## 3. Cómo se conecta con el proyecto

```
panel.html ──GET /pedidos + GET /mensajes (en paralelo)──► API (Pasos 4-7) ──► DEF-003 encontrado y corregido
     │
     ├──GET /salud──► defectos prendidos (Paso 8)
     ├──linea-de-tiempo──► DEF-001 visible (Paso 8)
     └──POST /cancelar {"por": "servicio"}──► Paso 7
                                │
README + DEF-001..003 + vista ──► etapa 2: tests de API, contrato JSON Schema y triage en CI
```

- El panel usa lo mismo que las páginas del Paso 9: `api.js` (`api`, `textoDeError`, `pesos`) y `estilos.css`.
- Los informes DEF-001 y DEF-002 describen los defectos del Paso 8; son el "resultado esperado" de las pruebas de la etapa 2.
- El DEF-003 deja una tarea para la etapa 2 (API) y la 5 (performance): una prueba con requests en paralelo contra el servidor real.
- La vista de la etapa es la primera de la portada del portfolio (§7 del spec).

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| El panel responde y trae sus `data-testid` | 📘 ISTQB | [Glosario ISTQB: *smoke test*](glosario.md#smoke-test) |
| Test del panel y del DEF-003 antes del código (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Informes DEF-001 a DEF-003 con severidad, prioridad y causa raíz | 📘 ISTQB | [CTFL v4.0 §5.5 *Gestión de defectos*](glosario.md#gestion-defectos) |
| El test del DEF-003 queda como regresión; la ráfaga confirma el arreglo | 📘 ISTQB | [CTFL v4.0 §2.2.3 *Pruebas de confirmación y de regresión*](glosario.md#regresion) |
| El panel muestra qué defectos sembrados están prendidos | 📘 ISTQB | [Glosario ISTQB: *defect seeding*](glosario.md#defect-seeding) |
| Los informes llevan los campos del informe de incidentes | 📐 Norma | [ISO/IEC/IEEE 29119-3 — *Incident report*](glosario.md#iso29119-3) |
| La línea de tiempo muestra `ocurrido_en` sin reformatear | 📐 Norma | [ISO 8601 / RFC 3339](glosario.md#iso8601) |
| `/salud` y el panel dicen en qué modo está el sistema | 📐 Norma | [ISO/IEC 25010 — Mantenibilidad › *Capacidad de ser probado*](glosario.md#capacidad-prueba) |
| Selectores del panel pensados para Playwright | ✅ Buena práctica | [Selectores estables (`data-testid`)](glosario.md#data-testid) |
| Ráfaga de requests en paralelo contra uvicorn: 194 → 0 errores | ✅ Buena práctica | [Pruebas con requests en paralelo](glosario.md#prueba-concurrencia) |
| 7 defectos a propósito, 7 detectados | ✅ Buena práctica | [Prueba de mutación, hecha a mano](glosario.md#mutacion) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q                         # 196 tests en verde (194 previos + 2)
.venv/Scripts/python -m pytest tests/test_paginas.py -v   # las 4 páginas y sus data-testid
```

**El panel con el defecto de zona horaria** (Git Bash):

```bash
DEMO_DB_PATH=data/panel.db DEMO_DEFECTO_ZONA_HORARIA=1 \
  .venv/Scripts/python -m uvicorn delivery.main:app --port 8765
```

1. Hacer un pedido hasta el pago, como en el §5 del Paso 9.
2. Abrir `http://localhost:8765/panel#1`: "Zona horaria" dice **PRENDIDO** y la línea de tiempo muestra **PAGADO antes que COTIZADO**.

**El DEF-003** (con el servidor levantado): la ráfaga del informe tiene que dar todo `200`.

```bash
B=http://127.0.0.1:8765
for r in 1 2 3; do for i in $(seq 1 10); do
  curl -s -o /dev/null -w "%{http_code} " $B/mensajes & curl -s -o /dev/null -w "%{http_code} " $B/pedidos &
done; wait; echo; done
```

**La vista:** abrir `vistas/etapa-1-sistema-demo.html` con doble clic.

## 6. En términos técnicos (para entrevista)

> "Cerré la primera etapa con un panel central del servicio que muestra todos los pedidos, la línea de tiempo de cada uno, la bandeja de mensajes simulados y qué defectos sembrados están activos. Al probarlo encontré un defecto real: errores 500 intermitentes cuando llegaban requests en paralelo. Lo reproduje con una ráfaga contra el servidor real (194 de 200 fallaban) y encontré la causa raíz: FastAPI abría la conexión de SQLite en un hilo del threadpool y la usaba en otro, y sqlite3 no lo permite por defecto. Escribí primero el test que lo reproducía, apliqué el arreglo mínimo y confirmé contra el servidor que bajaba a cero. Documenté ese defecto y los dos sembrados con informes en formato ISO/IEC/IEEE 29119-3, con severidad, prioridad, evidencia y causa raíz. La lección: la suite mandaba un request por vez y no podía verlo, así que en la etapa de API sumo pruebas concurrentes contra el servidor levantado."
