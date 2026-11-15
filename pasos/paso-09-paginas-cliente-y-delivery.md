# Paso 9: Páginas del cliente y del delivery

**Objetivo:** que el sistema se pueda usar con el dedo, como lo usaría una persona. Son tres pantallas mobile (360 px, el ancho del Galaxy A11), en HTML y JS plano y servidas por la misma app: el **inicio** (menú y teléfono), la del **cliente** (carga de datos con mapa, firma, pago y seguimiento) y la del **delivery** (retirar, llegar y entregar). Cada elemento interactivo lleva un `data-testid` fijo: son los puntos de enganche de Appium (etapa 3) y Playwright (etapa 4).

## 1. Qué hicimos

| Archivo | Qué contiene |
|---|---|
| `sistema-demo/delivery/main.py` | Rutas `GET /`, `GET /cliente/pedido/{id}` y `GET /delivery/pedido/{id}`, que devuelven el HTML con `FileResponse`. `StaticFiles` sirve `estilos.css` y `api.js` en `/estaticos`. Las páginas no aparecen en `/docs` (`include_in_schema=False`). |
| `sistema-demo/delivery/paginas/inicio.html` | Pasos 1 a 3: el menú (`GET /platos`), el teléfono y "Pedir" (`POST /pedidos`). El link llega por la bandeja de WhatsApp simulado, igual que en la vida real. |
| `sistema-demo/delivery/paginas/cliente.html` | Muestra la sección que corresponde al estado. **Carga de datos** (paso 4): cantidades, dirección, "Usar mi ubicación", mapa Leaflet y total estimado. **Cotización** (pasos 5 y 6): total, demora, firma en un `canvas` y "Pagar". **Seguimiento**: estado, "Recibí mi pedido" (paso 11), "Cancelar" (solo antes de pagar) e historial de eventos. |
| `sistema-demo/delivery/paginas/delivery.html` | Dirección, punto marcado e ítems. Solo muestra el botón que corresponde: "Retiré" (paso 8), "Llegué a la puerta" (paso 10) y "Entregué" (paso 12). |
| `sistema-demo/delivery/paginas/api.js` | Lo compartido: `api()` (fetch que lanza el error con su `status` y `detail`), `textoDeError`, `pesos`, los nombres legibles de los estados y `seguirPedido`, que consulta el pedido cada 3 s. |
| `sistema-demo/delivery/paginas/estilos.css` | Mobile-first: una columna de 480 px como máximo, botones de 48 px de alto y el canvas con `touch-action: none` para firmar sin hacer scroll. |
| `sistema-demo/tests/test_paginas.py` | 6 tests: cada página da 200, `text/html` y trae sus `data-testid`; los dos estáticos se sirven con su tipo; la página de un pedido inexistente igual responde 200. |

**Los `data-testid`** (exactos, los usan las etapas 3 y 4):

| Página | `data-testid` |
|---|---|
| Inicio | `catalogo`, `plato-{id}`, `input-telefono`, `btn-pedir`, `msg-link-enviado`, `msg-error` |
| Cliente: carga de datos | `cantidad-{plato_id}`, `input-direccion`, `btn-ubicacion`, `mapa`, `total-estimado`, `btn-confirmar-datos` |
| Cliente: cotización | `total`, `demora`, `canvas-firma`, `btn-limpiar-firma`, `btn-pagar` |
| Cliente: seguimiento | `estado-pedido`, `btn-recibido`, `btn-cancelar`, `linea-de-tiempo`, `msg-error` |
| Delivery | `direccion-entrega`, `btn-retirado`, `btn-en-puerta`, `btn-entregado`, `estado-pedido`, `msg-error` |

`plato-{id}` y `cantidad-{plato_id}` los arma el JS con los platos de `/platos`. `linea-de-tiempo` no estaba en el plan para esta página: se sumó para cumplir lo que anunció el Paso 8 (que el defecto de zona horaria se vea en la pantalla), con el mismo nombre que usará el panel del Paso 10.

## 2. Por qué lo hicimos así

- **Las páginas son cascarones:** el HTML no sabe nada del pedido. El JS lee el id de la URL y pide los datos a la API. Por eso `/cliente/pedido/999` responde 200 y el 404 lo muestra la página en `msg-error`, como en una app real. Así no hay una segunda copia de las reglas: todo lo decide la API de los pasos 1 a 8.
- **Los defectos se ven en la pantalla:** `total-estimado` se calcula con `precio * cantidad` **sin convertir**. Si la API manda `"$ 9.000"` (defecto de contrato), la cuenta da `NaN` y queda a la vista. La línea de tiempo muestra `ocurrido_en` tal cual: con el defecto de zona horaria se ve desordenada y sin `Z`. Esconder un defecto en la UI le quitaría el blanco a las etapas 3 y 4.
- **"Pagar" no se deshabilita:** el doble clic lo resuelve el servidor, que es idempotente (Paso 6). Así el riesgo se puede probar desde la página. Para que el doble clic no choque consigo mismo, los dos clics esperan **el mismo** envío de firma (una promesa por dibujo) y después los dos pagan: el segundo pago responde 200 sin duplicar nada.
- **Sin `confirm()` para cancelar:** un diálogo nativo traba a Playwright y a Appium. "Cancelar" se muestra solo antes de pagar. Si el pedido se paga desde otra pestaña, la página tarda hasta 3 s en enterarse; si en ese rato se cancela, la API responde 409 `no_cancelable` y se muestra el mensaje.
- **Los errores llevan su código:** "Firmá antes de pagar. `[firma_requerida]`". La persona lee el texto; la prueba automática y el reporte de un defecto usan el código, que no cambia si se reescribe el texto.
- **Sin firma no se manda firma:** "Pagar" con el canvas vacío va directo a `POST /pago`, y el 409 `firma_requerida` lo decide el servidor, no la página.
- **El mapa es opcional:** sin internet no carga Leaflet; la página avisa y el pedido se puede hacer igual (`lat` y `lng` en `null`). "Usar mi ubicación" necesita un contexto seguro (HTTPS o `localhost`): por `http` desde el celular falla, y entonces se marca el punto en el mapa.
- **Leaflet con `integrity`:** los hashes SHA-256 se verificaron descargando los dos archivos de unpkg.
- **La consulta cada 3 s solo redibuja si cambió algo** (estado o confirmaciones): si no, pisaría lo que la persona está escribiendo en el formulario.
- **Prueba de mutación manual: 7 de 7.** Cambiar `btn-pedir`, `canvas-firma`, `btn-pagar`, `btn-entregado` o `linea-de-tiempo`, servir `cliente.html` en la ruta del delivery o montar los estáticos en `/static`: todos rompieron al menos un test.

## 3. Cómo se conecta con el proyecto

```
inicio.html ──POST /pedidos──► bandeja (Paso 4) ──link──► cliente.html
cliente.html ──PUT, /firma, /pago──► API (Pasos 5-6) ──link al delivery──► delivery.html
delivery.html ──/retirado, /en-puerta, /entregado──► API (Paso 7) ◄──/recibido── cliente.html
                                    │
             data-testid ──► Appium (etapa 3) y Playwright (etapa 4)
```

- Los links que se abren son los de `GET /mensajes`: la bandeja hace de celular del cliente y del delivery.
- Los botones del delivery son las rutas del Paso 7, y cada botón aparece solo en el estado en que la máquina de estados (Paso 3) lo permite.
- Con `DEMO_DEFECTO_CONTRATO=1`, `total-estimado` muestra `NaN`; con `DEMO_DEFECTO_ZONA_HORARIA=1`, la `linea-de-tiempo` sale desordenada (Paso 8).
- El Paso 10 suma el panel central, que muestra todos los pedidos y la bandeja.

## 4. Norma o buena práctica

| Qué | Tipo | Referencia |
|---|---|---|
| Cada página responde y trae sus `data-testid` | 📘 ISTQB | [Glosario ISTQB: *smoke test*](glosario.md#smoke-test) |
| Test escrito antes de las páginas (rojo → verde) | 📘 ISTQB | [CTFL v4.0 §2.1.3 *Enfoques test-first* (TDD)](glosario.md#tdd) |
| Los dos defectos del Paso 8 se ven en la pantalla | 📘 ISTQB | [Glosario ISTQB: *defect seeding*](glosario.md#defect-seeding) |
| `data-testid` fijos y errores con su código | 📐 Norma | [ISO/IEC 25010 — Mantenibilidad › *Capacidad de ser probado*](glosario.md#capacidad-prueba) |
| `total-estimado` muestra `NaN` si el precio llega como texto | 📐 Norma | [ISO/IEC 25010 — Compatibilidad › *Interoperabilidad*](glosario.md#interoperabilidad) |
| La línea de tiempo muestra `ocurrido_en` sin reformatear | 📐 Norma | [ISO 8601 / RFC 3339](glosario.md#iso8601) |
| Leaflet desde un CDN con `integrity` | 📐 Norma | [W3C Subresource Integrity](glosario.md#sri) |
| "Usar mi ubicación" solo en un contexto seguro | 📐 Norma | [W3C Geolocation API; Secure Contexts](glosario.md#geolocalizacion) |
| Botones de 48 px de alto y de todo el ancho | 📐 Norma | [WCAG 2.2 — 2.5.8 *Target Size (Minimum)*](glosario.md#wcag-objetivo-tactil) |
| Selectores pensados para la automatización | ✅ Buena práctica | [Selectores estables (`data-testid`)](glosario.md#data-testid) |
| Diseño para 360 px primero | ✅ Buena práctica | [Mobile-first](glosario.md#mobile-first) |
| El mapa es opcional: sin internet, el pedido se hace igual | ✅ Buena práctica | [Mejora progresiva](glosario.md#mejora-progresiva) |
| "Pagar" no se deshabilita: el servidor es idempotente | ✅ Buena práctica | [Operaciones idempotentes](glosario.md#idempotencia) |
| Un test por página, parametrizado | ✅ Buena práctica | [`pytest.mark.parametrize`](glosario.md#parametrizados) |
| 7 defectos a propósito, 7 detectados | ✅ Buena práctica | [Prueba de mutación, hecha a mano](glosario.md#mutacion) |

## 5. Cómo se verifica

```bash
cd sistema-demo
.venv/Scripts/python -m pytest -q                         # 194 tests en verde (188 previos + 6)
.venv/Scripts/python -m pytest tests/test_paginas.py -v   # las páginas y sus data-testid
```

**Prueba manual** (en el navegador de la PC). Levantar el servidor con una base aparte:

```bash
DEMO_DB_PATH=data/manual.db .venv/Scripts/python -m uvicorn delivery.main:app --port 8765
```

1. Abrir `http://localhost:8765/`, poner un teléfono y tocar "Pedir".
2. Abrir `http://localhost:8765/mensajes?destino=cliente`, copiar el `link` del mensaje (`/cliente/pedido/N`) y abrirlo agregándole `http://localhost:8765` adelante.
3. Elegir cantidades, escribir la dirección, tocar el mapa y "Confirmar datos".
4. Firmar en el recuadro y "Pagar".
5. Abrir `http://localhost:8765/mensajes?destino=delivery` y abrir el link en **otra pestaña**.
6. En la del delivery: "Retiré", "Llegué a la puerta" y "Entregué". En la del cliente: "Recibí mi pedido". El estado de las dos pestañas se actualiza solo y termina en `CERRADO`.

Repetir con `DEMO_DEFECTO_CONTRATO=1` (y otra base) y verificar que `total-estimado` muestra `NaN` al elegir una cantidad. Con `DEMO_DEFECTO_ZONA_HORARIA=1`, el historial del cliente sale desordenado.

## 6. En términos técnicos (para entrevista)

> "Hice las pantallas mobile del cliente y del delivery en HTML y JavaScript plano, servidas por la misma app FastAPI. Son cascarones: leen el id de la URL y todo lo decide la API, así que las reglas no se duplican en el front. Cada elemento interactivo tiene un `data-testid` fijo que acordé de antemano con las etapas de Appium y Playwright, y los errores muestran su código para que las pruebas no dependan del texto. Diseñé la UI para que los defectos sembrados se vean: el total estimado se calcula sin convertir y da `NaN` si el contrato manda texto, y la línea de tiempo muestra las marcas sin reformatear. El botón de pagar no se deshabilita a propósito, porque el pago es idempotente en el servidor y así ese riesgo se puede probar desde la UI. El mapa es una mejora progresiva con integridad SRI, y los botones cumplen el tamaño táctil de WCAG 2.2. Un *smoke test* parametrizado cubre las tres páginas, y la mutación manual detectó 7 de 7."
