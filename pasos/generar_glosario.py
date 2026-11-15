"""Genera las fichas por concepto a partir de pasos/terminos.json (fuente única).

Actualiza:
  - pasos.html: los datos TERMINOS del modal y el data-term de cada etiqueta de las tablas.
  - glosario.md: la sección "Fichas por concepto".
  - paso-NN-*.md: la columna Referencia de la tabla de normas enlaza a su ficha.

Uso (desde la raíz del repo):  python pasos/generar_glosario.py
Es idempotente: correrlo dos veces deja los archivos igual.
"""

import json
import re
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
ETIQUETA = {"istqb": "📘 ISTQB", "norma": "📐 Norma", "bp": "✅ Buena práctica"}
SECCION = {"istqb": "📘 ISTQB", "norma": "📐 Normas", "bp": "✅ Buenas prácticas"}


def leer(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def escribir(p: Path, texto: str) -> None:
    p.write_text(texto, encoding="utf-8", newline="\n")


def reemplazar_entre(texto: str, inicio: str, fin: str, nuevo: str, archivo: str) -> str:
    patron = re.compile(re.escape(inicio) + r".*?" + re.escape(fin), re.S)
    if not patron.search(texto):
        sys.exit(f"Faltan los marcadores {inicio} … {fin} en {archivo}")
    return patron.sub(lambda _: inicio + nuevo + fin, texto, count=1)


def validar(datos: dict) -> None:
    terminos, filas = datos["terminos"], datos["filas"]
    for paso, ids in filas.items():
        for tid in ids:
            if tid not in terminos:
                sys.exit(f"Paso {paso}: el id '{tid}' no existe en 'terminos'")
            if paso not in terminos[tid]["pasos"]:
                sys.exit(f"'{tid}' se usa en el paso {paso} pero no explica cómo se aplica ahí")
    usados = {t for ids in filas.values() for t in ids}
    sobrantes = set(terminos) - usados
    if sobrantes:
        sys.exit(f"Términos sin uso en ninguna tabla: {sorted(sobrantes)}")


def ids_en_orden(filas: dict) -> list[str]:
    return [tid for paso in sorted(filas, key=int) for tid in filas[paso]]


# ---------- pasos.html ----------

def generar_html(datos: dict) -> None:
    p = DIR / "pasos.html"
    html = leer(p)
    orden = ids_en_orden(datos["filas"])
    patron = re.compile(r'<td><span class="tag (istqb|norma|bp)"(?: data-term="[^"]*")?>')
    encontradas = patron.findall(html)
    if len(encontradas) != len(orden):
        sys.exit(f"pasos.html tiene {len(encontradas)} filas con etiqueta y terminos.json {len(orden)}")
    it = iter(orden)

    def sello(m: re.Match) -> str:
        tid = next(it)
        tipo = datos["terminos"][tid]["tipo"]
        if tipo != m.group(1):
            sys.exit(f"'{tid}' es {tipo} pero la etiqueta de su fila en pasos.html es {m.group(1)}")
        return f'<td><span class="tag {tipo}" data-term="{tid}">'

    html = patron.sub(sello, html)
    js = json.dumps(datos["terminos"], ensure_ascii=False, separators=(",", ":"))
    js = js.replace("</", "<\\/")  # no cerrar el <script> por accidente
    html = reemplazar_entre(html, "/* TERMINOS:INICIO */", "/* TERMINOS:FIN */",
                            f"const TERMINOS = {js};", "pasos.html")
    escribir(p, html)


# ---------- glosario.md ----------

def generar_glosario(datos: dict) -> None:
    p = DIR / "glosario.md"
    partes = ["\n"]
    for tipo in ("istqb", "norma", "bp"):
        items = [(tid, t) for tid, t in datos["terminos"].items() if t["tipo"] == tipo]
        partes.append(f"### {SECCION[tipo]}\n\n")
        for tid, t in items:
            partes.append(f'<a id="{tid}"></a>\n\n#### {t["titulo"]}\n\n')
            partes.append(f'{ETIQUETA[tipo]} · **Referencia:** {t["ref"]}\n\n')
            partes.append(f'{t["que"]}\n\n**En este proyecto:**\n\n')
            for paso in sorted(t["pasos"], key=int):
                partes.append(f'- [Paso {paso}]({archivo_paso(paso)}): {t["pasos"][paso]}\n')
            partes.append("\n")
    md = reemplazar_entre(leer(p), "<!-- TERMINOS:INICIO -->", "<!-- TERMINOS:FIN -->",
                          "".join(partes), "glosario.md")
    escribir(p, md)


def archivo_paso(paso: str) -> str:
    encontrados = sorted(DIR.glob(f"paso-{int(paso):02d}-*.md"))
    if not encontrados:
        sys.exit(f"No existe pasos/paso-{int(paso):02d}-*.md")
    return encontrados[0].name


# ---------- paso-NN-*.md ----------

FILA_MD = re.compile(r"^\| (?P<que>.+?) \| (?P<tag>📘 ISTQB|📐 Norma|✅ Buena práctica) \| (?P<ref>.+?) \|$")
LINK = re.compile(r"^\[(?P<txt>.*)\]\(glosario\.md#[\w-]+\)$")


def generar_pasos_md(datos: dict) -> None:
    for paso, ids in datos["filas"].items():
        p = DIR / archivo_paso(paso)
        lineas = leer(p).split("\n")
        filas = [k for k, l in enumerate(lineas) if FILA_MD.match(l)]
        if len(filas) != len(ids):
            sys.exit(f"{p.name}: {len(filas)} filas con etiqueta y terminos.json {len(ids)}")
        for k, tid in zip(filas, ids):
            m = FILA_MD.match(lineas[k])
            ref = m["ref"]
            lm = LINK.match(ref)
            if lm:
                ref = lm["txt"]
            lineas[k] = f'| {m["que"]} | {m["tag"]} | [{ref}](glosario.md#{tid}) |'
        escribir(p, "\n".join(lineas))


def main() -> None:
    datos = json.loads(leer(DIR / "terminos.json"))
    validar(datos)
    generar_html(datos)
    generar_glosario(datos)
    generar_pasos_md(datos)
    print(f"OK: {len(datos['terminos'])} fichas, {len(ids_en_orden(datos['filas']))} filas enlazadas.")


if __name__ == "__main__":
    main()
