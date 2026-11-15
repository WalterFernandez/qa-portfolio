# Paso 2: Base de datos SQLite y catálogo (`GET /platos`)

**Objetivo:** que el sistema tenga memoria (una base de datos) y un menú de platos con precios fijos que el servidor controla.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/db.py` | Esquema de las 5 tablas, siembra de los 4 platos y la conexión que recibe cada request (`Ctx`). |
| `sistema-demo/delivery/catalogo.py` | `listar_platos(ctx)` para mostrar el menú y `precios(ctx)` para que el servidor calcule totales (Paso 5). |
| `sistema-demo/delivery/main.py` | Al arrancar se crea la base (`db.inicializar`) y se agrega la ruta `GET /platos`. |
| `sistema-demo/tests/test_catalogo.py` | 2 tests: el menú es exactamente el esperado con precios enteros, y reiniciar no duplica platos. |

**Las 5 tablas:**

| Tabla | Para qué sirve | Se usa en |
|---|---|---|
| `platos` | Menú: nombre y precio en pesos enteros. | Paso 2 (ya), Paso 5 |
| `pedidos` | Un pedido: teléfono, estado, dirección, total, firma, confirmaciones. | Pasos 4–7 |
| `pedido_items` | Qué platos y cuántos tiene cada pedido, con el precio del momento. | Paso 5 |
| `eventos` | Historial: cada cambio de estado con quién lo hizo y cuándo. | Pasos 4–8 |
| `mensajes` | Bandeja del WhatsApp simulado. | Paso 4 en adelante |

## 2. Por qué lo hicimos así

- **SQLite:** viene con Python, no hay que instalar un servidor y la base es un solo archivo. Mantiene el proyecto liviano, sin Docker.
- **Sin ORM, con SQL a mano:** se ve exactamente qué consulta se ejecuta, lo que sirve para explicar y depurar.
- **Precios como enteros (`9000`, no `9000.0`):** los números con decimales (`float`) tienen errores de redondeo (`0.1 + 0.2 = 0.30000000000000004`). Con dinero eso es inaceptable, y el test verifica que el precio sea `int`.
- **El precio lo define el servidor:** el cliente nunca manda precios ni totales. Así nadie puede pagar $1 modificando la página (riesgo que prueba el Paso 5).
- **Siembra que no se duplica:** los platos se cargan solo si la tabla está vacía. Si el servidor se reinicia diez veces, sigue habiendo 4 platos, y hay un test que lo comprueba.
- **Restricciones en la propia base:**
  - `CHECK (precio > 0)`: un precio negativo es imposible.
  - `FOREIGN KEY`: no puede existir un evento de un pedido que no existe.
  - `PRIMARY KEY (pedido_id, plato_id)` en `pedido_items`: el mismo plato no puede repetirse dentro de un pedido (base del error `plato_repetido` del Paso 5).
- **Una conexión por request (`obtener_ctx`):** si todo sale bien se guardan los cambios (*commit*); si algo falla, no queda nada a medias (*rollback*).
- **Consultas con parámetros `?`:** nunca se arma SQL pegando texto, lo que evita la inyección SQL.

## 3. Cómo se conecta con el proyecto

```
crear_app(cfg) ──► db.inicializar(cfg.db_path)   crea tablas + siembra platos
       │
       └─ GET /platos ──► Depends(obtener_ctx) ──► Ctx(con, cfg) ──► catalogo.listar_platos
                                                        │
                    (Paso 4+) pedidos, mensajes, eventos usan el mismo Ctx
                    (Paso 5) catalogo.precios() → total calculado en el servidor
```

- `Ctx` es la "llave" que reciben **todas** las funciones de negocio de los pasos siguientes: la conexión a la base más la configuración (para saber si hay defectos encendidos).
- La tabla `eventos` es donde el Paso 8 va a sembrar el defecto de **zona horaria**: los eventos se ordenan solo por fecha, y si una fecha está mal, el orden se rompe.
- La página del cliente (Paso 9) usa `GET /platos` para mostrar el menú. Playwright y Appium (etapas 3–4) lo van a recorrer.
- Como la base es un archivo, **los pedidos sobreviven a un reinicio** (Review Focus #5 del plan).

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| Test escrito antes del código (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Precio decidido por el servidor, dinero sin `float` | 📘 ISTQB | [CTFL v4.0 §5.2 *Pruebas basadas en riesgos* (riesgo de producto: cobro incorrecto)](glosario.md#riesgos) |
| Reiniciar y verificar que no se duplica | 📘 ISTQB | [Prueba de **re-ejecución/regresión** de la inicialización (CTFL v4.0 §2.2.3)](glosario.md#regresion) |
| Integridad de datos (CHECK, FOREIGN KEY, PRIMARY KEY) | 📐 Norma | [ISO/IEC 25010 — Seguridad › *Integridad*; Fiabilidad](glosario.md#integridad) |
| Datos persistentes tras reinicio | 📐 Norma | [ISO/IEC 25010 — Fiabilidad › *Capacidad de recuperación*](glosario.md#recuperabilidad) |
| Lenguaje SQL de las tablas | 📐 Norma | [ISO/IEC 9075 (estándar SQL; SQLite implementa un subconjunto)](glosario.md#sql) |
| `GET /platos` solo lee, no modifica | 📐 Norma | [RFC 9110 §9.2.1 — métodos HTTP *seguros* (safe)](glosario.md#metodos-seguros) |
| Consultas parametrizadas (`?`) | ✅ Buena práctica | [OWASP *SQL Injection Prevention Cheat Sheet*](glosario.md#owasp-sql) |
| Tablas separadas, sin datos repetidos (`pedido_items`) | ✅ Buena práctica | [Normalización relacional (3FN)](glosario.md#3fn) |
| Una transacción por request, commit/rollback | ✅ Buena práctica | [Patrón *Unit of Work*](glosario.md#unit-of-work) |
| Conexión entregada por `Depends` | ✅ Buena práctica | [Inyección de dependencias (FastAPI)](glosario.md#inyeccion-dependencias) |
| Siembra idempotente | ✅ Buena práctica | [Inicialización idempotente (se puede repetir sin efectos extra)](glosario.md#idempotencia) |
| Montos en enteros | ✅ Buena práctica | [Manejo de dinero en unidades enteras (evitar coma flotante binaria, IEEE 754)](glosario.md#dinero-enteros) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q          # 4 tests en verde (2 de salud + 2 de catálogo)
.venv/Scripts/python -m uvicorn delivery.main:app
# abrir http://127.0.0.1:8000/platos
```

Respuesta esperada:

```json
[
  {"id": 1, "nombre": "Empanadas (docena)", "precio": 9000},
  {"id": 2, "nombre": "Milanesa con papas", "precio": 12500},
  {"id": 3, "nombre": "Pizza muzzarella", "precio": 11000},
  {"id": 4, "nombre": "Flan casero", "precio": 4500}
]
```

## 6. En términos técnicos (para entrevista)

> "Modelé la persistencia en SQLite sin ORM, con el esquema protegido por restricciones (CHECK, FK, PK compuesta) y una transacción por request mediante inyección de dependencias. Los montos son enteros y los fija el servidor para eliminar el riesgo de manipulación del precio desde el cliente, que es un riesgo de producto que después cubro con pruebas basadas en riesgos. La siembra es idempotente y un test de reinicio lo garantiza."
