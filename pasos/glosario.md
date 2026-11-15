# Glosario de etiquetas

Qué significa cada etiqueta usada en los pasos. Es la misma información del modal de [`pasos.html`](pasos.html).

- **[Fichas por concepto](#fichas-por-concepto):** cada fila de las tablas de normas de los pasos enlaza acá, a la ficha de su concepto (qué es, referencia exacta y dónde se aplica).
- Las tres categorías en general: [📘 ISTQB CTFL v4.0](#-istqb-ctfl-v40) · [📐 Norma](#-norma) · [✅ Buena práctica](#-buena-práctica)

---

## 📘 ISTQB CTFL v4.0

**ISTQB** (International Software Testing Qualifications Board) publica el **syllabus CTFL v4.0** (Certified Tester Foundation Level, nivel básico, 2023). Es el vocabulario común del testing: cuando una práctica lleva la etiqueta 📘, usa un término o técnica de ese syllabus.

### Cómo está organizado el syllabus

- **Cap. 1 — Fundamentos de las pruebas:** qué es probar, los 7 principios, base de pruebas (*test basis*), oráculo.
- **Cap. 2 — Pruebas en el ciclo de vida:** enfoques *test-first* como TDD, ATDD y BDD (§2.1.3), *shift-left* (§2.1.5), niveles y tipos de prueba, pruebas de confirmación y regresión (§2.2.3).
- **Cap. 3 — Pruebas estáticas:** revisiones y análisis sin ejecutar el software.
- **Cap. 4 — Análisis y diseño de pruebas:** las técnicas, detalladas abajo.
- **Cap. 5 — Gestión de las pruebas:** planificación y criterios de entrada/salida, pruebas basadas en riesgos (§5.2), monitoreo, gestión de la configuración (§5.4), gestión de defectos (§5.5).
- **Cap. 6 — Herramientas de prueba.**

### Técnicas del Capítulo 4

- **Caja negra** (§4.2): miran entradas y salidas, sin conocer el código.
  - Partición de equivalencia (*Equivalence Partitioning*)
  - Análisis de valores límite (*Boundary Value Analysis*), en sus variantes de 2 y de 3 valores
  - Tablas de decisión (*Decision Table Testing*)
  - Transición de estados (*State Transition Testing*)
- **Caja blanca** (§4.3): se basan en la estructura interna del código.
  - Pruebas y cobertura de sentencias (*Statement Testing*)
  - Pruebas y cobertura de ramas (*Branch Testing*), lo que en versiones anteriores se llamaba cobertura de decisión
- **Basadas en la experiencia** (§4.4): aprovechan el conocimiento y la intuición del tester.
  - Predicción de errores (*Error Guessing*)
  - Pruebas exploratorias (*Exploratory Testing*)
  - Pruebas basadas en listas de comprobación (*Checklist-based Testing*)
- **Basadas en la colaboración** (§4.5), novedad de la v4.0: testers, desarrollo y negocio trabajan juntos.
  - Escritura colaborativa de historias de usuario
  - Criterios de aceptación, por ejemplo en formato *Given-When-Then* (estilo Gherkin)
  - Desarrollo guiado por pruebas de aceptación (ATDD)

### Dónde lo aplicamos en este proyecto

- TDD y *shift-left*: pasos 1 a 3, el test se escribe antes que el código.
- *Smoke test*: `GET /salud` (paso 1).
- Gestión de la configuración: versiones fijas y `.gitignore` (paso 1).
- Pruebas basadas en riesgos: el precio lo fija el servidor (paso 2); no se cancela después de pagar (paso 3).
- Transición de estados, con cobertura de transiciones válidas y de todas las transiciones: máquina de estados del pedido (paso 3).
- Prueba de componente (nivel unitario, sin HTTP ni base): paso 3.
- Próximamente: valores límite y particiones (paso 5), defectos sembrados (paso 8).

*Fuente: ISTQB® Certified Tester Foundation Level Syllabus v4.0 (2023). Este proyecto aplica sus prácticas; no implica una certificación.*

---

## 📐 Norma

Una **norma** es un documento formal, publicado por un organismo reconocido, que fija reglas o especificaciones. En software garantiza que los sistemas se construyan, prueben y comuniquen de forma compatible, segura y verificable.

### Organismos y ejemplos

- **ISO/IEC** (Organización Internacional de Normalización y Comisión Electrotécnica Internacional): estándares globales de calidad, procesos y seguridad.
  - **ISO/IEC/IEEE 29119:** procesos, documentación y técnicas de prueba de software. El syllabus ISTQB la toma como referencia, por ejemplo para la documentación de pruebas.
  - **ISO/IEC 25010:** modelo de calidad del producto de software, con características como adecuación funcional, eficiencia de desempeño, compatibilidad, fiabilidad, seguridad y mantenibilidad.
  - **ISO/IEC 9075:** el lenguaje SQL.
- **RFC de la IETF** (Internet Engineering Task Force): documentos técnicos que definen los protocolos de internet.
  - **RFC 9110:** semántica de HTTP (métodos, códigos de estado como 404, 409 y 422).
  - **RFC 8259:** el formato JSON.
  - **RFC 6749:** el marco de autorización OAuth 2.0.
- **OpenAPI Initiative** (bajo la Linux Foundation):
  - **OpenAPI Specification 3.1:** describe una API REST (rutas, parámetros, respuestas) en YAML o JSON, para que humanos y máquinas la entiendan sin ver el código. FastAPI la genera sola en `/docs`.

### Relación con ISTQB

- **Base de pruebas (*test basis*):** una norma o especificación indica *qué* hay que verificar.
- **Oráculo de pruebas:** una RFC o un contrato OpenAPI es la fuente de verdad para decidir si una respuesta es correcta.
- **Pruebas estáticas** (Cap. 3): se puede revisar el código, la arquitectura o el contrato de la API contra la norma antes de ejecutar nada.

### Dónde lo aplicamos en este proyecto

- ISO/IEC 25010: capacidad de ser probado (paso 1), integridad y fiabilidad de los datos (paso 2), corrección y completitud funcional de las transiciones (paso 3).
- UML 2.5 (ISO/IEC 19505): diagrama de máquina de estados del pedido (paso 3).
- RFC 9110: `GET` solo lee (paso 2). Próximamente: códigos 404, 409 (preparado en el paso 3) y 422.
- OpenAPI 3.1: documentación automática en `/docs` (paso 1). En la etapa 2, contrato JSON Schema.
- ISO/IEC/IEEE 29119-3: plan, casos e informes de incidentes (etapa 2).

---

## ✅ Buena práctica

Una **buena práctica** es una forma de trabajar que la industria adoptó porque probó que reduce errores y facilita el mantenimiento. A diferencia de una norma, **nadie la "publica" como obligatoria**: la sostienen comunidades, guías abiertas o autores de referencia.

### Norma vs. buena práctica

| | 📐 Norma | ✅ Buena práctica |
|---|---|---|
| Quién la define | Organismo formal (ISO, IETF…) | Comunidad, guía abierta, autor reconocido |
| Cómo cambia | Versiones oficiales y procesos de revisión | Evoluciona con el uso |
| Ejemplo | RFC 9110 dice qué significa un 409 | OWASP recomienda consultas parametrizadas |

### Fuentes que usamos

- **The Twelve-Factor App:** 12 reglas para aplicaciones de servicio (por ejemplo, la configuración va en variables de entorno).
- **OWASP Cheat Sheets:** guías abiertas de seguridad (por ejemplo, prevenir la inyección SQL).
- **Conventional Commits 1.0:** formato de mensajes de commit (`feat(…)`, `docs(…)`).
- **PEP** (Python Enhancement Proposals): convenciones de Python, como PEP 8 (estilo) y PEP 405 (entornos virtuales).
- **Patrones de diseño:** *Application Factory*, *Unit of Work*, inyección de dependencias.
- **Principios FIRST** de los tests unitarios: *Fast, Independent, Repeatable, Self-validating, Timely*.

### Relación con ISTQB

El syllabus no impone herramientas ni patrones de código, pero muchas buenas prácticas sostienen sus objetivos: tests independientes y repetibles hacen confiable la regresión (§2.2.3), y versionar bien es parte de la gestión de la configuración (§5.4).

### Dónde lo aplicamos en este proyecto

- Paso 1: Twelve-Factor (configuración), Application Factory, FIRST, Conventional Commits, PEP 405.
- Paso 2: OWASP (SQL parametrizado), 3FN, Unit of Work, inyección de dependencias, siembra idempotente, dinero en enteros.
- Paso 3: fuente única de verdad y diseño *table-driven*, tests parametrizados, *fail fast*, prueba de mutación manual.

---

## Fichas por concepto

> Generado desde [`terminos.json`](terminos.json) con `python pasos/generar_glosario.py`. No editar a mano entre los marcadores.

<!-- TERMINOS:INICIO -->
### 📘 ISTQB

<a id="tdd"></a>

#### TDD: el test antes que el código

📘 ISTQB · **Referencia:** CTFL v4.0 §2.1.3 Enfoques test-first

*Test-Driven Development*: primero se escribe un test que falla (rojo), después el código mínimo para que pase (verde) y al final se ordena (*refactor*). El test funciona como especificación y como red de seguridad.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): El primer test fue `GET /salud`; falló porque no existía `delivery.main`, y recién ahí se escribió la app.
- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Los tests del catálogo fallaron con 404 en `/platos` antes de crear la base y la ruta.
- [Paso 3](paso-03-maquina-de-estados.md): `test_estados.py` falló porque no existía `delivery.estados`; después se escribió la máquina de estados.

<a id="smoke-test"></a>

#### Smoke test (prueba de humo)

📘 ISTQB · **Referencia:** Glosario ISTQB: smoke test

Prueba mínima y rápida que confirma que el sistema arranca y responde. Si falla, no tiene sentido correr el resto de las pruebas.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): `GET /salud` responde `{"estado": "ok"}`: si eso falla, la app ni siquiera levantó.

<a id="shift-left"></a>

#### Shift-left: probar temprano

📘 ISTQB · **Referencia:** CTFL v4.0 §2.1.5 Shift-left

Mover las pruebas hacia el inicio del desarrollo. Un defecto encontrado temprano es más barato de corregir que uno encontrado al final.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): Desde el primer commit hay tests automáticos; ninguna pieza se suma sin su prueba.

<a id="gestion-configuracion"></a>

#### Gestión de la configuración

📘 ISTQB · **Referencia:** CTFL v4.0 §5.4 Gestión de la configuración

Identificar y controlar las versiones de todo lo que forma el sistema (código, dependencias, tests) para poder reproducir exactamente qué se probó.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): Versiones exactas en `requirements.txt`, `.gitignore` para no versionar basura y commits con mensajes identificables.

<a id="defect-seeding"></a>

#### Defect seeding (siembra de defectos)

📘 ISTQB · **Referencia:** Glosario ISTQB: fault seeding / defect seeding

Introducir defectos conocidos a propósito para medir si las pruebas los detectan. Sirve para evaluar la calidad de la propia suite.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): `Config` trae los interruptores `defecto_zona_horaria` y `defecto_contrato`, y `/salud` informa si están encendidos. Se usan en el Paso 8.

<a id="riesgos"></a>

#### Pruebas basadas en riesgos

📘 ISTQB · **Referencia:** CTFL v4.0 §5.2 Gestión de riesgos

Priorizar qué probar según la probabilidad y el impacto de que algo salga mal. Los riesgos de producto más graves se mitigan primero.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Riesgo: cobro incorrecto. Mitigación: el precio lo fija el servidor y se guarda en enteros.
- [Paso 3](paso-03-maquina-de-estados.md): Riesgo: cancelar con el pago hecho y el delivery asignado. Mitigación: cancelar solo es posible en los 4 estados previos al pago.

<a id="regresion"></a>

#### Pruebas de regresión

📘 ISTQB · **Referencia:** CTFL v4.0 §2.2.3 Pruebas de confirmación y de regresión

Volver a ejecutar pruebas para confirmar que algo que funcionaba sigue funcionando después de un cambio o, en este caso, después de un reinicio.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): `test_siembra_no_duplica_al_reiniciar` arranca la app dos veces sobre la misma base y verifica que sigan siendo 4 platos.

<a id="transicion-estados"></a>

#### Prueba de transición de estados

📘 ISTQB · **Referencia:** CTFL v4.0 §4.2.4 Prueba de transición de estados

Técnica de caja negra: se modela el sistema como estados y transiciones (diagrama o tabla) y se diseñan casos que recorren las transiciones válidas e intentan las inválidas.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Diagrama de 13 estados y tabla `TRANSICIONES`; 18 casos válidos y 6 inválidos con nombre (salto, retroceso, cancelar después de pagar…).

<a id="cobertura-transiciones"></a>

#### Criterios de cobertura de estados

📘 ISTQB · **Referencia:** CTFL v4.0 §4.2.4 Criterios de cobertura

El syllabus define tres niveles: todos los estados, todas las transiciones válidas (cobertura 0-switch) y todas las transiciones, incluidas las inválidas.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Se logró el nivel más alto: 18/18 transiciones válidas y los 169 pares de la tabla 13 × 13.

<a id="prueba-componente"></a>

#### Prueba de componente (unitaria)

📘 ISTQB · **Referencia:** CTFL v4.0 §2.2.1 Niveles de prueba

Primer nivel de prueba: se prueba una pieza aislada, sin sus dependencias externas (red, base de datos).

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): `estados.py` se prueba sin HTTP ni SQLite; la cobertura fina queda en este nivel, el más barato.

### 📐 Normas

<a id="capacidad-prueba"></a>

#### ISO/IEC 25010: capacidad de ser probado

📐 Norma · **Referencia:** ISO/IEC 25010 — Mantenibilidad › Capacidad de ser probado

Característica de calidad: qué tan fácil es establecer criterios de prueba y ejecutarlos sobre el sistema.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): `crear_app(cfg)` recibe la configuración por parámetro, así cada test arma su app con una base temporal propia.

<a id="openapi"></a>

#### OpenAPI Specification 3.1

📐 Norma · **Referencia:** OpenAPI Initiative — OAS 3.1

Formato estándar para describir una API REST (rutas, parámetros, respuestas) que entienden humanos y herramientas.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): FastAPI genera la especificación sola y la muestra en `/docs`. En la etapa 2 se usa como contrato.

<a id="json"></a>

#### RFC 8259: formato JSON

📐 Norma · **Referencia:** IETF RFC 8259

Define la sintaxis de JSON, el formato de intercambio de datos de la API.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): Todas las respuestas, empezando por `/salud`, son JSON válido.

<a id="integridad"></a>

#### ISO/IEC 25010: integridad

📐 Norma · **Referencia:** ISO/IEC 25010 — Seguridad › Integridad

El sistema impide modificaciones indebidas de los datos.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Restricciones en la base: `CHECK (precio > 0)`, `FOREIGN KEY` y `PRIMARY KEY (pedido_id, plato_id)`.

<a id="recuperabilidad"></a>

#### ISO/IEC 25010: capacidad de recuperación

📐 Norma · **Referencia:** ISO/IEC 25010 — Fiabilidad › Capacidad de recuperación

Ante una interrupción, el sistema recupera los datos y su estado.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): La base es un archivo SQLite: al reiniciar el servidor los datos siguen ahí.

<a id="sql"></a>

#### ISO/IEC 9075: lenguaje SQL

📐 Norma · **Referencia:** ISO/IEC 9075

Norma que define el lenguaje SQL. Cada motor implementa un subconjunto con extensiones propias.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Las 5 tablas se crean con SQL estándar; SQLite implementa un subconjunto.

<a id="metodos-seguros"></a>

#### RFC 9110: métodos HTTP seguros

📐 Norma · **Referencia:** IETF RFC 9110 §9.2.1 Safe Methods

Un método *seguro* (como `GET`) solo lee: no cambia nada en el servidor.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): `GET /platos` solo consulta el menú; nunca modifica la base.

<a id="adecuacion-funcional"></a>

#### ISO/IEC 25010: adecuación funcional

📐 Norma · **Referencia:** ISO/IEC 25010 — Adecuación funcional › Corrección y Completitud

El sistema hace todo lo que tiene que hacer (completitud) y lo hace bien (corrección).

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Las 18 transiciones permitidas están todas (completitud) y ninguna de más (corrección), verificado por test.

<a id="uml-estados"></a>

#### UML 2.5: máquinas de estados

📐 Norma · **Referencia:** OMG UML 2.5 (también ISO/IEC 19505) — State Machines

Notación estándar para dibujar estados, transiciones y estados finales.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): El diagrama del pedido sigue esa notación: estados, flechas y dos estados finales (`CERRADO`, `CANCELADO`).

<a id="http-409"></a>

#### RFC 9110: 409 Conflict

📐 Norma · **Referencia:** IETF RFC 9110 §15.5.10 409 Conflict

El pedido no se puede completar porque choca con el estado actual del recurso.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): `TransicionInvalida` lleva el estado actual y el destino; en el Paso 4 se traduce en un 409 con esos datos.

### ✅ Buenas prácticas

<a id="twelve-factor"></a>

#### Twelve-Factor App, factor III: configuración

✅ Buena práctica · **Referencia:** The Twelve-Factor App — III. Config

La configuración que cambia entre entornos (rutas, interruptores) va en variables de entorno, no escrita en el código.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): `Config` lee la ruta de la base y los defectos desde variables de entorno.

<a id="application-factory"></a>

#### Patrón Application Factory

✅ Buena práctica · **Referencia:** Patrón de diseño Application Factory

En vez de una app global, una función que la construye a pedido con la configuración que se le pase.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): `crear_app(cfg)` permite tener varias apps independientes, por ejemplo una por test.

<a id="first"></a>

#### Principios FIRST de los tests

✅ Buena práctica · **Referencia:** FIRST: Fast, Independent, Repeatable, Self-validating, Timely

Buenos tests unitarios: rápidos, independientes entre sí, repetibles, que se validan solos (pasa o falla) y escritos a tiempo.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): Cada test usa su propia base temporal (`tmp_path`): ninguno depende de otro.
- [Paso 3](paso-03-maquina-de-estados.md): Los 29 tests de estados corren en milisegundos, sin HTTP ni base.

<a id="conventional-commits"></a>

#### Conventional Commits 1.0

✅ Buena práctica · **Referencia:** conventionalcommits.org 1.0

Formato de mensajes de commit `tipo(alcance): descripción` que hace legible el historial.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): Mensajes como `feat(demo): esqueleto FastAPI con /salud` o `docs(pasos): …`.

<a id="pep405"></a>

#### PEP 405: entornos virtuales

✅ Buena práctica · **Referencia:** Python PEP 405

Cada proyecto tiene sus propias dependencias aisladas, sin mezclarse con las del sistema.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): `sistema-demo/.venv` con las versiones fijas de `requirements.txt`.

<a id="owasp-sql"></a>

#### OWASP: prevención de inyección SQL

✅ Buena práctica · **Referencia:** OWASP SQL Injection Prevention Cheat Sheet

Nunca armar SQL pegando texto del usuario; usar consultas parametrizadas para que los datos no se interpreten como código.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Todas las consultas usan parámetros `?`.

<a id="3fn"></a>

#### Normalización relacional (3FN)

✅ Buena práctica · **Referencia:** Tercera forma normal

Organizar las tablas para que cada dato viva en un solo lugar y no se repita.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Los items de un pedido van en `pedido_items`, separados de `pedidos` y de `platos`.

<a id="unit-of-work"></a>

#### Patrón Unit of Work

✅ Buena práctica · **Referencia:** Patrón Unit of Work (Fowler, PoEAA)

Todos los cambios de una operación se guardan juntos o no se guarda ninguno.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): `obtener_ctx` abre una conexión por request: *commit* si todo sale bien, *rollback* si algo falla.

<a id="inyeccion-dependencias"></a>

#### Inyección de dependencias

✅ Buena práctica · **Referencia:** Patrón Dependency Injection

Una función recibe lo que necesita desde afuera en vez de crearlo ella misma. Facilita probarla y reemplazar piezas.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Las rutas reciben el `Ctx` (conexión + configuración) mediante `Depends(obtener_ctx)` de FastAPI.

<a id="idempotencia"></a>

#### Inicialización idempotente

✅ Buena práctica · **Referencia:** Idempotencia

Una operación idempotente puede repetirse muchas veces con el mismo resultado que si se hiciera una sola vez.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): La siembra solo carga platos si la tabla está vacía: diez reinicios siguen dando 4 platos.

<a id="dinero-enteros"></a>

#### Dinero en unidades enteras

✅ Buena práctica · **Referencia:** Evitar coma flotante binaria (IEEE 754) con dinero

Los `float` tienen errores de redondeo (`0.1 + 0.2 = 0.30000000000000004`). Con dinero se usan enteros.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Los precios son `int` en pesos y un test verifica el tipo.

<a id="table-driven"></a>

#### Fuente única de verdad, diseño table-driven

✅ Buena práctica · **Referencia:** Single source of truth; table-driven design

Las reglas se escriben como datos (una tabla) en un solo lugar, no repartidas en `if` por todo el código.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): `TRANSICIONES` es un diccionario; toda mutación de estado pasará por `validar_transicion`.

<a id="parametrizados"></a>

#### Tests parametrizados

✅ Buena práctica · **Referencia:** pytest.mark.parametrize

Un mismo test se ejecuta con muchos datos, y cada combinación aparece como un caso separado en el reporte.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Un test recorre las 18 válidas y otro las 6 inválidas, cada una con su nombre (`salto`, `retroceso`…).

<a id="fail-fast"></a>

#### Fail fast con errores descriptivos

✅ Buena práctica · **Referencia:** Fail fast

Ante una operación inválida, fallar enseguida con un error que diga qué pasó, en vez de seguir con datos corruptos.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): `TransicionInvalida(actual, destino)`: el error dice exactamente qué cambio se intentó.

<a id="mutacion"></a>

#### Prueba de mutación

✅ Buena práctica · **Referencia:** Mutation testing

Se cambia el código a propósito (una *mutación*) y se verifica que algún test falle. Si ninguno falla, la suite tiene un hueco.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Se agregó la flecha prohibida `EN_PUERTA → CERRADO`: 2 tests fallaron. Después se revirtió.

<!-- TERMINOS:FIN -->
