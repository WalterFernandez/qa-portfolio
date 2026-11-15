# Paso 6: Firma, pago idempotente y asignación

**Objetivo:** el cliente firma (`POST /pedidos/{id}/firma`) y paga (`POST /pedidos/{id}/pago`). En la misma llamada del pago el servicio asigna el pedido a un delivery y le manda el link por WhatsApp simulado, y el pedido queda en `ASIGNADO`. El pago es **idempotente**: un doble clic en "Pagar" responde lo mismo y no duplica nada.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/pedidos.py` | `firmar(...)`: guarda la firma sin cambiar de estado (se puede volver a firmar antes de pagar). `pagar(...)`: avanza a `PAGADO`, avisa al delivery y avanza a `ASIGNADO`. Suma `FirmaRequerida` y `YA_PAGADOS` (los estados donde pagar no hace nada). |
| `sistema-demo/delivery/rutas_pedidos.py` | Rutas `POST /pedidos/{id}/firma` (modelo `Firma`, patrón `FIRMA_PNG`, máximo `FIRMA_MAX = 200_000`) y `POST /pedidos/{id}/pago` (sin body). |
| `sistema-demo/delivery/main.py` | Nuevo manejador: `FirmaRequerida` → **409** `{"detail": {"error": "firma_requerida"}}`. |
| `sistema-demo/delivery/db.py` | Columna `firma TEXT` en `pedidos` y `COLUMNAS_NUEVAS`: al arrancar se agrega la columna a una base vieja que no la tiene. |
| `sistema-demo/tests/conftest.py` | Constante `FIRMA_OK` y fixture `pedido_cotizado` (un pedido en `COTIZADO`). |
| `sistema-demo/tests/test_pago.py` | 32 tests: camino feliz, idempotencia, formato de la firma, estados, existencia y base vieja. |

**Qué pasa en `POST /pedidos/{id}/pago`** (pasos 6 y 7 del flujo de negocio, en una sola llamada):

```
cliente: POST /pedidos/1/pago
   │
   ├─ ¿existe el pedido? ─────────────────────────────────────► 404 pedido_no_encontrado
   ├─ ¿ya está PAGADO o más adelante? ────────────────────────► 200 con el pedido, sin tocar nada
   ├─ ¿el estado permite PAGADO? (solo COTIZADO) ─────────────► 409 transicion_invalida
   ├─ ¿firmó? ────────────────────────────────────────────────► 409 firma_requerida
   ├─ _avanzar(PAGADO) ───────────────► evento (actor: cliente)
   ├─ mensajes.enviar(delivery, "Nuevo pedido #1: retirar y entregar en ...", /delivery/pedido/1)
   └─ _avanzar(ASIGNADO) ─────────────► evento (actor: servicio)
   │
   ◄─ 200 + pedido completo (estado ASIGNADO)
```

**Tabla de decisión del pago:**

| Estado | ¿Firmó? | Resultado |
|---|---|---|
| Antes de `COTIZADO` | da igual | 409 `transicion_invalida` |
| `COTIZADO` | no | 409 `firma_requerida` |
| `COTIZADO` | sí | 200, pasa a `ASIGNADO` y avisa al delivery |
| `PAGADO` o posterior | da igual | 200 con el pedido, sin cambios |
| `CANCELADO` | da igual | 409 `transicion_invalida` |

**Los tests:**

| Grupo | Cantidad | Qué verifica |
|---|---|---|
| Camino feliz | 3 | Firmar marca `firmado` sin cambiar de estado y la imagen no viaja en el JSON; volver a firmar reemplaza la firma; pagar deja `PAGADO` (cliente) y `ASIGNADO` (servicio) y un WhatsApp al teléfono del delivery con la dirección y el link. |
| Idempotencia | 9 | Pagar dos veces → 200 con el mismo pedido, un solo `PAGADO` y un solo mensaje. Pagar en cada uno de los 8 estados de `PAGADO` a `CERRADO` → 200 sin cambios. |
| Formato de la firma | 12 | PNG válido, `jpeg`, sin prefijo, prefijo sin datos, caracteres fuera de base64, espacio adelante; 200 000 caracteres pasa y 200 001 no. Body vacío, con campos de más o `null` → 422. Una firma rechazada no marca el pedido. |
| Estados | 5 | Pagar sin firma → 409 `firma_requerida` sin eventos ni mensajes. Pagar o firmar antes de cotizar → 409 `transicion_invalida`. Firmar después de pagar → 409. Pagar un `CANCELADO` → 409. |
| Existencia | 2 | Firma y pago sobre el pedido 999 → 404. |
| Base vieja | 1 | Una base sin la columna `firma` se completa al arrancar y se puede firmar. |

## 2. Por qué lo hicimos así

- **Idempotencia del pago:** HTTP no garantiza que `POST` sea idempotente. Un doble clic o un reintento por una red lenta mandan dos pagos. Si el pedido ya está pagado (o más adelante), `pagar` no hace nada y la ruta devuelve el pedido como está. Así no hay un segundo `PAGADO` ni un segundo aviso al delivery.
- **`CANCELADO` no cuenta como pagado:** un pedido cancelado no se puede pagar. Responder 200 ahí diría "todo bien" cuando no hubo pago, así que da 409.
- **Primero el estado, después la firma:** pagar un pedido sin cotizar da `transicion_invalida`, no `firma_requerida`. El error dice lo que de verdad falta.
- **Firmar no cambia de estado:** la firma es una condición del pago, no un paso propio de la máquina de estados. Por eso firmar valida la transición a `PAGADO`: solo se puede firmar donde el próximo paso es pagar.
- **La imagen se guarda pero no viaja:** la firma puede pesar hasta 200 000 caracteres. El JSON del pedido solo trae `firmado: true`, para no mandar la imagen en cada respuesta ni en el listado.
- **Formato de la firma por lista blanca:** el patrón `^data:image/png;base64,[A-Za-z0-9+/]+={0,2}$` exige el prefijo del PNG, al menos un dato y solo el alfabeto base64. Es lo que entrega un `<canvas>` del navegador (Paso 9).
- **Migración aditiva:** `CREATE TABLE IF NOT EXISTS` no toca una tabla que ya existe, así que una base creada antes de este paso no tendría `firma`. Al arrancar, `db.py` revisa `PRAGMA table_info` y agrega la columna si falta. Un test lo prueba partiendo de una base sin la columna.
- **El teléfono del delivery sale de la configuración** (`cfg.delivery_telefono`, ficticio): el pedido nunca lo trae.
- **Prueba de mutación manual: 12 de 12.** Se metieron 12 defectos: sacar la idempotencia, sacar el chequeo de firma, invertir estado y firma, contar `CANCELADO` como pagado, firmar en cualquier estado, no guardar la imagen, no asignar, mandar el WhatsApp al cliente, actor del pago `servicio`, aceptar el prefijo sin datos, correr el límite en uno y sacar la migración. Todos rompieron al menos un test.

## 3. Cómo se conecta con el proyecto

```
COTIZADO (Paso 5) ──► firmar ──► pagar ──► PAGADO → ASIGNADO
estados.py (Paso 3) ──► _avanzar (Paso 4) ──► los dos eventos del pago
mensajes.enviar (Paso 4) ──► "Nuevo pedido #..." ──► bandeja del delivery ──► (Paso 9) su pantalla
ASIGNADO ──► (Paso 7) el delivery retira, va en camino, llega a la puerta y se cierra
```

- El total que se cobra es el que cotizó el servidor en el Paso 5; el pago no recibe montos.
- El link `/delivery/pedido/{id}` es la página que se construye en el Paso 9.
- `CANCELABLES` (Paso 3) define, por resta, los estados donde pagar no hace nada: `YA_PAGADOS = todos − CANCELABLES − {CANCELADO}`.
- En la etapa 3, Playwright repite el doble clic en "Pagar" desde el navegador.

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| `COTIZADO → PAGADO → ASIGNADO`; firmar o pagar fuera de `COTIZADO` se rechaza | 📘 ISTQB | [CTFL v4.0 §4.2.4 *Prueba de transición de estados*](glosario.md#transicion-estados) |
| Estado × firma → resultado del pago | 📘 ISTQB | [CTFL v4.0 §4.2.3 *Prueba de tabla de decisión*](glosario.md#tabla-decision) |
| Firma válida, otro formato, sin prefijo, sin datos, fuera de base64 | 📘 ISTQB | [CTFL v4.0 §4.2.1 *Partición de equivalencia*](glosario.md#particiones) |
| Largo de la firma: 200 000 y 200 001 | 📘 ISTQB | [CTFL v4.0 §4.2.2 *Análisis de valores límite*](glosario.md#valores-limite) |
| Test escrito antes del código (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Ruta, servicio, SQLite y bandeja probados juntos | 📘 ISTQB | [CTFL v4.0 §2.2.1 Nivel de prueba: *integración de componentes*](glosario.md#integracion-componentes) |
| Doble clic en "Pagar" = cobro doble | 📘 ISTQB | [CTFL v4.0 §5.2 *Gestión de riesgos*](glosario.md#riesgos) |
| Firma o pago de un pedido inexistente | 📐 Norma | [RFC 9110 §15.5.5 — *404 Not Found*](glosario.md#http-404) |
| Pagar sin firma, firmar o pagar fuera de `COTIZADO` | 📐 Norma | [RFC 9110 §15.5.10 — *409 Conflict*](glosario.md#http-409) |
| Firma con otro formato, demasiado larga o con campos de más | 📐 Norma | [RFC 9110 §15.5.21 — *422 Unprocessable Content*](glosario.md#http-422) |
| `POST` no es idempotente por norma: lo garantiza el servidor | 📐 Norma | [RFC 9110 §9.2.2 — *Idempotent Methods*](glosario.md#metodos-idempotentes) |
| Firma como `data:image/png;base64,...` | 📐 Norma | [RFC 2397 (*data URL*) y RFC 4648 (base64)](glosario.md#data-url) |
| Un pago o una firma rechazados no dejan nada | 📐 Norma | [ISO/IEC 25010 — Seguridad › *Integridad*](glosario.md#integridad) |
| Pagar dos veces = pagar una vez | ✅ Buena práctica | [Operaciones idempotentes](glosario.md#idempotencia) |
| Patrón de la firma y nada de campos de más | ✅ Buena práctica | [OWASP *Input Validation Cheat Sheet* (lista blanca)](glosario.md#validacion-entrada) |
| La columna `firma` se agrega a una base vieja al arrancar | ✅ Buena práctica | [Migraciones de esquema aditivas](glosario.md#migracion-esquema) |
| Pago, mensaje y asignación en una sola transacción | ✅ Buena práctica | [Patrón *Unit of Work*](glosario.md#unit-of-work) |
| Primero el estado, después la firma, con códigos de error | ✅ Buena práctica | [Fallar rápido (*fail fast*) con errores descriptivos](glosario.md#fail-fast) |
| Un caso con nombre por estado y por formato de firma | ✅ Buena práctica | [`pytest.mark.parametrize`](glosario.md#parametrizados) |
| 12 defectos a propósito, 12 detectados | ✅ Buena práctica | [Prueba de mutación, hecha a mano](glosario.md#mutacion) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q                      # 126 tests en verde (94 previos + 32 nuevos)
.venv/Scripts/python -m pytest tests/test_pago.py -v   # cada estado y cada formato por nombre
```

Probarlo a mano (con el servidor levantado, `uvicorn delivery.main:app`, y el pedido 1 ya cotizado como en el Paso 5):

```bash
curl -s -X POST localhost:8000/pedidos/1/pago
# 409: {"detail": {"error": "firma_requerida"}}
curl -s -X POST localhost:8000/pedidos/1/firma -H "Content-Type: application/json" \
  -d '{"imagen": "data:image/png;base64,iVBORw0KGgo="}'
curl -s -X POST localhost:8000/pedidos/1/pago    # 200: estado ASIGNADO
curl -s -X POST localhost:8000/pedidos/1/pago    # 200: el mismo pedido, un solo PAGADO
curl -s "localhost:8000/mensajes?destino=delivery&pedido_id=1"   # un solo aviso al delivery
```

## 6. En términos técnicos (para entrevista)

> "Implementé el pago como una operación idempotente del lado del servidor: `POST` no lo es por RFC 9110, así que si el pedido ya está pagado o más adelante la ruta devuelve el pedido sin registrar otro evento ni volver a avisar al delivery. Eso cubre el doble clic y los reintentos de red. La firma es una precondición del pago y no un estado propio. La valido por lista blanca como *data URL* PNG en base64, con un tope de largo. Diseñé los casos con una tabla de decisión de estado por firma, partición de equivalencia y valores límite sobre la imagen, y agregué la columna nueva con una migración aditiva que tiene su propio test. La prueba de mutación manual detectó 12 de 12 defectos."
