# Paso 8: Defectos sembrados

**Objetivo:** dejar dentro del sistema dos defectos **a propósito**, apagados por defecto, que se prenden con una variable de entorno. Son el blanco de las etapas siguientes: las pruebas de API, de UI y de mobile tienen que poder encontrarlos. Uno es de **zona horaria**: la línea de tiempo del pedido sale desordenada. El otro es de **contrato**: los montos salen como texto (`"$ 9.000"`) en vez de números.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/reloj.py` | `marca_tiempo` con `defecto_zona_horaria`: devuelve la hora **local del actor** (según `ZONAS`) con el formato `FORMATO_LOCAL_SIN_OFFSET` (`%Y-%m-%dT%H:%M:%S.%f`), sin offset y sin `Z`. Apagado, sigue en UTC con `Z`. |
| `sistema-demo/delivery/formato.py` | Nuevo. `pesos(n)` → `"$ 9.000"` (separador de miles con punto). |
| `sistema-demo/delivery/catalogo.py` | `monto(ctx, n)`: el único lugar donde se decide cómo sale un monto por la API. Con `defecto_contrato` devuelve `formato.pesos(n)`; si no, el entero. `None` sigue siendo `None`. `listar_platos` lo usa para `precio`. |
| `sistema-demo/delivery/pedidos.py` | `precio_unitario`, `subtotal` y `total` del pedido pasan por `catalogo.monto`. La base no cambia. |
| `sistema-demo/tests/test_defectos.py` | 18 tests: cada defecto prendido y su par con el defecto apagado. |

**Cómo se prenden** (variables de entorno, leídas por `Config.desde_entorno` desde el Paso 1):

| Variable | Defecto | Qué se ve |
|---|---|---|
| `DEMO_DEFECTO_ZONA_HORARIA=1` | Zona horaria | `ocurrido_en` en hora local de cada actor y sin offset; `eventos` sale desordenado. |
| `DEMO_DEFECTO_CONTRATO=1` | Contrato | `precio`, `precio_unitario`, `subtotal` y `total` como texto `"$ 9.000"`. |

`GET /salud` informa cuáles están prendidos: `{"defectos": {"zona_horaria": true, "contrato": false}}`.

**Por qué se desordena la línea de tiempo.** Cada actor vive en otra zona: el cliente en México (UTC-6), el servicio en Nueva York (UTC-5) y el delivery en Buenos Aires (UTC-3). `_eventos` ordena **solo** por `ocurrido_en`, que es texto. Con el reloj fijo a las 15:00 UTC, avanzando 5 segundos por marca:

| Evento | Actor | Hora real (UTC) | Se guarda con el defecto |
|---|---|---|---|
| `INICIADO` | cliente | 15:00:05 | `09:00:05` |
| `LINK_ENVIADO` | servicio | 15:00:15 | `10:00:15` |
| `DATOS_CARGADOS` | cliente | 15:00:20 | `09:00:20` |
| `COTIZADO` | servicio | 15:00:30 | `10:00:30` |
| `PAGADO` | cliente | 15:00:35 | `09:00:35` |
| `ASIGNADO` | servicio | 15:00:45 | `10:00:45` |

Ordenado por texto: `INICIADO, DATOS_CARGADOS, PAGADO, LINK_ENVIADO, COTIZADO, ASIGNADO`. **`PAGADO` aparece antes que `COTIZADO`**: el cliente pagó algo que todavía no estaba cotizado. En el recorrido completo, los eventos quedan agrupados por zona (cliente, servicio, delivery) en vez de por orden real.

**Los tests:**

| Grupo | Cantidad | Qué verifica |
|---|---|---|
| Zona horaria | 5 | Con el defecto: `PAGADO` antes que `COTIZADO` y el orden exacto de la tabla; marcas `09:00:05` (cliente) y `10:00:15` (servicio) sin `Z` ni `+`; en los 13 pasos, eventos agrupados por actor. Sin el defecto: orden correcto y `2026-11-14T15:00:05.000000Z`. |
| Formato de pesos | 6 | `0`, `999`, `1000` (primer separador), `9000`, `22500` y `1234567` (dos separadores). |
| Contrato | 6 | Con el defecto: `precio` `"$ 9.000"` en `/platos`; `total` `"$ 22.500"`, `precio_unitario` y `subtotal` en el pedido; también en `GET /pedidos`; un pedido sin cotizar sigue con `total: null`. La misma base leída sin el defecto devuelve `22500`. Sin el defecto: enteros. |
| Salud | 1 | `/salud` informa los dos defectos prendidos. |

## 2. Por qué lo hicimos así

- **Defectos que se encuentran en la vida real:** guardar la hora local sin offset y ordenar fechas como texto es un error clásico cuando hay usuarios en varias zonas. Devolver montos ya formateados para la pantalla rompe a cualquier cliente que esperaba un número. Los dos son creíbles y no se ven en un test que solo mira el camino feliz con un actor.
- **Apagados por defecto:** los 170 tests de los pasos 1 a 7 siguen en verde sin tocar nada. Así se demuestra que el defecto está aislado detrás de su interruptor y que los tests de antes son el **oráculo** del comportamiento correcto.
- **Cada test con defecto tiene su par sin defecto:** el par apagado prueba que el test no pasa por casualidad. Si `test_defecto_contrato_total_como_texto` pasara también con el defecto apagado, no estaría probando el defecto.
- **El reloj se fija en el test:** con la hora real, el resultado dependería de la hora en que corre la suite y del reloj de Windows (que avanza cada 15,6 ms). `reloj.ahora_utc` es la única fuente de "ahora" desde el Paso 4, y el fixture `reloj_fijo` la reemplaza con instantes de 5 en 5 segundos: el test da siempre el mismo orden.
- **El defecto de contrato vive en un solo lugar:** `catalogo.monto` decide cómo sale cada monto. La base sigue guardando enteros y el total se sigue calculando con enteros (Paso 5): el defecto está solo en la salida. Un test lo comprueba leyendo la misma base con y sin el defecto.
- **`test_flujo_completo_los_13_pasos` no se tocó:** es el oráculo, con el defecto apagado. Con el defecto prendido, ese mismo test falla porque el orden de eventos no coincide; para mostrarlo sin romper la suite, `test_defecto_zona_horaria_en_el_flujo_completo` recorre los 13 pasos con el defecto prendido y verifica el desorden.
- **Prueba de mutación manual: 13 de 13.** Ignorar el interruptor de zona (siempre UTC o siempre local), usar la zona del servicio para todos, agregar el offset (`%z`), no convertir a la zona local, cambiar el separador de miles, sacar el `"$ "`, no respetar `None`, invertir el interruptor de contrato, y olvidar el formato en `precio`, `total`, `precio_unitario` o `subtotal`: todos rompieron al menos un test.

## 3. Cómo se conecta con el proyecto

```
Config (Paso 1) ──► DEMO_DEFECTO_ZONA_HORARIA / DEMO_DEFECTO_CONTRATO ──► /salud los informa
reloj.ahora_utc (Paso 4) ──► marca_tiempo ──► con el defecto: hora local sin offset
_eventos (Paso 4) ──► ORDER BY ocurrido_en (texto) ──► la línea de tiempo se desordena
catálogo y total en enteros (Pasos 2 y 5) ──► catalogo.monto ──► con el defecto: "$ 9.000"
                                                        │
                                  etapas 2 a 4: las pruebas de API, UI y mobile los tienen que encontrar
```

- El interruptor existe desde el Paso 1; este paso le da el comportamiento.
- En el Paso 9, la pantalla del cliente muestra la línea de tiempo: con el defecto prendido se ve desordenada.
- En la etapa 2, un contrato JSON Schema dice que `total` es `integer`: con el defecto de contrato, esa validación falla. Ese es el hallazgo que se espera que encuentren las pruebas de API.

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| Dos defectos conocidos, apagados por defecto y activables por entorno | 📘 ISTQB | [Glosario ISTQB: *fault seeding / defect seeding*](glosario.md#defect-seeding) |
| Cada test con defecto tiene su par sin defecto; el orden de la tabla del spec es la fuente de verdad | 📘 ISTQB | [Glosario ISTQB: *test oracle* (oráculo de prueba)](glosario.md#oraculo) |
| Test escrito antes del código (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Defectos elegidos por probabilidad e impacto: varias zonas horarias y clientes que esperan números | 📘 ISTQB | [CTFL v4.0 §5.2 *Gestión de riesgos*](glosario.md#riesgos) |
| Los 170 tests de antes siguen en verde con los defectos apagados | 📘 ISTQB | [CTFL v4.0 §2.2.3 *Pruebas de regresión*](glosario.md#regresion) |
| La hora local sin offset no se puede comparar entre actores | 📐 Norma | [ISO 8601 / RFC 3339 §5.6 — la marca lleva `Z` u offset](glosario.md#iso8601) |
| Un cliente que espera un número recibe texto | 📐 Norma | [ISO/IEC 25010 — Compatibilidad › *Interoperabilidad*](glosario.md#interoperabilidad) |
| `precio` y `total` son enteros en el contrato de la API | 📐 Norma | [OpenAPI 3.1 — tipos del contrato](glosario.md#openapi) |
| Los defectos se prenden con `DEMO_DEFECTO_*`, sin tocar el código | ✅ Buena práctica | [Twelve-Factor App — III. Config](glosario.md#twelve-factor) |
| La base sigue en enteros; el texto es solo presentación | ✅ Buena práctica | [Dinero en unidades enteras](glosario.md#dinero-enteros) |
| `reloj_fijo` hace el orden repetible | ✅ Buena práctica | [Reloj reemplazable (*seam*)](glosario.md#reloj-inyectable) |
| Seis montos con nombre para `formato.pesos` | ✅ Buena práctica | [`pytest.mark.parametrize`](glosario.md#parametrizados) |
| 13 defectos a propósito, 13 detectados | ✅ Buena práctica | [Prueba de mutación, hecha a mano](glosario.md#mutacion) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q                          # 188 tests en verde (170 previos + 18)
.venv/Scripts/python -m pytest tests/test_defectos.py -v   # cada defecto y su par
```

Probarlo a mano (Git Bash), con una base aparte para no mezclar con la normal:

```bash
DEMO_DB_PATH=data/defectos.db DEMO_DEFECTO_ZONA_HORARIA=1 DEMO_DEFECTO_CONTRATO=1 \
  .venv/Scripts/python -m uvicorn delivery.main:app
curl -s localhost:8000/salud     # "defectos": {"zona_horaria": true, "contrato": true}
curl -s localhost:8000/platos    # "precio": "$ 9.000"
```

Después, crear un pedido y llevarlo hasta el pago como en los pasos 4 a 6: `GET /pedidos/1` muestra `"total": "$ 22.500"` y los eventos con `PAGADO` antes que `COTIZADO`.

## 6. En términos técnicos (para entrevista)

> "Sembré dos defectos conocidos en el sistema demo para medir después si mis pruebas de API, UI y mobile los detectan. Están apagados por defecto y se prenden con variables de entorno, siguiendo el factor de configuración de Twelve-Factor, y el endpoint de salud informa cuáles están activos. El primero es de zona horaria: cada actor guarda su hora local sin offset, cuando RFC 3339 lo exige, y como la línea de tiempo se ordena por texto, el pago aparece antes que la cotización. El segundo rompe el contrato: los montos salen formateados como texto en vez de enteros, aunque la base sigue guardando enteros, así que es un problema de interoperabilidad y no de datos. Cada test con el defecto prendido tiene su par con el defecto apagado, que actúa como oráculo, y fijé el reloj con un *seam* para que el orden sea repetible. Los 170 tests anteriores siguieron en verde como regresión, y la mutación manual detectó 13 de 13."
