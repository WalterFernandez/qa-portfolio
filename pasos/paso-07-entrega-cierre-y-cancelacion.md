# Paso 7: Entrega, cierre y cancelación

**Objetivo:** completar el recorrido del pedido. El delivery lo retira y el servicio avisa al cliente que va en camino. En la puerta, cliente y delivery confirman cada uno por su lado, en cualquier orden, y con las dos confirmaciones el pedido se **cierra**. Antes de pagar, el cliente o el servicio lo pueden **cancelar**; después, no. Con este paso, los 13 pasos del negocio funcionan de punta a punta.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/pedidos.py` | `marcar_retirado` (pasos 8 y 9: `RETIRADO`, aviso "Tu pedido está en camino" y `EN_CAMINO`), `marcar_en_puerta` (paso 10), `confirmar_recibido` y `confirmar_entregado` (pasos 11 a 13, sobre `_confirmar`), `cancelar(por)` y la excepción `NoCancelable`. Suma `FINALES` y `CONFIRMACIONES`. |
| `sistema-demo/delivery/rutas_pedidos.py` | Rutas `POST /pedidos/{id}/retirado`, `/en-puerta`, `/recibido`, `/entregado` (sin body) y `/cancelar` (modelo `Cancelacion`: `por` es `"cliente"` o `"servicio"`). |
| `sistema-demo/delivery/main.py` | Nuevo manejador: `NoCancelable` → **409** `{"detail": {"error": "no_cancelable", "estado_actual": ..., "mensaje": ...}}`. |
| `sistema-demo/tests/conftest.py` | Fixture `pedido_asignado`, la lista `RECORRIDO` y el helper `avanzar_hasta`, que lleva un pedido hasta un estado usando solo la API. |
| `sistema-demo/tests/test_entrega.py` | 14 tests: flujo completo, retiro, en la puerta, confirmaciones y cierre. |
| `sistema-demo/tests/test_cancelacion.py` | 14 tests: tabla de decisión de la cancelación y `por` inválido. |
| `sistema-demo/tests/test_rutas_404.py` | 9 tests: cada ruta de un pedido con el id 999 → 404. |
| `sistema-demo/tests/test_concurrencia.py` | 4 tests nuevos: dos confirmaciones a la vez, la misma confirmación dos veces a la vez, y cancelar contra pagar en los dos órdenes. La barrera ahora también puede frenar por estado de origen (`desde`). |

**El recorrido después del pago** (pasos 8 a 13 del negocio):

```
ASIGNADO
   │  POST /retirado   (delivery)
   ├─ _avanzar(RETIRADO) ─────────► evento (actor: delivery)
   ├─ WhatsApp al cliente: "Tu pedido está en camino"  (/cliente/pedido/{id})
   └─ _avanzar(EN_CAMINO) ────────► evento (actor: servicio)
EN_CAMINO
   │  POST /en-puerta  (delivery)
EN_PUERTA
   │  POST /recibido (cliente) ─► RECIBIDO ─┐
   │  POST /entregado (delivery) ► ENTREGADO ┤   en cualquier orden
   │                                         └─► la segunda confirmación cierra:
CERRADO  (actor: servicio)
```

**Tabla de decisión de la cancelación:**

| Regla | Estado de partida | Quién cancela | Resultado |
|---|---|---|---|
| R1 | `LINK_ENVIADO` (antes del pago) | cliente | 200, `CANCELADO`, `cancelado_por = cliente` |
| R2 | `COTIZADO` (antes del pago) | servicio | 200, `CANCELADO`, `cancelado_por = servicio` |
| R3 | `ASIGNADO` (pagado) | cliente | 409 `no_cancelable`: "No se puede cancelar un pedido que ya fue pagado" |
| R4 | `CERRADO` (final) | servicio | 409 `no_cancelable`: "El pedido ya está finalizado" |
| R5 | `CANCELADO` (final) | cliente | 409 `no_cancelable`: "El pedido ya está finalizado" |
| — | cualquiera | `delivery`, vacío, otro texto o sin `por` | 422 |

**Los tests:**

| Grupo | Cantidad | Qué verifica |
|---|---|---|
| Flujo completo | 1 | Desde `POST /pedidos` hasta `CERRADO`: los 12 eventos exactos con su actor (`RECIBIDO` antes de `ENTREGADO`) y 4 mensajes (link, cotización, delivery, en camino). |
| Retiro y en la puerta | 5 | Retirar deja `RETIRADO` (delivery) y `EN_CAMINO` (servicio) y avisa al cliente. Retirar antes de pagar o dos veces → 409 sin otro aviso. En la puerta antes de retirar → 409. |
| Confirmaciones y cierre | 8 | Antes de llegar → 409. Una sola confirmación no cierra. El orden inverso (entregado y después recibido) también cierra. La misma confirmación dos veces → 409. Confirmar un pedido cerrado → 409. |
| Cancelación | 14 | R1 a R5, un representante por tramo pagado (`EN_CAMINO`, `EN_PUERTA`, `RECIBIDO`) con el mensaje "ya fue pagado", 5 bodies inválidos → 422 y un cancelado no se puede pagar. Cada 409 deja el pedido igual que antes. |
| Rutas 404 | 9 | `GET`, `PUT`, `firma`, `pago`, `retirado`, `en-puerta`, `recibido`, `entregado` y `cancelar` sobre el pedido 999 → 404 `pedido_no_encontrado`, con bodies válidos para que no los tape un 422. |
| Concurrencia | 4 | Cliente y delivery confirman a la vez → los dos 200 y un solo `CERRADO`. El cliente confirma dos veces a la vez → 200 y 409. El pago se adelanta a la cancelación → 409 `no_cancelable`. La cancelación se adelanta al pago → 409 y ningún aviso al delivery. |

## 2. Por qué lo hicimos así

- **Retiro y aviso en una sola llamada:** igual que el pago y la asignación. El delivery toca "Retirado" y el servicio manda el WhatsApp y pasa a `EN_CAMINO` en la misma transacción. Primero se "toma" el pedido con `_avanzar(RETIRADO)`: un doble toque da 409 antes de mandar un segundo aviso.
- **Dos confirmaciones independientes:** en la puerta, el cliente dice "lo recibí" y el delivery dice "lo entregué". Ninguna alcanza sola: el pedido se cierra recién con las dos. Así un delivery no puede cerrar un pedido que el cliente nunca recibió, ni al revés. Las banderas `recibido_cliente` y `entregado_delivery` quedan en el pedido para que se vea quién confirmó.
- **Estado y bandera en un solo `UPDATE` condicional:** `estado = RECIBIDO, recibido_cliente = 1 ... WHERE estado = <el leído>`. Si se escribieran en dos `UPDATE`, entre uno y otro podría entrar la otra confirmación y reabrir la carrera del Paso 6.
- **Dos confirmaciones al mismo tiempo no son un error:** las dos leen `EN_PUERTA` y una gana. La que pierde no responde 409, porque su confirmación es legítima: relee el estado nuevo y se reintenta una vez. Si en cambio se repite la *misma* confirmación, el reintento ve `RECIBIDO → RECIBIDO`, que la máquina de estados no permite, y da 409. La que confirma segunda es la que cierra, así que hay un solo `CERRADO`.
- **`no_cancelable` y no `transicion_invalida`:** para cancelar, el cliente necesita saber *por qué* no puede. El error trae un mensaje para cada caso: "ya fue pagado" (hay plata de por medio) o "ya está finalizado". Y si un pago se adelanta entre la lectura y la escritura de la cancelación, la respuesta es la misma `no_cancelable`: el resultado no depende de quién llegó primero por milisegundos.
- **El delivery no cancela:** `por` acepta solo `cliente` o `servicio`. Si el delivery no puede entregar, avisa y cancela el servicio. Mandar `delivery` da 422.
- **Una tabla de decisión deja ver los huecos:** cruzar estado (antes del pago, pagado, final) con quién cancela fija cada resultado esperado antes de escribir el código. Los estados pagados se cubren con un representante por tramo (partición de equivalencia), no los ocho.
- **Los 404, todos juntos:** la Review Focus #2 del plan pedía verificar que *cada* ruta pide el pedido antes de hacer otra cosa. Un solo test parametrizado sobre las 9 rutas lo muestra en una tabla, y una ruta nueva que se olvide queda a la vista.
- **Carreras con orden fijo:** el primer test de cancelar contra pagar dejaba ganar a cualquiera de los dos, así que cada rama se probaba solo a veces. Se reemplazó por dos tests que frenan a uno con un `Event` y dejan pasar al otro entero: los dos órdenes se prueban siempre.
- **Prueba de mutación manual: 16 de 16.** Sacar el reintento, cerrar siempre o nunca, no guardar la bandera, cerrar mirando la bandera propia, no traducir la carrera de la cancelación, invertir los mensajes, fijar `cancelado_por` o el actor, no avisar al cliente, quedarse en `RETIRADO`, actor del retiro equivocado, cruzar las confirmaciones, aceptar `delivery`, aceptar campos de más y permitir `RECIBIDO → RECIBIDO`: todos rompieron al menos un test. Un mutante de la primera tanda tenía un error de sintaxis (mataba la suite por no compilar): se rehízo para que simule el defecto real, y lo detectó el test que debía.

## 3. Cómo se conecta con el proyecto

```
ASIGNADO (Paso 6) ──► retirado ──► EN_CAMINO ──► en-puerta ──► recibido + entregado ──► CERRADO
estados.py (Paso 3) ──► las transiciones del cierre y CANCELABLES ya estaban definidas
_actualizar_si_sigue (Paso 6) ──► confirmaciones y cancelación sin carreras
mensajes.enviar (Paso 4) ──► "Tu pedido está en camino" ──► bandeja del cliente ──► (Paso 9) su pantalla
```

- La máquina de estados no cambió: las transiciones del cierre y de la cancelación existen desde el Paso 3. Este paso solo las conecta con rutas.
- `test_flujo_completo_los_13_pasos` es la base del Paso 8: con el defecto de zona horaria encendido, la lista de eventos sale en otro orden y ese test lo muestra.
- El helper `avanzar_hasta` reemplaza a los `UPDATE` directos a la base para preparar estados en los tests nuevos. Los de `test_pago.py` (`_forzar_estado`) quedaron como estaban.
- Las rutas `/retirado`, `/en-puerta` y `/entregado` son los botones de la página del delivery (Paso 9).

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| `ASIGNADO → … → CERRADO`; retirar sin pagar o confirmar dos veces se rechaza | 📘 ISTQB | [CTFL v4.0 §4.2.4 *Prueba de transición de estados*](glosario.md#transicion-estados) |
| Las 6 transiciones del cierre, con las confirmaciones en los dos órdenes | 📘 ISTQB | [CTFL v4.0 §4.2.4 *Criterios de cobertura*](glosario.md#cobertura-transiciones) |
| Estado de partida × quién cancela → resultado | 📘 ISTQB | [CTFL v4.0 §4.2.3 *Prueba de tabla de decisión*](glosario.md#tabla-decision) |
| `por` válido o inválido; un estado por tramo pagado | 📘 ISTQB | [CTFL v4.0 §4.2.1 *Partición de equivalencia*](glosario.md#particiones) |
| Test escrito antes del código (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Los 13 pasos de punta a punta por la API | 📘 ISTQB | [CTFL v4.0 §2.2.1 Nivel de prueba: *integración de componentes*](glosario.md#integracion-componentes) |
| Cerrar sin que el cliente reciba; cancelar con el pago hecho | 📘 ISTQB | [CTFL v4.0 §5.2 *Gestión de riesgos*](glosario.md#riesgos) |
| Las 9 rutas de un pedido inexistente | 📐 Norma | [RFC 9110 §15.5.5 — *404 Not Found*](glosario.md#http-404) |
| `no_cancelable`, confirmación repetida, retiro fuera de orden | 📐 Norma | [RFC 9110 §15.5.10 — *409 Conflict*](glosario.md#http-409) |
| `por` inválido o con campos de más | 📐 Norma | [RFC 9110 §15.5.21 — *422 Unprocessable Content*](glosario.md#http-422) |
| Los 13 pasos del negocio implementados y probados | 📐 Norma | [ISO/IEC 25010 — Adecuación funcional › *Completitud*](glosario.md#adecuacion-funcional) |
| Un 409 deja el pedido igual que antes | 📐 Norma | [ISO/IEC 25010 — Seguridad › *Integridad*](glosario.md#integridad) |
| Dos confirmaciones a la vez; cancelar contra pagar | ✅ Buena práctica | [Control de concurrencia optimista (CWE-367)](glosario.md#concurrencia-optimista) |
| Retiro, aviso y `EN_CAMINO` en una sola transacción | ✅ Buena práctica | [Patrón *Unit of Work*](glosario.md#unit-of-work) |
| `no_cancelable` con un mensaje para cada caso | ✅ Buena práctica | [Fallar rápido (*fail fast*) con errores descriptivos](glosario.md#fail-fast) |
| Un caso con nombre por regla, por ruta y por body | ✅ Buena práctica | [`pytest.mark.parametrize`](glosario.md#parametrizados) |
| 16 defectos a propósito, 16 detectados | ✅ Buena práctica | [Prueba de mutación, hecha a mano](glosario.md#mutacion) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q                              # 170 tests en verde (129 previos + 41)
.venv/Scripts/python -m pytest tests/test_entrega.py -v        # el recorrido y el cierre
.venv/Scripts/python -m pytest tests/test_cancelacion.py -v    # R1 a R5 por nombre
.venv/Scripts/python -m pytest tests/test_concurrencia.py -v   # las 7 carreras
```

Probarlo a mano (con el servidor levantado, `uvicorn delivery.main:app`, y el pedido 1 en `ASIGNADO` como en el Paso 6):

```bash
curl -s -X POST localhost:8000/pedidos/1/retirado    # 200: EN_CAMINO
curl -s "localhost:8000/mensajes?destino=cliente&pedido_id=1"   # el último: "Tu pedido está en camino"
curl -s -X POST localhost:8000/pedidos/1/en-puerta   # 200: EN_PUERTA
curl -s -X POST localhost:8000/pedidos/1/entregado   # 200: ENTREGADO (falta el cliente)
curl -s -X POST localhost:8000/pedidos/1/recibido    # 200: CERRADO
curl -s -X POST localhost:8000/pedidos/1/cancelar -H "Content-Type: application/json" \
  -d '{"por": "cliente"}'                            # 409 no_cancelable: "El pedido ya está finalizado"
```

## 6. En términos técnicos (para entrevista)

> "Completé el flujo del pedido de punta a punta: retiro, aviso al cliente, llegada, doble confirmación y cierre, más la cancelación. El cierre exige dos confirmaciones independientes, en cualquier orden, y probé las seis transiciones del cierre con los dos órdenes. Diseñé la cancelación con una tabla de decisión de estado de partida por quién cancela, con un error de dominio `no_cancelable` y un mensaje para cada caso. Como ya tenía control de concurrencia optimista del paso anterior, analicé las carreras nuevas: dos confirmaciones simultáneas no deben dar 409, así que la que pierde el `UPDATE` condicional relee y reintenta una vez; y una cancelación que pierde contra un pago devuelve el mismo `no_cancelable` que si hubiera llegado tarde. Las reproduje con orden fijo, frenando un hilo con un evento, para que cada rama se pruebe siempre y no según el scheduler. También verifiqué que las nueve rutas de un pedido devuelven el mismo 404. La mutación manual detectó 16 de 16 defectos, y en el camino encontré un mutante inválido que mataba la suite por error de sintaxis: lo rehíce para que simulara el defecto real."
