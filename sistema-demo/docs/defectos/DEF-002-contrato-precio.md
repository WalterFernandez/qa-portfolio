# DEF-002: Los montos salen como texto y el total estimado del cliente muestra NaN

Informe de incidente con los campos de ISO/IEC/IEEE 29119-3 (*Incident report*).

| Campo | Valor |
|---|---|
| **Identificador** | DEF-002 |
| **Tipo** | Defecto **sembrado** a propósito (Paso 8). Se deja sin corregir: es el blanco de las pruebas de contrato de la etapa 2. |
| **Fecha** | 2026-11-15 |
| **Ítem de prueba** | Sistema demo: `GET /platos` (`precio`), `GET /pedidos` y `GET /pedidos/{id}` (`precio_unitario`, `subtotal`, `total`); página del cliente |
| **Entorno** | Windows 10, Python 3.12, uvicorn 0.32.1, SQLite; Chrome de escritorio |
| **Activación** | `DEMO_DEFECTO_CONTRATO=1` |
| **Severidad** | **Crítica para los clientes de la API.** Cualquier consumidor que espera un número (la página del cliente, una app, un reporte) calcula mal o se rompe. Los datos guardados están bien: el problema está solo en la salida. |
| **Prioridad** | **Alta.** El precio aparece en el catálogo y en el total de todos los pedidos. |
| **Estado** | Abierto (sembrado). Corrección propuesta abajo. |

## Pasos para reproducir

1. Levantar el sistema con el defecto prendido y una base aparte:
   ```bash
   cd sistema-demo
   DEMO_DB_PATH=data/def-002.db DEMO_DEFECTO_CONTRATO=1 \
     .venv/Scripts/python -m uvicorn delivery.main:app
   ```
2. `curl -s localhost:8000/platos` y mirar el tipo de `precio`.
3. Abrir http://localhost:8000/, elegir un plato y dejar un teléfono.
4. Abrir `/cliente/pedido/1` y subir la cantidad de un plato: mirar el **total estimado** (`data-testid="total-estimado"`).

## Resultado esperado

- `precio`, `precio_unitario`, `subtotal` y `total` son **enteros** en pesos (`9000`), como define el OpenAPI de la API.
- El total estimado muestra un monto, por ejemplo `$ 18.000`.

## Resultado obtenido

- `"precio": "$ 9.000"` (texto) en `/platos`; `"total": "$ 22.500"` en el pedido.
- El total estimado del cliente muestra **`NaN`**: la página multiplica `"$ 9.000" × 2`.
- Un pedido sin cotizar sigue con `"total": null` (eso está bien).

## Evidencia

- Tests automáticos que lo detectan (`tests/test_defectos.py`):
  - Con el defecto: `precio` `"$ 9.000"` en `/platos`; `total` `"$ 22.500"`, `precio_unitario` y `subtotal` como texto en el pedido y en `GET /pedidos`.
  - La **misma base** leída sin el defecto devuelve `22500`: los datos están bien, la salida no.
  - Par sin el defecto: enteros en todos los campos.
- Captura del `NaN` en la página del cliente: queda para la prueba manual del Paso 9 (pendiente del usuario). Se guarda en `evidencia/` cuando esté.

## Causa raíz

`delivery/catalogo.py` `monto` es el único lugar donde se decide cómo sale un monto por la API. Con el defecto devuelve `formato.pesos(n)` (`"$ 9.000"`), un texto pensado para **mostrar**, en vez del entero. Se mezcló la presentación con el contrato de datos.

## Corrección propuesta

- La API devuelve siempre **enteros**; el formato `$ 9.000` lo aplica cada pantalla (como ya hace `pesos()` en `api.js`).
- Prueba de contrato en la etapa 2: un JSON Schema generado del OpenAPI con `"total": {"type": ["integer", "null"]}` hace fallar este defecto en el gate de QA.

## Referencias

- OpenAPI 3.1: tipos del contrato (`integer`).
- ISO/IEC 25010: Compatibilidad › Interoperabilidad.
- ISTQB CTFL v4.0: pruebas de integración de componentes (contrato entre la API y sus clientes); defecto sembrado (*fault seeding*).
- Construcción del defecto: [`pasos/paso-08-defectos-sembrados.md`](../../../pasos/paso-08-defectos-sembrados.md).
