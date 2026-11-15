# Paso 1: Esqueleto del proyecto, git y `GET /salud`

**Objetivo:** tener una aplicación mínima que arranca, se puede probar automáticamente y deja todo listo para crecer.

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `.gitignore` | Lista de lo que **no** se sube al repositorio: notas privadas, entorno virtual, bases `*.db`, `.env`, cachés. |
| `sistema-demo/requirements.txt` | Dependencias con versión **exacta** (`fastapi==0.115.5`, `pytest==8.3.3`, …). |
| `sistema-demo/pytest.ini` | Configuración de pytest: dónde están los tests y desde dónde se importa el código. |
| `sistema-demo/delivery/config.py` | `Config`: ruta de la base y **interruptores de defectos sembrados**, que se leen de variables de entorno. |
| `sistema-demo/delivery/main.py` | `crear_app(cfg)`, que fabrica la aplicación, y la ruta `GET /salud`. |
| `sistema-demo/tests/conftest.py` | *Fixtures* `cliente` y `crear_cliente`: cada test recibe una app nueva con su propia base temporal. |
| `sistema-demo/tests/test_salud.py` | Primeros 2 tests: la app responde y muestra qué defectos están encendidos. |

## 2. Por qué lo hicimos así

- **Versiones exactas:** cualquiera que clone el repo instala lo mismo y obtiene los mismos resultados. Si una versión nueva rompe algo, no nos enteramos "de sorpresa".
- **`.gitignore` desde el primer commit:** el repo es público, así que las notas privadas y los datos nunca deben llegar ahí, ni siquiera por error.
- **Configuración por variables de entorno:** el mismo código corre "sano" o "con defectos" sin tocar una línea. Más adelante se van a sembrar 2 defectos a propósito (zona horaria y contrato) para mostrar que las pruebas los detectan.
- **`crear_app(cfg)` en vez de una app global fija:** cada test arma su propia app con su propia base. Así los tests no se pisan entre sí.
- **`/salud` como primera ruta:** es la prueba más simple posible (*smoke test*). Si `/salud` falla, no tiene sentido correr el resto.
- **Test primero y código después:** primero escribimos el test, lo vimos fallar (rojo) y recién ahí escribimos el código hasta que pasó (verde).

## 3. Cómo se conecta con el proyecto

```
variables de entorno ──► Config ──► crear_app(cfg) ──► app.state.cfg
                                         │
                     ┌───────────────────┼─────────────────────┐
                     ▼                   ▼                     ▼
               GET /salud         (Paso 2) base de datos   (Paso 8) defectos
                     │
     usado por: tests, pipeline CI (etapa 2), Playwright/Appium (etapas 3–4)
```

- **Todos** los pasos siguientes agregan rutas dentro de `crear_app`.
- `Config.db_path` lo usa el Paso 2 para saber dónde está la base.
- `defecto_zona_horaria` y `defecto_contrato` se activan en el Paso 8.
- `/salud` le va a servir a los *quality gates* (etapa 2) para verificar que el sistema está arriba antes de correr la suite, y para saber si se está probando la versión "con defectos".
- La fixture `crear_cliente(**flags)` permite escribir tests con defectos encendidos sin cambiar el entorno.

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| Escribir el test antes que el código | 📘 ISTQB | CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD) |
| Prueba rápida de "¿está vivo?" (`/salud`) | 📘 ISTQB | *Smoke test* (glosario ISTQB) |
| Probar temprano, desde el primer commit | 📘 ISTQB | CTFL v4.0 §2.1.5 *Shift-left* |
| Versiones fijas, `.gitignore`, commits identificables | 📘 ISTQB | CTFL v4.0 §5.4 *Gestión de la configuración* |
| Activar defectos a propósito para validar las pruebas | 📘 ISTQB | *Defect seeding / bug seeding* (glosario ISTQB) |
| Código fácil de probar (app por parámetro, base aislada) | 📐 Norma | ISO/IEC 25010 — Mantenibilidad › *Capacidad de ser probado* (testability) |
| Documentación automática de la API en `/docs` | 📐 Norma | OpenAPI Specification 3.1 (FastAPI la genera sola) |
| Respuestas JSON | 📐 Norma | RFC 8259 (formato JSON) |
| Configuración fuera del código (variables de entorno) | ✅ Buena práctica | *The Twelve-Factor App*, factor III "Config" |
| Fábrica de aplicación (`crear_app`) | ✅ Buena práctica | Patrón *Application Factory* |
| Cada test con sus propios datos | ✅ Buena práctica | Principios **FIRST** de los tests unitarios (la "I" es *Independent*) |
| Mensajes de commit `feat(demo): …` | ✅ Buena práctica | *Conventional Commits* 1.0 |
| Entorno virtual (`.venv`) | ✅ Buena práctica | PEP 405 (entornos virtuales de Python) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q          # 2 tests de /salud en verde
.venv/Scripts/python -m uvicorn delivery.main:app
# abrir http://127.0.0.1:8000/docs  → documentación OpenAPI interactiva
```

## 6. En términos técnicos (para entrevista)

> "Armé el esqueleto con una *application factory* configurable por entorno siguiendo *twelve-factor*. Con TDD, el primer test fue un *smoke test* de `/salud`. Cada test corre aislado con su propia base temporal (*fixture* de pytest), y la configuración ya trae interruptores para *bug seeding*, que después uso para demostrar que la suite detecta defectos reales."
