#!/usr/bin/env python3
"""OCR de las actas del Pleno que el Ayuntamiento publica como imagen escaneada.

Las actas escaneadas no tienen capa de texto (pdftotext devuelve vacío). Este proceso PUNTUAL las
lee con RapidOCR (modelo PP-OCRv5 latino, reconoce tildes y ñ) y guarda el texto en
scripts/politicos/pleno/fuentes/ocr/<uuid-del-documento>.txt, con una sangría aproximada a la de
`pdftotext -layout` para que parse_actas.py las trate igual. El texto OCR se versiona (el acta ya
no cambia) y parse_actas.py lo usa solo cuando el PDF no trae texto.

Dependencias (solo para este proceso): pip install pymupdf rapidocr onnxruntime numpy
Uso:  PYTHONUTF8=1 python3 scripts/politicos/pleno/ocr_actas.py DOC.pdf [DOC2.pdf ...]
      (el nombre del PDF debe ser el uuid del documento, como lo deja descargar_actas.py)
"""
import sys
from pathlib import Path

import fitz
import numpy as np
from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR

OUT = Path(__file__).resolve().parent / "fuentes" / "ocr"
DPI = 200
PT_POR_COLUMNA = 4.5      # anchura media de carácter de pdftotext -layout


def pagina_a_texto(ocr, pag):
    pix = pag.get_pixmap(dpi=DPI)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    r = ocr(img)
    if r.txts is None:
        return ""
    k = 72 / DPI
    items = []
    for box, txt in zip(r.boxes, r.txts):
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        items.append(((min(ys) + max(ys)) / 2 * k, min(xs) * k, (max(ys) - min(ys)) * k, txt))
    items.sort()
    lineas, cur, ycur, alto = [], [], None, 0
    for y, x, h, t in items:
        if ycur is None or abs(y - ycur) > max(alto, h) * 0.6:
            if cur:
                lineas.append(cur)
            cur, ycur, alto = [], y, h
        cur.append((x, t))
    if cur:
        lineas.append(cur)
    out = []
    for l in lineas:
        l.sort()
        s, col = "", 0
        for x, t in l:
            c = int(x / PT_POR_COLUMNA)
            s += " " * max(c - col, 1 if s else c) + t
            col = len(s)
        out.append(s.rstrip())
    return "\n".join(out)


def main(pdfs):
    OUT.mkdir(parents=True, exist_ok=True)
    ocr = RapidOCR(params={"Rec.lang_type": LangRec.LATIN, "Rec.ocr_version": OCRVersion.PPOCRV5,
                           "Rec.model_type": ModelType.MOBILE})
    for ruta in pdfs:
        ruta = Path(ruta)
        doc = fitz.open(ruta)
        parcial = OUT / (ruta.stem + ".partial")
        FF = chr(12)
        pags = open(parcial, encoding="utf-8", newline="").read().split(FF) if parcial.exists() else []
        for n in range(len(pags), len(doc)):
            pags.append(pagina_a_texto(ocr, doc[n]))
            with open(parcial, "w", encoding="utf-8", newline="\n") as f:
                f.write(FF.join(pags))
            print(ruta.stem[:8], f"{n + 1}/{len(doc)}", flush=True)
        with open(OUT / (ruta.stem + ".txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(FF.join(pags) + FF)
        parcial.unlink()


if __name__ == "__main__":
    main(sys.argv[1:])
