# Pasos del sistema demo

Bitácora de construcción del sistema demo "delivery de comidas" (ficticio). Hay un archivo por cada paso (tarea del plan) que explica:

1. **Qué hicimos**: archivos y piezas que se agregaron.
2. **Por qué**: el problema que resuelve.
3. **Cómo se conecta con el proyecto**: quién usa esta pieza y en qué pasos siguientes.
4. **Norma o buena práctica**: con qué estándar se alinea.

> Prácticas alineadas al syllabus ISTQB CTFL v4.0.

**Versión visual:** [`pasos.html`](pasos.html). Se abre con doble clic. El botón **▶ Presentación** (o la tecla `P`) lo pasa a diapositivas a pantalla completa: ← → para avanzar y `Esc` para salir.

## Leyenda de etiquetas

Explicación completa de cada etiqueta, con dónde se aplica en el proyecto: [glosario.md](glosario.md).

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
     catálogo       pedidos + estados       mensajes (WhatsApp simulado)
     Paso 2         Pasos 3–7               Paso 4
          └──────────────┬───────────────────────┘
                         ▼
                 SQLite (db.py)          ◄── Paso 2
```
