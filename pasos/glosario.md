# Glosario de etiquetas

Qué significa cada etiqueta usada en los pasos. Es la misma información del modal de [`pasos.html`](pasos.html).

- [📘 ISTQB CTFL v4.0](#-istqb-ctfl-v40)
- [📐 Norma](#-norma)
- [✅ Buena práctica](#-buena-práctica)

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
