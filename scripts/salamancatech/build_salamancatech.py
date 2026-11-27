# -*- coding: utf-8 -*-
"""Genera las fichas de Salamanca Tech / Centro Tormes+ / distrito tecnologico.

Salida:
  _data/salamancatech/<slug>.json      (fuente unica)
  salamanca-tech/<slug>.html           (stub con front matter; layout salamancatech)
  salamanca-tech/<slug>-json.json      (descarga)
  salamanca-tech.html                  (stub del hub, slug estrategia-salamanca-tech)
Uso: python scripts/salamancatech/build_salamancatech.py
Solo datos con fuente; lo no contrastado va en "no_verificado".
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FECHA = "2026-11-27"
FECHA_TXT = "27 de noviembre de 2026"
BASE = "https://opensalamanca.es"


def S(t, u):
    return {"t": t, "u": u}


# ---------------------------------------------------------------- fuentes
STECH = S("Salamanca Tech: ¿Qué es Salamanca Tech? (web oficial, sin fecha)", "https://salamancatech.es/que-es-salamanca-tech/")
AREA = S("Ayuntamiento de Salamanca: Salamanca Tech (área del inversor, sin fecha)", "https://www.aytosalamanca.es/en/area-del-inversor")
HEX = S("Salamanca24horas: El «Hexágono Tecnológico de Salamanca» (26/08/2026)", "https://www.salamanca24horas.com/local/hexagono-tecnologico-salamanca-centros-transformaran-ciudad-capital-talento-innovacion")
EITT_AYTO = S("Ayuntamiento de Salamanca: inicia la construcción del Espacio de Innovación Tecnológica Tormes (fecha de la página: 22/09/2023)", "https://www.aytosalamanca.es/en/w/el-ayuntamiento-de-salamanca-inicia-la-construcci%C3%B3n-del-espacio-de-innovaci%C3%B3n-tecnol%C3%B3gica-tormes-para-potenciar-el-apoyo-a-aut%C3%B3nomos-en-sectores-emergentes-y-la-creaci%C3%B3n-de-oportunidades-de-empleo")
TRIB = S("Tribuna de Salamanca: Salamanca impulsa la innovación con el nuevo Espacio Tecnológico Tormes+ (25/04/2025)", "https://www.tribunasalamanca.com/noticias/402870/salamanca-impulsa-la-innovacion-con-el-nuevo-espacio-tecnologico-tormesmas")
RTV = S("SALAMANCArtv AL DÍA: Inaugurado el Espacio de Innovación Tecnológica Tormes+ (25/04/2025)", "https://salamancartvaldia.es/noticia/2025-04-25-inaugurado-el-espacio-de-innovacion-tecnologica-tormes-que-facilita-formacion-gratuita-367803")
STEAM = S("SALAMANCArtv AL DÍA: El Centro Tormes+ se incorpora al proyecto europeo STEAMbrace (28/08/2026)", "https://salamancartvaldia.es/noticia/2026-08-28-el-centro-tormes-se-incorpora-al-proyecto-europeo-steambrace-para-impulsar-la-educacion-tecnologica-396538")
DEBATE = S("El Debate: El nuevo distrito empresarial tecnológico de Salamanca está licitado por casi 800.000 euros (12/05/2026)", "https://www.eldebate.com/espana/castilla-y-leon/20260512/nuevo-distrito-empresarial-tecnologico-salamanca-esta-licitado-casi-800000-euros_416850_amp.html")
ESP1221 = S("El Español (Invertia): la lejanía del proyecto estrella no impide el desarrollo de la estrategia Salamanca Tech (21/12/2024)", "https://elespanol.com/invertia/disruptores/autonomias/castilla-leon/20241221/lejania-proyecto-estrella-no-impide-desarrollo-estrategia-avanza-marca-salamanca-tech/909159233_0.html")
ESP0212 = S("El Español (Invertia): De mercado mayorista a distrito tecnológico (12/02/2024)", "https://www.elespanol.com/invertia/disruptores/autonomias/castilla-leon/20240212/mercado-mayorista-distrito-tecnologico-jugada-urbanistica-refuerza-marca-salamanca-tech/831417113_0.html")
ESP0407 = S("El Español: La Casa de la Juventud de Garrido, sexto «pulmón» de Salamanca Tech (07/04/2026)", "https://www.elespanol.com/castilla-y-leon/region/salamanca/20260407/casa-juventud-garrido-sexto-pulmon-salamanca-tech-millones-euros-inversion/1003744197304_0.html")
ESP0605 = S("El Español: Licitadas las obras para transformar la Casa de la Juventud en el sexto centro tecnológico (05/06/2026)", "https://www.elespanol.com/castilla-y-leon/region/salamanca/20260605/licitadas-obras-transformar-casa-juventud-sexto-centro-tecnologico-salamanca/1003744275743_0.html")
ESP0415 = S("El Español: Mañueco promete crear 2.000 empleos tecnológicos al año (15/04/2026)", "https://www.elespanol.com/castilla-y-leon/region/salamanca/20260415/manueco-promete-crear-empleos-tecnologicos-ano-aumentar-inversiones-innovacion/1003744207502_0.html")
ESP0324 = S("El Español (Invertia): Salamanca cita a las empresas en la cumbre de la red de innovación tech (24/03/2026)", "https://www.elespanol.com/invertia/disruptores/autonomias/castilla-leon/20260324/salamanca-cita-empresas-cumbre-red-innovacion-tech/1003744181626_0.html")
INCYDE = S("El Español: Salamanca e INCYDE, alianza para retener talento joven e impulsar el emprendimiento (27/04/2026)", "https://www.elespanol.com/castilla-y-leon/region/salamanca/20260427/salamanca-incyde-alianza-euros-retener-talento-joven-impulsar-emprendimiento/1003744222453_0.html")
ABIO_CONV = S("Sacyl investigación: Abioinnova publica convocatoria abierta permanente (17/09/2026)", "https://www.saludcastillayleon.es/investigacion/es/noticias/abioinnova-publica-convocatoria-abierta-permanente-incorpor")
RECTOR = S("El Español: el rector de la USAL anuncia en el Salamanca Tech Summit nuevas bioincubadoras tecnológicas (15/04/2026)", "https://www.elespanol.com/castilla-y-leon/region/salamanca/20260415/rector-usal-anuncia-salamanca-tech-summit-creacion-nuevas-bioincubadoras-tecnologicas/1003744207700_0.amp.html")
TORMES_WEB = S("Tormes+: web del centro (inscripciones y cursos)", "https://tormesplus.com/")

AVISO_CITA = "Open Salamanca ({f}). {t}. {u}. Licencia CC BY 4.0. Cita también la fuente primaria de cada dato."

AVISO_GLOBAL = ("Esta ficha recopila datos publicados por el Ayuntamiento de Salamanca, la Junta de Castilla y León y medios; "
                "no es una web oficial. Cuando dos fuentes se contradicen, se indica.")

# Aclaracion de nomenclatura, repetida en varias fichas porque es la confusion mas probable
NOMEN = ("Tres cosas distintas que suelen mezclarse: (1) Salamanca Tech es la estrategia y marca municipal de innovación; "
         "(2) el Centro de Emprendimiento y Formación Tormes+ es uno de sus centros, ya abierto desde 2022, en la avenida de La Salle; "
         "(3) el Distrito Tecnológico es un proyecto aparte, aún sin construir, en los terrenos del antiguo Mercasalamanca (sector Sendero de las Cregas).")

REL_ORDER = [
    "estrategia-salamanca-tech", "centro-tormes-plus", "espacio-innovacion-tecnologica-tormes",
    "distrito-tecnologico-salamanca", "abioinnova", "centro-internet-cosas-inteligencia-artificial",
    "centro-innovacion-juvenil-garrido", "centro-ciudad-del-talento", "financiacion-salamanca-tech",
    "cronologia-salamanca-tech",
]

F = {}

# ================================================================ 1. ESTRATEGIA
F["estrategia-salamanca-tech"] = dict(
    titulo="Salamanca Tech: estrategia de innovación, centros, Centro Tormes+ y distrito tecnológico",
    descripcion="Qué es Salamanca Tech, qué centros la forman (Tormes+, Abioinnova, IoT e IA, Garrido, Ciudad del Talento), qué es el Distrito Tecnológico y cuánto dinero hay detrás, con fuentes y lo no verificado",
    schema_type="Organization",
    nombre_habitual="Salamanca Tech",
    resumen=("Salamanca Tech es la estrategia y marca de innovación del Ayuntamiento de Salamanca que conecta universidades, centros de investigación, empresas, instituciones y ciudadanía. "
             "Agrupa una red de centros municipales: el Centro de Emprendimiento y Formación Tormes+ (2022), el Centro de Internet de las Cosas e IA (2023), la incubadora Abioinnova, el Espacio de Innovación Tecnológica Tormes+ (abril de 2025) y, en obra o en proyecto, el Centro de Innovación Juvenil de Garrido y el Centro Ciudad del Talento. "
             "El Distrito Tecnológico, en los terrenos del antiguo Mercasalamanca, es un proyecto distinto y todavía sin construir: la Junta prevé invertir 25,7 millones de euros y en mayo de 2026 solo se había licitado la redacción de proyectos (781.419 euros)."),
    rapida=[
        {"k": "Qué es", "v": "Estrategia y marca municipal de innovación y emprendimiento tecnológico (Ayuntamiento de Salamanca)"},
        {"k": "Promotor", "v": "Ayuntamiento de Salamanca; concejal de Promoción Económica, Comercio, Mercados y Juventud: Pedro Martínez; alcalde: Carlos García Carbayo"},
        {"k": "Estructura", "v": "Seis ámbitos en tres «constelaciones»: PIENSA (Tecnología y Ciencia), HACE (Emprendimiento y Logística) y CUIDA (Sostenibilidad y Salud)"},
        {"k": "Arranque", "v": "El Centro Tormes+ se presentó el 9/03/2022; la prensa sitúa el arranque de la estrategia en la primavera de 2023 (ver «no verificado»)"},
        {"k": "Centros abiertos", "v": "Tormes+ (CEFE), Espacio de Innovación Tecnológica Tormes+, Centro de IoT e IA, Abioinnova"},
        {"k": "Centros en desarrollo", "v": "Centro de Innovación Juvenil (Casa de la Juventud de Garrido), Centro Ciudad del Talento (antiguo albergue Lazarillo de Tormes) y Distrito Tecnológico (antiguo Mercasalamanca)"},
        {"k": "Contacto oficial", "v": "salamancatech@aytosalamanca.es · +34 613 248 716 (web oficial salamancatech.es)"},
        {"k": "Web oficial", "v": "salamancatech.es; Tormes+: tormesplus.com; Talentum: talentum.salamancatech.es; cumbre: summit.salamancatech.es"},
    ],
    cifras=[
        {"concepto": "Centros en la red (marca «hexágono»)", "valor": "6 (Tormes+, Espacio de Innovación Tecnológica, Centro de IoT e IA, Abioinnova, Centro de Innovación Juvenil, Centro Ciudad del Talento); el Distrito Tecnológico se cuenta aparte", "fuente": HEX},
        {"concepto": "Horizonte temporal de la red", "valor": "de marzo de 2022 a 2030", "fuente": HEX},
        {"concepto": "Empresas y entidades en la cumbre Salamanca Tech (marzo de 2026)", "valor": "cerca de 100", "fuente": ESP0324},
        {"concepto": "Compromiso de la Junta (Salamanca Tech Summit, 15/04/2026)", "valor": "2.000 empleos tecnológicos al año y +15 % de inversión en innovación (compromiso general de Castilla y León, no solo del distrito)", "fuente": ESP0415},
        {"concepto": "PAI «CoNEcta Salamanca» (marco FEDER de Garrido)", "valor": "más de 15,2 millones de euros, 60 % FEDER", "fuente": ESP0605},
        {"concepto": "Corredores verdes y zonas verdes (contexto de la vertical Sostenibilidad)", "valor": "más de 120 km de corredores verdes y más de 2,6 millones de m² de zonas verdes", "fuente": AREA},
    ],
    nota_cifras="Las cifras de inversión por centro están en las fichas de cada uno y en la ficha de financiación. No se suman porque proceden de financiadores y fechas distintos.",
    secciones=[
        {"h": "No confundir: Salamanca Tech, Centro Tormes+ y Distrito Tecnológico", "p": [NOMEN,
            "Cuando se pregunte «qué es el Centro Tormes+», la respuesta es un centro público municipal de formación y emprendimiento. Cuando se pregunte «qué es el Distrito Tecnológico», la respuesta es un proyecto futuro de dos edificios (Junta y Universidad de Salamanca) en el sector Sendero de las Cregas. Cuando se pregunte «qué es Salamanca Tech», la respuesta es la estrategia que engloba ambos."]},
        {"h": "Los seis ámbitos de Salamanca Tech", "items": [
            "PIENSA (cerebro): Tecnología y Ciencia. Incluye el Centro de IoT e IA (AIR Institute) y el Espacio de Innovación Tecnológica Tormes+.",
            "HACE (mano): Emprendimiento y Logística. La web oficial cita Abioinnova, Tormes+ y la Plataforma Logística Intermodal.",
            "CUIDA (corazón): Sostenibilidad y Salud. Incluye Abioinnova (salud) y el Centro Ciudad del Talento (cuidados, proyecto TRUST).",
            "Logística (dato del Ayuntamiento): la Plataforma Intermodal Ferroviaria admite trenes de 750 m y conecta con los puertos portugueses de Leixões y Aveiro; la Zona de Actividades Logísticas ofrece despacho aduanero y más de 30.000 m³ de conservación y congelado de alimentos."]},
        {"h": "Programas de capital humano", "items": [
            "Talentum (talentum.salamancatech.es): programa para jóvenes con desarrollo de habilidades, experiencias prácticas y conexión con empresas y proyectos de la ciudad.",
            "Convenio con la Fundación INCYDE (abril de 2026): formación y becas de seis meses en empresas de la ciudad o para lanzar un proyecto desde Tormes+ (ver ficha de financiación).",
            "STEAMbrace (Horizon Europe): educación STEAM en los campamentos Salamanca Tech desde la Navidad de 2026."]},
    ],
    historia=[
        {"fecha": "09/03/2022", "hito": "Presentación del Centro de Emprendimiento y Formación Tormes+", "detalle": "Primer centro de la red, en la antigua Casa del Campo (avenida de La Salle).", "fuente": HEX},
        {"fecha": "2023", "hito": "Arranque de la estrategia Salamanca Tech con seis verticales", "detalle": "Salud, ciencia, tecnología, emprendimiento, logística y sostenibilidad, según El Español.", "fuente": ESP1221},
        {"fecha": "29/09/2023", "hito": "Inauguración del Centro de IoT e IA", "detalle": "Con Ayuntamiento, Junta y Universidad de Salamanca; gestionado por AIR Institute.", "fuente": HEX},
        {"fecha": "25/04/2025", "hito": "Inauguración del Espacio de Innovación Tecnológica Tormes+", "detalle": "Robótica colaborativa, gemelo digital y realidad mixta.", "fuente": RTV},
        {"fecha": "15/04/2026", "hito": "Salamanca Tech Summit 2026", "detalle": "Inauguración por el presidente de la Junta en funciones, Alfonso Fernández Mañueco.", "fuente": ESP0415},
        {"fecha": "12/05/2026", "hito": "Licitación de proyectos del Distrito Tecnológico", "detalle": "781.419 € por Somacyl (Junta).", "fuente": DEBATE},
    ],
    no_verificado=[
        "Fecha de nacimiento de Salamanca Tech: El Español la sitúa en la primavera de 2023, pero el primer centro (Tormes+) se presentó en marzo de 2022 y la web oficial no da fecha. Conviene hablar de «red de centros desde 2022».",
        "La web oficial dice que los nuevos espacios son «proyectos en desarrollo, todavía no abiertos al público»; no da plazos para ninguno.",
        "Número exacto de empresas, usuarios y alumnos de toda la red: no hay un balance oficial consolidado en las fuentes consultadas.",
        "El reportaje de Salamanca24horas (26/08/2026) tiene incoherencias de plazo en el Centro de Innovación Juvenil (finales de 2027 frente a «tres años y medio»); para ese centro prevalece El Español (obras de un año).",
    ],
    faq=[
        {"q": "¿Qué es Salamanca Tech?", "a": "La estrategia y marca de innovación del Ayuntamiento de Salamanca. Conecta universidades, centros de investigación, empresas, instituciones y ciudadanía y se articula en una red de centros municipales (Tormes+, Abioinnova, Centro de IoT e IA y otros) con seis ámbitos: tecnología, ciencia, emprendimiento, logística, sostenibilidad y salud."},
        {"q": "¿Es lo mismo el Centro Tormes+ que el Distrito Tecnológico?", "a": "No. Tormes+ es un centro municipal de formación y emprendimiento abierto desde 2022 en la avenida de La Salle. El Distrito Tecnológico es un proyecto futuro de la Junta, el Ayuntamiento y la USAL en los terrenos del antiguo Mercasalamanca (sector Sendero de las Cregas), aún sin obras en mayo de 2026."},
        {"q": "¿Cuántos centros forma la red Salamanca Tech?", "a": "Seis, según el Ayuntamiento y la prensa: Tormes+, el Espacio de Innovación Tecnológica Tormes+, el Centro de IoT e IA, la incubadora Abioinnova, el Centro de Innovación Juvenil de Garrido (en obra) y el Centro Ciudad del Talento (adjudicado). El Distrito Tecnológico no entra en esa cuenta."},
        {"q": "¿Quién financia Salamanca Tech?", "a": "Varias vías: fondos municipales, fondos FEDER en Garrido (60 %) y Ciudad del Talento (4,4 de 5,44 millones), la Junta de Castilla y León (Espacio de Innovación Tecnológica, 955.158,86 € de adjudicación; Distrito Tecnológico, 25,7 millones previstos), Horizon Europe (STEAMbrace) y convenios como el de INCYDE."},
        {"q": "¿Dónde puedo informarme o contactar?", "a": "En salamancatech.es y, para cursos y talleres, en tormesplus.com. El contacto publicado en la web oficial es salamancatech@aytosalamanca.es."},
    ],
    fuentes=[STECH, AREA, HEX, ESP1221, ESP0324, ESP0415, ESP0605, DEBATE],
)

# ================================================================ 2. CENTRO TORMES+
F["centro-tormes-plus"] = dict(
    titulo="Centro Tormes+ (Salamanca): qué es, dónde está, instalaciones, cursos e inversión",
    descripcion="Ficha del Centro de Emprendimiento y Formación Tormes+ del Ayuntamiento de Salamanca: ubicación en la antigua Casa del Campo, 1,49 millones de inversión, salas, FabLab, cursos gratuitos y programas europeos",
    schema_type="Organization",
    nombre_habitual="Centro Tormes+",
    resumen=("El Centro de Emprendimiento y Formación Tormes+ (CEFE) es un centro público del Ayuntamiento de Salamanca para formación, coworking y emprendimiento tecnológico, ubicado en la antigua Casa del Campo (avenida de La Salle). "
             "Se presentó el 9 de marzo de 2022 con una inversión global de 1.487.618 euros, una parcela de 3.500 m² y un edificio de 1993 reformado. Cuenta con aulas, una sala diáfana de coworking y un FabLab con impresión 3D. "
             "Es el primer centro de la red Salamanca Tech; no es el Distrito Tecnológico."),
    rapida=[
        {"k": "Nombre oficial", "v": "Centro de Emprendimiento y Formación Tormes+ (CEFE); en prensa, «Centro Tormes+» o «Tormes+»"},
        {"k": "Titular", "v": "Ayuntamiento de Salamanca (Concejalía de Promoción Económica); coordinado con la Escuela de Organización Industrial (EOI) según prensa especializada"},
        {"k": "Ubicación", "v": "Antigua Casa del Campo, avenida de La Salle (Salamanca)"},
        {"k": "Presentación", "v": "9 de marzo de 2022"},
        {"k": "Edificio y parcela", "v": "Edificio de 1993 reformado; parcela de 3.500 m²"},
        {"k": "Inversión global", "v": "1.487.618 €"},
        {"k": "Espacios", "v": "Planta baja: sala polivalente de 115 m² (aulario) y sala diáfana de 165 m² con 19 puestos y taquillas. Planta superior: 5 aulas (2 con ordenadores y pizarras digitales). FabLab."},
        {"k": "FabLab (laboratorio de fabricación digital)", "v": "Impresora 3D, mini fresadora CNC, plotter de corte y plancha de calor"},
        {"k": "Anexo", "v": "Espacio de Innovación Tecnológica Tormes+ (robótica colaborativa y gemelo digital), abierto en abril de 2025"},
        {"k": "Inscripciones y cursos", "v": "tormesplus.com"},
    ],
    cifras=[
        {"concepto": "Inversión global del centro", "valor": "1.487.618 €", "fuente": HEX},
        {"concepto": "Parcela", "valor": "3.500 m²", "fuente": HEX},
        {"concepto": "Sala polivalente (aulario)", "valor": "115 m²", "fuente": HEX},
        {"concepto": "Sala diáfana de coworking", "valor": "165 m², 19 puestos con taquillas", "fuente": HEX},
        {"concepto": "Aulas en la planta superior", "valor": "5 (2 con ordenadores y pizarras digitales)", "fuente": HEX},
        {"concepto": "Beca INCYDE/Salamanca Tech asociada al centro (2026)", "valor": "bolsa de 500.000 € para formación y prácticas en empresas o para lanzar un proyecto desde Tormes+ (el titular del medio habla de 250.000 €; ver ficha de financiación)", "fuente": INCYDE},
    ],
    nota_cifras="No hay en las fuentes consultadas un balance oficial de alumnos, usuarios o empresas atendidas por Tormes+ desde 2022.",
    secciones=[
        {"h": "Qué ofrece", "items": [
            "Formación gratuita: cursos y talleres (por ejemplo, talleres con CDTI e INCYDE sobre financiación de proyectos de I+D+i para startups y Sello PYME Innovadora; cursos de edición de vídeo, según titulares de prensa local de noviembre de 2026).",
            "Coworking y espacio de trabajo para emprendedores y autónomos en la sala diáfana de 165 m².",
            "FabLab con impresión 3D, fresado CNC y corte para prototipos.",
            "Espacio de Innovación Tecnológica Tormes+ (anexo): robots colaborativos (cobots UR3 y UR5), gemelos digitales y gafas de realidad mixta (ver su ficha).",
            "Programa europeo STEAMbrace (Horizon Europe): el centro se incorporó en agosto de 2026; aplicación en los campamentos Salamanca Tech, empezando por el campamento de Navidad de 2026 para el grupo de 10 a 12 años, con plataforma STEAM Digital Hub y contenidos de realidad virtual para edades de 11 a 18 años, con adaptaciones para 6 a 12."]},
        {"h": "Cómo se relaciona con el resto de Salamanca Tech", "p": [NOMEN]},
    ],
    historia=[
        {"fecha": "09/03/2022", "hito": "Presentación del centro", "detalle": "Con el alcalde Carlos García Carbayo, en la antigua Casa del Campo.", "fuente": HEX},
        {"fecha": "2023–2024", "hito": "Funcionamiento a pleno rendimiento", "detalle": "Descrito así por El Español en 2024.", "fuente": ESP0212},
        {"fecha": "25/04/2025", "hito": "Apertura del Espacio de Innovación Tecnológica Tormes+ (anexo)", "detalle": "Siete cursos gratuitos de 15 plazas en mayo y junio de 2025.", "fuente": RTV},
        {"fecha": "27/04/2026", "hito": "Segundo convenio con la Fundación INCYDE", "detalle": "Becas para formación y emprendimiento desde Tormes+.", "fuente": INCYDE},
        {"fecha": "28/08/2026", "hito": "Incorporación al proyecto europeo STEAMbrace", "detalle": "Horizon Europe; campamento de Navidad de 2026.", "fuente": STEAM},
    ],
    no_verificado=[
        "Dirección postal con número exacto: aparecen referencias a «avenida de La Salle, 131» en buscadores, pero no se ha confirmado en una fuente oficial legible. Las fuentes oficiales consultadas solo dicen «avenida de La Salle».",
        "No está claro en las fuentes si el CEFE y el Espacio de Innovación Tecnológica ocupan el mismo edificio o dos edificios en la misma parcela.",
        "Coordinación con la EOI: procede de prensa especializada (ecosistemastartup.com), no de una nota oficial leída.",
        "Aforo, horarios y tarifas: no figuran en las fuentes leídas (la web tormesplus.com no pudo cargarse en la verificación).",
        "El PDF municipal «a59_centro_tormes_plus» no se pudo leer (binario), por lo que no se han extraído sus datos.",
    ],
    faq=[
        {"q": "¿Qué es el Centro Tormes+ de Salamanca?", "a": "Un centro público municipal de formación, coworking y emprendimiento tecnológico, en la antigua Casa del Campo (avenida de La Salle), presentado el 9 de marzo de 2022 con 1.487.618 € de inversión. Forma parte de la red Salamanca Tech."},
        {"q": "¿Dónde está el Centro Tormes+?", "a": "En la avenida de La Salle de Salamanca, en el edificio de la antigua Casa del Campo (construido en 1993 y reformado), sobre una parcela de 3.500 m²."},
        {"q": "¿Los cursos de Tormes+ son gratuitos?", "a": "Los cursos y talleres difundidos por el Ayuntamiento y la prensa (robótica colaborativa, gemelo digital, talleres CDTI/INCYDE, edición de vídeo) se anuncian como gratuitos y con inscripción en tormesplus.com. Cada convocatoria tiene sus plazas; por ejemplo, 15 por curso en 2025."},
        {"q": "¿Qué instalaciones tiene?", "a": "Sala polivalente de 115 m², sala diáfana de coworking de 165 m² con 19 puestos, cinco aulas y un FabLab con impresora 3D, mini fresadora CNC, plotter de corte y plancha de calor. El anexo Espacio de Innovación Tecnológica añade cobots, gemelo digital y realidad mixta."},
        {"q": "¿Es el Centro Tormes+ el distrito tecnológico?", "a": "No. El distrito tecnológico es un proyecto distinto, aún sin construir, en el antiguo Mercasalamanca (sector Sendero de las Cregas), con edificios de la Junta y de la Universidad de Salamanca."},
    ],
    fuentes=[HEX, AREA, STECH, RTV, TRIB, STEAM, INCYDE, TORMES_WEB],
)

# ================================================================ 3. EITT
F["espacio-innovacion-tecnologica-tormes"] = dict(
    titulo="Espacio de Innovación Tecnológica Tormes+ (Salamanca): robótica colaborativa, gemelo digital y cursos",
    descripcion="Ficha del Espacio de Innovación Tecnológica Tormes (EITT), anexo del Centro Tormes+: 955.158,86 € de adjudicación financiados por la Junta, inauguración en abril de 2025, cobots UR3/UR5 y cursos gratuitos",
    schema_type="Organization",
    nombre_habitual="Espacio de Innovación Tecnológica Tormes+",
    resumen=("El Espacio de Innovación Tecnológica Tormes (EITT, «Tormes+» en prensa) es un anexo del Centro de Formación y Emprendimiento Tormes+ dedicado a tecnologías inmersivas y robótica: realidad virtual, aumentada y mixta, gemelos digitales y robots colaborativos (cobots UR3 y UR5). "
             "Se adjudicó por 955.158,86 euros con financiación de la Junta de Castilla y León y nueve meses de plazo, y se inauguró el 25 de abril de 2025 con siete cursos gratuitos de 15 plazas."),
    rapida=[
        {"k": "Nombre", "v": "Espacio de Innovación Tecnológica Tormes (EITT), también «Espacio de Innovación Tecnológica Tormes+»"},
        {"k": "Promotor", "v": "Concejalía de Promoción Económica del Ayuntamiento de Salamanca"},
        {"k": "Financiación de la obra", "v": "Junta de Castilla y León (según nota municipal)"},
        {"k": "Adjudicación", "v": "955.158,86 €; plazo de ejecución de 9 meses"},
        {"k": "Inauguración", "v": "25 de abril de 2025 (alcalde Carlos García Carbayo)"},
        {"k": "Ubicación", "v": "Avenida de La Salle, junto al Centro Tormes+ (anexo)"},
        {"k": "Tecnologías", "v": "Realidad virtual, aumentada y mixta; robótica colaborativa y de servicios; gemelo digital; célula flexible de fabricación (FMS); impresión 3D"},
        {"k": "Inscripción en cursos", "v": "tormesplus.com (secciones robots-colaborativos e inteligencia-artificial)"},
    ],
    cifras=[
        {"concepto": "Presupuesto de adjudicación de las obras", "valor": "955.158,86 €", "fuente": EITT_AYTO},
        {"concepto": "Plazo de ejecución", "valor": "9 meses", "fuente": EITT_AYTO},
        {"concepto": "Cursos de la primera convocatoria", "valor": "7 cursos gratuitos, 15 plazas cada uno", "fuente": RTV},
        {"concepto": "Robótica colaborativa", "valor": "3 cursos (básico, medio y avanzado): 14, 21 y 28 de mayo de 2025, 16:30–19:30 h; cobots UR3 y UR5 y sistemas FMS", "fuente": TRIB},
        {"concepto": "Gemelo digital", "valor": "4 cursos: 13, 20 y 27 de mayo y 3 de junio de 2025, 16:30–18:30 h", "fuente": TRIB},
    ],
    nota_cifras="El plazo de nueve meses y la adjudicación proceden de una nota municipal cuya fecha visible es 22/09/2023; la propia página puede haberse actualizado después. La nota no nombra a la empresa adjudicataria ni da la superficie.",
    secciones=[
        {"h": "Actividad prevista y realizada", "items": [
            "Experimentación con realidad virtual, realidad aumentada y robótica de servicios o colaborativa.",
            "Robots colaborativos para industria, con posibilidad de uso por empresas e investigadores.",
            "Simulaciones en sanidad, educación, arquitectura o cine.",
            "Formación y consultoría gratuita para ciudadanos, autónomos y empresas, incluido el acceso a entornos digitales y servicios de metaverso.",
            "Jornada inaugural (25/04/2025): talleres simultáneos de robótica colaborativa, gemelo digital y gafas de realidad mixta con alumnado de Bachillerato Tecnológico del IES Francisco Salinas, FP del Centro Río Tormes, Ingeniería Mecánica de la USAL y usuarios del FabLab."]},
        {"h": "Posición en la red", "p": ["El alcalde lo presentó como un «nuevo eje» de la red de infraestructuras de transferencia de I+D+i de Salamanca Tech, junto con Abioinnova, el Centro de IoT e IA y el Centro Tormes+."]},
    ],
    historia=[
        {"fecha": "22/09/2023 (fecha de la nota)", "hito": "Inicio de las obras", "detalle": "La nota municipal dice que «esta semana han comenzado las obras»; la fecha visible podría no ser la de publicación original.", "fuente": EITT_AYTO},
        {"fecha": "25/04/2025", "hito": "Inauguración", "detalle": "Talleres inaugurales y anuncio de siete cursos.", "fuente": RTV},
        {"fecha": "13/05–03/06/2025", "hito": "Primera tanda de cursos", "detalle": "Cuatro de gemelo digital y tres de robótica colaborativa.", "fuente": TRIB},
    ],
    no_verificado=[
        "Superficie, empresa adjudicataria y coste final: no figuran en las fuentes leídas.",
        "Fecha real de la nota de inicio de obras: la página muestra 22/09/2023, pero la imagen de cabecera lleva un parámetro de abril de 2024.",
        "El cuarto curso de gemelo digital aparece titulado de forma distinta según el medio («implementación en empresa» o «en empresas y hospitales»).",
        "Si se han mantenido cursos de estas tecnologías después de junio de 2025: no se ha verificado el calendario posterior.",
    ],
    faq=[
        {"q": "¿Qué es el Espacio de Innovación Tecnológica Tormes+?", "a": "Un anexo del Centro Tormes+ de Salamanca con robots colaborativos, gemelo digital y realidad virtual, aumentada y mixta, inaugurado el 25 de abril de 2025 y orientado a formación gratuita de ciudadanos, autónomos, empresas y estudiantes."},
        {"q": "¿Cuánto costó el Espacio de Innovación Tecnológica Tormes?", "a": "La adjudicación fue de 955.158,86 € con financiación de la Junta de Castilla y León y nueve meses de plazo, según la nota municipal. No hay en las fuentes un coste final."},
        {"q": "¿Qué cursos se impartieron al abrir?", "a": "Siete gratuitos de 15 plazas: tres de robótica colaborativa (básico, medio y avanzado, con cobots UR3 y UR5) y cuatro de gemelo digital, entre el 13 de mayo y el 3 de junio de 2025."},
        {"q": "¿Cómo me inscribo?", "a": "A través de tormesplus.com, que es la web del centro."},
    ],
    fuentes=[EITT_AYTO, TRIB, RTV, AREA, HEX],
)

# ================================================================ 4. DISTRITO
F["distrito-tecnologico-salamanca"] = dict(
    titulo="Distrito Tecnológico de Salamanca (antiguo Mercasalamanca): edificios, inversión, estado y calendario",
    descripcion="Ficha del Distrito Tecnológico de Salamanca: parcela M4 del sector Sendero de las Cregas, edificio de la Junta (8.800 m²) y de la USAL (5.800 m²), 25,7 millones de la Junta, licitación de proyectos de 781.419 € y contradicciones entre fuentes",
    schema_type="Place",
    nombre_habitual="Distrito Tecnológico de Salamanca",
    resumen=("El Distrito Tecnológico de Salamanca es un proyecto de la Junta de Castilla y León, el Ayuntamiento y la Universidad de Salamanca en los terrenos del antiguo Mercasalamanca (sector SUNC 52 «Sendero de las Cregas», parcela M4, calle Julita Ramos). "
             "Prevé dos edificios: uno tecnológico-empresarial de la Junta (unos 8.800 m² construidos) y otro polivalente de la USAL (unos 5.800 m²). La Junta cifra su inversión en 25,7 millones de euros y el Ayuntamiento aporta algo más de 11 millones. "
             "En mayo de 2026 solo se había licitado la redacción de proyectos (781.419 euros, vía Somacyl) y la parcela seguía en trámite urbanístico: no hay obras ni fechas oficiales de apertura. No es el Centro Tormes+."),
    rapida=[
        {"k": "Qué es", "v": "Proyecto futuro de distrito tecnológico-empresarial con formación universitaria, investigación y empresas"},
        {"k": "Impulsores", "v": "Junta de Castilla y León, Ayuntamiento de Salamanca y Universidad de Salamanca (protocolo de colaboración; la prensa menciona también a la Diputación, ver contradicciones)"},
        {"k": "Ubicación", "v": "Terrenos del antiguo Mercasalamanca; ámbito SUNC 52 «Sendero de las Cregas»; parcela M4; calle Julita Ramos (Salamanca)"},
        {"k": "Fase 1", "v": "Edificio Tecnológico-Empresarial de la Junta: unos 8.800 m² construidos (emprendimiento, transferencia tecnológica, formación e investigación, estudio y biblioteca, escuela de negocio, salas, despachos, restauración)"},
        {"k": "Fase 2", "v": "Edificio Polivalente de la USAL: unos 5.800 m² construidos (docencia, aulas, laboratorios, administración)"},
        {"k": "Inversión prevista", "v": "Junta: 25,7 M€ (incluye la licitación de proyectos); Ayuntamiento: algo más de 11 M€"},
        {"k": "Último hito", "v": "12/05/2026: licitación de redacción de anteproyecto, proyecto básico y de ejecución y asistencia a la dirección de obra (781.419 €), por la Consejería de Medio Ambiente, Vivienda y Ordenación del Territorio a través de Somacyl"},
        {"k": "Estado urbanístico", "v": "En proceso urbanístico para su uso como equipamiento público (mayo de 2026)"},
        {"k": "Estado de obra", "v": "Sin obras ni fecha oficial de inicio o apertura en las fuentes consultadas"},
    ],
    cifras=[
        {"concepto": "Inversión prevista de la Junta", "valor": "25,7 millones de euros (partida que engloba los 781.419 € de la licitación; la fuente no aclara qué cubre el resto)", "fuente": DEBATE},
        {"concepto": "Aportación del Ayuntamiento", "valor": "algo más de 11 millones de euros", "fuente": DEBATE},
        {"concepto": "Licitación de proyectos y dirección de obra", "valor": "781.419 € (el cuerpo del texto dice «superior a 780.000 euros»)", "fuente": DEBATE},
        {"concepto": "Edificio de la Junta (fase 1)", "valor": "unos 8.800 m² construidos", "fuente": DEBATE},
        {"concepto": "Edificio de la USAL (fase 2)", "valor": "unos 5.800 m² construidos", "fuente": DEBATE},
        {"concepto": "Superficie construida conjunta (cálculo de Open Salamanca)", "valor": "unos 14.600 m² (8.800 + 5.800)", "fuente": DEBATE},
        {"concepto": "Peso de la licitación sobre la inversión de la Junta (cálculo de Open Salamanca)", "valor": "≈3 % (781.419 / 25.700.000)", "fuente": DEBATE},
        {"concepto": "Explanada comprada por el Ayuntamiento", "valor": "más de 6.000 m² (dentro del sector SUNC-52); compra formalizada en diciembre de 2023, estimada por el medio en 11 millones de euros (no es un importe oficial)", "fuente": ESP0212},
    ],
    nota_cifras="Los 25,7 M€ y los «más de 11 M€» son cifras de prensa de una sola fuente (El Debate, 12/05/2026); no se ha localizado la nota oficial de la Junta. Las superficies proceden de un bloque relacionado del propio artículo.",
    secciones=[
        {"h": "Zonas comunes previstas", "p": ["Recepción, aparcamientos, salón de actos, restauración, servicios para empresas e instalaciones, en plantas baja, semisótano o sótano; aparcamiento de bicicletas y posibles ampliaciones futuras. Se describe una edificación «permeable e integrada con el entorno» con zonas verdes próximas."]},
        {"h": "Por qué se llama «antiguo Mercasalamanca»", "p": ["La explanada formaba parte de la parcela del mercado mayorista (Mercasalamanca), que el Ayuntamiento compró en diciembre de 2023. El sector SUNC-52 «Sendero de las Cregas» estaba clasificado como residencial en el PGOU, de modo que hace falta un cambio a usos terciarios y de equipamiento. El concejal de Hacienda, Fernando Rodríguez, calificó el proceso de «farragoso»."]},
        {"h": "Contradicciones entre fuentes", "items": [
            "Protocolo: El Debate habla de un «segundo protocolo» con Ayuntamiento, Diputación y USAL, pero cita Junta, Ayuntamiento y Universidad en la entradilla; El Español (2024) cita Junta, Diputación, Ayuntamiento y Universidad; El Español (2026) habla de «tres instituciones» y de un protocolo iniciado «hace cuatro años».",
            "Usos: El Español (2024) decía que el distrito incluiría viviendas; en 2026 se describe como equipamiento público sin viviendas.",
            "Calendario: en diciembre de 2024 se esperaba la urbanización en 2026 y los primeros edificios en 2027; en mayo de 2026 solo se había licitado la redacción de proyectos. Ese calendario no se cumplió o no es fiable.",
            "Nombres de edificios: algunas fuentes hablan de «I-Futuro» (Junta) y «USAL I-Quantum»; las páginas leídas usan «Tecnológico-Empresarial» y «Polivalente»."]},
    ],
    historia=[
        {"fecha": "12/2023", "hito": "El Ayuntamiento formaliza la compra de la parcela de Mercasalamanca", "detalle": "Importe estimado por el medio en 11 millones; no oficial.", "fuente": ESP0212},
        {"fecha": "02/2024", "hito": "Convenio Ayuntamiento–AIR Institute que incluye el Distrito Tecnológico", "detalle": "Aportación municipal de 150.000 € y vigencia inicial hasta 31/12/2024; firman Carlos García Carbayo y Juan Manuel Corchado.", "fuente": ESP0212},
        {"fecha": "21/12/2024", "hito": "El distrito sigue en fase administrativa", "detalle": "Despegue no previsto «al menos hasta 2027» según El Español.", "fuente": ESP1221},
        {"fecha": "15/04/2026", "hito": "Compromiso conjunto Junta–Ayuntamiento–USAL reiterado", "detalle": "En el Salamanca Tech Summit, el presidente de la Junta en funciones lo describe como un «amplio espacio urbano con instalaciones punteras».", "fuente": ESP0415},
        {"fecha": "12/05/2026", "hito": "Licitación de proyectos y asistencia a dirección de obra", "detalle": "781.419 € por Somacyl en la Plataforma de Contratación del Estado.", "fuente": DEBATE},
    ],
    no_verificado=[
        "Fecha de firma, texto y partes exactas del protocolo (en prensa: noviembre o diciembre de 2025 según algunas búsquedas): no se ha localizado un documento oficial.",
        "Superficie de la parcela M4 y edificabilidad: no figuran.",
        "Presupuesto de ejecución de las obras de los edificios: no figura; solo la licitación de proyectos, la inversión prevista de la Junta y la aportación municipal.",
        "Qué cubren exactamente los 25,7 M€ y los más de 11 M€ (compra del suelo, urbanización, edificios).",
        "Fecha de inicio de obras, de urbanización o de apertura: ninguna fuente de 2026 la da.",
        "Existencia de viviendas, bioincubadora o centro tecnológico propio dentro del distrito: solo aparecen en la descripción de 2024.",
        "La web oficial de Salamanca Tech lo describe como «en desarrollo», sin cifras, plazos ni presupuesto.",
    ],
    faq=[
        {"q": "¿Qué es el Distrito Tecnológico de Salamanca?", "a": "Un proyecto de la Junta, el Ayuntamiento y la USAL para crear un espacio con formación universitaria, investigación y empresas en los terrenos del antiguo Mercasalamanca. Constará de un edificio tecnológico-empresarial de la Junta (unos 8.800 m²) y otro polivalente de la USAL (unos 5.800 m²)."},
        {"q": "¿Dónde está el Distrito Tecnológico?", "a": "En la parcela M4 del sector SUNC 52 «Sendero de las Cregas», en la calle Julita Ramos, sobre los terrenos del antiguo mercado mayorista Mercasalamanca."},
        {"q": "¿Cuánto cuesta el Distrito Tecnológico?", "a": "La Junta prevé invertir 25,7 millones de euros y el Ayuntamiento aporta algo más de 11 millones. En mayo de 2026 solo estaba licitada la redacción de proyectos y la dirección de obra por 781.419 €. No hay un presupuesto de obra publicado."},
        {"q": "¿Cuándo se abrirá el Distrito Tecnológico?", "a": "No hay fecha oficial. En diciembre de 2024 se hablaba de un despegue no antes de 2027, y en mayo de 2026 la parcela seguía en trámite urbanístico y sin obras."},
        {"q": "¿Qué relación tiene con Salamanca Tech y Tormes+?", "a": "Forma parte de la estrategia Salamanca Tech como proyecto en desarrollo, pero es independiente del Centro Tormes+, que es un centro municipal ya abierto desde 2022 en la avenida de La Salle."},
        {"q": "¿Quién construye el distrito?", "a": "La licitación de proyectos corresponde a la Consejería de Medio Ambiente, Vivienda y Ordenación del Territorio de la Junta a través de Somacyl. El edificio de la fase 2 corresponde a la Universidad de Salamanca."},
    ],
    fuentes=[DEBATE, ESP0212, ESP1221, ESP0415, STECH],
)

# ================================================================ 5. ABIOINNOVA
F["abioinnova"] = dict(
    titulo="Abioinnova (Salamanca): incubadora biosanitaria de Salamanca Tech en La Platina",
    descripcion="Ficha de Abioinnova, incubadora y aceleradora de empresas biosanitarias del Ayuntamiento de Salamanca en el campus agroambiental de La Platina: laboratorios, empresas alojadas y convocatoria abierta",
    schema_type="Organization",
    nombre_habitual="Abioinnova",
    resumen=("Abioinnova es la incubadora y aceleradora de empresas biosanitarias y de ingeniería biomédica de Salamanca Tech, promovida por el Ayuntamiento con apoyo del ICE de Castilla y León, situada en el campus agroambiental de La Platina. "
             "Dispone de laboratorios de Biología Molecular y Celular y de Bioimpresión 3D, siete laboratorios privados, tres despachos y salas de coworking; en 2026 se citaban 17 empresas alojadas. El 17 de septiembre de 2026 publicó una convocatoria abierta y permanente para incorporar proyectos."),
    rapida=[
        {"k": "Qué es", "v": "Incubadora y aceleradora de empresas biosanitarias y de ingeniería biomédica"},
        {"k": "Promotor", "v": "Ayuntamiento de Salamanca, con apoyo del Instituto para la Competitividad Empresarial de Castilla y León (ICECyL)"},
        {"k": "Ubicación", "v": "Campus Agroambiental de La Platina (Salamanca)"},
        {"k": "Ámbitos", "v": "Medicina personalizada, enfermedades raras, diseño de dispositivos médicos y alimentación sostenible"},
        {"k": "Espacios", "v": "Laboratorios de Biología Molecular y Celular y de Bioimpresión 3D; 7 laboratorios privados; 3 despachos privados; 2 salas de coworking; 1 sala de reuniones; 1 sala polivalente"},
        {"k": "Empresas alojadas", "v": "17 según Salamanca24horas (26/08/2026)"},
        {"k": "Convocatoria", "v": "Abierta y permanente para proyectos empresariales biosanitarios (publicada 17/09/2026)"},
        {"k": "Web", "v": "abioinnova.tech"},
    ],
    cifras=[
        {"concepto": "Empresas alojadas", "valor": "17", "fuente": HEX},
        {"concepto": "Laboratorios privados", "valor": "7", "fuente": HEX},
        {"concepto": "Despachos privados", "valor": "3", "fuente": HEX},
        {"concepto": "Convocatoria abierta y permanente", "valor": "publicada el 17/09/2026", "fuente": ABIO_CONV},
    ],
    nota_cifras="Otras fuentes hablan de 18 empresas instaladas y de «diez nuevos proyectos que se suman a los ocho operativos»; las cifras varían por fecha. En el Salamanca Tech Summit de abril de 2026 el rector de la USAL anunció nuevas bioincubadoras (ver fuente).",
    secciones=[{"h": "Papel en la red", "p": ["Abioinnova es el pilar de salud de Salamanca Tech (constelación CUIDA). Las obras se iniciaron en 2023 y los cursos arrancaron un año después, según Salamanca24horas."]}],
    historia=[
        {"fecha": "2023", "hito": "Construcción de la incubadora", "detalle": "Cursos un año después.", "fuente": HEX},
        {"fecha": "15/04/2026", "hito": "Anuncio de nuevas bioincubadoras por el rector de la USAL", "detalle": "En el Salamanca Tech Summit.", "fuente": RECTOR},
        {"fecha": "17/09/2026", "hito": "Convocatoria abierta y permanente", "detalle": "Para proyectos biosanitarios.", "fuente": ABIO_CONV},
    ],
    no_verificado=[
        "Presupuesto y financiación: una referencia del BOE de 30/07/2021 (BOE-B-2021-34463) atribuiría 1.250.000 € con ayuda FEDER del 50 % (625.000 €); no se ha leído su texto íntegro y no se incluye como dato firme.",
        "Superficie: un artículo sin fecha habla de 13.248 m²; no se ha contrastado con una fuente oficial.",
        "Fecha de inauguración: no localizada.",
        "Número de empresas: varía entre 17 y 18 según la fuente y el momento.",
    ],
    faq=[
        {"q": "¿Qué es Abioinnova?", "a": "La incubadora y aceleradora de empresas biosanitarias y de ingeniería biomédica de Salamanca Tech, en el campus agroambiental de La Platina."},
        {"q": "¿Cuántas empresas tiene?", "a": "17 según Salamanca24horas en agosto de 2026; otras fuentes dan 18. Las cifras cambian con el tiempo."},
        {"q": "¿Cómo se accede?", "a": "A través de una convocatoria abierta y permanente publicada el 17 de septiembre de 2026 para proyectos empresariales biosanitarios."},
    ],
    fuentes=[HEX, AREA, STECH, ABIO_CONV, RECTOR],
)

# ================================================================ 6. IoT e IA
F["centro-internet-cosas-inteligencia-artificial"] = dict(
    titulo="Centro de Internet de las Cosas e Inteligencia Artificial de Salamanca (AIR Institute)",
    descripcion="Ficha del Centro de IoT e IA de Salamanca Tech, inaugurado el 29/09/2023 y gestionado por AIR Institute: investigadores, iniciativas acogidas y convenio municipal",
    schema_type="Organization",
    nombre_habitual="Centro de Internet de las Cosas e Inteligencia Artificial",
    resumen=("El Centro de Internet de las Cosas e Inteligencia Artificial es un centro tecnológico de la red Salamanca Tech, inaugurado el 29 de septiembre de 2023 por el Ayuntamiento, la Junta de Castilla y León y la Universidad de Salamanca y gestionado por AIR Institute, entidad sin ánimo de lucro de investigación en informática e IA presidida por Juan Manuel Corchado. "
             "Al abrir trabajaban 60 investigadores y ha acogido 20 iniciativas; en marzo de 2024 el alcalde hablaba de casi 100 trabajadores."),
    rapida=[
        {"k": "Inauguración", "v": "29 de septiembre de 2023 (Ayuntamiento, Junta de Castilla y León y Universidad de Salamanca)"},
        {"k": "Gestor", "v": "AIR Institute (web air-institute.com)"},
        {"k": "Actividad", "v": "Investigación en IA e IoT y formación a empresas en TIC (con el Ayuntamiento)"},
        {"k": "Convenio", "v": "Ayuntamiento–AIR Institute (firmado en febrero de 2024): 150.000 € municipales, vigencia inicial hasta 31/12/2024"},
    ],
    cifras=[
        {"concepto": "Investigadores al abrir", "valor": "60", "fuente": HEX},
        {"concepto": "Iniciativas acogidas", "valor": "20", "fuente": HEX},
        {"concepto": "Aportación municipal al convenio de 2024", "valor": "150.000 €", "fuente": ESP0212},
    ],
    nota_cifras="No se ha localizado la inversión de construcción del centro ni su ubicación exacta en una fuente verificable.",
    secciones=[{"h": "Contexto", "p": ["Forma parte de la constelación PIENSA (Tecnología y Ciencia). AIR Institute tiene sus instalaciones principales de investigación en Béjar y presencia en el Parque Científico de la USAL, según fuentes europeas consultadas."]}],
    historia=[
        {"fecha": "29/09/2023", "hito": "Inauguración", "detalle": "Con Ayuntamiento, Junta y USAL.", "fuente": HEX},
        {"fecha": "02/2024", "hito": "Convenio Ayuntamiento–AIR Institute", "detalle": "150.000 € y estrategia Salamanca Tech.", "fuente": ESP0212},
    ],
    no_verificado=[
        "Ubicación exacta: la nota municipal de 2023 cita «Puente Ladrillo» pero no se ha contrastado en fuente verificable.",
        "Inversión de construcción: no localizada.",
        "Renovación del convenio tras 31/12/2024: sin información.",
        "El número de trabajadores (casi 100 en 2024, según declaraciones del alcalde) y de investigadores (60 al abrir) corresponde a momentos distintos.",
    ],
    faq=[
        {"q": "¿Qué es el Centro de IoT e IA de Salamanca?", "a": "Un centro tecnológico municipal de Salamanca Tech, inaugurado el 29 de septiembre de 2023 y gestionado por AIR Institute, dedicado a investigación en IA e Internet de las Cosas y a formación de empresas en TIC."},
        {"q": "¿Quién lo gestiona?", "a": "AIR Institute, entidad sin ánimo de lucro de investigación en informática e IA, presidida por Juan Manuel Corchado (catedrático de IA de la USAL)."},
    ],
    fuentes=[HEX, AREA, STECH, ESP0212],
)

# ================================================================ 7. GARRIDO
F["centro-innovacion-juvenil-garrido"] = dict(
    titulo="Centro de Innovación Juvenil de Garrido (Salamanca): Casa de la Juventud, 2,3 millones y fondos FEDER",
    descripcion="Ficha del sexto centro de Salamanca Tech: reforma de la Casa de la Juventud de Garrido, 2,3 millones de euros, 1.267 m², cofinanciación FEDER del 60 % del PAI CoNEcta Salamanca y calendario de obras",
    schema_type="Organization",
    nombre_habitual="Centro de Innovación Juvenil de Garrido",
    resumen=("El Centro de Innovación Juvenil de Garrido es la transformación de la Casa de la Juventud de Garrido en el sexto centro de Salamanca Tech. "
             "Tendrá un presupuesto de unos 2,3 millones de euros, hasta 1.267 m² construidos, una «Factoría de Ideas» (coworking juvenil), un espacio de metaverso y una sala multimedia. Forma parte del PAI «CoNEcta Salamanca» (más de 15,2 millones, 60 % FEDER). "
             "Las obras se licitaron el 5 de junio de 2026 con un año de ejecución previsto."),
    rapida=[
        {"k": "Estado", "v": "Obras licitadas el 05/06/2026 (no abierto)"},
        {"k": "Edificio", "v": "Casa de la Juventud de Garrido (Salamanca)"},
        {"k": "Presupuesto", "v": "Casi 2,3 M€"},
        {"k": "Superficie", "v": "Ampliación hasta 1.267 m² construidos"},
        {"k": "Contenido", "v": "«Factoría de Ideas» (coworking juvenil), metaverso (realidad virtual, aumentada y extendida), sala multimedia; en el exterior, calistenia, parkour y pump track"},
        {"k": "Financiación", "v": "FEDER (60 %) a través de la estrategia CoNEcta Salamanca (barrios Garrido Norte y Sur, Chinchibarra, Estación y Salesas)"},
        {"k": "Plazo", "v": "Inicio de obras previsto en el último trimestre de 2026, con un año de ejecución"},
    ],
    cifras=[
        {"concepto": "Presupuesto base de licitación", "valor": "casi 2,3 M€", "fuente": ESP0605},
        {"concepto": "PAI CoNEcta Salamanca (total)", "valor": "más de 15,2 M€, 60 % FEDER", "fuente": ESP0605},
        {"concepto": "Superficie construida", "valor": "1.267 m²", "fuente": ESP0407},
        {"concepto": "Importe FEDER estimado (cálculo de Open Salamanca)", "valor": "≈1,38 M€ (60 % de 2,3 M€); no figura en el texto de la fuente", "fuente": ESP0407},
    ],
    nota_cifras="El reportaje de Salamanca24horas dice que la finalización sería a finales de 2027 y también «tres años y medio» de plazo (con erratas); se prefiere el plazo de un año de El Español.",
    secciones=[{"h": "Quién lo presentó", "p": ["Acto del 7 de abril de 2026 con el alcalde Carlos García Carbayo, el concejal de Hacienda Fernando Rodríguez y el concejal de Promoción Económica y Juventud Pedro Martínez."]}],
    historia=[
        {"fecha": "07/04/2026", "hito": "Presentación del proyecto", "detalle": "Sexto nodo de Salamanca Tech.", "fuente": ESP0407},
        {"fecha": "05/06/2026", "hito": "Licitación de las obras", "detalle": "Presupuesto de casi 2,3 M€ y plazo de un año.", "fuente": ESP0605},
    ],
    no_verificado=[
        "Empresa adjudicataria y fecha real de inicio de obras: no localizadas.",
        "Fecha de apertura: depende de la adjudicación; la previsión de finales de 2027 es inferida de un reportaje con errores de plazo.",
    ],
    faq=[
        {"q": "¿Qué es el Centro de Innovación Juvenil de Garrido?", "a": "La reforma de la Casa de la Juventud de Garrido para convertirla en el sexto centro de Salamanca Tech, con coworking juvenil, metaverso y sala multimedia."},
        {"q": "¿Cuánto cuesta y quién lo paga?", "a": "Casi 2,3 millones de euros, con un 60 % de fondos FEDER a través del PAI CoNEcta Salamanca."},
        {"q": "¿Cuándo abre?", "a": "No hay fecha oficial. Las obras se licitaron en junio de 2026 con un año de ejecución, con inicio previsto en el último trimestre de 2026."},
    ],
    fuentes=[ESP0407, ESP0605, HEX, STECH],
)

# ================================================================ 8. CIUDAD DEL TALENTO
F["centro-ciudad-del-talento"] = dict(
    titulo="Centro Salamanca Ciudad del Talento (antiguo albergue Lazarillo de Tormes): proyecto TRUST, 5,4 millones y FEDER",
    descripcion="Ficha del Centro Ciudad del Talento de Salamanca Tech: reforma del antiguo albergue Lazarillo de Tormes, proyecto europeo TRUST, 3,39 millones de licitación, 4,4 millones FEDER y apertura prevista en 2030",
    schema_type="Organization",
    nombre_habitual="Centro Salamanca Ciudad del Talento",
    resumen=("El Centro Salamanca Ciudad del Talento será la reforma integral del antiguo albergue Lazarillo de Tormes como sede del proyecto europeo TRUST, orientado a personas cuidadoras y emprendimiento tecnológico con enfoque social. "
             "El presupuesto del proyecto es de 5.438.871 €, de los que 4,4 millones son FEDER; la licitación fue de 3.390.325,06 €, se adjudicó en enero de 2026 y el plazo es de tres años y medio, con funcionamiento previsto en 2030."),
    rapida=[
        {"k": "Edificio", "v": "Antiguo albergue Lazarillo de Tormes (Salamanca); tres plantas y un sótano"},
        {"k": "Proyecto", "v": "TRUST (cofinanciado por FEDER)"},
        {"k": "Socios", "v": "Universidad de Salamanca, FAMASA y Khora Urban Thinkers"},
        {"k": "Presupuesto del proyecto", "v": "5.438.871 € (4,4 M€ FEDER)"},
        {"k": "Licitación de las obras", "v": "3.390.325,06 €"},
        {"k": "Adjudicación", "v": "enero de 2026"},
        {"k": "Plazo", "v": "Tres años y medio; funcionamiento previsto en 2030"},
        {"k": "Planta baja", "v": "«Innovation & Care Center», vestíbulo, sala de reuniones (unas 20 personas), salón de actos (70), vivienda monitorizada, tres salas de formación y cuatro despachos"},
        {"k": "Planta alta", "v": "«Hub» de emprendimiento tecnológico con enfoque social"},
    ],
    cifras=[
        {"concepto": "Presupuesto del proyecto TRUST", "valor": "5.438.871 €", "fuente": HEX},
        {"concepto": "Aportación FEDER", "valor": "4,4 millones de euros (≈81 % del presupuesto; cálculo de Open Salamanca)", "fuente": HEX},
        {"concepto": "Presupuesto de licitación de las obras", "valor": "3.390.325,06 €", "fuente": HEX},
    ],
    nota_cifras="Datos de un único reportaje (Salamanca24horas, 26/08/2026), que cita al Ayuntamiento. La web oficial lo describe como «en desarrollo, todavía no abierto al público».",
    secciones=[{"h": "Perfil", "p": ["Integra el eje CUIDA de Salamanca Tech y combina un centro de cuidados con innovación y un hub de emprendimiento tecnológico con enfoque social."]}],
    historia=[{"fecha": "01/2026", "hito": "Adjudicación del cambio integral del edificio", "detalle": "Cofinanciado por FEDER.", "fuente": HEX}],
    no_verificado=[
        "Empresa adjudicataria y fecha de inicio de obras: no localizadas.",
        "Contraste del reparto entre FEDER y fondos municipales más allá de los 4,4 M€ FEDER.",
        "La fecha de funcionamiento de 2030 es previsión; no hay fecha oficial de apertura.",
    ],
    faq=[
        {"q": "¿Qué es el Centro Salamanca Ciudad del Talento?", "a": "La reforma del antiguo albergue Lazarillo de Tormes para albergar el proyecto europeo TRUST, con un centro de cuidados (Innovation & Care Center) y un hub de emprendimiento tecnológico con enfoque social."},
        {"q": "¿Cuánto cuesta?", "a": "El presupuesto del proyecto es de 5.438.871 €, con 4,4 millones de FEDER; las obras se licitaron por 3.390.325,06 €."},
        {"q": "¿Cuándo abrirá?", "a": "Se prevé que funcione en 2030, con un plazo de obra de tres años y medio desde la adjudicación de enero de 2026."},
    ],
    fuentes=[HEX, STECH],
)

# ================================================================ 9. FINANCIACION
F["financiacion-salamanca-tech"] = dict(
    titulo="Financiación de Salamanca Tech: cuánto cuestan el Centro Tormes+, el distrito tecnológico y la red de centros",
    descripcion="Tabla de importes de Salamanca Tech con fuente y fecha: Tormes+ 1,49 M€, Espacio de Innovación 955.158,86 €, Garrido 2,3 M€, Ciudad del Talento 5,44 M€, distrito 25,7 M€ de la Junta, convenios INCYDE y AIR Institute",
    schema_type="Dataset",
    nombre_habitual="Financiación de Salamanca Tech",
    resumen=("Importes publicados de Salamanca Tech, con fuente y fecha: Centro Tormes+ 1.487.618 €; Espacio de Innovación Tecnológica 955.158,86 € (Junta); Centro de Innovación Juvenil de Garrido casi 2,3 M€ (60 % FEDER); Ciudad del Talento 5.438.871 € (4,4 M€ FEDER); "
             "Distrito Tecnológico 25,7 M€ previstos por la Junta y más de 11 M€ del Ayuntamiento; convenio con AIR Institute 150.000 €; bolsa de becas INCYDE de 500.000 €. "
             "No deben sumarse: son conceptos, financiadores y fechas distintos."),
    rapida=[
        {"k": "Alcance", "v": "Importes con fuente de centros y programas de Salamanca Tech (2022–2026)"},
        {"k": "Advertencia", "v": "Los importes son de licitación, adjudicación o previsión según el caso; no son gasto ejecutado"},
    ],
    cifras=[
        {"concepto": "Centro Tormes+: inversión global (2022)", "valor": "1.487.618 € · Ayuntamiento", "fuente": HEX},
        {"concepto": "Espacio de Innovación Tecnológica Tormes: adjudicación", "valor": "955.158,86 € · financia la Junta de Castilla y León", "fuente": EITT_AYTO},
        {"concepto": "Convenio Ayuntamiento–AIR Institute (2024)", "valor": "150.000 € municipales", "fuente": ESP0212},
        {"concepto": "Casa de la Juventud de Garrido: presupuesto", "valor": "casi 2,3 M€ · 60 % FEDER", "fuente": ESP0605},
        {"concepto": "PAI CoNEcta Salamanca (marco de Garrido)", "valor": "más de 15,2 M€ · 60 % FEDER", "fuente": ESP0605},
        {"concepto": "Ciudad del Talento: proyecto TRUST", "valor": "5.438.871 € (4,4 M€ FEDER)", "fuente": HEX},
        {"concepto": "Ciudad del Talento: licitación de obras", "valor": "3.390.325,06 €", "fuente": HEX},
        {"concepto": "Distrito Tecnológico: inversión prevista de la Junta", "valor": "25,7 M€", "fuente": DEBATE},
        {"concepto": "Distrito Tecnológico: aportación del Ayuntamiento", "valor": "algo más de 11 M€", "fuente": DEBATE},
        {"concepto": "Distrito Tecnológico: licitación de proyectos y dirección de obra", "valor": "781.419 € · Somacyl", "fuente": DEBATE},
        {"concepto": "Compra de la parcela de Mercasalamanca (diciembre de 2023)", "valor": "≈11 M€ (estimación periodística, no oficial)", "fuente": ESP0212},
        {"concepto": "Becas INCYDE–Salamanca Tech (abril de 2026)", "valor": "bolsa de 500.000 € (el titular habla de 250.000 €); líneas «Emprende tu futuro» y «Emplea tu futuro»: 50 plazas, 1.050 €/mes durante 6 meses según otro medio", "fuente": INCYDE},
        {"concepto": "Abioinnova (referencia 2021, no verificada)", "valor": "1.250.000 € con FEDER del 50 % según una referencia BOE sin leer íntegramente", "fuente": S("BOE-B-2021-34463", "https://www.boe.es/boe/dias/2021/07/30/pdfs/BOE-B-2021-34463.pdf")},
    ],
    nota_cifras="Importe del Distrito: los 25,7 M€ de la Junta engloban la licitación de 781.419 € (≈3 %). No se suman los importes para evitar dobles cuentas: la compra de la parcela, p. ej., podría coincidir con la aportación municipal de más de 11 M€ del distrito, pero la fuente no lo dice.",
    secciones=[{"h": "Cómo leer estos datos", "items": [
        "Licitación = importe máximo de salida; adjudicación = importe contratado; previsión = compromiso anunciado.",
        "FEDER: fondos europeos que cofinancian proyectos municipales (Garrido, Ciudad del Talento).",
        "Horizon Europe financia STEAMbrace (programa educativo); no hay importe publicado en la fuente leída."]}],
    historia=[],
    no_verificado=[
        "No hay un presupuesto consolidado oficial de Salamanca Tech en las fuentes consultadas.",
        "El importe exacto de la bolsa INCYDE: 250.000 € (titular) frente a 500.000 € (cuerpo).",
        "Gasto ejecutado real de cada centro.",
    ],
    faq=[
        {"q": "¿Cuánto cuesta el Centro Tormes+?", "a": "1.487.618 € de inversión global según el reportaje de Salamanca24horas sobre su presentación en 2022; el Espacio de Innovación Tecnológica anexo se adjudicó por 955.158,86 €."},
        {"q": "¿Cuánto invierte la Junta en el distrito tecnológico?", "a": "25,7 millones de euros previstos, que incluyen la licitación de proyectos de 781.419 €. El Ayuntamiento aporta algo más de 11 millones."},
        {"q": "¿Qué parte es fondos europeos?", "a": "FEDER financia el 60 % de la Casa de la Juventud de Garrido (dentro de CoNEcta Salamanca) y 4,4 M€ de los 5,44 M€ de Ciudad del Talento. STEAMbrace recibe fondos de Horizon Europe."},
    ],
    fuentes=[HEX, EITT_AYTO, ESP0212, ESP0605, ESP0407, DEBATE, INCYDE],
)

# ================================================================ 10. CRONOLOGIA
F["cronologia-salamanca-tech"] = dict(
    titulo="Cronología de Salamanca Tech y el Centro Tormes+ (2022–2030)",
    descripcion="Línea temporal fechada de Salamanca Tech: Tormes+ (2022), Centro de IoT e IA (2023), Espacio de Innovación (2025), Garrido, Ciudad del Talento, licitación del distrito tecnológico (2026) y previsiones hasta 2030",
    schema_type="Dataset",
    nombre_habitual="Cronología de Salamanca Tech",
    resumen=("Línea temporal de Salamanca Tech con 22 hitos fechados entre marzo de 2022 y 2030: presentación del Centro Tormes+ (09/03/2022), inauguración del Centro de IoT e IA (29/09/2023), compra de Mercasalamanca (diciembre de 2023), "
             "apertura del Espacio de Innovación Tecnológica (25/04/2025), licitación de los proyectos del Distrito Tecnológico (12/05/2026) y las previsiones de Garrido y Ciudad del Talento."),
    rapida=[{"k": "Cobertura", "v": "Marzo de 2022 – 2030 (incluye previsiones, marcadas como tales)"}, {"k": "Última actualización de datos", "v": "27/11/2026"}],
    cifras=[],
    secciones=[],
    historia=[
        {"fecha": "09/03/2022", "hito": "Presentación del Centro Tormes+ (CEFE)", "detalle": "1.487.618 € de inversión, antigua Casa del Campo.", "fuente": HEX},
        {"fecha": "primavera 2023", "hito": "Arranque de la estrategia Salamanca Tech con seis verticales", "detalle": "Según El Español (dato no confirmado por fuente oficial).", "fuente": ESP1221},
        {"fecha": "22/09/2023", "hito": "Inicio de obras del Espacio de Innovación Tecnológica Tormes", "detalle": "Fecha visible de la nota municipal; adjudicación de 955.158,86 €.", "fuente": EITT_AYTO},
        {"fecha": "29/09/2023", "hito": "Inauguración del Centro de IoT e IA", "detalle": "Gestionado por AIR Institute.", "fuente": HEX},
        {"fecha": "12/2023", "hito": "Compra de la parcela de Mercasalamanca por el Ayuntamiento", "detalle": "Importe estimado de 11 M€ (prensa).", "fuente": ESP0212},
        {"fecha": "02/2024", "hito": "Convenio Ayuntamiento–AIR Institute", "detalle": "150.000 €; vigencia inicial hasta 31/12/2024.", "fuente": ESP0212},
        {"fecha": "21/12/2024", "hito": "Distrito Tecnológico aún en fase administrativa", "detalle": "Despegue no previsto antes de 2027.", "fuente": ESP1221},
        {"fecha": "25/04/2025", "hito": "Inauguración del Espacio de Innovación Tecnológica Tormes+", "detalle": "Siete cursos gratuitos entre el 13/05 y el 03/06/2025.", "fuente": RTV},
        {"fecha": "01/2026", "hito": "Adjudicación del Centro Ciudad del Talento", "detalle": "Licitación de 3.390.325,06 €.", "fuente": HEX},
        {"fecha": "03/2026", "hito": "Cumbre Salamanca Tech", "detalle": "Cerca de 100 empresas y entidades; inauguran el alcalde y el rector.", "fuente": ESP0324},
        {"fecha": "07/04/2026", "hito": "Presentación del Centro de Innovación Juvenil de Garrido", "detalle": "2,3 M€; 60 % FEDER.", "fuente": ESP0407},
        {"fecha": "15/04/2026", "hito": "Salamanca Tech Summit 2026", "detalle": "Mañueco reitera el compromiso con el distrito; el rector anuncia nuevas bioincubadoras.", "fuente": ESP0415},
        {"fecha": "27/04/2026", "hito": "Segundo convenio con la Fundación INCYDE", "detalle": "Bolsa de becas de 500.000 €.", "fuente": INCYDE},
        {"fecha": "12/05/2026", "hito": "Licitación de proyectos del Distrito Tecnológico", "detalle": "781.419 € (Somacyl, Junta).", "fuente": DEBATE},
        {"fecha": "05/06/2026", "hito": "Licitación de las obras de Garrido", "detalle": "Casi 2,3 M€; un año de ejecución.", "fuente": ESP0605},
        {"fecha": "26/08/2026", "hito": "Reportaje «Hexágono Tecnológico de Salamanca»", "detalle": "Seis centros entre 2022 y 2030.", "fuente": HEX},
        {"fecha": "28/08/2026", "hito": "Tormes+ se incorpora a STEAMbrace (Horizon Europe)", "detalle": "Campamentos Salamanca Tech.", "fuente": STEAM},
        {"fecha": "17/09/2026", "hito": "Convocatoria abierta y permanente de Abioinnova", "detalle": "Proyectos biosanitarios.", "fuente": ABIO_CONV},
        {"fecha": "Navidad 2026 (previsto)", "hito": "Primer campamento STEAMbrace", "detalle": "Grupo de 10 a 12 años.", "fuente": STEAM},
        {"fecha": "Último trimestre de 2026 (previsto)", "hito": "Inicio de obras de Garrido", "detalle": "Previsión municipal.", "fuente": ESP0407},
        {"fecha": "2027 (no confirmado)", "hito": "Primeros edificios del Distrito Tecnológico (previsión de 2024)", "detalle": "Calendario que no se había cumplido en mayo de 2026.", "fuente": ESP1221},
        {"fecha": "2030 (previsto)", "hito": "Funcionamiento de Ciudad del Talento", "detalle": "Plazo de obra de tres años y medio.", "fuente": HEX},
    ],
    no_verificado=[
        "Fechas aproximadas (mes o estación) proceden de la fecha de publicación del medio.",
        "Las previsiones futuras no son compromisos oficiales fechados.",
        "No se ha localizado la fecha del protocolo Junta–Ayuntamiento–USAL del distrito.",
    ],
    faq=[
        {"q": "¿Cuándo se inauguró el Centro Tormes+?", "a": "Se presentó el 9 de marzo de 2022; el Espacio de Innovación Tecnológica Tormes+ (anexo) se inauguró el 25 de abril de 2025."},
        {"q": "¿Cuándo estará listo el distrito tecnológico?", "a": "No hay fecha oficial. En mayo de 2026 solo estaba licitada la redacción de proyectos y la parcela seguía en trámite urbanístico."},
    ],
    fuentes=[HEX, ESP1221, ESP0212, ESP0407, ESP0605, ESP0415, ESP0324, DEBATE, EITT_AYTO, RTV, INCYDE, STEAM, ABIO_CONV],
)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    titulos = {}
    for slug in REL_ORDER:
        d = F[slug]
        d.setdefault("historia", [])
        d["slug"] = slug
        d["url_canonica"] = f"{BASE}/salamanca-tech" if slug == "estrategia-salamanca-tech" else f"{BASE}/salamanca-tech/{slug}"
        d["actualizado"] = FECHA
        d["actualizado_texto"] = FECHA_TXT
        d["estado_ficha"] = "datos con fuente verificados a 27/11/2026; lo no contrastado figura en «Qué no está verificado»"
        d["licencia"] = "CC BY 4.0"
        d["aviso"] = AVISO_GLOBAL
        d["como_citar"] = AVISO_CITA.format(f=FECHA_TXT, t=d["titulo"], u=d["url_canonica"])
        titulos[slug] = d["titulo"]
    for slug in REL_ORDER:
        d = F[slug]
        d["relacionadas"] = [{"t": F[s]["nombre_habitual"], "u": ("/salamanca-tech" if s == "estrategia-salamanca-tech" else f"/salamanca-tech/{s}")} for s in REL_ORDER if s != slug]
        write(os.path.join(ROOT, "_data", "salamancatech", slug + ".json"), json.dumps(d, ensure_ascii=False, indent=2) + "\n")
        hub = slug == "estrategia-salamanca-tech"
        perma = "salamanca-tech" if hub else f"salamanca-tech/{slug}"
        stub_path = os.path.join(ROOT, "salamanca-tech.html" if hub else os.path.join("salamanca-tech", slug + ".html"))
        fecha_ini = ""
        tit = d["titulo"].replace('"', "'")
        desc = d["descripcion"].replace('"', "'")
        stub = (f"---\nlayout: salamancatech\nslug: {slug}\ntitle: \"{tit}\"\ndescription: \"{desc}\"\n"
                f"date: 27-11-2026\nmodified: 27-11-2026\n"
                + ("parent_url: /\nparent_title: Open Salamanca\n" if hub else "parent_url: /salamanca-tech\nparent_title: Salamanca Tech\n") +
                f"permalink: {perma}\n"
                f"dataset_name: \"{tit}\"\ndataset_temporal: \"2022/2030\"\n"
                f"dataset_source: \"Ayuntamiento de Salamanca, Junta de Castilla y León y prensa local\"\n"
                f"dataset_source_url: \"https://salamancatech.es/que-es-salamanca-tech/\"\n"
                f"dataset_files:\n  - salamanca-tech/{slug}.json\n---\n")
        write(stub_path, stub)
        write(os.path.join(ROOT, "salamanca-tech", slug + "-json.json"),
              f"---\npermalink: salamanca-tech/{slug}.json\nsitemap: false\n---\n{{{{ site.data.salamancatech[\"{slug}\"] | jsonify }}}}\n")
    print("OK", len(REL_ORDER), "fichas")


if __name__ == "__main__":
    sys.exit(main())
