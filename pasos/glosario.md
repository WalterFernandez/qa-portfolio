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

- TDD y *shift-left*: pasos 1 a 8, el test se escribe antes que el código.
- *Smoke test*: `GET /salud` (paso 1).
- Gestión de la configuración: versiones fijas y `.gitignore` (paso 1).
- Pruebas basadas en riesgos: el precio lo fija el servidor (paso 2); no se cancela después de pagar (paso 3); el cliente no puede mandar su propio total (paso 5); un doble clic en “Pagar” no cobra dos veces (paso 6); el delivery no cierra sin la confirmación del cliente y no se cancela con el pago hecho, ni siquiera a la vez (paso 7); los defectos sembrados se eligieron por probabilidad e impacto: varias zonas horarias y clientes que esperan números (paso 8).
- Transición de estados, con cobertura de transiciones válidas y de todas las transiciones: máquina de estados del pedido (paso 3); el alta recorre `INICIADO → LINK_ENVIADO` por `_avanzar` (paso 4); la carga recorre `LINK_ENVIADO → DATOS_CARGADOS → COTIZADO` y cargar dos veces da 409 (paso 5); el pago recorre `COTIZADO → PAGADO → ASIGNADO` y firmar o pagar fuera de `COTIZADO` da 409 (paso 6); el recorrido `ASIGNADO → … → CERRADO` y las 6 transiciones del cierre en los dos órdenes (paso 7).
- Prueba de componente (nivel unitario, sin HTTP ni base): paso 3.
- Prueba de integración de componentes (ruta, servicio, SQLite y bandeja juntos): pasos 4 a 6; los 13 pasos de punta a punta (paso 7).
- Partición de equivalencia y valores límite: el teléfono (paso 4); cantidad, items, dirección, coordenadas y los tramos de la demora (paso 5); formato y largo de la firma (paso 6); quién cancela y un estado por tramo pagado (paso 7).
- Tabla de decisión: estado × firma para el pago (paso 6); estado de partida × quién cancela (paso 7).
- Defectos sembrados (*defect seeding*): zona horaria y contrato, apagados por defecto y activables por entorno; cada test con el defecto prendido tiene su par apagado como oráculo, y los 170 tests anteriores sirven de regresión (paso 8).

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

- ISO/IEC 25010: capacidad de ser probado (paso 1), integridad y fiabilidad de los datos (paso 2), corrección y completitud funcional de las transiciones (paso 3), capacidad de recuperación tras un reinicio (paso 4), integridad: un rechazo no deja datos a medias (pasos 5 a 7), completitud: los 13 pasos del negocio (paso 7), interoperabilidad: el defecto de contrato manda texto donde se espera un número (paso 8).
- UML 2.5 (ISO/IEC 19505): diagrama de máquina de estados del pedido (paso 3).
- RFC 9110: `GET` solo lee (paso 2); códigos 404, 409 y 422 (paso 4); 409 al cargar dos veces y 422 con `plato_repetido` y `plato_inexistente` (paso 5); 409 `firma_requerida` y `POST /pago` idempotente aunque la norma no lo exija (paso 6); 404 en las 9 rutas de un pedido, 409 `no_cancelable` y 422 con `por` inválido (paso 7).
- ISO 8601 / RFC 3339: marcas de tiempo en UTC con `Z` (paso 4); el defecto de zona horaria las guarda en hora local sin offset y la línea de tiempo se desordena (paso 8).
- ITU-T E.164: máximo de 15 dígitos en el teléfono (paso 4).
- ISO 6709: latitud en [-90, 90] y longitud en [-180, 180] (paso 5).
- RFC 2397 y RFC 4648: la firma como *data URL* PNG en base64 (paso 6).
- OpenAPI 3.1: documentación automática en `/docs` (paso 1); `precio` y `total` son enteros en el contrato y el defecto de contrato lo rompe (paso 8). En la etapa 2, contrato JSON Schema.
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
- Paso 4: validación de entrada por lista blanca (OWASP), un solo camino para cambiar el estado, doble de prueba (*fake*) para el WhatsApp, reloj reemplazable, prueba de mutación (3 de 3).
- Paso 5: el total lo calcula el servidor con el catálogo (fuente única), lista blanca contra `total`, dinero en enteros, validar todo antes de escribir (*fail fast*) en una sola transacción, prueba de mutación (6 de 6, con un caso sumado por una sobreviviente).
- Paso 6: pago idempotente, firma por lista blanca, migración de esquema aditiva, pago y asignación en una sola transacción, primero el estado y después la firma (*fail fast*), control de concurrencia optimista contra la carrera del pago, prueba de mutación (12 de 12 y 7 de 7).
- Paso 7: concurrencia optimista en las confirmaciones (reintento único) y en cancelar contra pagar, retiro y aviso en una sola transacción, `no_cancelable` con un mensaje por caso (*fail fast*), tests parametrizados por regla y por ruta, prueba de mutación (16 de 16).
- Paso 8: defectos activables por variables de entorno (Twelve-Factor), dinero en enteros en la base aunque la salida sea texto, reloj fijo para un orden repetible, tests parametrizados para el formato de pesos, prueba de mutación (13 de 13).

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
- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Los 19 tests nuevos fallaron con 404 (no existían las rutas) e `ImportError` (no existía `pedidos.py`) antes de escribir el código.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): 41 tests de cotización escritos antes que `cargar_datos`: fallaron con 405 porque la ruta `PUT` no existía.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Los 32 tests de firma y pago fallaron con 404 (no existían las rutas) antes de escribir `firmar` y `pagar`.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Los 41 tests nuevos (entrega, cancelación, rutas 404 y carreras) fallaron con 404 porque las rutas no existían, antes de escribir `marcar_retirado`, `_confirmar` y `cancelar`.
- [Paso 8](paso-08-defectos-sembrados.md): Los 18 tests de `test_defectos.py` se escribieron primero: 12 fallaron (rojo) y los 6 de control, con el defecto apagado, ya pasaban.

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
- [Paso 8](paso-08-defectos-sembrados.md): Se encienden los dos: `DEMO_DEFECTO_ZONA_HORARIA` (cada actor guarda su hora local sin offset y la línea de tiempo se desordena) y `DEMO_DEFECTO_CONTRATO` (los montos salen como texto `"$ 9.000"`). Apagados por defecto; son el blanco de las pruebas de las etapas 2 a 4.

<a id="riesgos"></a>

#### Pruebas basadas en riesgos

📘 ISTQB · **Referencia:** CTFL v4.0 §5.2 Gestión de riesgos

Priorizar qué probar según la probabilidad y el impacto de que algo salga mal. Los riesgos de producto más graves se mitigan primero.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Riesgo: cobro incorrecto. Mitigación: el precio lo fija el servidor y se guarda en enteros.
- [Paso 3](paso-03-maquina-de-estados.md): Riesgo: cancelar con el pago hecho y el delivery asignado. Mitigación: cancelar solo es posible en los 4 estados previos al pago.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): Riesgo: que el cliente fije su propio precio. Mitigación: el body no tiene `total` (mandarlo da 422) y el total sale de los precios del catálogo.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Riesgo: cobrar dos veces por un doble clic en “Pagar”. Mitigación: el pago es idempotente, también con dos pagos simultáneos. Riesgo conocido y aceptado: sin autenticación, quien conozca el id puede firmar o pagar (IDOR); queda para las pruebas de seguridad de una etapa posterior.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Riesgo: que el delivery cierre un pedido que el cliente no recibió. Mitigación: el cierre exige las dos confirmaciones. Riesgo: cancelar con el pago hecho, también si cancelar y pagar llegan a la vez. Mitigación: `no_cancelable`, probado en los dos órdenes.
- [Paso 8](paso-08-defectos-sembrados.md): Los defectos se eligieron por probabilidad e impacto: usuarios en tres zonas horarias (el orden de los eventos engaña: `PAGADO` antes que `COTIZADO`) y clientes que esperan un número (el total no se puede sumar).

<a id="regresion"></a>

#### Pruebas de regresión

📘 ISTQB · **Referencia:** CTFL v4.0 §2.2.3 Pruebas de confirmación y de regresión

Volver a ejecutar pruebas para confirmar que algo que funcionaba sigue funcionando después de un cambio o, en este caso, después de un reinicio.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): `test_siembra_no_duplica_al_reiniciar` arranca la app dos veces sobre la misma base y verifica que sigan siendo 4 platos.
- [Paso 8](paso-08-defectos-sembrados.md): Con los defectos apagados, los 170 tests de los pasos 1 a 7 siguen en verde sin tocarlos: cada defecto queda aislado detrás de su interruptor.

<a id="transicion-estados"></a>

#### Prueba de transición de estados

📘 ISTQB · **Referencia:** CTFL v4.0 §4.2.4 Prueba de transición de estados

Técnica de caja negra: se modela el sistema como estados y transiciones (diagrama o tabla) y se diseñan casos que recorren las transiciones válidas e intentan las inválidas.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Diagrama de 13 estados y tabla `TRANSICIONES`; 18 casos válidos y 6 inválidos con nombre (salto, retroceso, cancelar después de pagar…).
- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Al crear el pedido se recorre `INICIADO → LINK_ENVIADO` por `_avanzar`; un salto a `PAGADO` se rechaza y no deja evento.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): La carga recorre `LINK_ENVIADO → DATOS_CARGADOS → COTIZADO`; cargar dos veces choca con `COTIZADO` y da 409.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): El pago recorre `COTIZADO → PAGADO → ASIGNADO`; firmar o pagar fuera de `COTIZADO` da 409, y pagar un pedido `CANCELADO` también.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): El recorrido `ASIGNADO → RETIRADO → EN_CAMINO → EN_PUERTA → RECIBIDO/ENTREGADO → CERRADO`; retirar antes de pagar, llegar antes de retirar, confirmar antes de llegar o confirmar dos veces dan 409.

<a id="cobertura-transiciones"></a>

#### Criterios de cobertura de estados

📘 ISTQB · **Referencia:** CTFL v4.0 §4.2.4 Criterios de cobertura

El syllabus define tres niveles: todos los estados, todas las transiciones válidas (cobertura 0-switch) y todas las transiciones, incluidas las inválidas.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Se logró el nivel más alto: 18/18 transiciones válidas y los 169 pares de la tabla 13 × 13.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Las 6 transiciones del cierre (`EN_PUERTA → RECIBIDO/ENTREGADO`, `RECIBIDO ↔ ENTREGADO` y las dos hacia `CERRADO`) se recorren probando las confirmaciones en los dos órdenes.

<a id="prueba-componente"></a>

#### Prueba de componente (unitaria)

📘 ISTQB · **Referencia:** CTFL v4.0 §2.2.1 Niveles de prueba

Primer nivel de prueba: se prueba una pieza aislada, sin sus dependencias externas (red, base de datos).

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): `estados.py` se prueba sin HTTP ni SQLite; la cobertura fina queda en este nivel, el más barato.

<a id="particiones"></a>

#### Partición de equivalencia

📘 ISTQB · **Referencia:** CTFL v4.0 §4.2.1 Partición de equivalencia

Técnica de caja negra: se dividen los datos en grupos que el sistema debería tratar igual, y se prueba al menos un valor de cada grupo, válido o inválido.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Teléfono: un grupo válido (8 a 15 dígitos, con `+` opcional) y grupos inválidos (vacío, con letras, muy corto, muy largo).
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): Cantidad (menor a 1, de 1 a 10, mayor a 10), cantidad de items (0, 1 a 4, más de 4), dirección (vacía, con espacios en los extremos, válida, demasiado larga) y la demora en tres tramos: hasta 2 unidades, de 3 a 7 y de 8 en adelante.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): La firma en clases: PNG válido, otro formato (`jpeg`), sin prefijo, prefijo sin datos y caracteres fuera de base64.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): `por` en clases: `cliente` y `servicio` válidos; `delivery`, mayúscula, vacío, ausente y con campos de más → 422. Los estados pagados se cubren con un representante por tramo (`EN_CAMINO`, `EN_PUERTA`, `RECIBIDO`).

<a id="valores-limite"></a>

#### Análisis de valores límite

📘 ISTQB · **Referencia:** CTFL v4.0 §4.2.2 Análisis de valores límite

Los defectos se concentran en los bordes de cada partición. Con 2 valores por borde se prueba el límite y su vecino del lado de afuera.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Bordes del teléfono: 8 y 15 dígitos dan 201; 7 y 16 dan 422.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): Cantidad 0, 1, 10 y 11; items 0, 1, 4 y 5; dirección de 1, 200 y 201 caracteres; latitud ±90 y ±90,1; longitud ±180 y ±180,1; demora en 2|3 unidades (empieza el recargo) y 7|8 (llega al tope de 60).
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Largo de la firma: 200 000 caracteres pasa y 200 001 da 422.

<a id="integracion-componentes"></a>

#### Prueba de integración de componentes

📘 ISTQB · **Referencia:** CTFL v4.0 §2.2.1 Niveles de prueba

Segundo nivel de prueba: se verifica que varias piezas funcionen juntas a través de sus interfaces.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Con `TestClient` cada test cruza ruta → servicio → SQLite → bandeja de mensajes, sin levantar un servidor real.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): `PUT /pedidos/{id}` prueba juntos el modelo Pydantic, el servicio, el catálogo, SQLite y la bandeja de mensajes.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Ruta, servicio, SQLite y bandeja juntos: el pago deja dos eventos y el WhatsApp al delivery en la misma llamada.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): `test_flujo_completo_los_13_pasos`: desde `POST /pedidos` hasta `CERRADO` por la API, con los 12 eventos y sus actores y los 4 WhatsApp en la bandeja.

<a id="tabla-decision"></a>

#### Prueba de tabla de decisión

📘 ISTQB · **Referencia:** CTFL v4.0 §4.2.3 Prueba de tabla de decisión

Se listan las condiciones (por ejemplo, estado y firma) y para cada combinación se fija el resultado esperado. Cada combinación es al menos un caso de prueba. Sirve cuando la respuesta depende de varias condiciones a la vez.

**En este proyecto:**

- [Paso 6](paso-06-firma-pago-y-asignacion.md): El pago: estado (antes de cotizar, `COTIZADO`, pagado o posterior, `CANCELADO`) × firma (sí o no) → 409 `transicion_invalida`, 409 `firma_requerida`, 200 con asignación o 200 sin cambios.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): La cancelación: estado de partida (antes del pago, pagado, final) × quién cancela (cliente o servicio) → 200 `CANCELADO` o 409 `no_cancelable` con un mensaje para cada caso. Cinco reglas, R1 a R5, con su nombre.

<a id="oraculo"></a>

#### Oráculo de prueba

📘 ISTQB · **Referencia:** Glosario ISTQB: test oracle

La fuente que dice cuál es el resultado correcto de una prueba: una especificación, una norma, otro sistema o una versión anterior. Sin oráculo, un test no puede decidir si pasó.

**En este proyecto:**

- [Paso 8](paso-08-defectos-sembrados.md): Cada test con el defecto prendido tiene su par con el defecto apagado. El orden de eventos de la tabla del spec y `test_flujo_completo_los_13_pasos` (Paso 7) dicen cuál es el resultado correcto.

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
- [Paso 8](paso-08-defectos-sembrados.md): El contrato dice que `precio`, `precio_unitario`, `subtotal` y `total` son enteros; el defecto de contrato manda texto. En la etapa 2, la validación con JSON Schema lo tiene que detectar.

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
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): Un 422 o un 409 no dejan nada a medias: se valida todo antes de escribir, y la PK `(pedido_id, plato_id)` nunca llega a dar un error 500.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Un pago rechazado no deja eventos ni mensajes, y una firma rechazada no marca el pedido como firmado.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Una cancelación rechazada deja el pedido exactamente igual que antes (el test compara el JSON completo), y una confirmación rechazada no suma eventos.

<a id="recuperabilidad"></a>

#### ISO/IEC 25010: capacidad de recuperación

📐 Norma · **Referencia:** ISO/IEC 25010 — Fiabilidad › Capacidad de recuperación

Ante una interrupción, el sistema recupera los datos y su estado.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): La base es un archivo SQLite: al reiniciar el servidor los datos siguen ahí.
- [Paso 4](paso-04-crear-pedido-y-mensajes.md): `test_pedido_sobrevive_reinicio`: se crea el pedido con una app y se lee con otra sobre el mismo archivo.

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
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Completitud: los 13 pasos del negocio quedan implementados y un test los recorre todos, de `INICIADO` a `CERRADO`.

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
- [Paso 4](paso-04-crear-pedido-y-mensajes.md): El manejador de `main.py` traduce `TransicionInvalida` en 409 con `estado_actual` y `destino`; un test lo verifica.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): Cargar datos de un pedido ya cotizado: `estado_actual` `COTIZADO`, `destino` `DATOS_CARGADOS`.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Pagar sin firma → 409 `firma_requerida`; firmar o pagar fuera de `COTIZADO` → 409 `transicion_invalida`.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Cancelar un pedido pagado o finalizado → 409 `no_cancelable` con `mensaje`; confirmar dos veces o retirar fuera de orden → 409 `transicion_invalida`.

<a id="http-404"></a>

#### RFC 9110: 404 Not Found

📐 Norma · **Referencia:** IETF RFC 9110 §15.5.5 404 Not Found

El recurso pedido no existe en el servidor.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): `GET /pedidos/999` responde 404 con `{"error": "pedido_no_encontrado"}`, nunca un 500.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): `POST /firma` y `POST /pago` sobre el pedido 999 → 404 `pedido_no_encontrado`.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Las 9 rutas de un pedido (`GET`, `PUT`, `firma`, `pago`, `retirado`, `en-puerta`, `recibido`, `entregado`, `cancelar`) sobre el pedido 999 → 404, en un solo test parametrizado.

<a id="http-422"></a>

#### RFC 9110: 422 Unprocessable Content

📐 Norma · **Referencia:** IETF RFC 9110 §15.5.21 422 Unprocessable Content

El cuerpo tiene un formato válido (JSON) pero su contenido no se puede procesar.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Teléfono fuera de patrón, campos de más o un `destino` desconocido en `/mensajes` responden 422.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): Body fuera de rango o con campos de más, y dos reglas que necesitan el catálogo: `plato_inexistente` y `plato_repetido`.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Firma que no es un PNG en base64, de más de 200 000 caracteres o con campos de más → 422.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): `POST /cancelar` con `por` que no es `cliente` ni `servicio`, sin `por` o con campos de más → 422.

<a id="iso8601"></a>

#### ISO 8601 / RFC 3339: fechas y horas

📐 Norma · **Referencia:** ISO 8601; IETF RFC 3339

Formato estándar de fecha y hora (`2026-11-15T13:43:08.029362Z`). La `Z` indica UTC; con una sola zona, el texto se ordena igual que el tiempo.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Toda marca de tiempo sale de `reloj.marca_tiempo` en UTC con `Z`, y un test lo verifica. Riesgo observado: el reloj de Windows avanza cada 15,6 ms, así que los dos eventos del alta suelen empatar.
- [Paso 8](paso-08-defectos-sembrados.md): Con el defecto de zona horaria, cada actor guarda su hora local sin `Z` ni offset (`2026-11-14T09:00:05.000000`), algo que RFC 3339 §5.6 no permite. Las marcas dejan de ser comparables entre actores y, ordenadas como texto, `PAGADO` queda antes que `COTIZADO`.

<a id="e164"></a>

#### ITU-T E.164: números de teléfono

📐 Norma · **Referencia:** ITU-T Recommendation E.164

Plan internacional de numeración telefónica: como máximo 15 dígitos, con el código de país adelante.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): El patrón `^\+?\d{8,15}$` toma de E.164 el máximo de 15 dígitos.

<a id="iso6709"></a>

#### ISO 6709: coordenadas geográficas

📐 Norma · **Referencia:** ISO 6709 (con el datum WGS 84)

Representación estándar de un punto geográfico: latitud entre -90 y 90 grados y longitud entre -180 y 180, en grados decimales.

**En este proyecto:**

- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): `lat` en [-90, 90] y `lng` en [-180, 180]; los bordes son válidos y ±0,1 más allá da 422.

<a id="metodos-idempotentes"></a>

#### RFC 9110: métodos idempotentes

📐 Norma · **Referencia:** IETF RFC 9110 §9.2.2 Idempotent Methods

Un método es idempotente si repetir la misma petición tiene el mismo efecto que hacerla una vez. `PUT`, `DELETE` y los métodos seguros lo son por definición; `POST` no, así que si hace falta lo tiene que garantizar el servidor.

**En este proyecto:**

- [Paso 6](paso-06-firma-pago-y-asignacion.md): `POST /pago` no es idempotente por norma: el servidor lo hace idempotente a propósito, para que un reintento (doble clic, red que se corta) no pague dos veces.

<a id="data-url"></a>

#### RFC 2397 y RFC 4648: data URL y base64

📐 Norma · **Referencia:** IETF RFC 2397 (esquema data:); IETF RFC 4648 (base64)

Una *data URL* lleva el contenido de un archivo dentro del texto: `data:<tipo>;base64,<datos>`. RFC 4648 fija el alfabeto base64: letras, dígitos, `+`, `/` y hasta dos `=` de relleno al final.

**En este proyecto:**

- [Paso 6](paso-06-firma-pago-y-asignacion.md): La firma llega como `data:image/png;base64,...`, que es lo que entrega un `<canvas>` del navegador (Paso 9). El patrón solo acepta el alfabeto base64.

<a id="interoperabilidad"></a>

#### ISO/IEC 25010: interoperabilidad

📐 Norma · **Referencia:** ISO/IEC 25010 — Compatibilidad › Interoperabilidad

Capacidad de un sistema de intercambiar información con otros y de que esos otros la puedan usar. Cambiar el tipo de un campo la rompe, aunque el dato "sea el mismo".

**En este proyecto:**

- [Paso 8](paso-08-defectos-sembrados.md): Con el defecto de contrato, `total` llega como `"$ 22.500"`: un cliente que lo suma o lo compara recibe texto. La página del cliente (Paso 9) muestra `NaN`.

### ✅ Buenas prácticas

<a id="twelve-factor"></a>

#### Twelve-Factor App, factor III: configuración

✅ Buena práctica · **Referencia:** The Twelve-Factor App — III. Config

La configuración que cambia entre entornos (rutas, interruptores) va en variables de entorno, no escrita en el código.

**En este proyecto:**

- [Paso 1](paso-01-esqueleto-y-salud.md): `Config` lee la ruta de la base y los defectos desde variables de entorno.
- [Paso 8](paso-08-defectos-sembrados.md): Los defectos se prenden con `DEMO_DEFECTO_ZONA_HORARIA=1` y `DEMO_DEFECTO_CONTRATO=1`, sin cambiar el código.

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
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): La carga escribe items, dirección, total, dos eventos y un mensaje en una sola transacción.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): `PAGADO`, el mensaje al delivery y `ASIGNADO` se confirman juntos o no se confirma nada.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): `RETIRADO`, el aviso "Tu pedido está en camino" y `EN_CAMINO` se confirman juntos; también la segunda confirmación y el `CERRADO`.

<a id="inyeccion-dependencias"></a>

#### Inyección de dependencias

✅ Buena práctica · **Referencia:** Patrón Dependency Injection

Una función recibe lo que necesita desde afuera en vez de crearlo ella misma. Facilita probarla y reemplazar piezas.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Las rutas reciben el `Ctx` (conexión + configuración) mediante `Depends(obtener_ctx)` de FastAPI.

<a id="idempotencia"></a>

#### Operaciones idempotentes

✅ Buena práctica · **Referencia:** Idempotencia

Una operación idempotente puede repetirse muchas veces con el mismo resultado que si se hiciera una sola vez.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): La siembra solo carga platos si la tabla está vacía: diez reinicios siguen dando 4 platos.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Pagar dos veces responde 200 con el mismo pedido: un solo `PAGADO` y un solo WhatsApp al delivery. También si los dos pagos llegan al mismo tiempo.

<a id="concurrencia-optimista"></a>

#### Control de concurrencia optimista

✅ Buena práctica · **Referencia:** Optimistic concurrency control; MITRE CWE-367 (TOCTOU)

Entre leer un dato (*check*) y escribirlo (*use*) puede entrar otro proceso: es una condición de carrera TOCTOU. En vez de bloquear antes de leer, se escribe con una condición (`UPDATE ... WHERE estado = <el leído>`): si otro se adelantó, no cambia ninguna fila y se avisa del conflicto.

**En este proyecto:**

- [Paso 6](paso-06-firma-pago-y-asignacion.md): `_avanzar` y `firmar` escriben con `AND estado = <el leído>`. Dos pagos simultáneos dejan un solo `PAGADO`; dos envíos simultáneos del formulario dan 200 y 409 en vez de un 500. Tres tests con dos hilos y una barrera lo reproducen siempre igual.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Estado y bandera de cada confirmación van en un solo `UPDATE` condicional. Dos confirmaciones a la vez: la que pierde relee y reintenta una vez, y hay un solo `CERRADO`. Cancelar contra pagar, en los dos órdenes: gana uno y el otro da 409.

<a id="dinero-enteros"></a>

#### Dinero en unidades enteras

✅ Buena práctica · **Referencia:** Evitar coma flotante binaria (IEEE 754) con dinero

Los `float` tienen errores de redondeo (`0.1 + 0.2 = 0.30000000000000004`). Con dinero se usan enteros.

**En este proyecto:**

- [Paso 2](paso-02-base-de-datos-y-catalogo.md): Los precios son `int` en pesos y un test verifica el tipo.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): El total es la suma de `cantidad × precio_unitario` en pesos enteros: `2 × 9000 + 4500 = 22500`.
- [Paso 8](paso-08-defectos-sembrados.md): Con el defecto de contrato, la base sigue guardando enteros y el total se calcula igual; solo la salida pasa a texto. Un test lee la misma base con y sin el defecto.

<a id="table-driven"></a>

#### Fuente única de verdad, diseño table-driven

✅ Buena práctica · **Referencia:** Single source of truth; table-driven design

Las reglas se escriben como datos (una tabla) en un solo lugar, no repartidas en `if` por todo el código.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): `TRANSICIONES` es un diccionario; toda mutación de estado pasará por `validar_transicion`.
- [Paso 4](paso-04-crear-pedido-y-mensajes.md): `pedidos._avanzar` es el único camino para cambiar el estado: valida, actualiza y registra el evento.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): El precio sale siempre del catálogo (`catalogo.precios`) y queda guardado en `precio_unitario`; el cliente no manda montos.

<a id="parametrizados"></a>

#### Tests parametrizados

✅ Buena práctica · **Referencia:** pytest.mark.parametrize

Un mismo test se ejecuta con muchos datos, y cada combinación aparece como un caso separado en el reporte.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Un test recorre las 18 válidas y otro las 6 inválidas, cada una con su nombre (`salto`, `retroceso`…).
- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Los teléfonos válidos e inválidos tienen nombre propio: `limite-8-digitos`, `16-digitos`, `con-letras`…
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): Cada valor límite es un caso con nombre (`3-unidades-primer-recargo`, `201-caracteres`, `mismos-platos`).
- [Paso 6](paso-06-firma-pago-y-asignacion.md): Los 8 estados de pagado en adelante y los 8 casos de formato de firma, cada uno con su nombre.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): Reglas R1 a R5 de la cancelación, las 9 rutas del 404 y los 5 bodies inválidos de `por`, cada uno con su id.
- [Paso 8](paso-08-defectos-sembrados.md): `formato.pesos` con seis montos con nombre: 0, 999, 1000 (primer separador), 9000, 22500 y 1234567 (dos separadores).

<a id="fail-fast"></a>

#### Fail fast con errores descriptivos

✅ Buena práctica · **Referencia:** Fail fast

Ante una operación inválida, fallar enseguida con un error que diga qué pasó, en vez de seguir con datos corruptos.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): `TransicionInvalida(actual, destino)`: el error dice exactamente qué cambio se intentó.
- [Paso 4](paso-04-crear-pedido-y-mensajes.md): `PedidoNoEncontrado` y `TransicionInvalida` se traducen a HTTP en un solo lugar (`main.py`), nunca un 500.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): `cargar_datos` valida estado, repetidos y platos antes del primer `INSERT`; cada rechazo trae su código (`plato_repetido`, `plato_inexistente`).
- [Paso 6](paso-06-firma-pago-y-asignacion.md): El pago chequea primero el estado y después la firma: un pedido sin cotizar da `transicion_invalida`, no `firma_requerida`.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): La cancelación responde `no_cancelable` con el estado real y un mensaje: "ya fue pagado" o "ya está finalizado".

<a id="mutacion"></a>

#### Prueba de mutación

✅ Buena práctica · **Referencia:** Mutation testing

Se cambia el código a propósito (una *mutación*) y se verifica que algún test falle. Si ninguno falla, la suite tiene un hueco.

**En este proyecto:**

- [Paso 3](paso-03-maquina-de-estados.md): Se agregó la flecha prohibida `EN_PUERTA → CERRADO`: 2 tests fallaron. Después se revirtió.
- [Paso 4](paso-04-crear-pedido-y-mensajes.md): 3 mutantes, los 3 detectados: sacar `validar_transicion`, aceptar campos de más y subir el límite a 16 dígitos.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): 6 de 6 detectadas. La primera vez sobrevivió una (sacar el chequeo temprano de estado) y eso llevó a un caso nuevo: cargar dos veces con los mismos platos.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): 12 defectos a propósito (sin idempotencia, sin chequeo de firma, orden invertido, límite corrido en uno, sin migración, entre otros): 12 de 12 detectados. Con el arreglo de concurrencia, 7 más (sacar la condición del `UPDATE`, ignorar `rowcount`, firmar sin condición, entre otros): 7 de 7.
- [Paso 7](paso-07-entrega-cierre-y-cancelacion.md): 16 mutantes, los 16 detectados: sin reintento, cerrar siempre o nunca, sin bandera, cancelar sin traducir la carrera, mensajes invertidos, sin aviso, actor equivocado, `delivery` puede cancelar, entre otros. Un mutante inválido (error de sintaxis) se rehízo.
- [Paso 8](paso-08-defectos-sembrados.md): 13 de 13 detectados: ignorar el interruptor de zona, una sola zona para todos, agregar el offset, no convertir a hora local, otro separador de miles, sin `$ `, no respetar `None`, interruptor de contrato invertido y olvidar el formato en cada campo.

<a id="validacion-entrada"></a>

#### Validación de entrada por lista blanca

✅ Buena práctica · **Referencia:** OWASP Input Validation Cheat Sheet

Aceptar solo lo que se sabe válido (lista blanca) y rechazar todo lo demás en la frontera del sistema, antes de que llegue a la lógica.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): Los modelos Pydantic usan `extra="forbid"`: un cliente que manda `"estado": "PAGADO"` al crear el pedido recibe 422.
- [Paso 5](paso-05-cargar-datos-y-cotizacion.md): `extra="forbid"` rechaza `total`, `estado` o `descuento`; la dirección tiene un patrón que no admite espacios en los extremos.
- [Paso 6](paso-06-firma-pago-y-asignacion.md): La firma solo pasa con el patrón `^data:image/png;base64,[A-Za-z0-9+/]+={0,2}$` y sin campos de más.

<a id="doble-prueba"></a>

#### Doble de prueba (fake)

✅ Buena práctica · **Referencia:** Test double: fake (Meszaros, xUnit Test Patterns)

Una implementación simple que reemplaza a un servicio real (una pasarela, un canal de mensajes) y permite ver qué se le pidió.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): El WhatsApp es simulado: cada mensaje queda en la tabla `mensajes` y se lee con `GET /mensajes`, como si fuera el celular del destinatario.

<a id="reloj-inyectable"></a>

#### Reloj reemplazable

✅ Buena práctica · **Referencia:** Seam: reloj como dependencia

La hora actual sale de una sola función que los tests pueden reemplazar, así las pruebas con fechas son repetibles.

**En este proyecto:**

- [Paso 4](paso-04-crear-pedido-y-mensajes.md): `reloj.ahora_utc()` es la única fuente de "ahora"; en el Paso 8 los tests la fijan con `monkeypatch` para provocar el defecto de zona horaria.
- [Paso 8](paso-08-defectos-sembrados.md): El fixture `reloj_fijo` reemplaza `reloj.ahora_utc` con instantes de 5 en 5 segundos desde las 15:00 UTC: el desorden de la zona horaria sale siempre igual, a cualquier hora.

<a id="migracion-esquema"></a>

#### Migraciones de esquema aditivas

✅ Buena práctica · **Referencia:** Evolutionary Database Design (Sadalage y Fowler)

El esquema de la base cambia en pasos chicos, sin perder datos. Una migración aditiva solo agrega (por ejemplo, una columna que admite nulos), así que las filas viejas siguen siendo válidas.

**En este proyecto:**

- [Paso 6](paso-06-firma-pago-y-asignacion.md): `CREATE TABLE IF NOT EXISTS` no toca una tabla que ya existe: al arrancar, `db.py` revisa `PRAGMA table_info` y agrega `firma` si falta. Un test parte de una base sin esa columna.

<!-- TERMINOS:FIN -->
