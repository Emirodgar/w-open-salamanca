#!/usr/bin/env python3
"""Descarga y estructura las fichas oficiales de los concejales de
aytosalamanca.es (Corporación municipal) en
scripts/politicos/fuentes/fichas_oficiales.json.

Cada ficha oficial publica: cargo, contacto institucional, enlaces a las
declaraciones de bienes y actividades, formación y actividad profesional.
Se guarda el texto tal como lo publica el Ayuntamiento (sin reescribirlo).

Uso:  PYTHONUTF8=1 python3 scripts/politicos/parse_fichas.py
"""
import html
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

BASE = "https://www.aytosalamanca.es"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "fuentes" / "fichas_oficiales.json"
UA = {"User-Agent": "Mozilla/5.0 (OpenSalamanca data bot; contact via opensalamanca.es)"}

# Encabezados de sección -> clave
SECCIONES = [
    (r"^Títulos? Académicos? .Oficial(es)?.$", "formacion_oficial"),
    (r"^Otros Títulos Académicos", "otros_titulos"),
    (r"^Diplomas, Cursos", "cursos_y_diplomas"),
    (r"^Actividad Profesional", "actividad_profesional"),
    (r"^Otras actividades", "otras_actividades"),
]
FECHA = re.compile(r"((19|20)\d{2}|actualidad|actualmente|null)", re.I)


def _abrir(req, intentos=5):
    """GET con reintentos: la web del Ayuntamiento devuelve 403 intermitentes a las IP de GitHub."""
    import time
    import urllib.error
    ultimo = None
    for n in range(intentos):
        try:
            return urllib.request.urlopen(req, timeout=90).read()
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code not in (403, 429, 500, 502, 503, 504):
                raise
        except OSError as e:
            ultimo = e
        time.sleep(15 * (n + 1))
    raise ultimo


def get(url):
    return _abrir(urllib.request.Request(url, headers=UA)).decode("utf8", "replace")


def texto_lineas(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", h))
    return [re.sub(r"\s+", " ", l).strip() for l in t.split("\n") if l.strip()]


def entradas(lineas):
    """Agrupa líneas en entradas 'título — entidad — periodo' usando el separador '-'."""
    # Regla: una línea que NO va precedida de «-» abre una entrada nueva, salvo
    # que sea solo una fecha corta (se une a la entrada anterior).
    out, cur, tras_guion = [], [], False
    for l in lineas:
        if l == "-":
            tras_guion = True
            continue
        solo_fecha = len(l) < 32 and bool(FECHA.search(l)) and not re.search(r"[a-z]{4,}", re.sub(r"(Desde|Hasta|hasta|actualidad|Actualmente|Actualidad|desde|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|Junio|Mayo|Enero|Octubre|Noviembre|Entre|años|Durante|de|y)", "", l))
        if cur and not tras_guion and not solo_fecha:
            out.append(cur)
            cur = []
        cur.append(l)
        tras_guion = False
    if cur:
        out.append(cur)
    res = []
    for e in out:
        e = [x for x in e if x.lower() != "null"]
        if e:
            res.append(" — ".join(e))
    return res


def parse(url):
    raw = get(url)
    decl = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*(Declaraci[^<]+?)\s*</a>', raw, flags=re.S)
    L = texto_lineas(raw)
    i = max(k for k, l in enumerate(L) if l == "Corporación municipal")
    j = min(k for k, l in enumerate(L) if l.startswith("Widget"))
    body = L[i + 1:j]
    d = {"url": url, "nombre_oficial": body[0]}
    k = 2
    cargo = None
    if k < len(body) and not body[k].startswith("Email") and not body[k].startswith("Patrimonio"):
        cargo = body[k]
        k += 1
    d["cargo_oficial"] = cargo
    em = [body[n + 1] for n, l in enumerate(body) if l.startswith("Email")]
    d["email"] = em[0] if em else None
    tel = []
    for n, l in enumerate(body):
        if l.startswith("Telefono"):
            m = n + 1
            while m < len(body) and re.fullmatch(r"\d{9}", body[m]):
                tel.append(body[m])
                m += 1
    d["telefonos"] = tel
    d["declaraciones"] = [
        {"titulo": re.sub(r"\s+", " ", n).strip(), "url": u if u.startswith("http") else BASE + u}
        for u, n in decl
    ]
    # secciones
    idx = []
    for n, l in enumerate(body):
        for pat, key in SECCIONES:
            if re.search(pat, l):
                idx.append((n, key))
                break
    idx.append((len(body), None))
    for (n, key), (m, _) in zip(idx, idx[1:]):
        d.setdefault(key, []).extend(entradas(body[n + 1:m]))
    return d


def main():
    corp = get(BASE + "/corporacion-municipal")
    rutas = list(dict.fromkeys(re.findall(r'/w/d[^"\' ]+', corp)))
    data = {"descargado": str(date.today()), "fuente": BASE + "/corporacion-municipal", "fichas": {}}
    for r in rutas:
        url = BASE + r
        slug_oficial = urllib.parse.unquote(r.split("/w/")[1])
        data["fichas"][slug_oficial] = parse(url)
        print("ok", slug_oficial)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
