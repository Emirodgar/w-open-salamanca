#!/usr/bin/env python3
"""Descarga las actas de los Plenos del mandato 2023-2027 desde
aytosalamanca.es (Transparencia > Actas de los Plenos Municipales) y las
convierte a texto con pdftotext.

Las actas son documentos públicos «anonimizados» del propio Ayuntamiento. Se
guardan en una carpeta de caché FUERA del repositorio (contenido externo, no
se versiona).

Uso:
    PYTHONUTF8=1 python3 scripts/politicos/pleno/descargar_actas.py CARPETA_CACHE
"""
import html
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://www.aytosalamanca.es"
LISTADO = BASE + "/w/actas-de-los-plenos-municipales"
UA = {"User-Agent": "Mozilla/5.0 (OpenSalamanca; datos abiertos)"}
# Primer pleno de trabajo del mandato: 27-06-2023 (el de constitución, 17-06-2023, es el anterior en el listado)
FECHA_MIN = "2023-06-17"


def get(url, binario=False):
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
    return d if binario else d.decode("utf8", "replace")


def fecha_de_nombre(nombre):
    """Intenta sacar la fecha del nombre; None si no se puede (se decidirá con el texto)."""
    n = urllib.parse.unquote(nombre).replace("+", " ")
    m = re.search(r"(\d{2})[-_](\d{2})[-_](\d{2,4})", n)
    if m:
        d, mo, y = m.groups()
        y = ("20" + y) if len(y) == 2 else y
        return f"{y}-{mo}-{d}"
    m = re.search(r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)", n)  # 220324
    if m:
        d, mo, y = m.groups()
        return f"20{y}-{mo}-{d}"
    m = re.search(r"(\d{1,2})_(\d{2})\b", n)  # 12_26 -> nº/año (sin fecha)
    return None


def main(cache):
    cache = Path(cache)
    (cache / "pdf").mkdir(parents=True, exist_ok=True)
    (cache / "txt").mkdir(parents=True, exist_ok=True)
    pagina = get(LISTADO)
    urls = list(dict.fromkeys(html.unescape(u) for u in re.findall(r'href="(/documents/[^"]+)"', pagina)))
    print("documentos en el listado:", len(urls))
    # El listado va de más reciente a más antiguo: el acta del 17-06-2023 es la última del mandato.
    seleccion = []
    for u in urls:
        nombre = urllib.parse.unquote(u.split("?")[0].split("/")[-2])
        seleccion.append((u, nombre))
        if re.search(r"17-06-2023", nombre):  # constitución del Pleno: último de la lista a descargar
            break
    print("actas del mandato a descargar:", len(seleccion))
    for i, (u, nombre) in enumerate(seleccion):
        clave = f"{i:03d}"
        pdf = cache / "pdf" / f"{clave}.pdf"
        txt = cache / "txt" / f"{clave}.txt"
        (cache / "txt" / f"{clave}.url").write_text(BASE + u + "\n" + nombre + "\n", encoding="utf-8")
        if not pdf.exists():
            pdf.write_bytes(get(BASE + u, binario=True))
            time.sleep(0.6)
        if not txt.exists():
            subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", str(pdf), str(txt)], check=True)
        print(clave, nombre[:70], pdf.stat().st_size)


if __name__ == "__main__":
    main(sys.argv[1])
