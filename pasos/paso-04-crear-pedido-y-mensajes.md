# Paso 4: Crear pedido, reloj, eventos y WhatsApp simulado

**Objetivo:** la primera ruta de pedidos. `POST /pedidos` crea el pedido, le manda el link al cliente por un WhatsApp simulado y registra cada cambio de estado en el historial. Además, la API empieza a responder con **404**, **409** y **422**.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/reloj.py` | `ahora_utc()` (la única fuente de "ahora"), `ZONAS` (la zona horaria de cada actor) y `marca_tiempo(actor, cfg)`, que devuelve la hora en UTC con sufijo `Z`. |
| `sistema-demo/delivery/mensajes.py` | La bandeja del WhatsApp simulado: `enviar(...)` guarda el mensaje en la tabla `mensajes` y `listar(...)` lo devuelve filtrado por destino o por pedido. |
| `sistema-demo/delivery/pedidos.py` | `crear_pedido`, `obtener_pedido`, `listar_pedidos`, la excepción `PedidoNoEncontrado` y `_avanzar`, **el único camino para cambiar el estado**. |
| `sistema-demo/delivery/rutas_pedidos.py` | Las rutas `POST /pedidos`, `GET /pedidos`, `GET /pedidos/{id}` y `GET /mensajes`, y el modelo de entrada `NuevoPedido`. |
| `sistema-demo/delivery/main.py` | Suma el router y dos manejadores: `PedidoNoEncontrado` → **404** y `TransicionInvalida` → **409**. |
| `sistema-demo/tests/test_crear_pedido.py` | 14 tests: alta, JSON completo, teléfonos válidos e inválidos, campo de más, 404, listado, reinicio, UTC y 409. |
| `sistema-demo/tests/test_mensajes.py` | 5 tests: filtros de la bandeja, contenido del mensaje, destino inválido y `_avanzar` rechazando un salto. |

**Qué pasa en `POST /pedidos`** (pasos 1 a 3 del flujo de negocio, en una sola llamada):

```
cliente: POST /pedidos {"telefono": "+5215512345678"}
   │
   ├─ INSERT pedido en INICIADO ─────────────► evento INICIADO      (actor: cliente)
   ├─ mensajes.enviar(... link=/cliente/pedido/1) ─► bandeja WhatsApp simulado
   └─ _avanzar(LINK_ENVIADO) ────────────────► evento LINK_ENVIADO  (actor: servicio)
   │
   ◄─ 201 + pedido completo (estado LINK_ENVIADO, 2 eventos)
```

**Los tests:**

| Grupo | Cantidad | Qué verifica |
|---|---|---|
| Alta y bandeja | 2 | 201, estado `LINK_ENVIADO`, eventos en orden con su actor, mensaje con link y canal `whatsapp`, JSON con los 14 campos. |
| Teléfono: particiones y límites | 6 | Válidos en el borde (8 y 15 dígitos). Inválidos: vacío, 7 dígitos, con letras, 16 dígitos. |
| Entrada no permitida | 2 | Campo de más (`"estado": "PAGADO"`) → 422. `destino=cocina` en `/mensajes` → 422. |
| Errores de dominio | 3 | Pedido inexistente → 404 `pedido_no_encontrado`. `TransicionInvalida` → 409 con `estado_actual` y `destino`. `_avanzar` rechaza un salto y no deja evento. |
| Lectura y persistencia | 3 | Listado del más nuevo al más viejo y sin eventos. El pedido sobrevive a un reinicio. Las marcas de tiempo terminan en `Z`. |
| Filtros de la bandeja | 3 | Por pedido, por destino y el contenido del mensaje (el texto incluye el link). |

## 2. Por qué lo hicimos así

- **Un solo camino para cambiar el estado:** `_avanzar` valida contra la máquina de estados del Paso 3, actualiza `pedidos.estado` y registra el evento. Si algo saltea ese camino, el historial y el estado dejan de coincidir.
- **WhatsApp simulado en una tabla:** no hay un servicio externo, pero el mensaje queda guardado y se puede leer. Así las pruebas verifican *qué* se envió, *a quién* y *con qué link*, sin depender de una red.
- **Un reloj, no muchos `datetime.now()`:** toda hora sale de `reloj.ahora_utc()`. En el Paso 8 los tests la van a fijar para provocar el defecto de zona horaria.
- **UTC con `Z`:** con una sola zona, ordenar el texto es igual que ordenar el tiempo. Por eso los eventos se ordenan solo por `ocurrido_en`, sin desempatar por id. En el Paso 8 se ve qué pasa cuando cada actor escribe en su propia zona.
- **Rechazar lo que no se pidió (`extra="forbid"`):** si el cliente manda `"estado": "PAGADO"` al crear el pedido, la API responde 422 en vez de ignorarlo en silencio.
- **Teléfono con patrón `^\+?\d{8,15}$`:** el máximo de 15 dígitos sale del estándar telefónico E.164.
- **Errores traducidos en un solo lugar:** los servicios lanzan excepciones de dominio, y `main.py` las convierte en 404 o 409. Nunca llega un 500 por un id inexistente.
- **Riesgo observado:** en Windows, el reloj de Python avanza cada 15,6 ms. Los dos eventos del alta suelen tener **la misma marca de tiempo**, y hoy el orden sale bien porque SQLite respeta el orden de inserción cuando hay empate. Lo verificamos repitiendo el test 30 veces (30 de 30 en verde). Queda anotado para el Paso 8.
- **Prueba de mutación manual:** 3 defectos metidos a propósito, los 3 detectados por la suite: sacar `validar_transicion` de `_avanzar`, cambiar `extra="forbid"` por `"ignore"` y subir el límite del teléfono a 16 dígitos. Después se revirtieron.

## 3. Cómo se conecta con el proyecto

```
estados.py (Paso 3) ──► pedidos._avanzar ──► UPDATE pedidos.estado + INSERT eventos (Paso 2)
                               │
                               └─ TransicionInvalida ──► main.py ──► 409

reloj.marca_tiempo ──► eventos.ocurrido_en, mensajes.creado_en ──► (Paso 8) defecto de zona horaria
mensajes.enviar    ──► GET /mensajes ──► (Paso 9) pantalla "celular" del cliente y del delivery
POST /pedidos      ──► (Paso 5) cargar datos y cotizar: los items y el total completan el mismo JSON
```

- El JSON del pedido ya tiene todos los campos (`items`, `total`, `firmado`…), aunque por ahora vacíos. Los pasos 5 a 7 los van llenando sin cambiar la forma de la respuesta: ese contrato es el que la etapa 2 va a validar.
- La etapa 2 parametriza el 404 sobre **todas** las rutas de pedido (Paso 7).

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| Teléfono: un grupo válido y varios inválidos | 📘 ISTQB | [CTFL v4.0 §4.2.1 *Partición de equivalencia*](glosario.md#particiones) |
| Bordes del teléfono: 8 y 15 válidos, 7 y 16 inválidos | 📘 ISTQB | [CTFL v4.0 §4.2.2 *Análisis de valores límite*](glosario.md#valores-limite) |
| Test escrito antes del código (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Ruta, servicio, SQLite y bandeja probados juntos | 📘 ISTQB | [CTFL v4.0 §2.2.1 Nivel de prueba: *integración de componentes*](glosario.md#integracion-componentes) |
| `INICIADO → LINK_ENVIADO` por `_avanzar`; un salto se rechaza | 📘 ISTQB | [CTFL v4.0 §4.2.4 *Prueba de transición de estados*](glosario.md#transicion-estados) |
| Pedido inexistente | 📐 Norma | [RFC 9110 §15.5.5 — *404 Not Found*](glosario.md#http-404) |
| Transición que choca con el estado actual | 📐 Norma | [RFC 9110 §15.5.10 — *409 Conflict*](glosario.md#http-409) |
| Teléfono inválido o campos de más | 📐 Norma | [RFC 9110 §15.5.21 — *422 Unprocessable Content*](glosario.md#http-422) |
| El pedido sobrevive a un reinicio | 📐 Norma | [ISO/IEC 25010 — Fiabilidad › *Capacidad de recuperación*](glosario.md#recuperabilidad) |
| Marcas de tiempo en UTC con `Z` | 📐 Norma | [ISO 8601 / RFC 3339](glosario.md#iso8601) |
| Máximo de 15 dígitos en el teléfono | 📐 Norma | [ITU-T E.164](glosario.md#e164) |
| Rechazar campos que no se pidieron (`extra="forbid"`) | ✅ Buena práctica | [OWASP *Input Validation Cheat Sheet* (lista blanca)](glosario.md#validacion-entrada) |
| Un solo camino para cambiar el estado | ✅ Buena práctica | [Fuente única de verdad](glosario.md#table-driven) |
| Excepciones de dominio traducidas en `main.py` | ✅ Buena práctica | [Fallar rápido (*fail fast*) con errores descriptivos](glosario.md#fail-fast) |
| WhatsApp simulado en una tabla | ✅ Buena práctica | [Doble de prueba: *fake*](glosario.md#doble-prueba) |
| La hora sale de una sola función reemplazable | ✅ Buena práctica | [Reloj como dependencia (*seam*)](glosario.md#reloj-inyectable) |
| Un caso con nombre por cada teléfono | ✅ Buena práctica | [`pytest.mark.parametrize`](glosario.md#parametrizados) |
| 3 defectos metidos a propósito, 3 detectados | ✅ Buena práctica | [Prueba de mutación, hecha a mano](glosario.md#mutacion) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q                         # 52 tests en verde (33 previos + 19 nuevos)
.venv/Scripts/python -m pytest tests/test_crear_pedido.py -v   # cada teléfono por nombre
```

Probarlo a mano (con el servidor levantado, `uvicorn delivery.main:app`):

```bash
curl -s -X POST localhost:8000/pedidos -H "Content-Type: application/json" -d '{"telefono": "1122334455"}'
# 201: estado LINK_ENVIADO y dos eventos
curl -s "localhost:8000/mensajes?destino=cliente"     # el mensaje con el link /cliente/pedido/1
curl -s localhost:8000/pedidos/999                   # 404 {"detail": {"error": "pedido_no_encontrado"}}
```

## 6. En términos técnicos (para entrevista)

> "Implementé el alta del pedido como una operación transaccional que encadena tres pasos del negocio: crea el pedido, envía el link por un canal de mensajería simulado (un *fake* que deja todo auditable) y avanza el estado por un único punto de mutación que valida contra la máquina de estados y registra el evento. Diseñé los casos del teléfono con partición de equivalencia y valores límite tomando el máximo de E.164, rechazo campos no declarados con validación por lista blanca y traduzco las excepciones de dominio a 404, 409 y 422 según RFC 9110. Confirmé con tres mutaciones manuales que la suite las detecta, y documenté un riesgo de empate de marcas de tiempo por la resolución del reloj en Windows."
