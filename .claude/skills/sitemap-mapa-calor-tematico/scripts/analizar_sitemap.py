#!/usr/bin/env python3
"""
analizar_sitemap.py
--------------------
Analiza un sitemap XML de un medio digital con URLs amigables y genera un
JSON con un "mapa de calor" temático: qué secciones han concentrado la
actividad editorial en el periodo cubierto por el sitemap, su evolución por
día, y un conjunto de "conceptos destacados" (temas agrupados, no una nube
de palabras sueltas) con ejemplos reales de titulares para dar una visión
rápida de lo ocurrido. El resumen en texto no menciona el nombre del medio.

Uso:
    python analizar_sitemap.py entrada.xml salida.json \
        --url-base "https://www.dominio-del-medio.es" \
        --excluir-secciones "tu-gaceta,nacional"

Solo usa librerías estándar de Python (no requiere pip install).
"""

import argparse
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. Extracción de <url>...</loc>/<lastmod>...</url>
# ---------------------------------------------------------------------------
# Cada bloque <url>...</url> se aísla primero como texto (no greedy, así no
# se cuela en el siguiente bloque), y luego se buscan <loc>/<lastmod> DENTRO
# de ese texto. Esto tolera con seguridad las etiquetas de extensión que
# muchos sitemaps de noticias insertan entre <lastmod> y el cierre </url>
# (p.ej. <news:news>...</news:news>, <image:image>...</image:image>).
URL_BLOCK_RE = re.compile(r"<url>(?P<block>.*?)</url>", re.IGNORECASE | re.DOTALL)
LOC_RE = re.compile(r"<loc>(.*?)</loc>", re.IGNORECASE | re.DOTALL)
LASTMOD_RE = re.compile(r"<lastmod>(.*?)</lastmod>", re.IGNORECASE | re.DOTALL)

CONTENT_TYPE_SUFFIXES = {
    "nt": "noticia",
    "ga": "galería",
    "di": "directo / en vivo",
    "aud": "audio / podcast",
    "vd": "vídeo",
    "cr": "crónica",
    "en": "entrevista",
    "op": "opinión",
}

FILENAME_RE = re.compile(
    r"^(?P<slug>.+?)-(?P<timestamp>\d{12,14})-(?P<tipo>[a-z]{2,4})\.html?$"
)

STOPWORDS_ES = set("""
a al algo algunas algunos ante antes como con contra cual cuando de del desde
donde durante e el ella ellas ellos en entre era erais eramos eran eras eres
es esa esas ese eso esos esta estaba estabais estabamos estaban estabas estad
estada estadas estado estados estais estamos estan estar estara estaran
estaras estare estareis estaremos estaria estariais estariamos estarian
estarias estas este esto estos estoy estuve estuviera estuvierais
estuvieramos estuvieran estuvieras estuvieron estuviese estuvieseis
estuviesemos estuviesen estuvieses estuvimos estuviste estuvisteis estuvo
etc fue fuera fuerais fueramos fueran fueras fueron fuese fueseis fuesemos
fuesen fueses fui fuimos gracias ha habida habidas habido habidos habiendo
habla hablan hace hacen hacia hago han has hasta hay haya hayamos hayan
hayas he hemos hicieron hizo hoy la las le les lo los mas me mi mientras
mia mias mio mios mis mucho muchos muy nada ni no nos nosotras nosotros
nuestra nuestras nuestro nuestros o os otra otras otro otros para pero
pero pese poca pocas poco pocos podemos podra podran podria porque pudo
pueda puede pueden puedo pues que quien quienes quiza se sea sean segun
ser sera seran seria si sido siendo siete sin sino sobre sois solo somos
son soy su sus suya suyas suyo suyos tal tambien tanto te tendra tendran
tenemos tener tengo ti tiene tienen todas todo todos tras tu tus tuve tuya
tuyas tuyo tuyos un una unas uno unos usted ustedes va vais vamos van vas
ve veces ver vez vosotras vosotros voy y ya yo tras deja dejan sigue
siguen vuelve vuelven llega llegan puede pueden mas años anos ano dias dia
segun tras contra cada nueva nuevo nuevos nuevas cinco tres dos primer
primero primera ultimo ultima ultimos ultimas gran mayor menor
enero febrero marzo abril mayo junio julio agosto septiembre octubre
noviembre diciembre lunes martes miercoles jueves viernes sabado domingo
noticias noticia hoy escucha boletin vineta tras mejor buen buena grande
""".split())


def dominio_compacto(url_base: str) -> str:
    """Devuelve el dominio en minúsculas y sin separadores, p.ej.
    'https://www.lagacetadesalamanca.es' -> 'lagacetadesalamancaes'.
    Se usa para detectar por subcadena palabras derivadas del nombre del
    medio (p.ej. 'salamanca' o 'gaceta' dentro de 'lagacetadesalamanca'),
    ya que el dominio suele ser una única palabra pegada, no varias."""
    texto = re.sub(r"https?://|www\.", "", url_base, flags=re.IGNORECASE)
    return re.sub(r"[^a-záéíóúñ]", "", texto.lower())


def es_palabra_del_sitio(palabra: str, dominio: str) -> bool:
    """True si la palabra parece derivada del nombre/dominio del medio y por
    tanto no aporta como tema (p.ej. 'salamanca' dentro de
    'lagacetadesalamancaes'). Exige longitud mínima para evitar falsos
    positivos con palabras cortas que casualmente sean subcadena."""
    return len(palabra) >= 5 and dominio and palabra in dominio


def descargar_o_leer(origen: str) -> str:
    """Lee el contenido del sitemap desde un fichero local o una URL http(s).
    Dentro de una conversación de Claude, si el dominio no está accesible
    por red desde `bash`, usa la herramienta web_fetch y guarda el
    resultado en un fichero antes de invocar este script."""
    if origen.startswith("http://") or origen.startswith("https://"):
        try:
            import urllib.request

            req = urllib.request.Request(
                origen, headers={"User-Agent": "Mozilla/5.0 (compatible; SmartupBot/1.0)"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            print(f"[aviso] No se pudo descargar {origen} directamente: {exc}", file=sys.stderr)
            print("       Usa web_fetch para obtener el XML y pásalo como fichero local.", file=sys.stderr)
            raise
    with open(origen, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def parsear_urls(xml_text: str):
    entradas = []
    for m in URL_BLOCK_RE.finditer(xml_text):
        block = m.group("block")
        loc_m = LOC_RE.search(block)
        if not loc_m:
            continue
        loc = loc_m.group(1).strip()
        lastmod_m = LASTMOD_RE.search(block)
        lastmod = lastmod_m.group(1).strip() if lastmod_m else ""
        if loc:
            entradas.append({"loc": loc, "lastmod": lastmod})
    return entradas


def parsear_fecha(lastmod: str):
    if not lastmod:
        return None
    try:
        dt = datetime.fromisoformat(lastmod)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def titulo_legible(slug: str) -> str:
    """Reconstruye una versión legible del slug para usarla como ejemplo de
    titular (aproximación a partir de la URL, no el titular real)."""
    texto = slug.replace("-", " ").strip()
    return texto[:1].upper() + texto[1:] if texto else texto


def analizar_url(loc: str, url_base: str, dominio: str):
    path = loc.replace(url_base.rstrip("/"), "", 1) if url_base else loc
    path = re.sub(r"^https?://[^/]+", "", path)
    partes = [p for p in path.split("/") if p]
    if not partes:
        return None

    seccion = partes[0]
    subseccion = partes[1] if len(partes) >= 3 else None
    archivo = partes[-1]

    m = FILENAME_RE.match(archivo)
    if m:
        slug = m.group("slug")
        tipo_codigo = m.group("tipo").lower()
    else:
        slug = re.sub(r"\.html?$", "", archivo)
        tipo_codigo = None

    tipo = CONTENT_TYPE_SUFFIXES.get(tipo_codigo, "noticia")

    palabras_crudas = [w for w in slug.split("-") if w and not w.isdigit()]
    palabras = [
        w for w in palabras_crudas
        if w.lower() not in STOPWORDS_ES
        and not es_palabra_del_sitio(w.lower(), dominio)
        and len(w) > 2
    ]

    return {
        "seccion": seccion,
        "subseccion": subseccion,
        "tipo": tipo,
        "palabras": palabras,
        "titulo": titulo_legible(slug),
    }


# ---------------------------------------------------------------------------
# 2. Conceptos destacados (agrupación de palabras que aparecen juntas)
# ---------------------------------------------------------------------------
# En lugar de listar palabras sueltas por frecuencia (una nube de tags no
# aporta contexto), se agrupan palabras que tienden a aparecer JUNTAS en el
# mismo titular. Cada grupo se convierte en un "concepto" con una etiqueta,
# el número de piezas relacionadas, el rango de fechas y 2-3 titulares reales
# como evidencia, para que un visitante entienda de un vistazo qué ha pasado.

def construir_conceptos_destacados(
    articulos, min_frecuencia=3, min_coocurrencia=2, top_n=8, umbral_plantilla=4
):
    # 0) Detectar titulares "de plantilla": el mismo texto reconstruido se
    # repite casi a diario (viñetas, boletines, secciones fijas). Aportan
    # ruido a los conceptos aunque sean piezas legítimas, así que sus
    # palabras no entran en el cálculo de conceptos (pero sí siguen
    # contando en por_seccion / heatmap).
    conteo_titulos = Counter(art["titulo"].lower() for art in articulos)
    es_plantilla = lambda art: conteo_titulos[art["titulo"].lower()] >= umbral_plantilla

    articulos_utiles = [a for a in articulos if not es_plantilla(a)]
    if not articulos_utiles:
        return []

    freq_palabra = Counter()
    palabra_a_articulos = defaultdict(set)
    for i, art in enumerate(articulos_utiles):
        for w in set(art["palabras"]):
            freq_palabra[w] += 1
            palabra_a_articulos[w].add(i)

    salientes = {w for w, c in freq_palabra.items() if c >= min_frecuencia}
    if not salientes:
        return []

    usados = set()
    clusters = []  # cada uno: {"palabras": [...], "articulos": set(idx)}

    # 1) Pase de FRASES: pares de palabras contiguas en el slug (más
    # precisas que la simple co-ocurrencia porque capturan nombres propios
    # y expresiones — "santa marta", "reina sofia", "casetas feria"...).
    freq_bigramas = Counter()
    bigrama_a_articulos = defaultdict(set)
    for i, art in enumerate(articulos_utiles):
        vistos_en_articulo = set()
        palabras = art["palabras"]
        for w1, w2 in zip(palabras, palabras[1:]):
            if w1 in salientes and w2 in salientes and w1 != w2:
                par = (w1, w2)
                if par not in vistos_en_articulo:
                    vistos_en_articulo.add(par)
                    freq_bigramas[par] += 1
                    bigrama_a_articulos[par].add(i)

    for (w1, w2), cnt in sorted(freq_bigramas.items(), key=lambda kv: -kv[1]):
        if cnt < min_coocurrencia:
            break
        if w1 in usados or w2 in usados:
            continue
        clusters.append({"palabras": [w1, w2], "articulos": set(bigrama_a_articulos[(w1, w2)])})
        usados.add(w1)
        usados.add(w2)

    # 2) Pase de CO-OCURRENCIA suelta: palabras salientes que aparecen
    # juntas en el mismo titular aunque no sean contiguas (p.ej. "ceuta"
    # y "sanchez" en un mismo slug largo). Solo cuentan los artículos donde
    # aparecen AMBAS palabras (intersección) — nunca la unión, o se mezclan
    # artículos que solo comparten una de las dos palabras por casualidad.
    coocurrencia = Counter()
    coocurrencia_a_articulos = defaultdict(set)
    for i, art in enumerate(articulos_utiles):
        presentes = sorted((set(art["palabras"]) & salientes) - usados)
        for w1, w2 in itertools.combinations(presentes, 2):
            coocurrencia[(w1, w2)] += 1
            coocurrencia_a_articulos[(w1, w2)].add(i)

    for (w1, w2), cnt in sorted(coocurrencia.items(), key=lambda kv: -kv[1]):
        if cnt < min_coocurrencia:
            break
        if w1 in usados or w2 in usados:
            continue
        clusters.append({"palabras": [w1, w2], "articulos": set(coocurrencia_a_articulos[(w1, w2)])})
        usados.add(w1)
        usados.add(w2)

    # 3) Palabras salientes que ni así encontraron pareja: concepto propio.
    restantes = sorted(salientes - usados, key=lambda w: -freq_palabra[w])
    for w in restantes:
        if freq_palabra[w] < min_frecuencia:
            continue
        clusters.append({"palabras": [w], "articulos": set(palabra_a_articulos[w])})
        usados.add(w)

    clusters.sort(key=lambda c: -len(c["articulos"]))
    articulos = articulos_utiles  # las referencias por índice de aquí en adelante son a esta lista

    resultado = []
    for c in clusters[:top_n]:
        idxs = sorted(c["articulos"], key=lambda i: articulos[i].get("fecha") or "", reverse=True)
        secciones_cluster = Counter(articulos[i]["seccion"] for i in idxs)
        seccion_principal = secciones_cluster.most_common(1)[0][0]
        fechas_cluster = sorted(articulos[i]["fecha"] for i in idxs if articulos[i].get("fecha"))

        ejemplos = []
        vistos = set()
        for i in idxs:
            t = articulos[i]["titulo"]
            if t in vistos:
                continue
            vistos.add(t)
            ejemplos.append(t)
            if len(ejemplos) == 3:
                break

        etiqueta = " · ".join(p.capitalize() for p in c["palabras"])

        resultado.append({
            "concepto": etiqueta,
            "piezas": len(idxs),
            "seccion_principal": seccion_principal,
            "desde": fechas_cluster[0] if fechas_cluster else None,
            "hasta": fechas_cluster[-1] if fechas_cluster else None,
            "evidencia": ejemplos,
            "ejemplos_redactados": None,
        })

    return resultado


def construir_analisis(entradas, url_base: str, excluir_secciones=None, top_n_conceptos: int = 8):
    excluir_secciones = {s.strip().lower() for s in (excluir_secciones or []) if s.strip()}
    dominio = dominio_compacto(url_base)

    por_seccion = Counter()
    por_subseccion = Counter()
    por_dia = Counter()
    por_dia_y_seccion = defaultdict(Counter)
    por_tipo = Counter()
    fechas = []
    total_validas = 0
    articulos = []

    for e in entradas:
        info = analizar_url(e["loc"], url_base, dominio)
        if info is None:
            continue
        if info["seccion"].lower() in excluir_secciones:
            continue

        total_validas += 1
        por_seccion[info["seccion"]] += 1
        if info["subseccion"]:
            por_subseccion[f'{info["seccion"]}/{info["subseccion"]}'] += 1
        por_tipo[info["tipo"]] += 1

        fecha_dt = parsear_fecha(e["lastmod"])
        dia = None
        if fecha_dt:
            fechas.append(fecha_dt)
            dia = fecha_dt.strftime("%Y-%m-%d")
            por_dia[dia] += 1
            por_dia_y_seccion[dia][info["seccion"]] += 1

        articulos.append({
            "palabras": info["palabras"],
            "titulo": info["titulo"],
            "fecha": dia,
            "seccion": info["seccion"],
        })

    rango = None
    if fechas:
        rango = {
            "desde": min(fechas).strftime("%Y-%m-%d"),
            "hasta": max(fechas).strftime("%Y-%m-%d"),
        }

    dias_ordenados = sorted(por_dia.keys())
    secciones_top = [s for s, _ in por_seccion.most_common()]

    heatmap_calendario = []
    for dia in dias_ordenados:
        fila = {"fecha": dia, "total": por_dia[dia]}
        for sec in secciones_top:
            fila[sec] = por_dia_y_seccion[dia].get(sec, 0)
        heatmap_calendario.append(fila)

    conceptos = construir_conceptos_destacados(articulos, top_n=top_n_conceptos)

    resumen_borrador = generar_borrador_resumen(
        rango=rango,
        total=total_validas,
        por_seccion=por_seccion,
        conceptos=conceptos,
    )

    return {
        "url_base": url_base,
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "periodo_cubierto": rango,
        "total_urls_analizadas": total_validas,
        "secciones_excluidas": sorted(excluir_secciones) if excluir_secciones else [],
        "nota_cobertura": (
            "El análisis cubre únicamente las URLs presentes en el sitemap "
            "en el momento de la consulta (excluyendo, si se indicó, las "
            "secciones filtradas). Si el sitemap es incremental o "
            "'rolling', el periodo real puede ser más corto que el "
            "solicitado — revisa 'periodo_cubierto' para confirmarlo."
        ),
        "por_seccion": por_seccion.most_common(),
        "por_subseccion": por_subseccion.most_common(20),
        "por_tipo_contenido": por_tipo.most_common(),
        "heatmap_calendario": heatmap_calendario,
        "conceptos_destacados": conceptos,
        "resumen_borrador": resumen_borrador,
        "resumen": None,
    }


def generar_borrador_resumen(rango, total, por_seccion, conceptos):
    """Genera un borrador puramente mecánico (cifras + etiquetas de
    concepto), útil como material de partida o como resumen de emergencia
    en ejecuciones totalmente automatizadas sin revisión. NO es el resumen
    final: no cuenta qué ha pasado, solo describe el propio análisis. El
    campo 'resumen' final debe redactarlo Claude en lenguaje natural a
    partir de 'conceptos_destacados' (ver SKILL.md, sección "Redactar el
    resumen final")."""
    if total == 0:
        return "No se han encontrado noticias en el periodo analizado."

    top_secciones = por_seccion.most_common(3)
    periodo_txt = f" entre el {rango['desde']} y el {rango['hasta']}" if rango else ""
    secciones_txt = ", ".join(f"{sec} ({n} piezas)" for sec, n in top_secciones)

    parrafo1 = (
        f"Se han publicado {total} noticias{periodo_txt}. "
        f"La actividad se ha concentrado sobre todo en {secciones_txt}."
    )

    if conceptos:
        top_conceptos = [c["concepto"] for c in conceptos[:4]]
        parrafo2 = (
            "Los conceptos con más piezas relacionadas son: "
            + "; ".join(top_conceptos)
            + ". Revisa 'evidencia' de cada concepto para redactar el resumen final."
        )
    else:
        parrafo2 = "No se han detectado conceptos claramente recurrentes en este periodo."

    return f"{parrafo1}\n\n{parrafo2}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("entrada", help="Ruta a un fichero XML local, o una URL http(s)")
    ap.add_argument("salida", help="Ruta del JSON de salida")
    ap.add_argument("--url-base", default="", help="URL base del sitio (solo para limpiar rutas y derivar stopwords; nunca aparece en los textos)")
    ap.add_argument("--excluir-secciones", default="", help="Lista separada por comas de secciones a excluir, p.ej. 'tu-gaceta,nacional'")
    ap.add_argument("--top-conceptos", type=int, default=8)
    args = ap.parse_args()

    xml_text = descargar_o_leer(args.entrada)
    entradas = parsear_urls(xml_text)
    if not entradas:
        print("No se han encontrado bloques <url> en el fichero.", file=sys.stderr)
        sys.exit(1)

    excluir = args.excluir_secciones.split(",") if args.excluir_secciones else []

    resultado = construir_analisis(
        entradas,
        url_base=args.url_base,
        excluir_secciones=excluir,
        top_n_conceptos=args.top_conceptos,
    )

    with open(args.salida, "w", encoding="utf-8") as fh:
        json.dump(resultado, fh, ensure_ascii=False, indent=2)

    print(f"OK: {resultado['total_urls_analizadas']} URLs analizadas -> {args.salida}")
    if resultado["periodo_cubierto"]:
        print(f"Periodo cubierto: {resultado['periodo_cubierto']}")


if __name__ == "__main__":
    main()
