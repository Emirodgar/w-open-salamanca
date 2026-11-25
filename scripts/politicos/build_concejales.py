#!/usr/bin/env python3
"""Genera las fichas de los concejales del Ayuntamiento de Salamanca (mandato
2023-2027) excepto la del alcalde (build_carbayo.py):

  _data/politicos/<slug>.json            fuente única de cada ficha
  elecciones/politicos/<slug>.html       página (layout politico)
  elecciones/politicos/<slug>-json.json  descarga del JSON
  _data/concejales_indice.json           índice ordenado (alimenta el listado)
  llms.txt                               bloque entre marcadores

Entradas: scripts/politicos/fuentes/fichas_oficiales.json (parse_fichas.py),
retribuciones 2025 del Ayuntamiento (PDF oficial, transcritas abajo),
concejales-salamanca.json (mandatos) y hechos de prensa citados en cada ficha.

Uso (desde la raíz del sitio):
    PYTHONUTF8=1 python3 scripts/politicos/parse_fichas.py      # opcional, refresca
    PYTHONUTF8=1 python3 scripts/politicos/build_carbayo.py
    PYTHONUTF8=1 python3 scripts/politicos/build_concejales.py
"""
import json
import re
import unicodedata
from pathlib import Path
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent))
import fechas as FE  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FECHA_ACT = FE.iso()
FECHA_ACT_TXT = FE.largo()
BASEURL = "https://opensalamanca.es/elecciones/politicos/"


def es(n, dec=0):
    s = f"{n:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if c.isalnum() or c == " ")


# ------------------------------------------------------------------ fuentes
S = {
    "corp": {"t": "Ayuntamiento de Salamanca: Corporación municipal", "u": "https://www.aytosalamanca.es/corporacion-municipal"},
    "retrib": {"t": "Ayuntamiento de Salamanca: retribuciones percibidas por los miembros de la Corporación en 2025 (PDF)", "u": "https://www.aytosalamanca.es/documents/d/guest/02-retribuciones-percibidas-miembros-corporacion-2025"},
    "transp": {"t": "Ayuntamiento de Salamanca: Portal de Transparencia", "u": "https://www.aytosalamanca.es/transparencia"},
    "os_conc": {"t": "Open Salamanca: concejales del Ayuntamiento de Salamanca por mandato", "u": "https://opensalamanca.es/concejales-ayuntamiento-salamanca"},
    "wiki_ayto": {"t": "Wikipedia (es): Ayuntamiento de Salamanca", "u": "https://es.wikipedia.org/wiki/Ayuntamiento_de_Salamanca"},
    "tribuna27": {"t": "Tribuna de Salamanca: estos son los 27 concejales que dirigirán Salamanca (2023)", "u": "https://www.tribunasalamanca.com/noticias/332749/estos-son-los-27-concejales-que-dirigiran-salamanca"},
    "reparto_es": {"t": "El Español (19-06-2023): competencias de los concejales del equipo de gobierno", "u": "https://www.elespanol.com/castilla-y-leon/region/salamanca/20230619/competencias-concejales-equipo-gobierno-salamanca/772673033_0.html"},
    "reparto_gaceta": {"t": "La Gaceta de Salamanca (19-06-2023): Carbayo reparte las concejalías", "u": "https://www.lagacetadesalamanca.es/salamanca/carbayo-reparte-concejalias-ayuntamiento-salamanca-20230619163234-nt.html"},
    "reparto_tv": {"t": "SALAMANCArtv AL DÍA (19-06-2023): así quedan las concejalías", "u": "https://salamancartvaldia.es/noticia/2023-06-19-asi-quedan-las-concejalias-en-el-ayuntamiento-de-salamanca-324554"},
    "psoe_eldiario": {"t": "eldiario.es: María Sánchez releva a José Luis Mateos en la portavocía del PSOE (2026)", "u": "https://www.eldiario.es/castilla-y-leon/provincias/salamanca/cambios-psoe-ayuntamiento-salamanca-maria-sanchez-releva-jose-luis-mateos-portavocia_1_13202004.html"},
    "psoe_hoy": {"t": "Salamancahoy (7-05-2026): el PSOE de Salamanca tiene nueva portavoz, María Sánchez", "u": "https://www.salamancahoy.es/salamanca/ciudad/psoe-salamanca-nueva-portavoz-maria-sanchez-relevara-20260507094220-nt_amp.html"},
    "psoe_gaceta": {"t": "La Gaceta de Salamanca (6-05-2026): el PSOE releva a José Luis Mateos como portavoz municipal", "u": "https://www.lagacetadesalamanca.es/salamanca/psoe-relega-jose-luis-mateos-portavoz-municipal-20260506181944-nt.html"},
    "vox_eldiario": {"t": "eldiario.es: Vox rompe en Salamanca, concejales críticos destituyen al portavoz municipal (2025)", "u": "https://www.eldiario.es/castilla-y-leon/provincias/salamanca/vox-rompe-salamanca-concejales-criticos-destituyen-portavoz-municipal_1_12042242.html"},
    "vox_infobae": {"t": "Infobae/Europa Press (24-02-2025): Vox se queda sin grupo municipal en el Ayuntamiento de Salamanca", "u": "https://www.infobae.com/espana/agencias/2025/02/24/vox-se-queda-sin-grupo-municipal-en-el-ayuntamiento-de-salamanca-por-su-crisis-interna/"},
    "magdalena": {"t": "La Gaceta de Salamanca (27-06-2024): Laura Magdalena (Vox) renuncia al acta de concejal", "u": "https://www.lagacetadesalamanca.es/salamanca/laura-magdalena-vox-renuncia-acta-concejal-ayuntamiento-20240627150608-nt.html"},
    "cope_carpio": {"t": "COPE (26-07-2024): María de los Ángeles Carpio Pérez, nueva concejala de Vox", "u": "https://www.cope.es/actualidad/espana/noticias/maria-los-angeles-carpio-perez-nueva-concejala-vox-ayuntamiento-salamanca-20240726_3418351"},
    "gb_ayto": {"t": "Ayuntamiento de Salamanca: César Gómez Barthe Celada toma posesión como nuevo concejal", "u": "https://www.aytosalamanca.es/w/c%C3%A9sar-g%C3%B3mez-barthe-celada-toma-posesi%C3%B3n-como-nuevo-concejal-del-ayuntamiento-de-salamanca"},
    "gb_es": {"t": "El Español (30-07-2026): César Gómez Barthe se incorpora como concejal y asume Comercio y Juventud", "u": "https://www.elespanol.com/castilla-y-leon/region/salamanca/20260730/cesar-gomez-barthe-incorpora-concejal-ayuntamiento-salamanca-asume-comercio-juventud/1003744339657_0.html"},
    "gb_tv": {"t": "SALAMANCArtv AL DÍA (30-07-2026): César Gómez-Barthe toma posesión como concejal de Promoción Económica y Juventud", "u": "https://salamancartvaldia.es/noticia/2026-07-30-cesar-gomez-barthe-toma-posesion-como-concejal-de-promocion-economica-y-juventud-394984"},
    "actas": {"t": "Ayuntamiento de Salamanca: actas de los Plenos Municipales", "u": "https://www.aytosalamanca.es/w/actas-de-los-plenos-municipales"},
    "votaciones": {"t": "Open Salamanca: votaciones del Pleno del Ayuntamiento de Salamanca, mandato 2023-2027", "u": "https://opensalamanca.es/elecciones/politicos/votaciones-pleno"},
    "carbayo": {"t": "Open Salamanca: ficha de Carlos García Carbayo, alcalde de Salamanca", "u": "https://opensalamanca.es/elecciones/politicos/carlos-garcia-carbayo"},
}

# ----------------------------------------- retribuciones 2025 (PDF oficial)
# importe bruto anual en euros; True = marcado con asterisco («dedicaciones exclusivas / parciales»)
RET = {
    "ANTOLIN MONTERO, ALVARO": (12562.62, False), "CARABIAS ACOSTA, JOSE FERNANDO": (78930.20, True),
    "CARPIO PEREZ, MARIA ANGELES": (23188.20, False), "COCA SANCHEZ, MARIA JOSE": (23138.70, False),
    "COLLADOS GRANDE, JOSE MARIA": (13965.70, False), "FERNANDEZ SILVA, ANGEL": (63982.96, True),
    "FRANCES SANCHEZ, FIDEL JUAN": (15691.20, False), "FUENTES CHAVES, MARIA DEL MAR": (13693.12, False),
    "GARCIA CARBAYO, CARLOS MANUEL": (83022.96, True), "GARCIA GOMEZ, MARIA": (16405.20, False),
    "GARCIA MEILAN, JUAN JOSE": (14050.12, False), "MACIAS TELLO, MARIA ISABEL": (22841.20, False),
    "MARTIN PARRA, ROBERTO ANGEL": (63982.96, True), "MARTINEZ CORDOBA, PEDRO JOSE": (23852.70, False),
    "MATEOS CRESPO, JOSE LUIS": (29681.64, True), "MOLINA MARTINEZ, ANGEL": (23733.70, False),
    "PARRES CABRERA, ALMUDENA": (78930.20, True), "PEREZ DE LA SOTA, ALEJANDRO MIGUEL": (17654.70, False),
    "RIVAS SERRANO, IGNACIO JAVIER": (63982.96, True), "RODRIGUEZ ALONSO, FERNANDO JAVIER": (78930.20, True),
    "RODRIGUEZ LOPEZ, MYRIAM": (24551.35, False), "SANCHEZ AREVALO, LUIS": (22960.20, False),
    "SANCHEZ GOMEZ, MARIA": (13990.62, False), "SANCHEZ SANCHEZ, ELVIRA": (14501.20, False),
    "SANTA MARIA TRIGO, MARIA JESUS": (13132.70, False), "SEGUIN KATTAN, MARIA DEL CARMEN": (78930.20, True),
    "VILLAR GUTIERREZ DE CEBALLOS, MARIA DE LA VEGA": (31991.54, True),
}
EJERCICIO_RETRIB = 2025  # el workflow avisa cuando el Ayuntamiento publique el listado del ejercicio siguiente
TOTAL_LISTADO = len(RET)  # 27
IMPORTES = sorted((v[0] for v in RET.values()), reverse=True)


def posicion(importe):
    mejor = 1 + sum(1 for x in IMPORTES if x > importe)
    empate = sum(1 for x in IMPORTES if x == importe) - 1
    txt = f"puesto {mejor} de {TOTAL_LISTADO}"
    if empate:
        txt += f", empatado con {empate} más" if empate > 1 else ", empatado con otro miembro"
    return txt


# ------------------------------------------------------------- las personas
# g: 'm'/'f'. rol: gobierno|oposicion. grupo: PP|PSOE|Vox.
GOB = "gobierno"
OPO = "oposicion"
PEOPLE = [
    dict(slug="almudena-parres-cabrera", match="parres cabrera", ret="PARRES CABRERA, ALMUDENA", g="f", grupo="PP", rol=GOB,
         nombre="María Almudena Parres Cabrera", hab="Almudena Parres Cabrera", pila="María Almudena", apell="Parres Cabrera",
         cargo="Primera teniente de alcalde y concejala delegada de Deportes", desde="2023-06-19",
         perfil="Licenciada en Filología Inglesa por la Universidad de Salamanca (2005); su ficha oficial recoge trabajo como técnico administrativo en la UPSA (1999-2000) y en banca (Unicaja, 2000).",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-19", "Primera teniente de alcalde y concejala de Deportes", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"]),
               ("2019-06-15", "Concejala de Participación Social y Voluntariado (2019-2023)", "Delegación que ocupó durante todo el mandato 2019-2023.", ["os_conc", "wiki_ayto"]),
               ("2015-06-13", "Concejala del gobierno municipal del PP (2015-2019)", "Área sin confirmar en las fuentes consultadas.", ["os_conc"])]),
    dict(slug="miryam-rodriguez-lopez", match="miryam rodriguez", ret="RODRIGUEZ LOPEZ, MYRIAM", g="f", grupo="PP", rol=GOB,
         nombre="Miryam Rodríguez López", hab="Miryam Rodríguez López", pila="Miryam", apell="Rodríguez López",
         cargo="Segunda teniente de alcalde y concejala delegada de Familia e Igualdad de Oportunidades", desde="2023-06-19",
         perfil="Licenciada en Derecho por la Universidad de Salamanca (2003) y funcionaria de carrera de la Junta de Castilla y León, donde ha sido jefa del Área de Administración de la Gerencia Territorial de Servicios Sociales de Salamanca.",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-19", "Segunda teniente de alcalde y concejala de Familia e Igualdad de Oportunidades", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"]),
               ("2019-07", "Cuarta teniente de alcalde y concejala de Medio Ambiente, Parques y Jardines (2019-2023)", "Teniente de alcalde desde julio de 2019.", ["os_conc", "wiki_ayto"])]),
    dict(slug="jose-fernando-carabias-acosta", match="carabias acosta", ret="CARABIAS ACOSTA, JOSE FERNANDO", g="m", grupo="PP", rol=GOB,
         nombre="José Fernando Carabias Acosta", hab="Fernando Carabias Acosta", pila="José Fernando", apell="Carabias Acosta",
         cargo="Tercer teniente de alcalde y concejal delegado de Fomento, Gestión Urbana y Policía Administrativa", desde="2023-06-19",
         perfil="Licenciado en Ciencias Matemáticas por la Universidad de Granada (1980); fue profesor de Matemáticas en Secundaria (1981-2003) e inspector de Educación de la Junta de Castilla y León desde 2004.",
         alumni=["Universidad de Granada"],
         tray=[("2023-06-19", "Tercer teniente de alcalde y concejal de Fomento, Urbanismo, Policía Administrativa, Mantenimiento, Alumbrado y Coordinación Territorial", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo. La ficha oficial resume el área como «Fomento, Gestión Urbana, Policía Administrativa».", ["reparto_es", "reparto_gaceta", "reparto_tv"]),
               ("2021-06", "Suma Fomento y Patrimonio a su delegación (2021-2023)", "Desde junio de 2021 compaginó Protección Ciudadana, Tráfico y Transportes con Fomento y Patrimonio.", ["os_conc"]),
               ("2019-06-15", "Concejal de Protección Ciudadana, Tráfico y Transportes (2019-2023)", "Delegación que ocupó durante el mandato 2019-2023.", ["os_conc", "wiki_ayto"])]),
    dict(slug="fernando-javier-rodriguez-alonso", match="rodriguez alonso", ret="RODRIGUEZ ALONSO, FERNANDO JAVIER", g="m", grupo="PP", rol=GOB,
         nombre="Fernando Javier Rodríguez Alonso", hab="Fernando Rodríguez Alonso", pila="Fernando Javier", apell="Rodríguez Alonso",
         cargo="Cuarto teniente de alcalde y concejal delegado de Hacienda, Régimen Interior y Contratación", desde="2023-06-19",
         perfil="Licenciado en Derecho por la Universidad de Salamanca (1991); fue abogado (1992-1995) y profesor asociado en la Universidad de Salamanca (1995-2004).",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-19", "Cuarto teniente de alcalde y concejal de Hacienda, Régimen Interior y Contratación", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"]),
               ("2015-06-13", "Concejal de Hacienda (2015-2019)", "El decreto exacto de 2015 no está confirmado en las fuentes consultadas.", ["os_conc"])]),
    dict(slug="maria-del-carmen-seguin-kattan", match="seguin kattan", ret="SEGUIN KATTAN, MARIA DEL CARMEN", g="f", grupo="PP", rol=GOB,
         nombre="María del Carmen Seguín Kattán", hab="Carmen Seguín Kattán", pila="María del Carmen", apell="Seguín Kattán",
         cargo="Quinta teniente de alcalde y concejala delegada de Relaciones Institucionales, Festejos y Tradiciones", desde="2023-06-19",
         perfil="Licenciada en Ciencias de la Comunicación (Periodismo); fue redactora y presentadora de televisión en Mérida, Málaga, Valladolid y Ecuador, jefa de Prensa de la Consejería de Salud de Extremadura y directora de Comunicación del Ayuntamiento de Salamanca.",
         alumni=[],
         tray=[("2023-06-19", "Quinta teniente de alcalde y concejala de Relaciones Institucionales, Festejos y Tradiciones", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"])]),
    dict(slug="angel-molina-martinez", match="molina martinez", ret="MOLINA MARTINEZ, ANGEL", g="m", grupo="PP", rol=GOB,
         nombre="Ángel Molina Martínez", hab="Ángel Molina Martínez", pila="Ángel", apell="Molina Martínez",
         cargo="Concejal delegado de Protección Ciudadana, Tráfico y Transportes", desde="2023-06-19",
         perfil="Doctor (2009), licenciado en Psicopedagogía (2003) y diplomado en Educación Social (2000) por la Universidad de Salamanca; técnico superior en prevención de riesgos laborales, fue vicepresidente nacional del Consejo General de Profesionales de Seguridad y Salud en el Trabajo (2013-2016).",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-19", "Concejal de Protección Ciudadana, Tráfico y Transportes", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"])]),
    dict(slug="maria-jose-coca-sanchez", match="coca sanchez", ret="COCA SANCHEZ, MARIA JOSE", g="f", grupo="PP", rol=GOB,
         nombre="María José Coca Sánchez", hab="María José Coca Sánchez", pila="María José", apell="Coca Sánchez",
         cargo="Concejala delegada de Medio Ambiente y Oficina de Bienestar Animal", desde="2023-06-19",
         perfil="Licenciada en Derecho por la Universidad de Salamanca (2000), con un máster en Derecho de las Nuevas Tecnologías; funcionaria de la Junta de Castilla y León y técnico jurídico en la Gerencia Territorial de Servicios Sociales de Salamanca.",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-19", "Concejala de Medio Ambiente y Bienestar Animal", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"])]),
    dict(slug="maria-de-la-vega-villar", match="vega villar", ret="VILLAR GUTIERREZ DE CEBALLOS, MARIA DE LA VEGA", g="f", grupo="PP", rol=GOB,
         nombre="María de la Vega Villar Gutiérrez de Ceballos", hab="Vega Villar", pila="María de la Vega", apell="Villar Gutiérrez de Ceballos",
         cargo="Concejala delegada de Salud Pública", desde="2023-06-19",
         perfil="Licenciada en Geografía e Historia (Historia del Arte) por la Universidad de Salamanca (1986); trabajó 26 años en el ámbito de bibliotecas y literatura infantil y juvenil de la Fundación Germán Sánchez Ruipérez y es miembro del patronato de la Fundación FUNDANEED.",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-19", "Concejala de Salud Pública y Consumo", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo. La ficha oficial indica «Salud Pública».", ["reparto_es", "reparto_gaceta", "reparto_tv"])]),
    dict(slug="angel-fernandez-silva", match="fernandez silva", ret="FERNANDEZ SILVA, ANGEL", g="m", grupo="PP", rol=GOB,
         nombre="Ángel Fernández Silva", hab="Ángel Fernández Silva", pila="Ángel", apell="Fernández Silva",
         cargo="Concejal delegado de Cultura y Turismo", desde="2023-06-19",
         perfil="Doctor en Derecho por la Universidad de Salamanca (2019, cum laude) y profesor asociado de Derecho Constitucional; presidió Nuevas Generaciones del PP de Salamanca (2009-2021) y fue coordinador del Grupo Político del PP en el Ayuntamiento (2011-2021).",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-19", "Concejal de Cultura y Turismo", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"]),
               ("2021-06-04", "Concejal de Juventud (2021-2023)", "Entra en el pleno como sustituto de Daniel Llanos y asume Juventud hasta el final del mandato 2019-2023.", ["os_conc"])]),
    dict(slug="roberto-martin-parra", match="martin parra", ret="MARTIN PARRA, ROBERTO ANGEL", g="m", grupo="PP", rol=GOB,
         nombre="Roberto Martín Parra", hab="Roberto Martín Parra", pila="Roberto", apell="Martín Parra",
         cargo="Concejal delegado de Participación Social y Voluntariado", desde="2023-06-19",
         perfil="Licenciado en Derecho (abogado no ejerciente); fue responsable de la Asesoría de Vivienda del Espacio Joven (2010-2013) y asesor de Alcaldía y de la Junta de Gobierno Local del Ayuntamiento.",
         alumni=[],
         tray=[("2023-06-19", "Concejal de Participación Social y Voluntariado", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"])]),
    dict(slug="maria-isabel-macias-tello", match="macias tello", ret="MACIAS TELLO, MARIA ISABEL", g="f", grupo="PP", rol=GOB,
         nombre="María Isabel Macías Tello", hab="Isabel Macías Tello", pila="María Isabel", apell="Macías Tello",
         cargo="Concejala delegada de Mayores", desde="2023-06-19",
         perfil="Diplomada en Enfermería por la Universidad de Granada (1975); fue supervisora de Enfermería en el Hospital Clínico y el Complejo Universitario de Salamanca y profesora asociada de la Universidad Pontificia de Salamanca (2011-2016).",
         alumni=["Universidad de Granada"],
         tray=[("2023-06-19", "Concejala de Mayores", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"]),
               ("2019-06-15", "Concejala de Mayores (2019-2023)", "Delegación que ocupó durante todo el mandato 2019-2023.", ["os_conc", "wiki_ayto"]),
               ("2015-06-13", "Concejala del gobierno municipal del PP (2015-2019)", "Área sin confirmar en las fuentes consultadas.", ["os_conc"])]),
    dict(slug="luis-sanchez-arevalo", match="sanchez arevalo", ret="SANCHEZ AREVALO, LUIS", g="m", grupo="PP", rol=GOB,
         nombre="Luis Sánchez Arévalo", hab="Luis Sánchez Arévalo", pila="Luis", apell="Sánchez Arévalo",
         cargo="Concejal delegado de Educación", desde="2023-06-19",
         perfil="Licenciado en Matemáticas y diplomado en Estadística (2007); fue profesor de Secundaria, asesor de formación del CFIE de Salamanca (2012-2018) y asesor técnico docente de la Dirección Provincial de Educación desde 2018, con plaza de docente en el IES Lucía de Medrano.",
         alumni=[],
         tray=[("2023-06-19", "Concejal de Educación", "Reparto de concejalías del equipo de gobierno del PP tras la investidura de Carbayo.", ["reparto_es", "reparto_gaceta", "reparto_tv"])]),
    dict(slug="cesar-gomez-barthe-celada", match=None, ret=None, g="m", grupo="PP", rol=GOB,
         nombre="César Gómez-Barthe Celada", hab="César Gómez-Barthe", pila="César", apell="Gómez-Barthe Celada",
         cargo="Concejal delegado de Promoción Económica, Comercio, Mercados y Juventud", desde="2026-07-30",
         nacimiento=("1986-08-03", "3 de agosto de 1986", "León"),
         perfil="Nacido en León en 1986; licenciado en Derecho y en Ciencias Políticas y de la Administración por la Universidad de Salamanca, con un máster en Democracia y Buen Gobierno y otro en Dirección de Protocolo y Eventos (Universidad Camilo José Cela); abogado colegiado no ejerciente, fue responsable de Proyectos de la Asociación de Jóvenes Empresarios de Salamanca (2015-2019), asesor del Grupo Municipal Popular y secretario general de Nuevas Generaciones del PP de Salamanca (2012-2021).",
         alumni=["Universidad de Salamanca", "Universidad Camilo José Cela"],
         ficha=dict(url="https://www.aytosalamanca.es/w/c%C3%A9sar-g%C3%B3mez-barthe-celada-toma-posesi%C3%B3n-como-nuevo-concejal-del-ayuntamiento-de-salamanca",
                    texto="No tiene ficha propia en la Corporación municipal a fecha de consulta; los datos proceden de la nota oficial de su toma de posesión (30-07-2026), también recogida por El Español.",
                    formacion_oficial=["Licenciado en Derecho — Universidad de Salamanca", "Licenciado en Ciencias Políticas y de la Administración — Universidad de Salamanca",
                                       "Máster en Democracia y Buen Gobierno — Universidad de Salamanca",
                                       "Máster en Dirección de Protocolo, Producción, Organización y Diseño de Eventos — Universidad Camilo José Cela"],
                    otros_titulos=[],
                    actividad_profesional=["Abogado colegiado no ejerciente — Ilustre Colegio de la Abogacía de Salamanca",
                                           "Responsable de Proyectos — Asociación de Jóvenes Empresarios de Salamanca — 2015-2019",
                                           "Asesor del Grupo Municipal Popular — Ayuntamiento de Salamanca — hasta su toma de posesión"],
                    otras_actividades=["Secretario general de Nuevas Generaciones del Partido Popular de Salamanca — 2012-2021"]),
         tray=[("2026-07-30", "Toma posesión como concejal y asume Promoción Económica, Comercio, Mercados y Juventud", "Entra en la Corporación por la renuncia de Pedro Martínez Córdoba (PP), que dejó el acta el 6-07-2026 para asumir una responsabilidad política en Murcia.", ["gb_ayto", "gb_es", "gb_tv"]),
               ("2012", "Secretario general de Nuevas Generaciones del PP de Salamanca (2012-2021)", "Según la nota oficial de su toma de posesión.", ["gb_ayto"])],
         extra_nv=["Orden de los tenientes de alcalde y régimen de dedicación tras su incorporación (no consta en las fuentes consultadas).",
                   "Su ficha oficial individual en la Corporación municipal no estaba publicada a fecha de consulta."]),
    # ------------------------------------------------------------ PSOE
    dict(slug="jose-luis-mateos-crespo", match="mateos crespo", ret="MATEOS CRESPO, JOSE LUIS", g="m", grupo="PSOE", rol=OPO,
         nombre="José Luis Mateos Crespo", hab="José Luis Mateos Crespo", pila="José Luis", apell="Mateos Crespo",
         cargo="Concejal del Grupo Municipal Socialista (portavoz hasta el 7 de mayo de 2026)", desde="2023-06-17",
         perfil="Doctor en Derecho Constitucional por la Universidad de Salamanca (2022), licenciado en Derecho y en Administración y Dirección de Empresas, y profesor asociado de Derecho Constitucional en la USAL desde 2021.",
         alumni=["Universidad de Salamanca"],
         tray=[("2026-05-07", "Deja la portavocía del grupo socialista", "María Sánchez Gómez, hasta entonces viceportavoz, le sustituye como portavoz del PSOE en el Ayuntamiento; Mateos sigue como concejal.", ["psoe_eldiario", "psoe_hoy", "psoe_gaceta"]),
               ("2023-06-17", "Concejal del PSOE y portavoz en el mandato 2023-2027", "Elegido en la lista del PSOE en las municipales del 28-05-2023 (10 concejales); portavoz del grupo hasta el 7-05-2026.", ["tribuna27", "os_conc"]),
               ("2019-06-15", "Portavoz del Grupo Municipal Socialista y candidato a la alcaldía (2019-2023)", "Candidato socialista a la alcaldía en 2019 y portavoz durante todo el mandato.", ["os_conc", "wiki_ayto"]),
               ("2015-06-13", "Concejal del PSOE (2015-2019)", "Posible portavoz en el pleno desde 2015: dato no confirmado con certeza.", ["os_conc"])]),
    dict(slug="maria-sanchez-gomez", match="maria sanchez gomez", ret="SANCHEZ GOMEZ, MARIA", g="f", grupo="PSOE", rol=OPO,
         nombre="María Sánchez Gómez", hab="María Sánchez Gómez", pila="María", apell="Sánchez Gómez",
         cargo="Portavoz del Grupo Municipal Socialista desde el 7 de mayo de 2026", desde="2026-05-07",
         perfil="Licenciada en Derecho por la Universidad de Salamanca (2001); técnico superior y abogada de CC.OO. Castilla y León desde 2005, con cargos sindicales y, en el PSOE, secretaria de Organización de la agrupación local Jaime Vera, según su ficha oficial.",
         alumni=["Universidad de Salamanca"],
         tray=[("2026-05-07", "Portavoz del Grupo Municipal Socialista", "Releva a José Luis Mateos Crespo al frente del grupo del PSOE en el Ayuntamiento.", ["psoe_eldiario", "psoe_hoy", "psoe_gaceta"]),
               ("2023-06-17", "Concejala y viceportavoz del PSOE en el mandato 2023-2027", "Elegida en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"]),
               ("2019-06-15", "Concejala del Grupo Municipal Socialista (2019-2023)", "Concejala durante todo el mandato 2019-2023.", ["os_conc", "wiki_ayto"])]),
    dict(slug="juan-jose-garcia-meilan", match="garcia meilan", ret="GARCIA MEILAN, JUAN JOSE", g="m", grupo="PSOE", rol=OPO,
         nombre="Juan José García Meilán", hab="Juan José García Meilán", pila="Juan José", apell="García Meilán",
         cargo="Concejal del Grupo Municipal Socialista", desde="2023-06-17",
         perfil="Doctor en Psicología (1999) y licenciado en Filosofía y CC. de la Educación (Psicología) por la Universidad de Salamanca, de la que es profesor desde 2004; miembro investigador del Instituto de Neurociencias de Castilla y León.",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-17", "Concejal del PSOE en el mandato 2023-2027", "Elegido en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"]),
               ("2019-06-15", "Concejal del Grupo Municipal Socialista (2019-2023)", "Concejal durante todo el mandato 2019-2023.", ["os_conc", "wiki_ayto"])]),
    dict(slug="maria-garcia-gomez", match="maria garcia gomez", ret="GARCIA GOMEZ, MARIA", g="f", grupo="PSOE", rol=OPO,
         nombre="María García Gómez", hab="María García Gómez", pila="María", apell="García Gómez",
         cargo="Concejala del Grupo Municipal Socialista", desde="2023-06-17",
         perfil="Técnico de Cuidados Auxiliares de Enfermería en Sacyl desde 1977, con formación en gestión pública, salud pública y técnico de Prevención de Riesgos Laborales (nivel intermedio).",
         alumni=[],
         tray=[("2023-06-17", "Concejala del PSOE en el mandato 2023-2027", "Elegida en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"]),
               ("2019-06-15", "Concejala del Grupo Municipal Socialista (2019-2023)", "Concejala durante todo el mandato 2019-2023.", ["os_conc", "wiki_ayto"])]),
    dict(slug="jose-maria-collados-grande", match="collados grande", ret="COLLADOS GRANDE, JOSE MARIA", g="m", grupo="PSOE", rol=OPO,
         nombre="José María Collados Grande", hab="José María Collados Grande", pila="José María", apell="Collados Grande",
         cargo="Concejal del Grupo Municipal Socialista", desde="2023-06-17",
         perfil="Licenciado en Historia por la Universidad de Salamanca (2004); fue profesor de Geografía e Historia, educador y coordinador de empleo, y su ficha oficial recoge, sin fechas, la presidencia de la FEVESA (federación de asociaciones de vecinos de Salamanca y provincia) y de CAVECAL (confederación de Castilla y León).",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-17", "Concejal del PSOE en el mandato 2023-2027", "Elegido en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"]),
               ("2019-06-15", "Concejal del Grupo Municipal Socialista (2019-2023)", "Concejal durante todo el mandato 2019-2023.", ["os_conc", "wiki_ayto"])]),
    dict(slug="elvira-sanchez-sanchez", match="elvira sanchez", ret="SANCHEZ SANCHEZ, ELVIRA", g="f", grupo="PSOE", rol=OPO,
         nombre="Elvira Sánchez Sánchez", hab="Elvira Sánchez Sánchez", pila="Elvira", apell="Sánchez Sánchez",
         cargo="Concejala del Grupo Municipal Socialista", desde="2023-06-17",
         perfil="Licenciada en Geografía e Historia (Historia Antigua y Arqueología) por la Universidad de Salamanca; arqueóloga y gestora del patrimonio cultural desde 1995 y directora gerente de la consultora Adobe Gestión del Patrimonio Histórico S.L. desde 1998, según su ficha oficial.",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-17", "Concejala del PSOE en el mandato 2023-2027", "Elegida en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"])]),
    dict(slug="fidel-frances-sanchez", match="frances sanchez", ret="FRANCES SANCHEZ, FIDEL JUAN", g="m", grupo="PSOE", rol=OPO,
         nombre="Fidel Juan Francés Sánchez", hab="Fidel Francés Sánchez", pila="Fidel Juan", apell="Francés Sánchez",
         cargo="Concejal del Grupo Municipal Socialista", desde="2023-06-17",
         perfil="Licenciado en Derecho y diplomado en Relaciones Laborales por la Universidad de Salamanca; profesor de Secundaria (Formación y Orientación Laboral) durante 37 años, con puestos en la administración educativa y cargos en la ejecutiva provincial del PSOE.",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-17", "Concejal del PSOE en el mandato 2023-2027", "Elegido en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"])]),
    dict(slug="maria-del-mar-fuentes-chaves", match="fuentes chaves", ret="FUENTES CHAVES, MARIA DEL MAR", g="f", grupo="PSOE", rol=OPO,
         nombre="María del Mar Fuentes Chaves", hab="Mar Fuentes Chaves", pila="María del Mar", apell="Fuentes Chaves",
         cargo="Concejala del Grupo Municipal Socialista", desde="2023-06-17",
         perfil="Doctora en Literatura española e hispanoamericana por la Universidad de Salamanca (2017); fue profesora de español para extranjeros, de Lengua y Literatura en secciones bilingües en Eslovaquia (2018-2020) y es profesora asociada de la Universidad de Burgos desde 2020.",
         alumni=["Universidad de Salamanca", "Universidad de Burgos"],
         tray=[("2023-06-17", "Concejala del PSOE en el mandato 2023-2027", "Elegida en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"])]),
    dict(slug="alvaro-antolin-montero", match="antolin montero", ret="ANTOLIN MONTERO, ALVARO", g="m", grupo="PSOE", rol=OPO,
         nombre="Álvaro Antolín Montero", hab="Álvaro Antolín Montero", pila="Álvaro", apell="Antolín Montero",
         cargo="Concejal del Grupo Municipal Socialista", desde="2023-06-17",
         perfil="Graduado en Ingeniería Electrónica Industrial y Automática (2015) y máster en Ingeniería Industrial por la Universidad de Salamanca; fue ingeniero automatista y su ficha oficial lo sitúa como profesor del área de Economía Financiera y Contabilidad desde 2019.",
         alumni=["Universidad de Salamanca", "Universidad de León"],
         tray=[("2023-06-17", "Concejal del PSOE en el mandato 2023-2027", "Elegido en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"]),
               ("2019-06-15", "Concejal del Grupo Municipal Socialista (2019-2023)", "Concejal durante todo el mandato 2019-2023.", ["os_conc", "wiki_ayto"])],
         extra_nv=["Su ficha oficial atribuye su puesto de profesor del área de Economía Financiera y Contabilidad a «ENUSA Industrias Avanzadas» en el campo de entidad: la entrada parece inconsistente y se reproduce tal como figura."]),
    dict(slug="maria-jesus-santa-maria-trigo", match="santa maria trigo", ret="SANTA MARIA TRIGO, MARIA JESUS", g="f", grupo="PSOE", rol=OPO,
         nombre="María Jesús Santa María Trigo", hab="María Jesús Santa María Trigo", pila="María Jesús", apell="Santa María Trigo",
         cargo="Concejala del Grupo Municipal Socialista", desde="2023-06-17",
         perfil="Licenciada en Ciencias Biológicas por la Universidad de Salamanca (2000), con másteres en prevención de riesgos laborales; técnico especialista en Seguridad e Higiene en el Trabajo de la Consejería de Empleo de la Junta de Castilla y León desde 2004.",
         alumni=["Universidad de Salamanca"],
         tray=[("2023-06-17", "Concejala del PSOE en el mandato 2023-2027", "Elegida en la lista del PSOE en las municipales del 28-05-2023 (10 concejales).", ["tribuna27", "os_conc"])]),
    # ------------------------------------------------------------ ex-Vox
    dict(slug="ignacio-javier-rivas-serrano", match="rivas serrano", ret="RIVAS SERRANO, IGNACIO JAVIER", g="m", grupo="Vox", rol=OPO,
         nombre="Ignacio Javier Rivas Serrano", hab="Ignacio Rivas Serrano", pila="Ignacio Javier", apell="Rivas Serrano",
         cargo="Concejal del Grupo Mixto (elegido en la candidatura de Vox); portavoz de Vox hasta el 10 de febrero de 2025", desde="2023-06-17",
         perfil="Licenciado en Derecho por la Universidad de Salamanca; directivo bancario (Banco Comercial Español, Banco Guipuzcoano, La Caixa y CaixaBank) entre 1989 y 2019, director de zona en Salamanca entre 2015 y 2019.",
         alumni=["Universidad de Salamanca"],
         tray=[("2025-02-24", "El grupo municipal de Vox se disuelve por resolución del alcalde", "Tras la crisis interna, el Ayuntamiento deja a Vox sin grupo municipal. Desde entonces las actas de Pleno recogen a Ignacio Rivas en el Grupo Mixto (Vox) y a María de los Ángeles Carpio y Alejandro Pérez de la Sota como concejales no adscritos.", ["vox_infobae", "actas"]),
               ("2025-02-10", "Deja de ser portavoz de Vox", "Alejandro Pérez de la Sota pasa a ser el nuevo portavoz; la prensa lo describe como una crisis interna del partido en Salamanca.", ["vox_eldiario", "vox_infobae"]),
               ("2023-06-17", "Concejal y portavoz de Vox en el mandato 2023-2027", "Elegido en la candidatura de Vox en las municipales del 28-05-2023 (3 concejales).", ["tribuna27", "os_conc"])],
         extra_nv=["Su afiliación actual a Vox: las actas lo recogen en el Grupo Mixto (Vox), pero no se ha comprobado su situación como afiliado.",
                   "Motivo y alcance de su salida como portavoz: la prensa describe una crisis interna; no se detallan aquí versiones contrapuestas."]),
    dict(slug="alejandro-miguel-perez-de-la-sota", match="perez de la sota", ret="PEREZ DE LA SOTA, ALEJANDRO MIGUEL", g="m", grupo="Vox", rol=OPO,
         nombre="Alejandro Miguel Pérez de la Sota", hab="Alejandro Pérez de la Sota", pila="Alejandro Miguel", apell="Pérez de la Sota",
         cargo="Concejal no adscrito (elegido en la candidatura de Vox); portavoz de Vox desde el 10 de febrero de 2025 hasta la disolución del grupo", desde="2023-06-17",
         perfil="Licenciado en Derecho por la Universidad de Salamanca (1997) y abogado ejerciente con despacho propio desde 2005; fue tesorero de la Junta de Gobierno del Colegio de Abogados de Salamanca (2021-2023).",
         alumni=["Universidad de Salamanca"],
         tray=[("2025-02-24", "El grupo municipal de Vox se disuelve por resolución del alcalde", "Tras la crisis interna, el Ayuntamiento deja a Vox sin grupo municipal. Desde entonces las actas de Pleno recogen a Ignacio Rivas en el Grupo Mixto (Vox) y a María de los Ángeles Carpio y Alejandro Pérez de la Sota como concejales no adscritos.", ["vox_infobae", "actas"]),
               ("2025-02-10", "Nuevo portavoz de Vox", "Sustituye a Ignacio Rivas Serrano como portavoz; la prensa lo describe como una crisis interna del partido en Salamanca.", ["vox_eldiario", "vox_infobae"]),
               ("2023-06-17", "Concejal de Vox en el mandato 2023-2027", "Elegido en la candidatura de Vox en las municipales del 28-05-2023 (3 concejales).", ["tribuna27", "os_conc"])],
         extra_nv=["Su situación como afiliado a Vox: las actas lo recogen como concejal no adscrito; no se ha comprobado su afiliación."]),
    dict(slug="maria-de-los-angeles-carpio-perez", match="carpio perez", ret="CARPIO PEREZ, MARIA ANGELES", g="f", grupo="Vox", rol=OPO,
         nombre="María de los Ángeles Carpio Pérez", hab="María de los Ángeles Carpio Pérez", pila="María de los Ángeles", apell="Carpio Pérez",
         cargo="Concejala no adscrita (elegida en la candidatura de Vox); en el pleno desde el 26 de julio de 2024", desde="2024-07-26",
         perfil="Diplomada en Ciencias Empresariales por la Universidad de Salamanca (1995) y máster European Master in Management (ESCP, 1999); trabajó en ventas de renta variable en Londres (PaineWebber, UBS Warburg, Knight Securities) y fundó en 2009 la Fundación Carpio Pérez, que desarrolla programas en Tanzania.",
         alumni=["Universidad de Salamanca"],
         tray=[("2025-02-24", "El grupo municipal de Vox se disuelve por resolución del alcalde", "Tras la crisis interna, el Ayuntamiento deja a Vox sin grupo municipal. Desde entonces las actas de Pleno recogen a Ignacio Rivas en el Grupo Mixto (Vox) y a María de los Ángeles Carpio y Alejandro Pérez de la Sota como concejales no adscritos.", ["vox_infobae", "actas"]),
               ("2024-07-26", "Toma posesión como concejala", "Sustituye a Laura Magdalena Miguel (Vox), que renunció al acta el 27-06-2024 por incompatibilidad laboral.", ["cope_carpio", "magdalena"])],
         extra_nv=["Su situación como afiliada a Vox: las actas la recogen como concejala no adscrita; no se ha comprobado su afiliación.",
                   "Su ficha oficial solo enlaza la declaración inicial de 2023 (no las anuales de 2024 y 2025)."]),
]

# ---------------------------------------------------------------- utilidades
ficha_raw = json.loads((ROOT / "scripts/politicos/fuentes/fichas_oficiales.json").read_text(encoding="utf-8"))["fichas"]
FICHAS = {norm(v["nombre_oficial"]): v for v in ficha_raw.values()}


def buscar_ficha(match):
    cand = [v for k, v in FICHAS.items() if match in k]
    assert len(cand) == 1, (match, len(cand))
    return cand[0]


GRUPO_TXT_PERSONA = {
    "ignacio-javier-rivas-serrano": "Grupo Mixto (Vox): elegido en la candidatura de Vox en 2023; el grupo municipal de Vox se disolvió el 24-02-2025",
    "alejandro-miguel-perez-de-la-sota": "Concejal no adscrito: elegido en la candidatura de Vox en 2023; el grupo municipal de Vox se disolvió el 24-02-2025",
    "maria-de-los-angeles-carpio-perez": "Concejala no adscrita: elegida en la candidatura de Vox en 2023; el grupo municipal de Vox se disolvió el 24-02-2025",
}
ROL_TXT_PERSONA = {
    "ignacio-javier-rivas-serrano": "Oposición: concejal del Grupo Mixto (1 concejal), elegido en la candidatura de Vox (3 concejales en 2023).",
    "alejandro-miguel-perez-de-la-sota": "Oposición: concejal no adscrito, elegido en la candidatura de Vox (3 concejales en 2023).",
    "maria-de-los-angeles-carpio-perez": "Oposición: concejala no adscrita, elegida en la candidatura de Vox (3 concejales en 2023).",
}
GRUPO_TXT = {
    "PP": ("Partido Popular (PP)", "Partido Popular"),
    "PSOE": ("Partido Socialista Obrero Español (PSOE)", "Partido Socialista Obrero Español"),
    "Vox": ("Elegido en la candidatura de Vox en 2023; no adscrito o en grupo mixto desde la disolución del grupo municipal (24-02-2025), según fuentes contradictorias", "Vox"),
}
ROL_TXT = {
    "PP": "Equipo de gobierno: el PP gobierna con mayoría absoluta (14 de 27 concejales) con el alcalde Carlos García Carbayo.",
    "PSOE": "Oposición: Grupo Municipal Socialista, con 10 de los 27 concejales.",
    "Vox": "Oposición: concejal elegido en la candidatura de Vox (3 concejales en 2023); el grupo municipal de Vox se disolvió el 24-02-2025.",
}


def art(g, m, f):
    return m if g == "m" else f


PLENO_PERSONAS = {}
_pp = ROOT / "_data" / "pleno" / "personas.json"
if _pp.exists():
    PLENO_PERSONAS = json.loads(_pp.read_text(encoding="utf-8"))


def votaciones_bloque(slug, hab):
    """Bloque de votaciones del Pleno de la persona (build_pleno.py); None si no hay datos."""
    v = PLENO_PERSONAS.get(slug)
    if not v:
        return None
    return {**v, "fuente": S["actas"], "dataset": S["votaciones"],
            "metodo": "El acta de cada Pleno recoge el voto por grupo («el voto a favor del Grupo Popular [14 concejales]») y, por nombre, el de los concejales no adscritos. "
                      "El voto de cada persona se atribuye cuando el recuento de su grupo coincide con los presentes de ese grupo en la cabecera del acta; si alguien abandona la sala, no se atribuye."}


def build(p):
    g = p["g"]
    rol_txt = ROL_TXT_PERSONA.get(p["slug"], ROL_TXT[p["grupo"]])
    grupo_txt = GRUPO_TXT_PERSONA.get(p["slug"], GRUPO_TXT[p["grupo"]][0])
    concejal = art(g, "concejal", "concejala")
    grupo = p["grupo"]
    f = buscar_ficha(p["match"]) if p.get("match") else None
    ficha_url = f["url"] if f else p["ficha"]["url"]
    S_f = {"t": f"Ayuntamiento de Salamanca: ficha oficial de {p['nombre']}" if f else S["gb_ayto"]["t"], "u": ficha_url}

    def fu(keys):
        out = []
        for k in keys:
            out.append(S[k])
        return out

    # retribución
    if p.get("ret"):
        imp, marc = RET[p["ret"]]
        pos = posicion(imp)
        if marc:
            marcado = "Figura marcado como dedicación exclusiva o parcial (el listado oficial no distingue entre ambas)."
        else:
            marcado = "No figura marcado como dedicación exclusiva ni parcial en el listado oficial."
        ret_txt = (f"Según el listado oficial del Ayuntamiento, {p['hab']} percibió {es(imp, 2)} € brutos en 2025 ({pos}). {marcado} "
                   "El listado no desglosa los conceptos (retribución fija, asistencias u otros).")
        ret = {
            "ejercicio": 2025, "importe_bruto_anual_eur": imp, "dedicacion_marcada": marc,
            "posicion_en_la_corporacion": pos, "texto_resumen": ret_txt,
            "nota": "Importe tal como lo publica el Ayuntamiento en el listado de retribuciones percibidas por los miembros de la Corporación en 2025. El asterisco del listado corresponde a «dedicaciones exclusivas / parciales» sin distinguirlas. El PDF lleva internamente la etiqueta «2020» en el título, pero su contenido declara el ejercicio 2025.",
            "fuente": S["retrib"],
        }
    else:
        imp = marc = None
        ret = {"ejercicio": 2025, "importe_bruto_anual_eur": None, "dedicacion_marcada": None,
               "posicion_en_la_corporacion": None,
               "texto_resumen": f"{p['hab']} tomó posesión el 30-07-2026, por lo que no figura en el listado oficial de retribuciones de 2025 (que incluye a su antecesor, Pedro Martínez Córdoba). No se ha localizado un dato de retribución publicado para el cargo actual.",
               "nota": "Listado de 2025 consultado el " + FE.dmy() + ".", "fuente": S["retrib"]}

    # resumen
    desde_txt = {"2023-06-19": "19 de junio de 2023", "2023-06-17": "17 de junio de 2023", "2024-07-26": "26 de julio de 2024",
                 "2026-07-30": "30 de julio de 2026", "2026-05-07": "7 de mayo de 2026"}[p["desde"]]
    rol_corto = {"PP": "equipo de gobierno del PP", "PSOE": "oposición", "Vox": "oposición"}[grupo]
    quien = f"{p['cargo'][0].lower() + p['cargo'][1:]}, en el Ayuntamiento de Salamanca ({rol_corto})"
    resumen = f"{p['nombre']} es {quien}, mandato 2023-2027. {p['perfil']}"
    if imp:
        resumen += f" En 2025 percibió {es(imp, 2)} € brutos según el listado oficial del Ayuntamiento ({pos})."
    resumen = re.sub(r"\s+", " ", resumen)

    # ficha oficial
    if f:
        fo = {"url": ficha_url, "texto": "Texto tal como lo publica el Ayuntamiento de Salamanca en la ficha oficial de la persona (consultada el " + FE.dmy() + "), sin reescribir.",
              "formacion_oficial": f.get("formacion_oficial", []), "otros_titulos": f.get("otros_titulos", []),
              "actividad_profesional": f.get("actividad_profesional", []), "otras_actividades": f.get("otras_actividades", [])}
        contacto = {"direccion": "Casa Consistorial, Plaza Mayor, 1, 37002 Salamanca",
                    "telefono": " / ".join(f"+34 {t}" for t in f["telefonos"]) or None,
                    "email": f["email"]}
        decls = f["declaraciones"]
        cargo_of = f.get("cargo_oficial")
    else:
        fo = p["ficha"]
        fo = {**fo, "texto": p["ficha"]["texto"]}
        contacto = {"direccion": "Casa Consistorial, Plaza Mayor, 1, 37002 Salamanca", "telefono": None, "email": None}
        decls = []
        cargo_of = None

    # trayectoria
    tray = [{"fecha": a, "hito": b, "detalle": c, "fuentes": fu(k)} for a, b, c, k in p["tray"]]
    tray.sort(key=lambda t: t["fecha"], reverse=True)

    # preguntas frecuentes
    faq = [
        {"q": f"¿Quién es {p['hab']}?", "a": resumen},
        {"q": f"¿Qué cargo tiene {p['hab']} en el Ayuntamiento de Salamanca?",
         "a": f"{p['cargo']}. {rol_txt}" + (f" Cargo según su ficha oficial: «{cargo_of}»." if cargo_of else "")},
        {"q": f"¿A qué partido o grupo pertenece {p['hab']}?",
         "a": (f"Fue elegid{art(g,'o','a')} en la lista del {GRUPO_TXT[grupo][0]}." if grupo != "Vox" else
               f"Fue {art(g, 'elegido', 'elegida')} en la candidatura de Vox en las municipales de 2023 (Vox obtuvo 3 concejales). El grupo municipal de Vox se disolvió por resolución del alcalde el 24 de febrero de 2025 tras una crisis interna; desde entonces las actas de Pleno {art(g, 'lo', 'la')} recogen como {grupo_txt.split(':')[0].lower()}.")},
        {"q": f"¿Cuánto cobra {p['hab']}?", "a": ret["texto_resumen"]},
        {"q": f"¿Cuál es la formación y la profesión de {p['hab']}?", "a": p["perfil"]},
    ]
    vp = PLENO_PERSONAS.get(p["slug"])
    if vp and vp["votaciones_con_voto_atribuible"]:
        faq.append({"q": f"¿Cómo vota {p['hab']} en el Pleno del Ayuntamiento de Salamanca?",
                    "a": vp["texto_resumen"] + f" Coincidió con el voto del PP en el {es(vp['coincide_con_voto_del_PP']['pct'], 1)} % y con el del PSOE en el {es(vp['coincide_con_voto_del_PSOE']['pct'], 1)} % de las votaciones no unánimes. Fuente: actas de los Plenos Municipales."})
    if contacto["email"]:
        faq.append({"q": f"¿Cómo contactar con {p['hab']}?",
                    "a": f"Por el correo institucional {contacto['email']}" + (f" o por teléfono en el {contacto['telefono']}" if contacto["telefono"] else "") + ", según su ficha oficial en la web del Ayuntamiento de Salamanca."})

    nv = [
        "Cifras de patrimonio, bienes e ingresos de las declaraciones de bienes y actividades: se enlazan las publicadas por el Ayuntamiento, pero no se transcriben.",
        "Puesto en la lista de 2023 y votos personales en las urnas: no recopilados. Las votaciones del Pleno se resumen en la sección correspondiente, con sus límites.",
        "Fecha de nacimiento y trayectoria política previa al Ayuntamiento: no figuran en la ficha oficial salvo lo reproducido arriba." if not p.get("nacimiento") else
        "Trayectoria política y profesional anterior a la nota oficial de su toma de posesión.",
        "Controversias: ninguna contrastada en las fuentes consultadas; eso no prueba que no existan. No se ha recopilado la valoración de otros grupos.",
    ] + p.get("extra_nv", [])
    if grupo == "PP" and p["rol"] == GOB:
        nv.append("Delegaciones y organigrama detallado más allá del reparto de concejalías de 2023 y los cambios publicados: pueden haber variado.")

    fuentes = [S_f, S["corp"], S["transp"], S["os_conc"], S["wiki_ayto"], S["retrib"]]
    vistos = set()
    for t in tray:
        for s in t["fuentes"]:
            if s["u"] not in vistos:
                vistos.add(s["u"])
    for s in [x for t in tray for x in t["fuentes"]]:
        if s not in fuentes:
            fuentes.append(s)
    fuentes.append(S["carbayo"])

    nac = None
    if p.get("nacimiento"):
        nac = {"fecha": p["nacimiento"][0], "fecha_texto": p["nacimiento"][1], "lugar": p["nacimiento"][2]}

    data = {
        "schema_version": "1.0", "tipo": "ficha_politico", "slug": p["slug"],
        "url_canonica": BASEURL + p["slug"], "actualizado": FECHA_ACT, "actualizado_texto": FECHA_ACT_TXT,
        "licencia": "CC BY 4.0 (citar «Open Salamanca» y enlazar la ficha)",
        "aviso": "Ficha elaborada solo con fuentes públicas citadas en cada dato (principalmente la web oficial del Ayuntamiento). Lo no contrastado figura en «no_verificado»; no se omite ni se rellena. No es opinión política ni recomendación de voto.",
        "identidad": {
            "nombre_completo": p["nombre"], "nombre_habitual": p["hab"], "nombre_pila": p["pila"], "apellidos": p["apell"],
            "tratamiento_oficial": f["nombre_oficial"] if f else p["nombre"],
            "apodos_o_variantes": sorted({p["hab"], p["nombre"], p["apell"]} - {p["nombre"]} | {p["nombre"]}),
            "nacimiento": nac,
            "partido": {"siglas": grupo, "nombre": GRUPO_TXT[grupo][1]},
            "afiliacion_confirmada": False,
            "grupo_texto": grupo_txt,
            "alumni_of": p["alumni"],
            "formacion_resumen": (fo["formacion_oficial"][0].split(" — ")[0] if fo.get("formacion_oficial") else None),
            "profesion": None,
        },
        "cargo_actual": {
            "cargo": p["cargo"][0].upper() + p["cargo"][1:], "organizacion": "Ayuntamiento de Salamanca",
            "desde": p["desde"], "desde_texto": desde_txt, "mandato_actual": "2023-2027",
            "rol_en_pleno": p["rol"], "rol_en_pleno_texto": rol_txt, "otros_cargos": [],
            "cargo_segun_ficha_oficial": cargo_of, "contacto_institucional": contacto,
        },
        "resumen": resumen,
        "trayectoria": tray,
        "ficha_oficial": fo,
        "retribucion": ret,
        "transparencia": {
            "enlaces_declaraciones": decls,
            "nota": "Base legal: art. 75.7 de la Ley de Bases de Régimen Local. Se enlazan las declaraciones que el Ayuntamiento publica; las anuales solo recogen variaciones respecto a la inicial de 2023, cuyas cifras no se transcriben aquí.",
            "portal": S["transp"],
        },
        "gobierno_municipal": {
            "pleno": {"concejales": 27, "mayoria_absoluta": 14, "reparto_2023_2027": {"PP": 14, "PSOE": 10, "Vox": 3}},
            "texto": rol_txt, "fuente": S["corp"],
            "nota": "La web oficial agrupa la Corporación en alcalde, tenientes de alcalde, concejales delegados y concejales. El reparto de 2023 vino con la constitución del Pleno (17-06-2023) y las concejalías (19-06-2023).",
        },
        "votaciones_pleno": votaciones_bloque(p["slug"], p["hab"]),
        "no_verificado": nv,
        "faq": faq,
        "fuentes": fuentes,
        "como_citar": f"Open Salamanca ({FE.anio()}). {p['nombre']}, {concejal} del Ayuntamiento de Salamanca: ficha y dataset. {BASEURL}{p['slug']} (consultado el {FE.dmy()}). CC BY 4.0.",
        "enlaces_oficiales_y_externos": {"web_oficial_ayuntamiento": ficha_url},
    }
    data["identidad"]["apodos_o_variantes"] = sorted({p["hab"], p["apell"]})
    return data, imp, marc


def stub(p, data):
    g = p["g"]
    concejal = art(g, "concejal", "concejala")
    grupo_corto = {"PP": "PP", "PSOE": "PSOE", "Vox": "elegido por Vox" if g == "m" else "elegida por Vox"}[p["grupo"]]
    titulo = f"{p['hab']}, {concejal} del Ayuntamiento de Salamanca ({grupo_corto}): biografía, cargo, retribución y datos"
    desc = f"Ficha y dataset de {p['nombre']}: cargo, trayectoria, formación, retribución oficial 2025 y transparencia, con fuente en cada dato"
    if p["slug"] == "cesar-gomez-barthe-celada":
        desc = f"Ficha y dataset de {p['nombre']}: cargo, trayectoria, formación y transparencia, con fuente en cada dato"
    page = f'''---
layout: politico
slug: {p["slug"]}
title: "{titulo}"
description: "{desc}"
date: 24-11-2026
modified: {FE.dmy()}
parent_url: /elecciones/politicos/
parent_title: Concejales del Ayuntamiento de Salamanca
permalink: elecciones/politicos/{p["slug"]}
dataset_name: "Ficha de {p["nombre"]}, {concejal} del Ayuntamiento de Salamanca"
dataset_temporal: "2023/2026"
dataset_source: "Ayuntamiento de Salamanca y prensa citada"
dataset_source_url: "{data["fuentes"][0]["u"]}"
dataset_files:
  - elecciones/politicos/{p["slug"]}.json
---
'''
    js = f'''---
permalink: elecciones/politicos/{p["slug"]}.json
sitemap: false
---
{{{{ site.data.politicos["{p["slug"]}"] | jsonify }}}}
'''
    return page, js


def main():
    # Guarda: toda persona de la Corporación debe tener ficha definida en PEOPLE y viceversa.
    usadas = {id(buscar_ficha(p["match"])) for p in PEOPLE if p.get("match")}
    sobran = [v["nombre_oficial"] for v in FICHAS.values() if id(v) not in usadas and "garcia carbayo" not in norm(v["nombre_oficial"])]
    if sobran:
        print("ATENCIÓN: hay concejales en la web del Ayuntamiento sin ficha definida en PEOPLE:", sobran)
        print("Añádelos a PEOPLE (o retíralos si ya no están) antes de regenerar.")
        sys.exit(3)
    outdir = ROOT / "elecciones" / "politicos"
    datadir = ROOT / "_data" / "politicos"
    outdir.mkdir(parents=True, exist_ok=True)
    datadir.mkdir(parents=True, exist_ok=True)
    indice = []
    # Carbayo primero
    cb = json.loads((datadir / "carlos-garcia-carbayo.json").read_text(encoding="utf-8"))
    indice.append({
        "slug": "carlos-garcia-carbayo", "nombre": "Carlos García Carbayo", "rol": "alcalde", "grupo": "PP",
        "cargo": "Alcalde de Salamanca", "retribucion_2025_eur": cb["retribucion"]["importe_bruto_anual_eur"],
        "retribucion_2025_texto": es(cb["retribucion"]["importe_bruto_anual_eur"], 2) + " €",
        "dedicacion_marcada": True, "url": cb["url_canonica"]})
    for p in PEOPLE:
        data, imp, marc = build(p)
        (datadir / f"{p['slug']}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        page, js = stub(p, data)
        (outdir / f"{p['slug']}.html").write_text(page, encoding="utf-8")
        (outdir / f"{p['slug']}-json.json").write_text(js, encoding="utf-8")
        indice.append({
            "slug": p["slug"], "nombre": p["hab"], "rol": p["rol"], "grupo": p["grupo"],
            "cargo": data["cargo_actual"]["cargo"], "retribucion_2025_eur": imp,
            "retribucion_2025_texto": (es(imp, 2) + " €") if imp else "no figura en el listado de 2025",
            "dedicacion_marcada": marc,
            "url": data["url_canonica"]})
    # resúmenes por grupo (listado oficial de 2025: 27 miembros)
    def suma(f):
        return round(sum(v[0] for k, v in RET.items() if f(k)), 2)
    pp_keys = {"GARCIA CARBAYO, CARLOS MANUEL", "PARRES CABRERA, ALMUDENA", "RODRIGUEZ LOPEZ, MYRIAM", "CARABIAS ACOSTA, JOSE FERNANDO",
               "RODRIGUEZ ALONSO, FERNANDO JAVIER", "SEGUIN KATTAN, MARIA DEL CARMEN", "MOLINA MARTINEZ, ANGEL", "COCA SANCHEZ, MARIA JOSE",
               "VILLAR GUTIERREZ DE CEBALLOS, MARIA DE LA VEGA", "FERNANDEZ SILVA, ANGEL", "MARTIN PARRA, ROBERTO ANGEL",
               "MACIAS TELLO, MARIA ISABEL", "SANCHEZ AREVALO, LUIS", "MARTINEZ CORDOBA, PEDRO JOSE"}
    vox_keys = {"RIVAS SERRANO, IGNACIO JAVIER", "PEREZ DE LA SOTA, ALEJANDRO MIGUEL", "CARPIO PEREZ, MARIA ANGELES"}
    tot = suma(lambda k: True)
    tpp = suma(lambda k: k in pp_keys)
    tvox = suma(lambda k: k in vox_keys)
    tpsoe = round(tot - tpp - tvox, 2)
    def grupo_stats(nombre, claves):
        its = [RET[k] for k in claves]
        n = len(its)
        total = round(sum(i[0] for i in its), 2)
        return {"grupo": nombre, "miembros_listados": n, "con_dedicacion_marcada": sum(1 for i in its if i[1]),
                "total_bruto_eur": total, "total_texto": es(total, 2) + " €",
                "media_texto": es(total / n, 2) + " €"}
    psoe_keys = set(RET) - pp_keys - vox_keys
    grupos = [grupo_stats("PP (equipo de gobierno)", pp_keys), grupo_stats("PSOE", psoe_keys),
              grupo_stats("Elegidos en la candidatura de Vox", vox_keys)]
    resumen = {
        "grupos": grupos, "total_texto": es(tot, 2) + " €",
        "ejercicio": 2025, "miembros_listados": TOTAL_LISTADO,
        "total_bruto_eur": tot, "pp_eur": tpp, "psoe_eur": tpsoe, "vox_eur": tvox,
        "nota": "Suma de los importes del listado oficial de retribuciones 2025 (27 miembros). Incluye a Pedro Martínez Córdoba (PP), que renunció el 6-07-2026, y no incluye a su sustituto César Gómez-Barthe, ni a Laura Magdalena Miguel (Vox), que renunció en 2024. Elegidos por Vox: Rivas, Pérez de la Sota y Carpio.",
        "fuente": S["retrib"],
    }
    (ROOT / "_data" / "concejales_indice.json").write_text(
        json.dumps({"actualizado": FECHA_ACT, "actualizado_texto": FECHA_ACT_TXT, "resumen": resumen, "concejales": indice}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    FE.tocar_modified(ROOT / "elecciones/politicos/index.html")
    print("fichas:", len(PEOPLE) + 1, "| total 2025:", es(tot, 2), "PP", es(tpp, 2), "PSOE", es(tpsoe, 2), "Vox", es(tvox, 2))

    # llms.txt: bloque entre marcadores
    llms = ROOT / "llms.txt"
    txt = llms.read_text(encoding="utf-8")
    txt = re.sub(r"- \[Carlos García Carbayo, alcalde de Salamanca: ficha y dataset\].*\n", "", txt)
    txt = re.sub(r"\n?<!-- fichas-politicos:start -->.*?<!-- fichas-politicos:end -->\n?", "\n", txt, flags=re.S)
    bloque = ["", "<!-- fichas-politicos:start -->", "## Fichas de concejales del Ayuntamiento de Salamanca (mandato 2023-2027)", "",
              "- [Concejales del Ayuntamiento de Salamanca: listado, grupos y retribuciones 2025](https://opensalamanca.es/elecciones/politicos/): Las 27 personas de la Corporación (gobierno del PP y oposición) con cargo, grupo y retribución bruta 2025 del listado oficial; datos en JSON: https://opensalamanca.es/elecciones/politicos/concejales-salamanca-2023-2027.json"]
    bloque.append("- [Votaciones del Pleno del Ayuntamiento de Salamanca 2023-2027](https://opensalamanca.es/elecciones/politicos/votaciones-pleno): Voto de cada grupo y de cada concejal en las votaciones de fondo, mociones aprobadas y rechazadas por grupo y coincidencias entre grupos, extraído de las actas oficiales; datos en JSON: https://opensalamanca.es/elecciones/politicos/votaciones-pleno.json")
    for i in indice:
        nom = i["nombre"]
        bloque.append(f"- [{nom}]({i['url']}): {i['cargo']} ({i['grupo']}); biografía, formación, trayectoria, retribución oficial 2025 y transparencia con fuente en cada dato. JSON: {i['url']}.json")
    bloque += ["<!-- fichas-politicos:end -->", ""]
    llms.write_text(txt.rstrip("\n") + "\n" + "\n".join(bloque), encoding="utf-8")


if __name__ == "__main__":
    main()
