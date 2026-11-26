#!/usr/bin/env python3
"""Extrae las votaciones de los Plenos del mandato 2023-2027 de las actas
oficiales (texto de pdftotext) y las guarda en
scripts/politicos/pleno/fuentes/votaciones_pleno.json.

Cada acta recoge el sentido del voto POR GRUPO («el voto a favor del Grupo
Popular [14 concejales]») y por nombre para los concejales no adscritos o
con voto distinto. Aquí se extrae tal cual y se valida cada votación:

  - el recuento declarado por el acta («con 16 votos a favor») debe coincidir
    con la suma de los votos parseados;
  - los votos parseados deben sumar los concejales presentes en la cabecera.

Las votaciones que no cuadran quedan marcadas con `qa` y NO entran en las
estadísticas por persona.

Uso:
    PYTHONUTF8=1 python3 scripts/politicos/pleno/parse_actas.py CARPETA_CACHE
(CARPETA_CACHE/txt con *.txt y *.url generados por descargar_actas.py)
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fuentes" / "votaciones_pleno.json"

MESES = {m: i + 1 for i, m in enumerate("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split())}


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()


OCR_DIR = Path(__file__).resolve().parent / "fuentes" / "ocr"


def limpiar(t):
    """Quita pies de página y sellos que cortan las frases (CSV, Plaza Mayor, Tel., ****)."""
    out = []
    for ln in t.split(chr(10)):
        if re.search(r"Plaza Mayor n|cotejarcsv|Tel\.: \+34|ayuntamiento@aytosalamanca|www\.aytosalamanca|^\s*CSV:|^\s*Verificable|P.g\. \d+ de \d+|^\s*\*{5,}", ln):
            continue
        out.append(ln.replace(chr(12), ""))
    return chr(10).join(out)


# clave normalizada (apellidos) -> slug de ficha (None = persona sin ficha)
PERSONAS = {
    "garcia carbayo": "carlos-garcia-carbayo", "parres cabrera": "almudena-parres-cabrera",
    "rodriguez lopez": "miryam-rodriguez-lopez", "carabias acosta": "jose-fernando-carabias-acosta",
    "rodriguez alonso": "fernando-javier-rodriguez-alonso", "seguin kattan": "maria-del-carmen-seguin-kattan",
    "molina martinez": "angel-molina-martinez", "coca sanchez": "maria-jose-coca-sanchez",
    "villar gutierrez": "maria-de-la-vega-villar", "fernandez silva": "angel-fernandez-silva",
    "martin parra": "roberto-martin-parra", "macias tello": "maria-isabel-macias-tello",
    "sanchez arevalo": "luis-sanchez-arevalo", "gomez barthe": "cesar-gomez-barthe-celada",
    "martinez cordoba": None, "santa maria trigo": "maria-jesus-santa-maria-trigo",
    "fuentes chaves": "maria-del-mar-fuentes-chaves", "frances sanchez": "fidel-frances-sanchez",
    "mateos crespo": "jose-luis-mateos-crespo", "sanchez sanchez": "elvira-sanchez-sanchez",
    "collados grande": "jose-maria-collados-grande", "garcia gomez": "maria-garcia-gomez",
    "sanchez gomez": "maria-sanchez-gomez", "antolin montero": "alvaro-antolin-montero",
    "garcia meilan": "juan-jose-garcia-meilan", "perez de la sota": "alejandro-miguel-perez-de-la-sota",
    "carpio perez": "maria-de-los-angeles-carpio-perez", "rivas serrano": "ignacio-javier-rivas-serrano",
    "magdalena miguel": None,
}
# alias de menciones individuales en las cláusulas de voto
ALIAS_VOTO = {"carpio": "carpio perez", "perez de la sota": "perez de la sota", "rivas": "rivas serrano",
              "mateos": "mateos crespo", "magdalena": "magdalena miguel"}
GRUPOS = {"popular": "PP", "socialista": "PSOE", "vox": "Vox", "mixto": "Mixto", "ciudadanos": "Cs"}


def sesion_meta(t, nombre):
    cab = re.sub(r"\s+", " ", t[:4000])
    m = re.search(r"SESI[ÓO]N\s+(ORDINARIA|EXTRAORDINARIA(?:\s+Y\s+URGENTE)?)\s+N[UÚ]M\.?\s*(\d+)\s*/\s*(\d{4}).{0,200}?EL\s+D[ÍI]A\s+(\d{1,2})\s+DE\s+([A-ZÁÉÍÓÚ]+)\s+DE\s+(\d{4})", cab, re.I)
    if not m:
        m2 = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", cab, re.I)
        return None if not m2 else {"tipo": "desconocido", "numero": None, "fecha": f"{m2.group(3)}-{MESES[m2.group(2).lower()]:02d}-{int(m2.group(1)):02d}"}
    tipo, num, anio, d, mes, y = m.groups()
    return {"tipo": tipo.lower(), "numero": f"{int(num)}/{anio}", "fecha": f"{y}-{MESES[mes.lower()]:02d}-{int(d):02d}"}


GRUPO_DE = {}
for _k in ["garcia carbayo", "parres cabrera", "rodriguez lopez", "carabias acosta", "rodriguez alonso", "seguin kattan",
           "molina martinez", "coca sanchez", "villar gutierrez", "fernandez silva", "martin parra", "macias tello",
           "sanchez arevalo", "gomez barthe", "martinez cordoba"]:
    GRUPO_DE[_k] = "PP"
for _k in ["santa maria trigo", "fuentes chaves", "frances sanchez", "mateos crespo", "sanchez sanchez", "collados grande",
           "garcia gomez", "sanchez gomez", "antolin montero", "garcia meilan"]:
    GRUPO_DE[_k] = "PSOE"
for _k in ["rivas serrano", "perez de la sota", "carpio perez", "magdalena miguel"]:
    GRUPO_DE[_k] = "Vox"


def presentes(t):
    """Claves (apellidos normalizados) de los concejales presentes según la cabecera del acta."""
    m = re.search(r"al objeto de|convocada en forma legal|Asisten tambi", t, re.I)
    j = m.start() if m and m.start() < 8000 else 5000
    reg = re.sub(r"[ 	]+", " ", t[:j])
    # quitar a quienes excusan su asistencia
    reg = re.sub(r"(?is)(excusan? su asistencia|no asist\w+)[^\n]{0,260}(?:\n(?!\s*\n)[^\n]{0,200}){0,2}", " ", reg)
    reg = norm(re.sub(r"\s+", " ", reg))
    reg = reg.replace("perez carpio", "carpio perez")  # variante de la cabecera de algunas actas
    out = [k for k in PERSONAS if k in reg]
    if "garcia carbayo" not in out:
        out.append("garcia carbayo")  # preside la sesión
    return out


def parse_voto(a):
    """a = texto entre «Ayuntamiento Pleno» y «acuerda». Devuelve (lista de votos, unanimidad)."""
    a = re.sub(r"\s+", " ", a)
    if re.search(r"unanimidad", a, re.I):
        return [], True
    marc = list(re.finditer(r"(?:(?:el|los)\s+votos?\s+(a\s+favor|en\s+contra|en\s+blanco)|(?:la\s+)?abstenci[oó]n)", a, re.I))
    votos = []
    for n, m in enumerate(marc):
        fin = marc[n + 1].start() if n + 1 < len(marc) else len(a)
        sentido_txt = (m.group(1) or "abstención").lower()
        sentido = "favor" if "favor" in sentido_txt else "contra" if "contra" in sentido_txt else "blanco" if "blanco" in sentido_txt else "abstencion"
        chunk = a[m.end():fin]
        # grupos
        usados = []
        for g in re.finditer(r"(?:Grupos?\s+)?(Popular|Socialista|Vox|Mixto|Ciudadanos)\s*[\[(]\s*(\d+)\s*concejal", chunk, re.I):
            votos.append({"sujeto": GRUPOS[g.group(1).lower()], "tipo": "grupo", "n": int(g.group(2)), "sentido": sentido})
            usados.append(g.span())
        resto = chunk
        for s, e in sorted(usados, reverse=True):
            resto = resto[:s] + resto[e:]
        rn = norm(resto)
        for alias, clave in ALIAS_VOTO.items():
            if re.search(rf"\b{alias}\b", rn):
                votos.append({"sujeto": PERSONAS.get(clave) or clave, "tipo": "persona", "n": 1, "sentido": sentido})
    return votos, False


def parse_resultado(b):
    b = re.sub(r"\s+", " ", b)
    m = re.match(r"(?:(?:con|por)\s+(?:(\d+)\s+votos?\s+(?:en\s+)?(a favor|en contra|a favor)|unanimidad(?: de [^,]+)?),?\s*)?(.{0,160})", b, re.I)
    n, lado, resto = m.group(1), m.group(2), m.group(3)
    texto = re.split(r"(?<=\w)\.\s+(?=[A-ZÁÉÍÓÚ0-9])", resto)[0]
    return (int(n) if n else None), (lado.lower().replace("a favor", "favor").replace("en contra", "contra") if lado else None), texto.strip()


def clasifica(titulo):
    u = titulo.upper()
    prop = None
    if re.search(r"MOCI[ÓO]N\s+CONJUNTA", u):
        prop = "Conjunta"
    else:
        m = re.search(r"MOCI[ÓO]N\s+(?:DEL|DE LA)\s+(?:GRUPO\s+(?:MUNICIPAL\s+)?)?(POPULAR|SOCIALISTA|MIXTO|VOX)", u)
        if m:
            prop = {"POPULAR": "PP", "SOCIALISTA": "PSOE", "MIXTO": "Mixto", "VOX": "Vox"}[m.group(1)]
        elif re.search(r"MOCI[ÓO]N.*NO ADSCRIT", u):
            prop = "No adscrito"
        elif re.search(r"MOCI[ÓO]N.*CONCEJAL", u):
            prop = "Concejal"
    if "MOCI" in u:
        tipo = "moción"
    elif "DICTAMEN" in u:
        tipo = "dictamen"
    elif "PROPUESTA" in u:
        tipo = "propuesta"
    elif "ACTA" in u:
        tipo = "acta"
    elif "URGENCIA" in u:
        tipo = "urgencia"
    else:
        tipo = "otro"
    return tipo, prop


def parse_acta(texto, nombre, url):
    t = limpiar(texto)
    meta = sesion_meta(t, nombre) or {}
    pres = presentes(t)
    # encabezados de punto: «N.- TÍTULO», «N.  TÍTULO» o «N.M.- TÍTULO»; título en mayúsculas, a veces en varias líneas
    lineas = t.split(chr(10))
    offs, acc = [], 0
    for ln in lineas:
        offs.append(acc)
        acc += len(ln) + 1

    def mayus(x):
        L = [c for c in x if c.isalpha()]
        return bool(L) and sum(c.isupper() for c in L) / len(L) >= 0.6

    heads = []
    ult_top, ult_sub = 0, 0
    for i, ln in enumerate(lineas):
        m = re.match(r"^[ 	]{0,48}(\d{1,2})\.(\d{1,2})\s+(\S.*)$", ln)  # «9.1 MOCIÓN…» sin guion
        if not m:
            m = re.match(r"^[ 	]{0,48}(\d{1,2})(?:\.(\d{1,2}))?\s*(?:\.\s*-|\.|-)\s*(\S.*)$", ln)
        if not m:
            continue
        top, sub, l1 = int(m.group(1)), m.group(2), m.group(3).strip()
        if not mayus(l1):
            continue
        tit = [l1]
        j = i + 1
        while j < len(lineas) and len(tit) < 7:
            x = lineas[j].strip()
            if not x:
                j += 1
                continue
            if x.startswith("http") or not mayus(x) or re.match(r"^\d{1,2}(\.\d{1,2})?\s*(\.\s*-|\.)", x):
                break
            tit.append(x)
            j += 1
        titulo = re.sub(r"\s+", " ", " ".join(tit))
        if sub is None:
            if ult_top < top <= ult_top + 3 or (ult_top == 0 and top <= 3):
                ult_top, ult_sub = top, 0
            else:
                continue
        else:
            sub = int(sub)
            if top == ult_top and ult_sub < sub <= ult_sub + 3:
                ult_sub = sub
            else:
                continue
        heads.append({"pos": offs[i], "num": f"{top}" if sub is None else f"{top}.{sub}", "titulo": titulo})
    # cláusulas de voto
    claus = []
    marcas = [m.start() for m in re.finditer(r"El Excmo\. Ayuntamiento Pleno\b", t)]
    for n, st in enumerate(marcas):
        seg = t[st + len("El Excmo. Ayuntamiento Pleno"): (marcas[n + 1] if n + 1 < len(marcas) else st + 4000)][:1800]
        mm = re.search(r"\bacuerda\b[,:]?\s*", seg)
        if mm and mm.start() < 1400:
            claus.append((st, seg[:mm.start()], seg[mm.end():mm.end() + 260]))
        else:
            m2 = re.search(r",\s*(?:con|por)\s+\d+\s+votos?\b|\bse\s+(?:desestima|aprueba|rechaza|estima|acuerda)\b", seg)
            if m2 and m2.start() < 1400:
                claus.append((st, seg[:m2.start()], seg[m2.start():m2.start() + 260].lstrip(", ")))
    items = {}
    for pos, a, b in claus:
        h = None
        for hh in heads:
            if hh["pos"] <= pos:
                h = hh
        key = h["num"] if h else "?"
        if key not in items:
            titulo = h["titulo"] if h else "(sin título)"
            tipo, prop = clasifica(titulo)
            # vídeo del punto
            vid = None
            if h:
                seg = t[h["pos"]:h["pos"] + 900]
                mv = re.search(r"https://aytosalamanca\.seneca\.tv[^\s\"”]+", seg)
                vid = mv.group(0) if mv else None
            items[key] = {"punto": key, "titulo": titulo[:260], "tipo": tipo, "proponente": prop, "video": vid, "votaciones": []}
        votos, unan = parse_voto(a)
        n_decl, lado, texto = parse_resultado(b)
        suma = {"favor": 0, "contra": 0, "abstencion": 0, "blanco": 0}
        for v in votos:
            suma[v["sentido"]] += v["n"]
        pres_g = {"PP": 0, "PSOE": 0, "Vox": 0}
        for k in pres:
            pres_g[GRUPO_DE[k]] += 1
        qa, info = [], []
        if unan:
            suma = {"favor": len(pres), "contra": 0, "abstencion": 0, "blanco": 0}
        elif not votos:
            info.append("sin_votacion")
        else:
            for v in votos:
                if v["tipo"] == "grupo" and v["sujeto"] in ("PP", "PSOE") and v["n"] != pres_g[v["sujeto"]]:
                    qa.append(f"{v['sujeto']} votó con {v['n']} y hay {pres_g[v['sujeto']]} presentes")
            vox = sum(v["n"] for v in votos if (v["tipo"] == "grupo" and v["sujeto"] in ("Vox", "Mixto")) or v["tipo"] == "persona")
            if vox != pres_g["Vox"]:
                qa.append(f"Vox/Mixto/no adscritos votaron {vox} y hay {pres_g['Vox']} presentes")
            if n_decl is not None and lado in suma and suma[lado] != n_decl:
                qa.append(f"{lado} declarado {n_decl} != parseado {suma[lado]}")
        low = texto.lower()
        tv = "urgencia" if "urgencia" in low else "enmienda" if "enmienda" in low else "fondo"
        if re.search(r"darse por enterado|queda enterado|toma de conocimiento", low):
            info.append("enterado")
        resultado = "rechazado" if re.search(r"desestim|rechaz|deneg", low) else "aprobado"
        if not unan and votos and suma["favor"] <= suma["contra"] and not qa:
            resultado = "rechazado"
        items[key]["votaciones"].append({
            "ambito": tv, "unanimidad": unan, "votos": votos, "recuento": suma,
            "declarado": {"n": n_decl, "lado": lado}, "resultado": resultado, "texto": texto[:200], "qa": qa, "info": info, "clausula": re.sub(r"\s+", " ", a)[:700] if qa else None})
    return {"url": url, "nombre_fichero": nombre, **meta, "presentes": pres, "items": list(items.values())}


def main(cache):
    cache = Path(cache) / "txt"
    sesiones = []
    for f in sorted(cache.glob("*.txt")):
        u = (cache / (f.stem + ".url")).read_text(encoding="utf-8").split("\n")
        texto = f.read_text(encoding="utf-8")
        if len(texto.strip()) < 500:
            # Acta escaneada sin capa de texto: se usa el texto de OCR versionado (ocr_actas.py), si existe.
            ocr = OCR_DIR / (f.stem + ".txt")
            if ocr.exists():
                texto = ocr.read_text(encoding="utf-8")
        if re.match(r"\s*JUNTA DE GOBIERNO LOCAL", texto):
            print(f.stem, "OMITIDO: no es un acta del Pleno (convocatoria de la Junta de Gobierno Local)")
            continue
        s = parse_acta(texto, u[1], u[0])
        sesiones.append(s)
        nv = sum(len(i["votaciones"]) for i in s["items"])
        bad = sum(1 for i in s["items"] for v in i["votaciones"] if v["qa"])
        print(f.stem, s.get("fecha"), s.get("tipo"), s.get("numero"), "presentes", len(s["presentes"]), "items", len(s["items"]), "votaciones", nv, "qa", bad)
    sesiones.sort(key=lambda s: s.get("fecha") or "")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"sesiones": sesiones}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
