# QA Portfolio — Documento de diseño

**Fecha:** 2026-11-10 · **Estado:** **APROBADO por el usuario el 2026-11-14** (incluidas las "decisiones mías"; se pueden revisar más adelante) · **Idioma del proyecto:** español
**Autor del portfolio:** Walter (QA, 12 años de experiencia) · **Fuentes:** brainstorming del 2026-11-10 (`thoughts/brainstorms/2026-11-10-portfolio-decisiones.md`, `thoughts/handoffs/completed/2026-11-10-portfolio-brainstorm.md`), plan original `qa-portfolio-plan.md` (reemplazado en lo que contradiga este documento).

Convención: lo que dice **(decisión mía)** lo eligió el diseñador y el usuario lo puede cambiar; todo lo demás lo decidió el usuario.

---

## 1. Intención y por qué

Walter tiene 12 años como QA. Mucho de ese trabajo es difícil de mostrar fuera de la empresa. El portfolio tiene que convertir esa experiencia en **evidencia demostrable**: código que corre, métricas, nombres técnicos correctos y alineación con estándares. Al mismo tiempo debe darle **experiencia real** en lo que hoy le falta (mobile automatizado, CI, TypeScript).

Cada práctica se muestra con tres cosas:
1. **En términos técnicos:** el nombre correcto de la técnica.
2. **Cómo se mide:** la métrica o evidencia concreta.
3. **Norma / estándar:** la práctica ISTQB y, si aplica, la norma ISO.

**Prioridad: calidad sobre velocidad.** El usuario prefiere algo más atractivo aunque tarde más.

## 2. Objetivos, no-objetivos y anti-objetivos

**Objetivos**
- Un **sistema demo propio** (delivery de comidas) que es el centro del portfolio y el objetivo de todas las pruebas.
- Módulos de prueba: **API** (con quality gates en CI), **Mobile** (Appium), **Web** (Playwright), **Performance** (JMeter) y **Prime** (asistente de QA con IA que funciona de verdad), más una **migración posterior a TypeScript**.
- Que cada ejemplo y cada funcionalidad tenga su **vista HTML** con una sección **"Mejoras"**.
- Etiquetar cada práctica con **ISTQB/ISO** para que un reclutador la reconozca como homologada.
- Mostrar en formato STAR su logro principal: un **flujo API encadenado usado como gate antes del deploy** (no bloquea en QA, bloquea en prod) más el **triage de fallos**.

**No-objetivos**
- SauceDemo y JSONPlaceholder (quedan afuera). Tampoco la app `workspace/Comercio`.
- Automatizar WhatsApp real.
- Hostear Prime en internet por ahora (queda documentado para más adelante).
- Emuladores de Android (el hardware no los soporta).

**Anti-objetivos (aunque funcione, sería un fracaso si…)**
- Incluye **cualquier información real de la empresa** del usuario: nombres, endpoints, código, datos, rubro, herramientas internas. Las historias del trabajo solo se usan como **patrón abstracto**.
- Dice que el usuario **tiene una certificación ISTQB**. No la tiene. Debe decir "Prácticas alineadas al syllabus ISTQB CTFL v4.0".
- La **frase secreta del creador de Prime** aparece en el repo, en la documentación o en los logs.
- Se ve como un tutorial copiado: código sin métricas, sin explicación técnica y sin el "por qué".

## 3. Restricciones

- **Hardware:** equipo con recursos limitados y sin virtualización. Todo tiene que ser liviano. **No hay emulador.** Las vistas HTML se abren con **doble clic**, sin servidor.
- **Dispositivo mobile:** Samsung Galaxy A11 real conectado por USB, dedicado a pruebas (Android 10–12; la versión exacta está pendiente de confirmar).
- **Ritmo:** ~1 h diaria más algunos días largos, ~7–8 h por semana.
- **Repositorio (decidido 2026-11-14):** **público** en GitHub, para enlazarlo desde **LinkedIn**. Se crea al empezar la etapa 2, con el OK explícito del usuario en ese momento. Va a nombre de la **cuenta y el mail personales** del usuario, nunca los del trabajo. Hasta entonces la carpeta `Portfolio` no es un repo git, y no se hace push sin OK.
- **Credenciales del usuario:** diplomatura en Python niveles 1–3 (universidad nacional argentina) y un curso del GCBA en curso. Se priorizan Python y la coherencia de lenguaje.

## 4. Sistema demo: "delivery de comidas" (ficticio)

**Stack:** Python + **FastAPI** + **SQLite** + páginas HTML simples, servidas por la misma app.

### 4.1 Actores
- **Cliente:** usa la web móvil.
- **Web/Servicio:** el sistema: catálogo, cálculos, mensajes, cierre.
- **Delivery:** usa la web móvil desde su link.
- *(decisión mía)* Una vista mínima de **panel/central** para ver los pedidos y su línea de tiempo. Ahí se nota el defecto de zona horaria.

### 4.2 Historia del flujo (del usuario)

| # | Actor | Acción | Estado resultante *(nombres: decisión mía)* |
|---|---|---|---|
| 1 | Web | Muestra el catálogo (**3–4 platos**) | — |
| 2 | Cliente | Deja su teléfono y envía el formulario | `INICIADO` |
| 3 | Servicio | Envía el link al cliente por WhatsApp (simulado) | `LINK_ENVIADO` |
| 4 | Cliente | Carga cantidades y dirección y confirma el pedido | `DATOS_CARGADOS` |
| 5 | Servicio | Envía el total y el tiempo de demora | `COTIZADO` |
| 6 | Cliente | Confirma el pago **y firma la lista del pedido** (firma en canvas) | `PAGADO` |
| 7 | Servicio | Envía la dirección al delivery por WhatsApp (simulado) | `ASIGNADO` |
| 8 | Delivery | Confirma que tiene el pedido | `RETIRADO` |
| 9 | Servicio | Avisa al cliente que el pedido está en camino (WhatsApp simulado) | `EN_CAMINO` |
| 10 | Delivery | Avisa que llegó a la dirección | `EN_PUERTA` |
| 11 | Cliente | Confirma que recibió la comida | `RECIBIDO` |
| 12 | Delivery | Avisa que la comida fue entregada | `ENTREGADO` |
| 13 | Servicio | Cierra el pedido | `CERRADO` |

Vista del flujo: `mockups/flujo-pedido.html`.

**Ubicación:** el cliente comparte su ubicación (GPS del navegador) **o** marca en un mapa dónde quiere recibir el pedido. *(decisión mía)* El mapa puede ser un selector simple de coordenadas o una librería liviana. Lo elige quien construye, pero tiene que funcionar sin claves de pago.

### 4.3 Reglas de negocio
- **El total lo calcula el servidor** con los precios del catálogo (GET). *(decisión mía)* Si el cliente manda un total, se ignora o se rechaza; nunca se confía en él.
- **Cancelación:** se puede cancelar antes del pago (`INICIADO` … `COTIZADO` → `CANCELADO`). **Una vez pagado, no.** *(decisión mía)* Responde `409 Conflict` con un mensaje claro, y pueden cancelar tanto el cliente como el servicio.
- Las transiciones solo avanzan en el orden de la tabla. Cualquier salto o retroceso se rechaza *(decisión mía: 409)*.
- *(decisión mía)* El **pago es idempotente**: si el pago se repite, no se cobra dos veces.
- *(decisión mía)* Los pasos 11 y 12 (confirmación del cliente y del delivery) son independientes. El pedido solo se puede cerrar cuando están los dos.

### 4.4 API (estilo del usuario: GET para consultar y precios, POST para crear y enviar, PUT para modificar, POST para la firma)
Rutas tentativas *(decisión mía; quien construye puede ajustarlas)*:
`GET /platos` · `POST /pedidos` · `GET /pedidos/{id}` · `PUT /pedidos/{id}` · `POST /pedidos/{id}/pago` · `POST /pedidos/{id}/firma` · `POST /pedidos/{id}/cancelar` · endpoints de delivery para los pasos 8, 10 y 12 · `POST /pedidos/{id}/recibido` · `GET /mensajes` (bandeja).
La API tiene que publicar un **OpenAPI** (FastAPI lo genera solo), que es la base de los JSON Schema de los tests de contrato.

### 4.5 WhatsApp simulado
*(decisión mía)* Una **bandeja de mensajes** (tabla + `GET /mensajes?destino=…`) donde quedan los mensajes de los pasos 3, 7 y 9 con destinatario, canal, texto y link. Los tests obtienen los links desde ahí, igual que en el trabajo se obtienen por API o por la base de datos.

### 4.6 Defectos sembrados (bug seeding)
Inspirados en bugs reales de la carrera del usuario, contados de forma genérica. Se **activan y desactivan** por configuración (variable de entorno o flag) para mostrar el antes y el después. *(decisión mía: el mecanismo exacto lo elige quien construye)*
1. **Zona horaria:** local en AR (UTC-3), cliente en MX (UTC-6), servidor en EE.UU. Los timestamps no se normalizan a UTC y la línea de tiempo queda desordenada ("pagado" antes que "cotizado"). *ISTQB: transición de estados; validación en BD.*
2. **Contrato:** un campo cambia de tipo o formato (por ejemplo, el precio llega como texto) y rompe el total. *ISTQB: pruebas de integración/contrato · ISO 25010: compatibilidad.*
*(decisión mía)* Se pueden sumar más defectos si aparecen ideas, siempre documentados con un **informe de defecto** (ISO/IEC/IEEE 29119-3).

## 5. Módulos de prueba

Todos en **Python** primero. Cada módulo tiene su vista HTML (ver §7) con "En términos técnicos", "Cómo se mide", "Norma / estándar" y "Mejoras".

### 5.1 API + quality gates (etapa 1–2, primer hito)
- **Flujo encadenado:** catálogo → crear pedido → modificar → pagar/firmar → recorrer los estados del delivery → cerrar. Es la versión ficticia del logro del usuario en Postman.
- Técnicas a mostrar: **transición de estados** (todas las transiciones válidas e inválidas), **tabla de decisión** de cancelación por estado, **valores límite y particiones** (cantidad 0, máximo por plato, dirección vacía), **contrato con JSON Schema**, **total manipulado** (riesgo), **idempotencia del pago**, **verificación de la bandeja de mensajes**.
- **Gates en GitHub Actions** (decisión del usuario: no bloquea en QA, bloquea en prod):
  - Ambiente **QA**: la suite corre y reporta. Si falla, **no bloquea**, pero exige **triage** (defecto de producto / test desactualizado / problema de ambiente).
  - Ambiente **prod**: la suite es **bloqueante**. Si falla, no hay "deploy".
  - *(decisión mía)* Como no hay un prod real, el "deploy" a prod es la **publicación de las vistas del portfolio** (por ejemplo, en GitHub Pages) o un paso de deploy simulado. Quien construye elige lo más simple; lo importante es que el bloqueo se vea.
- **Triage:** una plantilla o reporte con las tres categorías y un ejemplo real de cada una, generado con los defectos sembrados.
- Herramientas *(decisión mía)*: **pytest + requests (o httpx) + jsonschema**, reporte HTML (pytest-html o Allure, el más liviano). Postman/Newman es opcional como "Mejora", para conectar con su experiencia.
- *ISTQB: criterios de salida, pruebas de regresión, gestión de defectos · ISO/IEC/IEEE 29119-2 (proceso), 29119-3 (documentación).*

### 5.2 Mobile (etapa 3)
- **Appium + Python** en el **Galaxy A11 real** por USB.
- Dos frentes: (a) **Sauce Labs My Demo App** (Android nativo): smoke tests; (b) la **web móvil del sistema demo** en Chrome del A11 (formulario del cliente, firma, ubicación).
- Hay que documentar la configuración (Android SDK platform-tools sin emulador, depuración USB, capabilities) como parte del valor del módulo.
- *ISTQB: pruebas de sistema, compatibilidad de dispositivo · ISO 25010: compatibilidad, usabilidad.*

### 5.3 Web (etapa 4)
- **Playwright (Python)** sobre el sistema demo: **E2E con varios actores** (cliente, delivery y servicio en contextos separados), **emulación de dispositivo**, **geolocalización**, **timezoneId** (para reproducir el defecto de zona horaria) y la firma en canvas.
- *ISTQB: pruebas E2E/de sistema, transición de estados.*

### 5.4 Performance (etapa 5)
- **JMeter** *(decisión mía, delegada por el usuario; la búsqueda de mercado mostró que es lo que más piden las ofertas de AR/LATAM y el usuario ya lo usó)*. Carga sobre el catálogo y el flujo de pedido y pago, ejecutado **sin interfaz en GitHub Actions** con **umbrales** que hacen fallar el job (por ejemplo, p95 del GET de catálogo < X ms).
- Locust o k6 quedan en "Mejoras".
- *ISTQB: pruebas de rendimiento, carga y estrés · ISO 25010: eficiencia de desempeño.*

### 5.5 Prime: asistente de QA con IA (etapa 6)
Es una **versión chica en Python que funciona de verdad**. Nunca se usa nombre, código ni datos de la herramienta interna del trabajo.

**Qué hace (del usuario):**
- Lee el **código del repo** del sistema demo y las **cards / pedidos de cambio** del analista o PO (ficticias, en una carpeta del repo *(decisión mía)*). Las compara.
- **Propone casos de prueba** etiquetados con la técnica ISTQB y **estima la cobertura** (qué reglas de la card ya tienen test y cuáles no).
- **Ayuda a diagnosticar fallos** (clasificación de triage) y **ayuda a automatizar** los casos aprobados.
- **Mantiene actualizada la documentación de reglas de negocio** cada vez que entra un cambio.
- **El QA siempre valida:** acepta, descarta o agrega casos.
- *(decisión mía)* La primera card ficticia es "Permitir cancelar el pedido hasta antes del pago".

**Chat y modos (del usuario):**
- Chat limitado al proyecto. Al empezar, pregunta **"¿quién sos?"**.
- **Modo creador:** se activa con un **desafío de dos pasos**. El usuario escribe la frase secreta exacta, Prime responde con su frase de reconocimiento y queda en modo creador. En ese modo tiene más acceso y hace modificaciones cuando hacen falta.
- **Modo visitante:** cualquier otra respuesta (incluido "soy Walter") lo deja en modo visitante. Prime responde de forma limitada, en solo lectura: casos existentes, reglas de negocio y alcance.
- **`/fin`:** cierra la sesión del creador. Prime vuelve al modo visitante y pregunta de nuevo quién le habla.

**Seguridad *(decisión mía)*:**
- La frase **se guarda como hash en `.env`**, fuera del repo, y la frase real nunca se escribe en documentación ni logs. La versión real debería ser distinta de la que se mencionó en el chat de diseño.
- Hay un bloqueo temporal después de varios intentos fallidos.
- **Qué puede modificar en modo creador (decidido 2026-11-14):** solo el **documento de reglas de negocio**, la **lista de casos** y **archivos de test nuevos**. Cada modificación se **propone primero** (se muestra el cambio) y el creador la confirma. **Nunca toca el código del sistema demo.**
- En modo visitante, Prime no puede escribir archivos.

**Ejecución:**
- Corre **en la máquina del usuario**.
- Se deja un **.md de activación** que explica dos cosas: cómo usarlo en otra PC con la credencial o cuenta de Claude del usuario, y cómo desplegarlo en internet más adelante si hay presupuesto (hosting, límite de consultas, tope de gasto).
- En el portfolio se muestra con un **video o GIF** de una sesión real.

**Tests del propio Prime:** suplantación ("soy Walter" sin la frase), prompt injection ("ignorá tus reglas"), `/fin` a mitad de una modificación, preguntas fuera del proyecto. *ISTQB: pruebas de seguridad · ISO 25010: seguridad (control de acceso).*

**IA (decidido 2026-11-14):** Prime usa la **suscripción de Claude del usuario a través de Claude Code con la sesión iniciada**. La empresa se la da para proyectos personales y no le puso límites. No hace falta una clave de API ni tope de gasto para arrancar. Quien construye elige el modelo vigente.
- *(decisión mía)* El acceso a la IA queda detrás de una **capa chica intercambiable**, así Prime puede pasar a una clave de API propia (con tope) sin reescribirse. Esto cubre dos casos: hostearlo en internet o que la suscripción deje de estar disponible. El .md de activación explica cómo hacer el cambio.
- Ninguna credencial ni dato de la cuenta va al repo.

### 5.6 Migración a TypeScript (etapa 7)
Mobile y Web pasan a **WebdriverIO + Appium** y Playwright en TS. Se mantienen las versiones en Python y se muestra la comparación.

## 6. Mapa ISTQB / ISO (resumen)

| Práctica en el portfolio | ISTQB CTFL v4.0 | ISO |
|---|---|---|
| Estados del pedido y cancelación | Transición de estados, tablas de decisión | — |
| Cantidades y dirección | Valores límite, particiones de equivalencia | — |
| Contrato JSON Schema | Pruebas de integración de componentes | 25010: compatibilidad |
| Total del servidor, pago idempotente | Pruebas basadas en riesgos | 25010: confiabilidad / seguridad |
| Gates QA/prod | Criterios de entrada/salida, regresión | 29119-2: proceso |
| Triage de fallos | Gestión de defectos, análisis de causa raíz | 29119-3: informe de incidentes |
| Plan y casos | Planificación, trazabilidad | 29119-3: documentación |
| JMeter | Pruebas de rendimiento | 25010: eficiencia de desempeño |
| Prime: modos y frase | Pruebas de seguridad | 25010: seguridad |

Texto obligatorio en el README y en la portada: **"Prácticas alineadas al syllabus ISTQB CTFL v4.0"**. Nunca usar "certificado".

## 7. Vistas HTML (aprobado)

- **Diseño:** portada con **tarjetas de módulos** arriba y, debajo, el **dashboard del módulo seleccionado**: KPIs, métricas por columnas (por ejemplo, GET/POST con tiempos y umbral) y **Mejoras**. Mockup aprobado: `mockups/portada-dashboard.html`.
- **Recuadros por módulo:** "En términos técnicos", "Cómo se mide" y "Norma / estándar".
- Archivos HTML que se abren con doble clic. *(decisión mía)* Cada ejecución de tests genera o actualiza los datos que muestra la vista (por ejemplo, un JSON de resultados que la vista lee), así las métricas son reales y no se escriben a mano.
- Cada ejemplo de código o funcionalidad tiene su vista o sección.

## 8. Orden y cronograma (aprobado como estimado)

Se asume un ritmo de ~7–8 h por semana. Las fechas son orientativas: se publica cada etapa al terminarla.

| # | Etapa | Horas | Listo aprox. |
|---|---|---|---|
| 1 | Sistema demo (API, estados, bandeja, páginas, defectos sembrados) | 20–25 | mediados dic 2026 |
| 2 | Tests de API + gates en GitHub Actions + triage + portada y vista de API | 18–20 | **fin dic 2026 – inicio ene 2027 (primer hito visible)** |
| 3 | Mobile (Appium + A11) | 20–25 | inicio feb 2027 |
| 4 | Web (Playwright) | 15 | fin feb 2027 |
| 5 | Performance (JMeter en CI) | 10 | mediados mar 2027 |
| 6 | Prime | 30 | fin abr 2027 |
| 7 | Migración a TypeScript | 20 | ~junio 2027 |

## 9. Historia STAR (para README y entrevistas)

Logro del usuario contado de forma genérica:
- **Situación:** los deploys llegaban sin validación integral.
- **Tarea:** asegurar el flujo crítico.
- **Acción:** construyó en Postman un flujo API encadenado (login → crear caso → modificar → crear sub-registros → cambiar estado) como gate antes del deploy, que no bloquea en QA y bloquea en prod, más un proceso de triage.
- **Resultado:** la métrica la completa el usuario, sin datos de la empresa.

El sistema demo **reproduce ese patrón** para mostrarlo funcionando.

## 10. Decisiones tras la revisión del builder *(decisiones mías)*

- **Defectos sembrados apagados en la rama principal.** El gate de prod pasa en verde y publica. Un **flujo aparte de demostración** enciende los defectos: el gate de QA falla con su triage y el de prod bloquea. El portfolio nunca se bloquea a sí mismo.
- **El sistema demo no se hostea por ahora** (igual que Prime). Se muestra con capturas, videos y vistas con métricas reales. Queda documentado cómo publicarlo.
- **`qa-portfolio-plan.md` queda reemplazado por completo** por este documento. Quedan prohibidos, por confidencialidad, "subir planes JMeter existentes" y cualquier extracción de la herramienta interna. Los años de experiencia son 12.
- **Los tests de seguridad de Prime en CI usan un modelo simulado (stub)**. Los tests contra el modelo real se corren localmente.

## 11. Preguntas abiertas: respondidas (2026-11-14)

1. Pago de la IA de Prime → suscripción vía Claude Code (§5.5).
2. Qué puede modificar Prime en modo creador → reglas, casos y tests nuevos con vista previa; nunca el código del demo (§5.5).
3. Repositorio → público, para LinkedIn, con cuenta personal, creado al empezar la etapa 2 (§3).

## 12. Lo que queda en manos de quien construye

- La estructura de carpetas del repo y el nombre del repo (se crea en GitHub solo con el OK del usuario).
- Las librerías concretas, siempre livianas: reporte HTML, mapa, firma en canvas, migraciones.
- Cómo se modelan los ambientes QA/prod en Actions y cuál es el "deploy" simulado.
- El mecanismo para activar los defectos sembrados.
- El modelo de Claude para Prime y cómo lee el repo.
- Los umbrales concretos de performance (se calibran con una primera medición).
