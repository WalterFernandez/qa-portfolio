# DEF-003: Error 500 al azar cuando llegan requests en paralelo

Informe de incidente con los campos de ISO/IEC/IEEE 29119-3 (*Incident report*).

| Campo | Valor |
|---|---|
| **Identificador** | DEF-003 |
| **Tipo** | Defecto **real**, no sembrado. Lo encontró el panel central (Paso 10) durante la verificación manual. |
| **Fecha** | 2026-11-15 |
| **Ítem de prueba** | Sistema demo, cualquier ruta que use la base (`/pedidos`, `/mensajes`, ...), commit `a6ea2b7` |
| **Entorno** | Windows 10, Python 3.12, FastAPI 0.115.5, uvicorn 0.32.1, SQLite; Chrome de escritorio |
| **Severidad** | **Mayor.** El request falla con `500` y la pantalla muestra "Algo salió mal". No se corrompen datos (la transacción hace rollback), pero la falla es intermitente y depende de la carga. |
| **Prioridad** | **Alta.** Cualquier pantalla que haga dos pedidos a la vez la dispara, y en producción habría varios usuarios. |
| **Estado** | **Cerrado.** Corregido en el commit `84b077f` con test de regresión. |

## Cómo se encontró

El panel central pide `/pedidos` y `/mensajes` **en paralelo** (`Promise.all`) cada 3 segundos. Al abrirlo en Chrome apareció el banner `Algo salió mal. [error_500]` sin una acción del usuario. El log de uvicorn mostraba:

```
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
```

Las páginas del cliente y del delivery no lo mostraban porque hacen un request por vez. Los 195 tests de entonces tampoco, porque `TestClient` manda los requests uno detrás del otro.

## Pasos para reproducir

1. Levantar el sistema (cualquier base) en el commit `a6ea2b7`:
   ```bash
   cd sistema-demo
   DEMO_DB_PATH=data/def-003.db .venv/Scripts/python -m uvicorn delivery.main:app --port 8765
   ```
2. Mandar ráfagas de requests en paralelo (Git Bash):
   ```bash
   B=http://127.0.0.1:8765
   for r in 1 2 3; do
     for i in $(seq 1 10); do
       curl -s -o /dev/null -w "%{http_code} " $B/mensajes &
       curl -s -o /dev/null -w "%{http_code} " $B/pedidos &
     done; wait; echo
   done
   ```

## Resultado esperado

Todas las respuestas `200`.

## Resultado obtenido

`500` al azar. Medido contra uvicorn:

| Cliente | Requests | `500` sin el arreglo | `500` con el arreglo |
|---|---:|---:|---:|
| `curl` en paralelo (ráfaga de arriba) | 60 | 4 | 0 de 120 |
| Python, 20 hilos, 10 ráfagas de 20 | 200 | **194** | **0** |

Con más concurrencia la falla pasa de ocasional a casi segura.

## Evidencia

- Captura del panel con el banner `[error_500]`: [`evidencia/panel-zona-horaria-y-500.jpg`](evidencia/panel-zona-horaria-y-500.jpg) (la misma captura muestra el DEF-001).
- Test de regresión: `tests/test_concurrencia.py::test_la_conexion_se_puede_usar_desde_otro_hilo`. Falló antes del arreglo (rojo) y pasa después (verde).

## Causa raíz

- `delivery/db.py` `obtener_ctx` es una **dependencia generadora sincrónica** de FastAPI: abre la conexión, la entrega con `yield` y al final hace commit y la cierra.
- FastAPI corre esa dependencia en un hilo del *threadpool* y el endpoint (también sincrónico) en **otro** hilo del mismo pool.
- `sqlite3.connect` trae `check_same_thread=True` por defecto: si la conexión se usa desde un hilo distinto al que la creó, lanza `ProgrammingError`.
- Con un solo request a la vez, el pool suele reusar el mismo hilo y no falla. Con varios en paralelo, los hilos se reparten y falla.

## Corrección aplicada

`conectar` usa `sqlite3.connect(db_path, check_same_thread=False)`, con un comentario que explica por qué.

Es seguro porque **cada conexión pertenece a un solo request** y se usa desde un hilo por vez, nunca desde dos al mismo tiempo. La concurrencia **entre** requests ya la resuelven SQLite y los `UPDATE` condicionales del pago y la cancelación (Paso 6, `test_concurrencia.py`).

Alternativas descartadas: volver `async` las rutas (cambia todo el código para un problema de configuración) o un *pool* de conexiones (innecesario en un sistema de una sola máquina).

## Lecciones

- Las pruebas que mandan un request por vez no ven defectos de concurrencia: hace falta al menos una prueba con requests **en paralelo contra el servidor real**. Queda como caso para la etapa 2 (API) y la etapa 5 (performance).
- Una pantalla nueva con un patrón de uso nuevo (pedidos en paralelo) es también una prueba: encontró un defecto que la suite no veía.

## Referencias

- ISTQB CTFL v4.0: gestión de defectos (informe, causa raíz, regresión); pruebas de confirmación y de regresión.
- ISO/IEC 25010: Confiabilidad › Madurez (fallas bajo uso normal).
- Documentación de Python, `sqlite3.connect(check_same_thread=...)`.
