# Paso 5: Cargar datos y cotización

**Objetivo:** el cliente elige platos y dirección con `PUT /pedidos/{id}`, y en la misma llamada el servidor calcula el **total** con los precios del catálogo y la **demora**, le manda la cotización por WhatsApp simulado y deja el pedido en `COTIZADO`. El cliente nunca manda montos.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/pedidos.py` | `cargar_datos(...)`: valida, guarda los items con el precio del catálogo, calcula total y demora, envía el mensaje y avanza dos estados. Suma `DatosInvalidos` y `calcular_demora(unidades)` con sus constantes con nombre. |
| `sistema-demo/delivery/rutas_pedidos.py` | Ruta `PUT /pedidos/{id}` y los modelos `ItemPedido` (cantidad de 1 a 10) y `DatosPedido` (1 a 4 items, dirección, `lat` y `lng` opcionales con su rango). Sin campo `total`. |
| `sistema-demo/delivery/main.py` | Nuevo manejador: `DatosInvalidos` → **422** `{"detail": {"error": "plato_repetido" \| "plato_inexistente"}}`. |
| `sistema-demo/tests/conftest.py` | Constante `DATOS_OK` y fixture `pedido_nuevo` (un pedido en `LINK_ENVIADO`). |
| `sistema-demo/tests/test_cotizacion.py` | 42 tests: camino feliz, demora por tramos, contrato, valores límite, reglas contra el catálogo y estados. |

**Qué pasa en `PUT /pedidos/{id}`** (pasos 4 y 5 del flujo de negocio, en una sola llamada):

```
cliente: PUT /pedidos/1 {"items": [{"plato_id": 1, "cantidad": 2}, {"plato_id": 4, "cantidad": 1}],
                         "direccion": "Av. Siempre Viva 742", "lat": -34.6, "lng": -58.4}
   │
   ├─ Pydantic: rangos, largo, patrón y campos de más ─────────► 422 (detalle de Pydantic)
   ├─ ¿el estado permite DATOS_CARGADOS? ───────────────────────► 409 transicion_invalida
   ├─ ¿plato repetido? ¿plato fuera del catálogo? ───────────────► 422 plato_repetido / plato_inexistente
   │      (todo esto ANTES del primer INSERT: no queda nada a medias)
   ├─ INSERT items con precio del catálogo + dirección
   ├─ _avanzar(DATOS_CARGADOS) ──────────────► evento (actor: cliente)
   ├─ total = Σ cantidad × precio   demora = min(60, 30 + 5 × max(0, unidades − 2))
   ├─ mensajes.enviar("Total $22500 - demora 35 min") ─► bandeja WhatsApp simulado
   └─ _avanzar(COTIZADO) ────────────────────► evento (actor: servicio)
   │
   ◄─ 200 + pedido completo (estado COTIZADO, 4 eventos)
```

**Demora en tres tramos:**

| Unidades | Demora | Por qué |
|---|---|---|
| 1 a 2 | 30 min | Base, sin recargo. |
| 3 a 7 | 35 a 55 min | +5 min por cada unidad después de la segunda. |
| 8 o más | 60 min | Tope. |

**Los tests:**

| Grupo | Cantidad | Qué verifica |
|---|---|---|
| Camino feliz | 4 | Total `2 × 9000 + 4500 = 22500`, demora 35, items con nombre, precio unitario y subtotal; los 4 eventos en orden con su actor; el mensaje `Total $22500 - demora 35 min`; coordenadas opcionales. |
| Demora por tramos | 7 | 1, 2, 3, 7, 8, 9 y 40 unidades: los bordes 2\|3 (empieza el recargo) y 7\|8 (llega al tope). |
| Contrato | 3 | `total`, `estado` o `descuento` en el body → 422, y el pedido queda en `LINK_ENVIADO` sin total. |
| Valores límite | 23 | Cantidad 0/1/10/11; items 0/1/4/5; dirección vacía, solo espacios, con espacio al inicio o al final, de 1, 200 y 201 caracteres; latitud ±90/±90,1 y longitud ±180/±180,1. |
| Reglas contra el catálogo | 2 | Plato repetido → 422 `plato_repetido`. Plato 99 → 422 `plato_inexistente` y no guarda ningún item. |
| Estados y existencia | 3 | Cargar dos veces (con los mismos platos y con otros) → 409, y la primera cotización queda intacta. Pedido 999 → 404. |

## 2. Por qué lo hicimos así

- **El total lo calcula el servidor:** el body no tiene campo `total`, y por `extra="forbid"` mandarlo da 422. El precio sale de `catalogo.precios` y se guarda en `precio_unitario`: si mañana cambia el catálogo, el pedido ya cotizado conserva su precio.
- **Validar todo antes de escribir:** primero el estado, después los repetidos y los platos, y recién ahí el primer `INSERT`. Así un 409 o un 422 no dejan items sueltos, y la PK `(pedido_id, plato_id)` nunca llega a explotar como un 500.
- **Dos niveles de validación:** Pydantic chequea forma y rangos (no sabe nada de la base). Las reglas que necesitan el catálogo (`plato_inexistente`, `plato_repetido`) las chequea el servicio y las devuelve con un código propio, más fácil de leer para el cliente y para un test.
- **Repetido es error, no suma:** si llegan dos líneas del mismo plato no se juntan en silencio: el cliente se entera.
- **Dirección sin espacios en los extremos:** el patrón `^\S(?:.*\S)?$` rechaza `"   "`, `" Calle 1"` y `"Calle 1 "`. Una dirección "en blanco" no llega a la base.
- **Constantes con nombre para la demora:** `DEMORA_BASE_MIN`, `DEMORA_TOPE_MIN`, `UNIDADES_SIN_RECARGO` y `RECARGO_POR_UNIDAD_MIN`. La fórmula se lee igual que la regla de negocio.
- **Riesgo observado (sigue del Paso 4):** `DATOS_CARGADOS` y `COTIZADO` se registran en la misma llamada y suelen tener la misma marca de tiempo en Windows. El test del orden de eventos pasó 5 de 5 seguidas; el desempate sigue dependiendo del orden de inserción de SQLite. Queda para el Paso 8.
- **Prueba de mutación manual: 6 de 6, pero no a la primera.** Se metieron 6 defectos: sacar el chequeo de repetidos, cantidad hasta 11, sacar el tope de 60, total con precio fijo, aceptar campos de más y sacar el chequeo temprano de estado. Este último **sobrevivió**: el test de "cargar dos veces" usaba otro plato y el *rollback* lo tapaba. Con los mismos platos habría dado 500 en vez de 409. Se sumó ese caso y la mutación pasó a detectarse.

## 3. Cómo se conecta con el proyecto

```
catalogo.precios (Paso 2) ──► cargar_datos ──► pedido_items.precio_unitario
estados.py (Paso 3) ──► _avanzar (Paso 4) ──► DATOS_CARGADOS → COTIZADO
mensajes.enviar (Paso 4) ──► "Total $... - demora ... min" ──► (Paso 9) pantalla del cliente
COTIZADO ──► (Paso 6) firma y pago: el total cotizado es el que se cobra
```

- El JSON del pedido ahora trae `items`, `direccion`, `lat`, `lng`, `total` y `demora_min` llenos, sin cambiar la forma de la respuesta.
- `lat` y `lng` son los que el mapa del delivery va a mostrar en el Paso 9.
- La etapa 2 vuelve sobre estos mismos límites desde afuera (contrato y pruebas de API).

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| Cantidad, items, dirección y demora por grupos | 📘 ISTQB | [CTFL v4.0 §4.2.1 *Partición de equivalencia*](glosario.md#particiones) |
| Bordes: cantidad 0/1/10/11, items 0/1/4/5, dirección 1/200/201, coordenadas, demora 2\|3 y 7\|8 | 📘 ISTQB | [CTFL v4.0 §4.2.2 *Análisis de valores límite*](glosario.md#valores-limite) |
| Test escrito antes del código (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Modelo, servicio, catálogo, SQLite y bandeja probados juntos | 📘 ISTQB | [CTFL v4.0 §2.2.1 Nivel de prueba: *integración de componentes*](glosario.md#integracion-componentes) |
| `LINK_ENVIADO → DATOS_CARGADOS → COTIZADO`; cargar dos veces se rechaza | 📘 ISTQB | [CTFL v4.0 §4.2.4 *Prueba de transición de estados*](glosario.md#transicion-estados) |
| El cliente no puede fijar su propio precio | 📘 ISTQB | [CTFL v4.0 §5.2 *Gestión de riesgos*](glosario.md#riesgos) |
| Cargar datos de un pedido ya cotizado | 📐 Norma | [RFC 9110 §15.5.10 — *409 Conflict*](glosario.md#http-409) |
| Fuera de rango, campos de más, plato repetido o inexistente | 📐 Norma | [RFC 9110 §15.5.21 — *422 Unprocessable Content*](glosario.md#http-422) |
| Un rechazo no deja datos a medias | 📐 Norma | [ISO/IEC 25010 — Seguridad › *Integridad*](glosario.md#integridad) |
| Latitud en [-90, 90] y longitud en [-180, 180] | 📐 Norma | [ISO 6709 (datum WGS 84)](glosario.md#iso6709) |
| Rechazar `total` y campos inventados; patrón de dirección | ✅ Buena práctica | [OWASP *Input Validation Cheat Sheet* (lista blanca)](glosario.md#validacion-entrada) |
| Total en pesos enteros | ✅ Buena práctica | [Dinero en unidades enteras](glosario.md#dinero-enteros) |
| Items, total, eventos y mensaje en una sola transacción | ✅ Buena práctica | [Patrón *Unit of Work*](glosario.md#unit-of-work) |
| Validar todo antes del primer `INSERT`, con códigos de error | ✅ Buena práctica | [Fallar rápido (*fail fast*) con errores descriptivos](glosario.md#fail-fast) |
| El precio sale siempre del catálogo | ✅ Buena práctica | [Fuente única de verdad](glosario.md#table-driven) |
| Un caso con nombre por cada valor límite | ✅ Buena práctica | [`pytest.mark.parametrize`](glosario.md#parametrizados) |
| 6 defectos a propósito; uno sobrevivió y sumó un caso | ✅ Buena práctica | [Prueba de mutación, hecha a mano](glosario.md#mutacion) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q                           # 94 tests en verde (52 previos + 42 nuevos)
.venv/Scripts/python -m pytest tests/test_cotizacion.py -v  # cada valor límite por nombre
```

Probarlo a mano (con el servidor levantado, `uvicorn delivery.main:app`):

```bash
curl -s -X POST localhost:8000/pedidos -H "Content-Type: application/json" -d '{"telefono": "1122334455"}'
curl -s -X PUT localhost:8000/pedidos/1 -H "Content-Type: application/json" \
  -d '{"items": [{"plato_id": 1, "cantidad": 2}, {"plato_id": 4, "cantidad": 1}], "direccion": "Av. Siempre Viva 742"}'
# 200: estado COTIZADO, total 22500, demora_min 35
curl -s "localhost:8000/mensajes?destino=cliente&pedido_id=1"   # el link y "Total $22500 - demora 35 min"
curl -s -X PUT localhost:8000/pedidos/1 -H "Content-Type: application/json" \
  -d '{"items": [{"plato_id": 1, "cantidad": 1}], "direccion": "Calle 1", "total": 1}'
# 422: el total no lo manda el cliente
```

## 6. En términos técnicos (para entrevista)

> "Implementé la cotización como una operación atómica que encadena dos pasos del negocio: el cliente carga sus datos y el servidor calcula el total con los precios del catálogo, nunca con montos del cliente, que se rechazan por validación de lista blanca. Separé la validación en dos niveles: forma y rangos en el modelo de entrada, y reglas que dependen del catálogo en el servicio, con códigos de error propios. Todo se valida antes de la primera escritura. Diseñé los casos con partición de equivalencia y valores límite, incluidos los dos bordes de la fórmula de demora y los rangos de ISO 6709 para las coordenadas. En la prueba de mutación manual sobrevivió un defecto: el *rollback* tapaba el chequeo de estado. Eso me llevó a sumar el caso que lo detecta, y quedaron 6 de 6."
