"""Bloque 'cifras de la declaración de bienes inicial (2023)' para las fichas.

Lee scripts/politicos/fuentes/declaraciones_2023.json (generado por extraer_declaraciones_2023.py)
y devuelve, por URL de ficha oficial, el bloque estructurado y su texto citable.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_RUTA = ROOT / "scripts" / "politicos" / "fuentes" / "declaraciones_2023.json"
DATOS = json.loads(_RUTA.read_text(encoding="utf-8"))["por_ficha"] if _RUTA.exists() else {}

LIMITES = [
    "Solo se agregan los valores que se pueden leer sin ambigüedad en el PDF: valor catastral de los inmuebles, nº de vehículos y deudas.",
    "La suma de valores catastrales no pondera por el % de participación ni equivale al valor de mercado.",
    "El patrimonio mobiliario (acciones, planes de pensiones, seguros) se indica solo por categorías: los PDF mezclan euros y nº de acciones y las columnas salen desalineadas, así que no se suman importes.",
    "Es la declaración presentada al inicio del mandato; las anuales posteriores solo recogen variaciones.",
]


def es(n):
    s = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s[:-3] if s.endswith(",00") else s


def _plural(n, uno, varios):
    return f"{n} {uno if n == 1 else varios}"


def bloque(url_ficha, nombre):
    d = DATOS.get(url_ficha)
    if not d:
        return None
    fuente = {"t": f"Ayuntamiento de Salamanca: {d.get('titulo_documento', 'declaración de bienes y actividades').rstrip('.')} (PDF)",
              "u": d.get("url_documento")}
    if d["estado"] != "ok":
        txt = (f"El documento de declaración de bienes inicial de {nombre} publicado por el Ayuntamiento es una imagen escaneada sin texto, "
               "por lo que sus cifras no se han transcrito. Puede consultarse en el PDF original.") if d["estado"] == "pdf_escaneado_sin_texto" else \
              f"No se ha encontrado en la ficha oficial de {nombre} el documento de declaración inicial de 2023."
        return {"estado": d["estado"], "texto_resumen": txt, "fuente": fuente if fuente["u"] else None}
    inm, mob, veh, deu = d["inmuebles"], d["mobiliario"], d["vehiculos"], d["deudas"]
    partes = []
    if inm["n_con_valor"]:
        partes.append(f"{_plural(inm['n_con_valor'], 'inmueble', 'inmuebles')} con valor catastral declarado "
                      f"(suma de {es(inm['suma_valores_catastrales_eur'])} €, sin ponderar por el % de participación)")
    else:
        partes.append("ningún inmueble con valor catastral")
    partes.append(_plural(veh["n"], "vehículo", "vehículos") if veh["n"] else "ningún vehículo")
    partes.append("patrimonio mobiliario en " + " y en ".join(mob["categorias"]) if mob["declara"] else "ningún patrimonio mobiliario")
    if deu["declara"]:
        partes.append(f"{_plural(deu['n'], 'deuda', 'deudas')} por un importe actual conjunto de {es(deu['suma_eur'])} €")
    else:
        partes.append("ninguna deuda")
    pres = d.get("fecha_presentacion")
    txt = f"En su declaración de bienes inicial del mandato 2023-2027{f' (presentada el {pres})' if pres else ''}, {nombre} declara: " + "; ".join(partes) + "."
    return {
        "estado": "ok", "tipo_documento": d["tipo_documento"], "fecha_presentacion": pres,
        "inmuebles": {"n_con_valor_catastral": inm["n_con_valor"], "valores_catastrales_eur": inm["valores_catastrales_eur"],
                      "suma_valores_catastrales_eur": inm["suma_valores_catastrales_eur"],
                      "suma_valores_catastrales_texto": es(inm["suma_valores_catastrales_eur"]) + " €"},
        "patrimonio_mobiliario": {"declara": mob["declara"], "categorias": mob["categorias"]},
        "vehiculos": veh["n"],
        "otros_bienes_de_especial_valor": d["otros_bienes"]["declara"],
        "deudas": {"n": deu["n"], "importes_actuales_eur": deu["importes_eur"], "suma_eur": deu["suma_eur"],
                   "suma_texto": es(deu["suma_eur"]) + " €"},
        "texto_resumen": txt, "limitaciones": LIMITES, "fuente": fuente,
    }
