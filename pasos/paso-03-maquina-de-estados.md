# Paso 3: Máquina de estados del pedido

**Objetivo:** definir en un solo lugar por qué estados pasa un pedido y qué cambios están permitidos, y probarlo con la técnica ISTQB de **transición de estados** antes de que exista cualquier ruta HTTP.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/estados.py` | `Estado` (los 13 estados), `TRANSICIONES` (la tabla de cambios permitidos), `CANCELABLES`, la excepción `TransicionInvalida` y `validar_transicion`. |
| `sistema-demo/tests/test_estados.py` | 29 tests unitarios, sin HTTP ni base de datos. |

**El diagrama de estados:**

```
INICIADO → LINK_ENVIADO → DATOS_CARGADOS → COTIZADO → PAGADO → ASIGNADO → RETIRADO → EN_CAMINO → EN_PUERTA
   │            │               │              │                                                   │
   └────────────┴───────┬───────┴──────────────┘                                         ┌─────────┴─────────┐
                        ▼                                                                ▼                   ▼
                    CANCELADO (final)                                                RECIBIDO ◄────────► ENTREGADO
                                                                                     (cliente)           (delivery)
                                                                                         └───────┬───────────┘
                                                                                                 ▼
                                                                                          CERRADO (final)
```

- **Cadena lineal:** 8 pasos hacia adelante, sin saltos ni retrocesos.
- **Cancelar:** solo antes de pagar (`CANCELABLES` = los 4 primeros estados).
- **En la puerta:** el cliente confirma "recibido" y el delivery "entregado", en cualquier orden. Recién con las dos confirmaciones se puede `CERRADO`.
- **Finales:** `CERRADO` y `CANCELADO` no tienen salidas.

**Los tests:**

| Grupo | Cantidad | Qué verifica |
|---|---|---|
| Transiciones válidas | 18 | Cada flecha del diagrama se acepta. |
| Inválidas con nombre | 6 | Salto (`INICIADO→COTIZADO`), retroceso (`PAGADO→COTIZADO`), cancelar después de pagar, salir de `CERRADO`, salir de `CANCELADO`, cerrar sin confirmaciones (`EN_PUERTA→CERRADO`). Además verifica que el error informe el estado actual y el destino. |
| Tabla completa | 1 | Recorre los 13 × 13 = 169 pares: los 151 que no están en la tabla tienen que fallar. |
| Estructura | 4 | Hay 13 estados, exactamente 18 transiciones, los finales sin salidas y `CANCELABLES` correcto. |

## 2. Por qué lo hicimos así

- **Una sola fuente de verdad:** las reglas viven en un diccionario (`TRANSICIONES`), no repartidas en `if` por todo el código. Desde el Paso 4, **toda** mutación de estado pasa por `validar_transicion`.
- **Primero la lógica, después HTTP:** la máquina de estados se prueba sola, en milisegundos. Cuando el Paso 4 la conecte a la API, el error `TransicionInvalida` se va a traducir en un **409 Conflict**.
- **`StrEnum`:** cada estado es a la vez un enum (el editor detecta errores de tipeo) y un texto (`"PAGADO"`), que se guarda en SQLite y viaja en el JSON tal cual.
- **Error con datos:** `TransicionInvalida` lleva `actual` y `destino`, para que la respuesta 409 diga exactamente qué se intentó.
- **Cancelar solo antes de pagar:** después del pago hay dinero de por medio y un delivery asignado. Ese riesgo de negocio queda bloqueado en la propia tabla.
- **Dos confirmaciones para cerrar:** un pedido no se cierra solo porque el delivery dice que lo entregó; también tiene que confirmarlo el cliente.
- **Fijar la cantidad de transiciones (18):** la tabla completa se compara contra `TRANSICIONES`, así que una flecha agregada por error pasaría inadvertida. El test que cuenta 18 lo evita.
- **Prueba de mutación manual:** agregamos a propósito la flecha prohibida `EN_PUERTA→CERRADO` y la suite la detectó con 2 tests en rojo. Después la sacamos. Así comprobamos que los tests no pasan "de casualidad".

## 3. Cómo se conecta con el proyecto

```
estados.py ──► (Paso 4) pedidos._avanzar(ctx, id, destino, actor)
                    │        valida con validar_transicion → actualiza pedidos.estado → inserta en eventos
                    │
                    └─ TransicionInvalida ──► manejador en main.py ──► HTTP 409 {"error": "transicion_invalida", ...}

CANCELABLES ──► (Paso 6–7) cancelar solo si el pedido está en uno de esos 4 estados
EN_PUERTA / RECIBIDO / ENTREGADO ──► (Paso 7) confirmaciones del cliente y del delivery
```

- La tabla `pedidos` (Paso 2) guarda el estado como texto, y `Estado` es justamente un texto.
- La tabla `eventos` (Paso 2) va a registrar cada transición aceptada con quién la hizo y cuándo.
- En la etapa 2, las pruebas de API van a repetir algunos de estos casos por HTTP (esperando 409), pero sin repetir los 169 pares: la cobertura fina queda acá, en el nivel unitario, que es el más barato.

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| Diagrama y tabla de estados, casos válidos e inválidos | 📘 ISTQB | [CTFL v4.0 §4.2.4 *Prueba de transición de estados*](glosario.md#transicion-estados) |
| Cobertura de transiciones válidas (18/18) y de todas las transiciones (169/169) | 📘 ISTQB | [CTFL v4.0 §4.2.4, criterios de cobertura](glosario.md#cobertura-transiciones) |
| Test escrito antes del código (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Probar la lógica sola, sin HTTP ni base | 📘 ISTQB | [CTFL v4.0 §2.2.1 Nivel de prueba: *prueba de componente* (unitaria)](glosario.md#prueba-componente) |
| Bloquear cancelar después de pagar | 📘 ISTQB | [CTFL v4.0 §5.2 *Pruebas basadas en riesgos*](glosario.md#riesgos) |
| Las transiciones del pedido son correctas y completas | 📐 Norma | [ISO/IEC 25010 — Adecuación funcional › *Corrección* y *Completitud*](glosario.md#adecuacion-funcional) |
| Diagrama de máquina de estados | 📐 Norma | [UML 2.5 (OMG; publicado también como ISO/IEC 19505) — *State Machines*](glosario.md#uml-estados) |
| Un 409 cuando el cambio choca con el estado actual (Paso 4) | 📐 Norma | [RFC 9110 §15.5.10 — *409 Conflict*](glosario.md#http-409) |
| Las reglas en una tabla de datos, no en `if` sueltos | ✅ Buena práctica | [Fuente única de verdad; diseño guiado por tablas (*table-driven*)](glosario.md#table-driven) |
| Tests parametrizados (un caso por fila) | ✅ Buena práctica | [`pytest.mark.parametrize`; principios FIRST](glosario.md#parametrizados) |
| Excepción de dominio con los datos del error | ✅ Buena práctica | [Fallar rápido (*fail fast*) con errores descriptivos](glosario.md#fail-fast) |
| Meter un defecto a propósito para ver si los tests lo detectan | ✅ Buena práctica | [Prueba de mutación (*mutation testing*), hecha a mano](glosario.md#mutacion) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q                      # 33 tests en verde (4 previos + 29 nuevos)
.venv/Scripts/python -m pytest tests/test_estados.py -v  # ver cada transición por nombre
```

Probarlo a mano en la consola de Python:

```python
>>> from delivery.estados import Estado, validar_transicion
>>> validar_transicion(Estado.COTIZADO, Estado.PAGADO)      # válido: no pasa nada
>>> validar_transicion(Estado.PAGADO, Estado.CANCELADO)
delivery.estados.TransicionInvalida: No se puede pasar de PAGADO a CANCELADO
```

## 6. En términos técnicos (para entrevista)

> "Modelé el ciclo de vida del pedido como una máquina de estados finita guiada por tablas, con una única función de validación por la que pasa toda mutación. La probé con la técnica de transición de estados de ISTQB a nivel de componente: 100 % de cobertura de transiciones válidas y de todas las transiciones (los 169 pares de la tabla), más casos inválidos con nombre como salto, retroceso y cancelar después de pagar. Para confirmar que la suite detecta defectos reales, hice una mutación manual con una transición prohibida y la suite falló como esperaba."
