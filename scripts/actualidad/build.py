#!/usr/bin/env python3
"""Actualiza actualidad, timeline, eventos y Opina usando la API de Gemini.

Es la versión "sin Claude Code" de la skill sitemap-mapa-calor-tematico
(.claude/skills/sitemap-mapa-calor-tematico/SKILL.md): mismas reglas y mismos
ficheros de salida, pero la redacción la hace Gemini y la lógica de fusión
(heatmap acumulado, meses, eventos vigentes, archivo de Opina) es código
determinista, no depende de que el modelo "se acuerde" de hacerla.

Uso (desde la raíz del repo):
    GEMINI_API_KEY=... python3 scripts/actualidad/build.py

Variables de entorno:
    GEMINI_API_KEY   obligatoria.
    GEMINI_MODEL     opcional (por defecto gemini-2.5-flash).
    SITEMAP_URL      opcional, sitemap a analizar (por defecto el incremental
                     de La Gaceta). También admite una ruta a un XML local.
    HOY              opcional, YYYY-MM-DD, para forzar la fecha (pruebas).

Solo usa la librería estándar de Python.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import unescape
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ANALIZADOR = RAIZ / ".claude/skills/sitemap-mapa-calor-tematico/scripts/analizar_sitemap.py"

URL_BASE = "https://www.lagacetadesalamanca.es"
SITEMAP_URL = os.environ.get("SITEMAP_URL") or f"{URL_BASE}/sitemap.incremental.xml"
EXCLUIR = "nacional,opinion,tu-gaceta,gente-estilo,podcast"
MODELO = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
USER_AGENT = "Mozilla/5.0 (compatible; OpenSalamancaBot/1.0; +https://opensalamanca.es/actualidad)"

CATEGORIAS = ["Sucesos", "Política", "Economía", "Cultura", "Deportes", "Sociedad", "Educación", "Urbanismo"]
MAX_HITOS_MES = 8
MAX_PREGUNTAS_NUEVAS = 2
MAX_RETIRADAS = 3
EDAD_MINIMA_RETIRADA_DIAS = 5

HOY = date.fromisoformat(os.environ["HOY"]) if os.environ.get("HOY") else datetime.now(timezone.utc).date()
AHORA = datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------
# Utilidades de ficheros
# --------------------------------------------------------------------------
def leer_json(ruta, defecto):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return defecto


def escribir_json(ruta, datos, indent=2):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


def descargar(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def normalizar(texto):
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def fecha_valida(s):
    try:
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Gemini
# --------------------------------------------------------------------------
def gemini(prompt, esquema, sistema, temperatura=0.4):
    """Llama a generateContent forzando salida JSON con `esquema`."""
    clave = os.environ.get("GEMINI_API_KEY")
    if not clave:
        sys.exit("Falta GEMINI_API_KEY en el entorno.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent"
    cuerpo = json.dumps({
        "systemInstruction": {"parts": [{"text": sistema}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": esquema,
            "temperature": temperatura,
        },
    }).encode("utf-8")
    ultimo_error = None
    for intento in range(5):
        req = urllib.request.Request(
            url, data=cuerpo, method="POST",
            headers={"Content-Type": "application/json", "x-goog-api-key": clave},
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                datos = json.loads(resp.read().decode("utf-8"))
            cand = (datos.get("candidates") or [{}])[0]
            partes = (cand.get("content") or {}).get("parts") or []
            texto = "".join(p.get("text", "") for p in partes)
            if not texto:
                raise ValueError(f"Respuesta vacía (finishReason={cand.get('finishReason')}, "
                                 f"promptFeedback={datos.get('promptFeedback')})")
            return json.loads(texto)
        except urllib.error.HTTPError as e:
            detalle = e.read().decode("utf-8", errors="replace")[:500]
            ultimo_error = f"HTTP {e.code}: {detalle}"
            if e.code not in (429, 500, 502, 503, 504):
                break  # 400/401/403/404: reintentar no arregla nada
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            ultimo_error = str(e)
        espera = 5 * (2 ** intento)
        log(f"[gemini] intento {intento + 1} fallido ({ultimo_error}); reintento en {espera}s")
        time.sleep(espera)
    raise RuntimeError(f"Gemini no respondió correctamente: {ultimo_error}")


def S(tipo, **kw):
    return {"type": tipo, **kw}


def lista(items):
    return S("ARRAY", items=items)


def obj(props, requeridos=None):
    return S("OBJECT", properties=props, required=requeridos or list(props))


SISTEMA = (
    "Eres el redactor de datos locales de opensalamanca.es, un portal de datos abiertos "
    "de Salamanca. Escribes en español de España, en tono periodístico neutral y "
    "sobrio. Trabajas solo con la información que se te da: no inventas hechos, cifras, "
    "nombres, fechas ni URLs. Si un detalle no está en el material, sé más genérico en "
    "vez de rellenar. Devuelves únicamente JSON válido según el esquema."
)


# --------------------------------------------------------------------------
# Paso 1 — análisis mecánico (analizador existente)
# --------------------------------------------------------------------------
def ventana_dias():
    """Días hacia atrás a analizar: desde el día anterior al último periodo ya
    cubierto (para no dejar huecos), con un mínimo de 3 y un máximo de 8. El
    sitemap incremental guarda ~6 semanas y el análisis solo debe ver lo nuevo."""
    hasta = fecha_valida(((leer_json(RAIZ / "actualidad.json", {}).get("periodo_cubierto")) or {}).get("hasta"))
    dias = (HOY - hasta).days + 1 if hasta else 3
    return max(3, min(8, dias))


def obtener_sitemap(tmp):
    if SITEMAP_URL.startswith("http"):
        xml = descargar(SITEMAP_URL)
    else:
        xml = Path(SITEMAP_URL).read_text(encoding="utf-8", errors="replace")
    corte = HOY - timedelta(days=ventana_dias())
    bloques = re.findall(r"<url>.*?</url>", xml, flags=re.I | re.S)
    recientes = []
    for b in bloques:
        loc = re.search(r"<loc>(.*?)</loc>", b, flags=re.I | re.S)
        f = fecha_valida(fecha_desde_url(loc.group(1).strip())) if loc else None
        if f is None:  # sin fecha en la URL: usar lastmod
            lm = re.search(r"<lastmod>(\d{4}-\d{2}-\d{2})", b)
            f = fecha_valida(lm.group(1)) if lm else None
        if f is None or f >= corte:
            recientes.append(b)
    log(f"[sitemap] {len(bloques)} URLs en origen; {len(recientes)} desde {corte.isoformat()}.")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(recientes) + "\n</urlset>\n")
    ruta = Path(tmp) / "sitemap.xml"
    ruta.write_text(xml, encoding="utf-8")
    urls = re.findall(r"<loc>(.*?)</loc>", xml, flags=re.I | re.S)
    return ruta, [u.strip() for u in urls]


def analizar(tmp):
    ruta_xml, urls = obtener_sitemap(tmp)
    salida = Path(tmp) / "analisis.json"
    subprocess.run(
        [sys.executable, str(ANALIZADOR), str(ruta_xml), str(salida),
         "--url-base", URL_BASE, "--excluir-secciones", EXCLUIR, "--top-conceptos", "14"],
        check=True,
    )
    return json.loads(salida.read_text(encoding="utf-8")), urls


def urls_permitidas(urls):
    """URLs de noticias del sitemap que no caen en secciones excluidas."""
    excluidas = set(EXCLUIR.split(","))
    out = []
    for u in urls:
        ruta = u.replace(URL_BASE, "").strip("/").split("/")
        if ruta and ruta[0] not in excluidas:
            out.append(u)
    return out


def titulo_desde_url(u):
    nombre = u.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"-\d{12,14}-[a-z]{2,4}\.html?$", "", nombre)
    return slug.replace("-", " ")


def fecha_desde_url(u):
    m = re.search(r"-(\d{4})(\d{2})(\d{2})\d{6,8}-[a-z]{2,4}\.html?$", u)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


# --------------------------------------------------------------------------
# Paso 2 y 3 — resumen semanal + hitos mensuales
# --------------------------------------------------------------------------
ESQ_REDACCION = obj({
    "conceptos": lista(obj({
        "concepto": S("STRING"),
        "piezas": S("INTEGER"),
        "seccion_principal": S("STRING"),
        "desde": S("STRING"),
        "hasta": S("STRING"),
        "ejemplos_redactados": lista(S("STRING")),
    })),
    "resumen": S("STRING"),
    "meses": lista(obj({
        "mes": S("STRING"),
        "resumen_mes": S("STRING"),
        "hitos": lista(obj({
            "fecha": S("STRING"),
            "titulo": S("STRING"),
            "categoria": S("STRING", enum=CATEGORIAS),
            "descripcion": S("STRING"),
            "fuente": S("STRING"),
            "destacado": S("BOOLEAN"),
        })),
    })),
    "candidatos_evento": lista(obj({"titulo": S("STRING"), "url": S("STRING")})),
})


def redactar(analisis, urls_ok, mensuales_previos):
    periodo = analisis.get("periodo_cubierto") or {}
    urls_txt = "\n".join(f"{fecha_desde_url(u)} | {u} | {titulo_desde_url(u)}" for u in urls_ok)
    conceptos = [{k: c[k] for k in ("concepto", "piezas", "seccion_principal", "desde", "hasta", "evidencia") if k in c}
                 for c in analisis.get("conceptos_destacados", [])]
    prompt = f"""FECHA DE EJECUCIÓN: {HOY.isoformat()}
PERIODO REAL CUBIERTO POR EL SITEMAP: {periodo.get('desde')} a {periodo.get('hasta')}
RECUENTO POR SECCIÓN: {json.dumps(analisis.get('por_seccion'), ensure_ascii=False)}

CONCEPTOS DETECTADOS POR EL ANÁLISIS LÉXICO (crudo; "evidencia" son slugs de titulares):
{json.dumps(conceptos, ensure_ascii=False, indent=1)}

URLS DE NOTICIAS DEL PERIODO (fecha | url | titular en forma de slug):
{urls_txt}

HITOS YA GUARDADOS DE LOS MESES AFECTADOS (para fusionar, no duplicar):
{json.dumps(mensuales_previos, ensure_ascii=False, indent=1)}

TAREA
1. "conceptos": cura la lista. Descarta ruido léxico (palabras genéricas emparejadas por casualidad); \
si en las URLs ves una historia noticiable que el análisis no agrupó, añádela. Máximo 8. Para cada uno, \
"concepto" es una etiqueta legible (titular breve) y "ejemplos_redactados" 1-2 frases en español correcto \
con verbos conjugados y sin inventar ningún dato que no esté implícito en los slugs. Mantén "piezas", \
"seccion_principal", "desde" y "hasta" del análisis (ajústalos solo si añades un concepto nuevo).
2. "resumen": resumen periodístico de 2-3 párrafos separados por una línea en blanco, agrupado por \
bloques temáticos con transiciones naturales. No describas el análisis ni menciones el sitemap. \
Si el periodo cubierto es más corto que una semana, no lo disimules ni lo alargues.
3. "meses": un elemento por cada mes (formato YYYY-MM) que toque el periodo cubierto. Cada uno \
devuelve la lista COMPLETA y final de hitos de ese mes (los ya guardados que sigan valiendo + los nuevos), \
fusionando sin duplicar el mismo suceso aunque el texto difiera. Reglas: entre 5 y {MAX_HITOS_MES} hitos \
por mes, priorizando diversidad de categorías; exactamente UN hito con destacado=true (el de mayor \
repercusión para el mes completo; no cambies el destacado actual salvo que el nuevo sea claramente más \
importante); "categoria" solo puede ser una de las 8 dadas; "fecha" es un día concreto YYYY-MM-DD dentro \
del mes y, para hitos nuevos, dentro del periodo cubierto; "titulo" de menos de 90 caracteres; \
"descripcion" de 1-2 frases; "fuente" es una URL copiada tal cual de la lista de arriba (o del hito ya guardado) \
o, si no hay ninguna fiable, el texto "sin fuente directa". Conserva sin cambios los hitos ya guardados \
que no se fusionen con nada. "resumen_mes": 1-2 frases sobre el mes completo con lo nuevo incorporado.
4. "candidatos_evento": hasta 12 noticias de la lista de URLs que suenen a un evento FUTURO con fecha \
de celebración propia (ferias, fiestas, festivales, exposiciones, jornadas, certámenes, carreras, \
citas deportivas con fecha fija). No incluyas resultados ya jugados, sucesos, política ni clima. \
Es normal devolver pocos o ninguno. "url" copiada tal cual de la lista."""
    return gemini(prompt, ESQ_REDACCION, SISTEMA, temperatura=0.5)


def limpiar_hitos(hitos, mes, urls_ok, previos):
    """Valida lo que devuelve el modelo: no confiamos en él para lo verificable."""
    urls_ok = set(urls_ok)
    fuentes_previas = {h.get("fuente") for h in previos}
    limpios = []
    for h in hitos:
        f = fecha_valida(h.get("fecha"))
        if not f or f.strftime("%Y-%m") != mes:
            continue
        if h.get("categoria") not in CATEGORIAS:
            continue
        fuente = h.get("fuente", "")
        if fuente not in urls_ok and fuente not in fuentes_previas:
            fuente = "sin fuente directa"
        limpios.append({
            "fecha": f.isoformat(),
            "titulo": (h.get("titulo") or "").strip()[:89],
            "categoria": h["categoria"],
            "descripcion": (h.get("descripcion") or "").strip(),
            "fuente": fuente,
            "destacado": bool(h.get("destacado")),
        })
    limpios = [h for h in limpios if h["titulo"] and h["descripcion"]]
    # Red de seguridad: si el modelo devuelve MENOS hitos que los ya guardados
    # (los ha soltado en vez de fusionarlos), se recuperan los que no aparezcan.
    if len(limpios) < len(previos):
        claves = {(h["fuente"], normalizar(h["titulo"])) for h in limpios}
        for h in previos:
            if len(limpios) >= len(previos):
                break
            if (h.get("fuente"), normalizar(h.get("titulo"))) not in claves and                     not any(x["fuente"] == h.get("fuente") != "sin fuente directa" for x in limpios):
                limpios.append({**h, "destacado": False})
    limpios.sort(key=lambda h: (not h["destacado"], h["fecha"]))
    limpios = limpios[:MAX_HITOS_MES]
    # Exactamente un destacado por mes.
    vistos = False
    for h in limpios:
        if h["destacado"] and not vistos:
            vistos = True
        else:
            h["destacado"] = False
    if limpios and not vistos:
        limpios[0]["destacado"] = True
    limpios.sort(key=lambda h: h["fecha"])
    return limpios


def meses_del_periodo(periodo):
    d, h = fecha_valida(periodo.get("desde")), fecha_valida(periodo.get("hasta"))
    if not d or not h:
        return [HOY.strftime("%Y-%m")]
    meses, actual = [], date(d.year, d.month, 1)
    while actual <= h:
        meses.append(actual.strftime("%Y-%m"))
        actual = date(actual.year + (actual.month == 12), actual.month % 12 + 1, 1)
    return meses


NOMBRES_MES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
               "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def escribir_mensuales(redaccion, urls_ok):
    tocados = []
    for m in redaccion.get("meses", []):
        mes = m.get("mes", "")
        if not re.fullmatch(r"\d{4}-\d{2}", mes):
            continue
        ruta = RAIZ / "actualidad" / f"{mes.replace('-', '')}.json"
        previo = leer_json(ruta, {})
        hitos = limpiar_hitos(m.get("hitos", []), mes, urls_ok, previo.get("hitos", []))
        if not hitos:
            log(f"[mensual] {mes}: el modelo no devolvió hitos válidos; no se toca el fichero.")
            continue
        a, mm = int(mes[:4]), int(mes[5:])
        escribir_json(ruta, {
            "mes": mes,
            "titulo_mes": f"{NOMBRES_MES[mm - 1]} {a}",
            "resumen_mes": (m.get("resumen_mes") or previo.get("resumen_mes") or "").strip(),
            "hitos": hitos,
        })
        tocados.append(str(ruta.relative_to(RAIZ)).replace("\\", "/"))
    return tocados


def escribir_actualidad(analisis, redaccion):
    conceptos = []
    for c in redaccion.get("conceptos", []):
        ej = [e.strip() for e in c.get("ejemplos_redactados", []) if e.strip()]
        if c.get("concepto") and ej:
            conceptos.append({
                "concepto": c["concepto"].strip(),
                "piezas": c.get("piezas"),
                "seccion_principal": c.get("seccion_principal"),
                "desde": c.get("desde"),
                "hasta": c.get("hasta"),
                "ejemplos_redactados": ej,
            })
    resumen = (redaccion.get("resumen") or "").strip()
    if not conceptos or not resumen:
        raise RuntimeError("Gemini no devolvió conceptos/resumen utilizables; se aborta sin tocar actualidad.json.")
    final = {k: v for k, v in analisis.items() if k not in ("conceptos_destacados", "resumen", "resumen_borrador")}
    final["conceptos_destacados"] = conceptos
    final["resumen_borrador"] = analisis.get("resumen_borrador")
    final["resumen"] = resumen
    final["generado_en"] = AHORA
    escribir_json(RAIZ / "actualidad.json", final)

    # Heatmap acumulado: fusiona por fecha, nunca borra días anteriores.
    ruta = RAIZ / "actualidad-heatmap.json"
    hm = leer_json(ruta, {"nota": "", "dias": []})
    por_fecha = {d["fecha"]: d for d in hm.get("dias", [])}
    for d in analisis.get("heatmap_calendario", []):
        por_fecha[d["fecha"]] = d
    hm["dias"] = [por_fecha[k] for k in sorted(por_fecha)]
    # Un día por línea, como el fichero original (diffs legibles en git).
    cabecera = "".join(f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)},\n" for k, v in hm.items() if k != "dias")
    filas = ",\n".join("    " + json.dumps(d, ensure_ascii=False) for d in hm["dias"])
    ruta.write_text("{\n" + cabecera + '  "dias": [\n' + filas + "\n  ]\n}\n", encoding="utf-8")
    return ["actualidad.json", "actualidad-heatmap.json"]


# --------------------------------------------------------------------------
# Paso 4 — eventos con fecha
# --------------------------------------------------------------------------
ESQ_EVENTOS = obj({
    "eventos": lista(obj({
        "titulo": S("STRING"),
        "categoria": S("STRING", enum=CATEGORIAS),
        "fecha_inicio": S("STRING"),
        "fecha_fin": S("STRING", nullable=True),
        "lugar": S("STRING", nullable=True),
        "descripcion": S("STRING"),
        "fuente": S("STRING"),
    }, requeridos=["titulo", "categoria", "fecha_inicio", "descripcion", "fuente"])),
})


def texto_articulo(html):
    """Título + meta descripción + articleBody del JSON-LD (donde suele estar la fecha)."""
    html = html[:700_000]  # evita backtracking caro en páginas enormes
    partes = []
    m = re.search(r"<title[^>]*>([^<]*)</title>", html, flags=re.I)
    if m:
        partes.append(unescape(m.group(1)).strip())
    for tag in re.findall(r"<meta\b[^>]*>", html, flags=re.I):
        nombre = re.search(r"""(?:property|name)=["']([^"']+)["']""", tag, flags=re.I)
        contenido = re.search(r"""content=["']([^"']*)["']""", tag, flags=re.I)
        if nombre and contenido and nombre.group(1).lower() in ("og:description", "description"):
            partes.append(unescape(contenido.group(1)).strip())
    for m in re.finditer(r'"articleBody"\s*:\s*"((?:[^"\\]|\\.)*)"', html):
        try:
            partes.append(json.loads('"' + m.group(1) + '"')[:3000])
        except ValueError:
            pass
    vistos, out = set(), []
    for p in partes:
        if p and p not in vistos:
            vistos.add(p)
            out.append(p)
    return "\n".join(out)[:4500]


def actualizar_eventos(candidatos, urls_ok):
    ruta = RAIZ / "eventos.json"
    previo = leer_json(ruta, {"eventos": []})
    eventos = list(previo.get("eventos", []))

    articulos = []
    for c in candidatos[:12]:
        url = c.get("url", "")
        if url not in urls_ok:
            continue
        try:
            articulos.append({"url": url, "titulo_orientativo": c.get("titulo"), "texto": texto_articulo(descargar(url, 20))})
        except Exception as e:  # noqa: BLE001 - una URL caída no debe tumbar el proceso
            log(f"[eventos] no se pudo abrir {url}: {e}")

    if articulos:
        prompt = f"""FECHA DE EJECUCIÓN: {HOY.isoformat()}

Estos son los textos reales (título, meta descripción y cuerpo) de artículos que podrían anunciar un evento futuro:
{json.dumps(articulos, ensure_ascii=False, indent=1)}

EVENTOS QUE YA TENEMOS (no los repitas; si un artículo aporta un dato nuevo de uno de ellos, devuélvelo actualizado):
{json.dumps(eventos, ensure_ascii=False, indent=1)}

TAREA: devuelve solo los eventos con FECHA DE CELEBRACIÓN EXPLÍCITA en el texto ("del 3 al 7 de septiembre", \
"el 3 de octubre de 2026"...). Si el año no aparece, deduce el más lógico a partir de la fecha de ejecución. \
Si no hay fecha explícita y verificable, NO incluyas el evento: no infieras nada a partir de "esta semana" ni \
"el próximo fin de semana". No incluyas eventos ya pasados a fecha de ejecución. Formato de fechas YYYY-MM-DD; \
"fecha_fin" null si es un solo día; "lugar" solo si el texto lo dice, si no null; "descripcion" 1-2 frases; \
"fuente" es la URL del artículo de donde sacaste la fecha. Es normal devolver una lista vacía."""
        nuevos = gemini(prompt, ESQ_EVENTOS, SISTEMA, temperatura=0.2).get("eventos", [])
        urls_articulos = {a["url"] for a in articulos}
        for n in nuevos:
            ini, fin = fecha_valida(n.get("fecha_inicio")), fecha_valida(n.get("fecha_fin"))
            if not ini or (n.get("fecha_fin") and not fin) or n.get("fuente") not in urls_articulos:
                continue
            if fin and fin < ini:
                continue
            ev = {
                "titulo": n["titulo"].strip(),
                "categoria": n["categoria"],
                "fecha_inicio": ini.isoformat(),
                "fecha_fin": fin.isoformat() if fin else None,
            }
            if n.get("lugar"):
                ev["lugar"] = n["lugar"].strip()
            ev["descripcion"] = n["descripcion"].strip()
            ev["fuente"] = n["fuente"]
            # ¿Ya existe? por fuente o por título aproximado -> se actualiza.
            for i, e in enumerate(eventos):
                if e.get("fuente") == ev["fuente"] or normalizar(e.get("titulo")) == normalizar(ev["titulo"]):
                    eventos[i] = {**e, **ev}
                    break
            else:
                eventos.append(ev)

    # Calendario vivo: fuera lo que ya pasó.
    def vigente(e):
        limite = fecha_valida(e.get("fecha_fin")) or fecha_valida(e.get("fecha_inicio"))
        return bool(limite) and limite >= HOY

    eventos = sorted((e for e in eventos if vigente(e)), key=lambda e: e["fecha_inicio"])
    escribir_json(ruta, {"generado_en": AHORA, "eventos": eventos})
    return ["eventos.json"], eventos


# --------------------------------------------------------------------------
# Paso 5 — Opina
# --------------------------------------------------------------------------
ESQ_OPINA = obj({
    "nuevas": lista(obj({
        "id": S("STRING"),
        "pregunta": S("STRING"),
        "opciones": lista(S("STRING")),
        "basado_en": S("STRING", enum=["actualidad.json", "eventos.json"]),
    })),
    "retirar": lista(obj({"id": S("STRING"), "motivo": S("STRING")})),
})


def votos_del_worker(worker_url, pid):
    """Recuento público de una pregunta; None si no se puede obtener (no archivamos a ciegas)."""
    if not worker_url or "TU-SUBDOMINIO" in worker_url:
        return None
    try:
        datos = json.loads(descargar(worker_url.rstrip("/") + "/votos/" + pid, 20))
        return {k: int(v) for k, v in datos.items()} if isinstance(datos, dict) else None
    except Exception as e:  # noqa: BLE001
        log(f"[opina] no se pudo leer el recuento de {pid}: {e}")
        return None


def actualizar_opina(resumen, conceptos, eventos):
    ruta_op, ruta_hi = RAIZ / "opina.json", RAIZ / "historico.json"
    opina = leer_json(ruta_op, {"preguntas": []})
    historico = leer_json(ruta_hi, {"preguntas_archivadas": []})
    activas = opina.get("preguntas", [])
    ids_usados = {p["id"] for p in activas} | {p["id"] for p in historico.get("preguntas_archivadas", [])}

    prompt = f"""FECHA DE EJECUCIÓN: {HOY.isoformat()}

RESUMEN DE LA ACTUALIDAD RECIENTE:
{resumen}

CONCEPTOS DESTACADOS:
{json.dumps([c["concepto"] for c in conceptos], ensure_ascii=False)}

PRÓXIMOS EVENTOS (eventos.json):
{json.dumps(eventos, ensure_ascii=False)}

PREGUNTAS ACTIVAS EN /opina (con su fecha de creación):
{json.dumps(activas, ensure_ascii=False, indent=1)}

IDS YA USADOS (no repetir): {sorted(ids_usados)}

TAREA
A) "nuevas": propón como máximo {MAX_PREGUNTAS_NUEVAS} preguntas nuevas. BARRA DE CALIDAD ESTRICTA: solo si la \
distribución de respuestas puede aportar una conclusión de interés real sobre la ciudad y está ligada a una noticia, \
decisión o evento local concreto (un evento próximo con opciones reales entre las que elegir; una decisión o \
resultado local con posturas claras). Descarta la charla trivial (tiempo, humor genérico, cosas obvias) y las \
preguntas sobre temas que ya tenga una pregunta activa. Es PREFERIBLE devolver una lista vacía a rellenar con una \
pregunta floja; ante la duda, no la añadas. Formato: "id" corto en kebab-case terminado en el año (p.ej. \
"ferias-salamanca-2026"), "pregunta" cerrada, en segunda persona del singular de cortesía o impersonal, que \
incluya en la propia frase el contexto necesario para entenderla; 3-5 "opciones" con redacción neutral que no \
induzca la respuesta (incluye una salida tipo "No tengo suficiente información" cuando proceda); "basado_en" \
indica el fichero de origen.
B) "retirar": ids de preguntas ACTIVAS que ya no son de actualidad (el evento pasó, el tema quedó resuelto u \
obsoleto). El criterio es relevancia, no antigüedad: no retires una pregunta solo porque lleve semanas si el tema \
sigue vigente. Máximo {MAX_RETIRADAS}. Lista vacía si no hay ninguna."""
    r = gemini(prompt, ESQ_OPINA, SISTEMA, temperatura=0.3)

    tocados = []
    worker = opina.get("worker_url")

    # Retiradas primero (así el id retirado queda reservado en el histórico).
    retiradas = 0
    for item in r.get("retirar", [])[:MAX_RETIRADAS]:
        p = next((x for x in activas if x["id"] == item.get("id")), None)
        if not p:
            continue
        creada = fecha_valida(p.get("fecha_creacion"))
        if creada and (HOY - creada).days < EDAD_MINIMA_RETIRADA_DIAS:
            log(f"[opina] {p['id']}: demasiado reciente para retirarla; se mantiene.")
            continue
        votos = votos_del_worker(worker, p["id"])
        if votos is None:
            log(f"[opina] {p['id']}: sin recuento del Worker; se mantiene activa para no perder los votos.")
            continue
        historico.setdefault("preguntas_archivadas", []).append({
            **p,
            "fecha_archivado": HOY.isoformat(),
            "resultados": votos,
            "total_votos": sum(votos.values()),
        })
        activas = [x for x in activas if x["id"] != p["id"]]
        retiradas += 1
        log(f"[opina] Retirada {p['id']} ({sum(votos.values())} votos). "
            f"PENDIENTE (manual): wrangler kv key put \"closed:{p['id']}\" \"1\" --namespace-id=<id>")

    añadidas = 0
    for n in r.get("nuevas", [])[:MAX_PREGUNTAS_NUEVAS]:
        pid = (n.get("id") or "").strip()
        ops = [o.strip() for o in n.get("opciones", []) if o.strip()]
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", pid) or pid in ids_usados:
            continue
        if not (3 <= len(ops) <= 5) or len(set(ops)) != len(ops) or not n.get("pregunta", "").strip():
            continue
        activas.append({
            "id": pid,
            "pregunta": n["pregunta"].strip(),
            "opciones": ops,
            "basado_en": n["basado_en"],
            "fecha_creacion": HOY.isoformat(),
        })
        ids_usados.add(pid)
        añadidas += 1

    if retiradas or añadidas:
        opina["preguntas"] = activas
        escribir_json(ruta_op, opina)
        tocados.append("opina.json")
    if retiradas:
        escribir_json(ruta_hi, historico)
        tocados.append("historico.json")
    log(f"[opina] {añadidas} nuevas, {retiradas} retiradas.")
    return tocados


# --------------------------------------------------------------------------
def main():
    with tempfile.TemporaryDirectory() as tmp:
        analisis, urls = analizar(tmp)
    periodo = analisis.get("periodo_cubierto") or {}
    urls_ok = urls_permitidas(urls)
    log(f"[analisis] {analisis.get('total_urls_analizadas')} URLs, periodo {periodo}, "
        f"{len(urls_ok)} candidatas tras exclusiones.")

    meses = meses_del_periodo(periodo)
    previos = {m: leer_json(RAIZ / "actualidad" / f"{m.replace('-', '')}.json", None) for m in meses}
    redaccion = redactar(analisis, urls_ok, {m: v for m, v in previos.items() if v})

    tocados = escribir_actualidad(analisis, redaccion)
    tocados += escribir_mensuales(redaccion, urls_ok)
    t_ev, eventos = actualizar_eventos(redaccion.get("candidatos_evento", []), set(urls_ok))
    tocados += t_ev
    actual = leer_json(RAIZ / "actualidad.json", {})
    tocados += actualizar_opina(actual.get("resumen", ""), actual.get("conceptos_destacados", []), eventos)

    # Lista para que el workflow haga `git add` solo de lo tocado.
    salida = os.environ.get("GITHUB_OUTPUT")
    resumen_periodo = f"{periodo.get('desde')} a {periodo.get('hasta')}"
    if salida:
        with open(salida, "a", encoding="utf-8") as fh:
            fh.write(f"ficheros={' '.join(dict.fromkeys(tocados))}\n")
            fh.write(f"periodo={resumen_periodo}\n")
    print("Ficheros tocados:", " ".join(dict.fromkeys(tocados)))


if __name__ == "__main__":
    main()
