# Pasos del sistema demo

Bitácora de construcción del sistema demo "delivery de comidas" (ficticio). Hay un archivo por cada paso (tarea del plan) que explica:

1. **Qué hicimos**: archivos y piezas que se agregaron.
2. **Por qué**: el problema que resuelve.
3. **Cómo se conecta con el proyecto**: quién usa esta pieza y en qué pasos siguientes.
4. **Norma o buena práctica**: con qué estándar se alinea.

> Prácticas alineadas al syllabus ISTQB CTFL v4.0.

**Versión visual:** [`pasos.html`](pasos.html). Se abre con doble clic. El botón **▶ Presentación** (o la tecla `P`) lo pasa a diapositivas a pantalla completa: ← → para avanzar y `Esc` para salir.

## Leyenda de etiquetas

Cada fila de las tablas de normas lleva a la **ficha de su concepto** (qué es, referencia exacta y en qué pasos se aplica): en `pasos.html` tocando la etiqueta, y en los `.md` con el enlace de la columna Referencia, que lleva a [glosario.md](glosario.md#fichas-por-concepto).

**Cómo agregar conceptos en un paso nuevo:** sumar la ficha en [`terminos.json`](terminos.json) (y el id de cada fila en `filas`), y después correr `python pasos/generar_glosario.py`. El script actualiza `pasos.html`, `glosario.md` y los enlaces de los `paso-NN.md`, y se detiene con un error si algo no coincide.

| Etiqueta | Significado |
|---|---|
| 📘 **ISTQB** | Término o técnica del syllabus ISTQB CTFL v4.0. |
| 📐 **Norma** | Estándar formal publicado: ISO/IEC, RFC de la IETF, especificación OpenAPI, etc. |
| ✅ **Buena práctica** | Convención de la industria muy aceptada, pero que no es una norma formal. |

## Índice

| Paso | Tema | Commit |
|---|---|---|
| [1](paso-01-esqueleto-y-salud.md) | Esqueleto del proyecto, git y `GET /salud` | `feat(demo): esqueleto FastAPI con /salud` |
| [2](paso-02-base-de-datos-y-catalogo.md) | Base SQLite y catálogo (`GET /platos`) | `feat(demo): base SQLite y catálogo` |
| [3](paso-03-maquina-de-estados.md) | Máquina de estados del pedido | `feat(demo): máquina de estados del pedido` |
| [4](paso-04-crear-pedido-y-mensajes.md) | Crear pedido, reloj, eventos y WhatsApp simulado | `feat(demo): crear pedido con link por WhatsApp simulado` |
| [5](paso-05-cargar-datos-y-cotizacion.md) | Cargar datos y cotización (`PUT /pedidos/{id}`) | `feat(demo): carga de datos y cotización calculada en el servidor` |
| [6](paso-06-firma-pago-y-asignacion.md) | Firma, pago idempotente y asignación al delivery | `feat(demo): firma, pago idempotente y asignación al delivery` |
| [7](paso-07-entrega-cierre-y-cancelacion.md) | Entrega, doble confirmación, cierre y cancelación | `feat(demo): entrega, cierre y cancelación` |
| [8](paso-08-defectos-sembrados.md) | Defectos sembrados: zona horaria y contrato | `feat(demo): defectos sembrados activables por variable de entorno` |
| [9](paso-09-paginas-cliente-y-delivery.md) | Páginas mobile del cliente y del delivery | `feat(demo): páginas mobile del cliente y del delivery` |

## Mapa general (hacia dónde vamos)

```
Cliente (página web / app)        Delivery (página)        Panel central
          │                              │                        │
          └──────────────┬───────────────┴────────────────────────┘
                         ▼
              API FastAPI  (crear_app)   ◄── Paso 1
                         │
          ┌──────────────┼───────────────────────┐
          ▼              ▼                       ▼
     catálogo       estados → pedidos       mensajes (WhatsApp simulado)
     Paso 2         Paso 3    Pasos 4–7     Paso 4
          └──────────────┬───────────────────────┘
                         ▼
                 SQLite (db.py)          ◄── Paso 2
```
