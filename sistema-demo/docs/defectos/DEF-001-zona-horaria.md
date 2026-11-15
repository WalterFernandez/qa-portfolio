# DEF-001: La línea de tiempo del pedido muestra PAGADO antes que COTIZADO

Informe de incidente con los campos de ISO/IEC/IEEE 29119-3 (*Incident report*).

| Campo | Valor |
|---|---|
| **Identificador** | DEF-001 |
| **Tipo** | Defecto **sembrado** a propósito (Paso 8). Se deja sin corregir: es el blanco de las pruebas de las etapas 2 a 4. |
| **Fecha** | 2026-11-15 |
| **Ítem de prueba** | Sistema demo, `GET /pedidos/{id}` (campo `eventos`) y páginas que lo muestran (cliente y panel central) |
| **Entorno** | Windows 10, Python 3.12, uvicorn 0.32.1, SQLite; Chrome de escritorio |
| **Activación** | `DEMO_DEFECTO_ZONA_HORARIA=1` |
| **Severidad** | **Mayor.** El historial del pedido miente sobre el orden real: el cliente "pagó" algo que todavía no estaba cotizado. No se pierden datos, pero cualquier reclamo o auditoría que use la línea de tiempo llega a una conclusión falsa. |
| **Prioridad** | **Alta.** Afecta a todo pedido con más de un actor, o sea, a todos. |
| **Estado** | Abierto (sembrado). Corrección propuesta abajo. |

## Pasos para reproducir

1. Levantar el sistema con el defecto prendido y una base aparte:
   ```bash
   cd sistema-demo
   DEMO_DB_PATH=data/def-001.db DEMO_DEFECTO_ZONA_HORARIA=1 \
     .venv/Scripts/python -m uvicorn delivery.main:app
   ```
2. Abrir http://localhost:8000/, elegir un plato y dejar un teléfono (crea el pedido 1).
3. Abrir el link del mensaje (`/cliente/pedido/1`), cargar cantidad y dirección, firmar y pagar.
4. Abrir http://localhost:8000/panel#1 y mirar la **línea de tiempo** del pedido 1.

## Resultado esperado

Los eventos en el orden en que ocurrieron, con marcas comparables entre sí (UTC con `Z`, RFC 3339 §5.6):

`INICIADO → LINK_ENVIADO → DATOS_CARGADOS → COTIZADO → PAGADO → ASIGNADO`

## Resultado obtenido

`INICIADO, DATOS_CARGADOS, PAGADO, LINK_ENVIADO, COTIZADO, ASIGNADO`

**PAGADO aparece antes que COTIZADO.** Las marcas no tienen `Z` ni offset: las del cliente están en la hora de México (UTC-6) y las del servicio en la de Nueva York (UTC-5), así que quedan agrupadas por actor y no por orden real.

## Evidencia

- Captura del panel central con el defecto prendido: [`evidencia/panel-zona-horaria-y-500.jpg`](evidencia/panel-zona-horaria-y-500.jpg). Se ven `PAGADO · cliente 12:43:27` antes que `COTIZADO · servicio 13:43:27`, y "Zona horaria **PRENDIDO**" en Defectos sembrados. (El banner `[error_500]` de la misma captura es otro defecto: [DEF-003](DEF-003-sqlite-entre-hilos.md).)
- Tests automáticos que lo detectan (`tests/test_defectos.py`), con el reloj fijo para que el orden sea repetible:
  - `PAGADO` antes que `COTIZADO` y el orden exacto de arriba.
  - Marcas `09:00:05` (cliente) y `10:00:15` (servicio) sin `Z` ni `+`.
  - En los 13 pasos, los eventos quedan agrupados por actor.
  - Par sin el defecto: orden correcto y `2026-11-14T15:00:05.000000Z`.

## Causa raíz

Dos decisiones que, juntas, rompen el orden:

1. `delivery/reloj.py` `marca_tiempo`: con el defecto, cada actor guarda su **hora local sin offset** (`%Y-%m-%dT%H:%M:%S.%f`). Una hora local sin zona no se puede comparar con la de otro actor.
2. `delivery/pedidos.py` `_eventos`: ordena **solo** por `ocurrido_en`, que es texto (`ORDER BY ocurrido_en`). Con marcas en zonas distintas, el orden alfabético deja de ser el orden en el tiempo.

## Corrección propuesta

- Guardar siempre en **UTC con `Z`** (es lo que hace el sistema con el defecto apagado) y convertir a la hora local **solo al mostrar**.
- Desempatar por el `id` del evento (`ORDER BY ocurrido_en, id`), que es el orden de inserción.
- Agregar una prueba de contrato que exija el formato RFC 3339 con zona en `ocurrido_en`.

## Referencias

- ISO 8601 / RFC 3339 §5.6: la marca de tiempo lleva `Z` u offset.
- ISTQB CTFL v4.0: pruebas de transición de estados (el orden de los eventos es la secuencia de la máquina de estados); defecto sembrado (*fault seeding*).
- Construcción del defecto: [`pasos/paso-08-defectos-sembrados.md`](../../../pasos/paso-08-defectos-sembrados.md).
