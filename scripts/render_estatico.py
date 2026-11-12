#!/usr/bin/env python3
"""Genera fragmentos HTML estáticos (en _includes/) a partir de los JSON que
hoy se pintan solo con JavaScript, para que buscadores y bots sin JS vean el
contenido de /actualidad y /hemeroteca. El JS de cada página sigue
reemplazando esos fragmentos al cargar, así que la experiencia no cambia.

Uso (desde la raíz del repo):
    python3 scripts/render_estatico.py actualidad
    python3 scripts/render_estatico.py hemeroteca
    python3 scripts/render_estatico.py            # ambos

Solo usa la librería estándar. Los workflows lo ejecutan justo después de
regenerar actualidad.json y hemeroteca.json.
"""
import html
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDES = ROOT / "_includes"

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
MAX_NOTICIAS_ESTATICAS = 150


def leer(nombre):
    return json.loads((ROOT / nombre).read_text(encoding="utf-8"))


def escribir(nombre, contenido):
    INCLUDES.mkdir(exist_ok=True)
    with open(INCLUDES / nombre, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("{% raw %}" + contenido + "{% endraw %}\n")


def esc(s):
    return html.escape(str(s), quote=True)


def ultimo_domingo(anio, mes):
    d = datetime(anio, mes + 1, 1) - timedelta(days=1) if mes < 12 else datetime(anio, 12, 31)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def a_hora_madrid(iso):
    """Convierte un ISO UTC a hora local de Madrid (CET/CEST) sin tzdata."""
    t = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    inicio = ultimo_domingo(t.year, 3).replace(hour=1)
    fin = ultimo_domingo(t.year, 10).replace(hour=1)
    return t + timedelta(hours=2 if inicio <= t < fin else 1)


def medio_slug(medio):
    import re
    import unicodedata
    s = unicodedata.normalize("NFD", medio.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s)


def rango(desde, hasta):
    if not desde:
        return ""
    return desde if desde == hasta else f"{desde} – {hasta}"


def actualidad():
    d = leer("actualidad.json")
    periodo = f"{d.get('total_urls_analizadas')} noticias analizadas"
    if d.get("periodo_cubierto"):
        periodo += f" · del {d['periodo_cubierto']['desde']} al {d['periodo_cubierto']['hasta']}"
    escribir("actualidad-periodo.html", esc(periodo))

    # El resumen y los ejemplos pueden llevar HTML propio del pipeline (igual que en el JS).
    resumen = "".join(f"<p>{p}</p>" for p in (d.get("resumen") or "").split("\n\n"))
    escribir("actualidad-resumen.html", resumen)

    cards = []
    for c in d.get("conceptos_destacados") or []:
        ejemplos = "".join(f"<li>{e}</li>" for e in c.get("ejemplos_redactados") or [])
        cards.append(
            '<div class="concepto-card"><div class="concepto-top">'
            f'<span class="concepto-nombre">{c["concepto"]}</span>'
            f'<span class="concepto-piezas">{c["piezas"]} noticias</span></div>'
            f'<div class="concepto-meta">{c["seccion_principal"].replace("-", " ")} · {rango(c.get("desde"), c.get("hasta"))}</div>'
            f'<ul class="concepto-ejemplos">{ejemplos}</ul></div>')
    escribir("actualidad-conceptos.html", "".join(cards))
    print(f"actualidad: {len(cards)} conceptos, resumen de {len(resumen)} caracteres")


def hemeroteca():
    d = leer("hemeroteca.json")
    noticias = (d.get("noticias") or [])[:MAX_NOTICIAS_ESTATICAS]
    gen = a_hora_madrid(d["generado_en"]) if d.get("generado_en") else None
    gen_txt = f" · actualizado {gen:%d/%m %H:%M}" if gen else ""
    meta = f"{d.get('total')} publicaciones de los últimos {d.get('dias_ventana')} días · {', '.join(d.get('medios') or [])}{gen_txt}"
    escribir("hemeroteca-meta.html", esc(meta))

    out, dia_actual = [], None
    for n in noticias:
        if n["fecha"] != dia_actual:
            if dia_actual is not None:
                out.append("</ul></div>")
            dia_actual = n["fecha"]
            y, m, dd = map(int, n["fecha"].split("-"))
            sem = DIAS_SEMANA[datetime(y, m, dd).weekday()].capitalize()
            out.append(f'<div class="hemeroteca-dia" data-dia="{n["fecha"]}"><h2 class="hemeroteca-dia-titulo">'
                       f'{sem}, {dd} de {MESES[m - 1]} de {y}</h2><ul class="hemeroteca-lista">')
        texto = f'{n["titulo"]} {n["medio"]}'.lower()
        hora = a_hora_madrid(n["fecha_hora"]).strftime("%H:%M")
        out.append(
            f'<li class="hemeroteca-item" data-texto="{esc(texto)}"><span class="hemeroteca-hora">{hora}</span>'
            f'<a class="hemeroteca-titulo" href="{esc(n["url"])}" target="_blank" rel="nofollow noopener noreferrer">{esc(n["titulo"])}</a>'
            f'<span class="hemeroteca-medio hemeroteca-medio--{medio_slug(n["medio"])}">{esc(n["medio"])}</span></li>')
    if dia_actual is not None:
        out.append("</ul></div>")
    escribir("hemeroteca-listado.html", "".join(out))
    print(f"hemeroteca: {len(noticias)} titulares estáticos de {d.get('total')}")


if __name__ == "__main__":
    objetivos = sys.argv[1:] or ["actualidad", "hemeroteca"]
    for o in objetivos:
        {"actualidad": actualidad, "hemeroteca": hemeroteca}[o]()
