#!/usr/bin/env python3
"""Construye los datos de votaciones del Pleno a partir de
scripts/politicos/pleno/fuentes/votaciones_pleno.json (parse_actas.py):

  _data/pleno/votaciones.json   votaciones, sesiones y resumen por grupo
  _data/pleno/personas.json     agregados por concejal (asistencia y voto)

Regla de atribución del voto a una persona (el acta registra el voto por grupo):
  * PP / PSOE: se atribuye el voto del grupo SOLO si el número de concejales con
    el que vota el grupo coincide con los presentes de ese grupo en la cabecera
    del acta (si alguien abandona la sala a mitad de sesión, no se atribuye).
  * Concejales de origen Vox: voto por nombre si el acta los nombra; si no, el voto del
    Grupo Vox / Grupo Mixto cuando el recuento cuadra con los presentes sin nombrar.
  * Asistencia = aparece en la cabecera del acta y no consta como excusado.

Uso: PYTHONUTF8=1 python3 scripts/politicos/pleno/build_pleno.py
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "scripts/politicos/pleno/fuentes/votaciones_pleno.json"
OUT_DIR = ROOT / "_data" / "pleno"

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_actas import PERSONAS, GRUPO_DE  # noqa: E402

SLUG = {k: v for k, v in PERSONAS.items() if v}
CLAVE_DE_SLUG = {v: k for k, v in SLUG.items()}
# primera sesión en la que cada concejal forma parte del Pleno
INICIO = {"maria-de-los-angeles-carpio-perez": "2024-07-26", "cesar-gomez-barthe-celada": "2026-07-30"}
NO_PROCESADAS = [
    {"fecha": "2023-06-17", "sesion": "Extraordinaria 8/2023 (constitución del Ayuntamiento)", "motivo": "acta escaneada sin texto; no se aplica OCR"},
    {"fecha": "2024-02-09", "sesion": "Ordinaria 1/2024", "motivo": "acta escaneada sin texto; no se aplica OCR"},
    {"fecha": "2024-03-22", "sesion": "Ordinaria 7/2024", "motivo": "acta escaneada sin texto; no se aplica OCR"},
]
SENT = {"favor": "a favor", "contra": "en contra", "abstencion": "abstención", "blanco": "en blanco"}


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def dmy(f):
    return f"{f[8:10]}-{f[5:7]}-{f[0:4]}"


def es_pct(x):
    return None if x is None else (f"{x:.1f}".replace(".", ",") + " %")


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    sesiones_ok = [s for s in data["sesiones"] if s.get("fecha") and len(s["presentes"]) > 1 and s["fecha"] >= "2023-06-18"]
    sesiones_ok.sort(key=lambda s: s["fecha"])
    votaciones, ses_out = [], []
    # sentido por grupo y persona de cada votación
    for s in sesiones_ok:
        pres = set(s["presentes"])
        pres_slug = {SLUG[k] for k in pres if k in SLUG}
        pres_g = Counter(GRUPO_DE[k] for k in pres)
        sid = s["fecha"]
        nvot = 0
        for it in s["items"]:
            for n, v in enumerate(it["votaciones"]):
                if "sin_votacion" in v["info"] and not v["unanimidad"]:
                    continue
                nvot += 1
                grupos, indiv = {}, {}
                if v["unanimidad"]:
                    grupos = {"PP": "favor", "PSOE": "favor", "Vox": "favor", "Mixto": "favor"}
                else:
                    for x in v["votos"]:
                        if x["tipo"] == "grupo":
                            grupos[x["sujeto"]] = (x["sentido"], x["n"])
                        else:
                            indiv[x["sujeto"]] = x["sentido"]
                    grupos = {g: (t[0] if isinstance(t, tuple) else t) for g, t in grupos.items()}
                    gn = {x["sujeto"]: x["n"] for x in v["votos"] if x["tipo"] == "grupo"}
                # voto por persona
                personas = {}
                for k in pres:
                    sl = SLUG.get(k)
                    if not sl:
                        continue
                    g = GRUPO_DE[k]
                    if v["unanimidad"]:
                        personas[sl] = "favor"
                        continue
                    if sl in indiv:
                        personas[sl] = indiv[sl]
                    elif g in ("PP", "PSOE"):
                        if g in grupos and gn.get(g) == pres_g[g]:
                            personas[sl] = grupos[g]
                    else:  # origen Vox sin nombrar
                        sin_nombrar = [kk for kk in pres if GRUPO_DE[kk] == "Vox" and SLUG.get(kk) not in indiv]
                        vg = [t for t in ("Vox", "Mixto") if t in grupos]
                        if len(vg) == 1 and gn.get(vg[0]) == len(sin_nombrar):
                            personas[sl] = grupos[vg[0]]
                tot = v["recuento"]
                votaciones.append({
                    "id": f"{sid}#{it['punto']}" + (f"/{n + 1}" if len(it["votaciones"]) > 1 else ""),
                    "fecha": sid, "sesion": s.get("numero"), "punto": it["punto"], "titulo": it["titulo"],
                    "tipo": it["tipo"], "proponente": it["proponente"], "ambito": v["ambito"],
                    "unanimidad": v["unanimidad"], "resultado": v["resultado"],
                    "recuento": {"favor": tot["favor"], "contra": tot["contra"], "abstencion": tot["abstencion"]},
                    "voto_grupos": grupos, "voto_individual": indiv,
                    "voto_personas": personas, "video": it["video"], "acta": s["url"],
                    "cuadra_con_acta": not v["qa"], "nota_calidad": "; ".join(v["qa"]) or None,
                    "texto_resultado": v["texto"],
                })
        ses_out.append({"fecha": sid, "tipo": s["tipo"], "numero": s["numero"], "acta": s["url"],
                        "presentes": sorted(pres_slug), "presentes_n": len(pres), "votaciones": nvot})

    fondo = [v for v in votaciones if v["ambito"] != "urgencia"]
    no_unan = [v for v in fondo if not v["unanimidad"]]

    # -------- resumen por grupo (votos de grupo explícitos en el acta)
    def stats_grupo(etq, claves):
        c = Counter()
        for v in no_unan:
            for k in claves:
                if k in v["voto_grupos"]:
                    c[v["voto_grupos"][k]] += 1
                    break
        n = sum(c.values())
        return {"grupo": etq, "votaciones_no_unanimes": n, "favor": c["favor"], "contra": c["contra"], "abstencion": c["abstencion"],
                "pct_favor": pct(c["favor"], n), "pct_contra": pct(c["contra"], n), "pct_abstencion": pct(c["abstencion"], n)}

    def coincide(claves_a, claves_b):
        n = ok = 0
        for v in no_unan:
            a = next((v["voto_grupos"][k] for k in claves_a if k in v["voto_grupos"]), None)
            b = next((v["voto_grupos"][k] for k in claves_b if k in v["voto_grupos"]), None)
            if a and b:
                n += 1
                ok += a == b
        return {"votaciones": n, "coinciden": ok, "pct": pct(ok, n)}

    resumen_grupos = [stats_grupo("PP", ["PP"]), stats_grupo("PSOE", ["PSOE"]), stats_grupo("Vox / Grupo Mixto (Vox)", ["Vox", "Mixto"])]
    coincidencias = {"PSOE_con_PP": coincide(["PSOE"], ["PP"]), "Vox_Mixto_con_PP": coincide(["Vox", "Mixto"], ["PP"]),
                     "Vox_Mixto_con_PSOE": coincide(["Vox", "Mixto"], ["PSOE"])}

    # -------- mociones por proponente
    motiv = defaultdict(lambda: Counter())
    ultimo = {}
    for v in votaciones:
        if v["tipo"] == "moción" and v["ambito"] == "fondo" and v["proponente"]:
            ultimo[(v["fecha"], v["punto"])] = v  # una votación de fondo por moción: la última del punto
    for v in ultimo.values():
        motiv[v["proponente"]]["total"] += 1
        motiv[v["proponente"]]["aprobadas" if v["resultado"] == "aprobado" else "rechazadas"] += 1
    mociones = [{"proponente": k, "votadas": c["total"], "aprobadas": c["aprobadas"], "rechazadas": c["rechazadas"],
                 "pct_aprobadas": pct(c["aprobadas"], c["total"])} for k, c in sorted(motiv.items(), key=lambda kv: -kv[1]["total"])]
    conteo_tipos = Counter(v["tipo"] for v in fondo)

    # -------- agregados por persona
    personas = {}
    for sl, k in CLAVE_DE_SLUG.items():
        ini = INICIO.get(sl, "2023-06-18")
        if sl in INICIO:  # entra a mitad de mandato: se cuenta desde la primera acta en la que figura presente
            ini = min([x["fecha"] for x in ses_out if sl in x["presentes"]] or [ini])
        mis_ses = [s for s in ses_out if s["fecha"] >= ini]
        asist = [s for s in mis_ses if sl in s["presentes"]]
        mis_v = [v for v in fondo if v["fecha"] >= ini]
        computables = [v for v in mis_v if sl in v["voto_personas"]]
        c = Counter(v["voto_personas"][sl] for v in computables)
        cn = [v for v in computables if not v["unanimidad"]]
        def coin(claves):
            n = ok = 0
            for v in cn:
                b = next((v["voto_grupos"][x] for x in claves if x in v["voto_grupos"]), None)
                if b:
                    n += 1
                    ok += v["voto_personas"][sl] == b
            return {"votaciones": n, "coinciden": ok, "pct": pct(ok, n)}
        nominal = sum(1 for v in computables if sl in v["voto_individual"])
        g = GRUPO_DE[k]
        nn = len(cn)
        resumen = None
        if computables:
            resumen = (f"Entre el {dmy(ini) if ini > '2023-06-18' else '27-06-2023'} y el {dmy(mis_ses[-1]['fecha'])}, consta en la cabecera de {len(asist)} de las "
                       f"{len(mis_ses)} actas de Pleno analizadas ({es_pct(pct(len(asist), len(mis_ses)))}). En {len(computables)} votaciones de fondo con voto atribuible, "
                       f"votó a favor en {c['favor']}, en contra en {c['contra']} y se abstuvo en {c['abstencion']}.")
        personas[sl] = {
            "periodo_desde": ini, "periodo_hasta": ses_out[-1]["fecha"],
            "sesiones_analizadas": len(mis_ses), "sesiones_presente": len(asist), "asistencia_pct": pct(len(asist), len(mis_ses)),
            "votaciones_de_fondo": len(mis_v), "votaciones_con_voto_atribuible": len(computables),
            "favor": c["favor"], "contra": c["contra"], "abstencion": c["abstencion"],
            "pct_favor": pct(c["favor"], len(computables)), "pct_contra": pct(c["contra"], len(computables)), "pct_abstencion": pct(c["abstencion"], len(computables)),
            "votaciones_no_unanimes": nn,
            "coincide_con_voto_del_PP": coin(["PP"]), "coincide_con_voto_del_PSOE": coin(["PSOE"]),
            "votos_registrados_por_nombre": nominal, "grupo_en_acta": g,
            "texto_resumen": resumen,
        }

    meta = {
        "titulo": "Votaciones del Pleno del Ayuntamiento de Salamanca, mandato 2023-2027",
        "generado": "2026-11-25",
        "fuente": "Actas de los Plenos Municipales (anonimizadas), Ayuntamiento de Salamanca",
        "fuente_url": "https://www.aytosalamanca.es/w/actas-de-los-plenos-municipales",
        "periodo": f"{ses_out[0]['fecha']} a {ses_out[-1]['fecha']}",
        "sesiones_analizadas": len(ses_out), "votaciones": len(votaciones),
        "votaciones_que_cuadran_con_el_recuento_del_acta": sum(1 for v in votaciones if v["cuadra_con_acta"]),
        "votaciones_de_fondo_no_unanimes": len(no_unan), "votaciones_unanimes_de_fondo": len(fondo) - len(no_unan),
        "tipos_de_votacion_de_fondo": dict(conteo_tipos),
        "sesiones_no_procesadas": NO_PROCESADAS,
        "votaciones_sin_proponente": sum(1 for v in ultimo.values()) and sum(1 for v in votaciones if v["tipo"] == "moción" and v["ambito"] == "fondo" and not v["proponente"]),
        "metodo": [
            "Se extraen las cláusulas «El Excmo. Ayuntamiento Pleno, con el voto a favor del Grupo X [N concejales]… acuerda…» de cada acta.",
            "Cada votación se valida contra el recuento que declara el propio acta («con 16 votos a favor») y contra los concejales presentes en la cabecera.",
            "El acta registra el voto por grupo; el voto de cada persona se atribuye solo cuando el recuento de su grupo coincide con los presentes de ese grupo.",
            "Las votaciones sobre urgencia se cuentan aparte; los puntos sin votación (toma de conocimiento, ruegos y preguntas) no se incluyen.",
        ],
        "limitaciones": [
            "Tres actas son imágenes escaneadas sin texto y no se han procesado (constitución del Pleno de 17-06-2023, 09-02-2024 y 22-03-2024).",
            "Las actas de las sesiones de sorteo de mesas electorales no recogen votación.",
            "Cuando un concejal abandona la sala a mitad de sesión, su voto no se atribuye: el acta solo da el recuento del grupo.",
            "El sentido del voto no mide el contenido de cada propuesta: se registra el voto, no su motivación.",
        ],
        "licencia": "CC BY 4.0 (citar «Open Salamanca» y enlazar la fuente)",
    }
    por = {m["proponente"]: m for m in mociones}
    resumen = {"grupos": resumen_grupos, "coincidencias": coincidencias, "mociones_por_grupo": mociones, "mociones_psoe": por["PSOE"], "mociones_pp": por["PP"]}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # el voto individual y la URL del acta por votación se derivan de los grupos y de la sesión: no se publican
    publico = [{k: v for k, v in x.items() if k not in ("voto_personas", "acta")} for x in votaciones]
    (OUT_DIR / "votaciones.json").write_text(json.dumps({"meta": meta, "resumen": resumen, "sesiones": ses_out, "votaciones": publico}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (OUT_DIR / "personas.json").write_text(json.dumps(personas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("sesiones", len(ses_out), "votaciones", len(votaciones), "de fondo", len(fondo), "no unánimes", len(no_unan))
    print(json.dumps(resumen, ensure_ascii=False, indent=1)[:2600])


if __name__ == "__main__":
    main()
