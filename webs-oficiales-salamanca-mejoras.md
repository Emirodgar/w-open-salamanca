# Webs oficiales de Salamanca: carencias y oportunidades para Open Salamanca

Base: `webs-oficiales-salamanca.csv` (46 webs, verificadas con HTTP el 2026-11-24).
Lo que sigue combina lo observado en las webs con inferencias mías. Las marco como **(observado)** o **(hipótesis a validar)**.

## Hallazgos sobre el ecosistema

1. **El ayuntamiento reparte sus servicios en al menos cuatro dominios** (observado): `aytosalamanca.es` (institucional), `aytosalamanca.gob.es` (sede electrónica), `salamanca.es` (turismo) y `opendata.aytosalamanca.es` (datos). Más una decena de microsites (`consigna`, `formacion`, `salamancatech`, `salamancafilmcommission`, etc.). No hay un único punto de entrada para "qué necesito hacer".
2. **Datos abiertos pobre y frágil** (observado): el catálogo muestra muy pocos conjuntos (bibliotecas, portafirmas, cortes de tráfico, estudio de plantilla 2018, percepción 2023). Durante la comprobación, la raíz del portal y la página de ayuda devolvieron error 502.
3. **Información en PDF** (observado en transparencia, plenos, tributos): presupuestos, actas y contratación se publican como documentos, no como datos.
4. **Turismo con buena presentación, pero sin datos** (observado): fichas por evento y monumento, sin API ni iCal verificados.
5. **Sin web municipal localizada para bus urbano ni ORA** (observado: no aparecieron en el portal ni en el mapa web). El bus tiene apps de terceros (BMS, Bus Urbano Salamanca).

## Carencias y cómo cubrirlas desde Open Salamanca

| # | Qué no hacen bien | Evidencia | Propuesta para el portal | Esfuerzo | Impacto |
|---|---|---|---|---|---|
| 1 | No hay un buscador único de trámites ("quiero empadronarme") | Cuatro dominios; la sede está aparte | Guía "Qué hago si..." que enlaza al trámite exacto de la sede, con requisitos, plazos y tasas en lenguaje llano | Medio | Alto |
| 2 | Presupuestos y contratos en PDF | Transparencia y presupuestos | Visualizar la ejecución presupuestaria (ya hay base CONPREL), con comparativa interanual y "¿en qué se gasta cada euro?" | Medio | Alto |
| 3 | Plenos: actas largas sin resumen | Sección Plenos | Resumen por pleno: acuerdos, mociones, quién votó qué. Enlazar con las fichas de concejales | Alto | Alto |
| 4 | Edictos y anuncios sin alertas | Tablón de edictos en la sede | Alertas por barrio o tema (obras, licencias, cortes) y feed RSS | Medio | Medio |
| 5 | Subvenciones dispersas (BOP, BOCYL, BOE, infosubvenciones) | Cuatro boletines distintos | Calendario único de ayudas para Salamanca con plazo, cuantía y requisitos (encaja con la skill `investigacion-boe-ayudas`) | Medio | Alto |
| 6 | Agenda cultural sin exportación | `salamanca.es/agenda` solo HTML | Agenda unificada con filtros por barrio, precio, familia y botón "añadir al calendario" (iCal). Hay base con `eventos.json` | Bajo | Medio |
| 7 | Movilidad: sin web oficial de bus ni ORA localizada | Búsqueda en portal y mapa web | Ficha de líneas, paradas y zonas ORA con mapa (ya existen `paradas-bus.json` y `ora-servicios.json`), más avisos de cortes de tráfico del catálogo | Bajo | Alto |
| 8 | Datos sin histórico ni comparativa | Catálogo con pocas series | Series temporales propias por barrio: población, precio vivienda, empleo, comercio | Alto | Alto |
| 9 | Cortes de tráfico y obras solo en mapa | Conjunto "Cortes de Tráfico" | Vista por barrio y calle, con aviso "obras que te afectan esta semana" | Medio | Medio |
| 10 | Participación sin devolución de resultados (hipótesis a validar) | Sección "Participa" | Cuadro de seguimiento de propuestas ciudadanas: estado, responsable, fecha | Medio | Medio |
| 11 | Cada administración muestra su dato aparte | Ayuntamiento, Diputación, Junta, INE | Fichas por barrio que cruzan fuentes (INE, Sacyl, Educa, Catastro) | Alto | Alto |
| 12 | Disponibilidad intermitente de fuentes | 502 en opendata | Espejo en caché de los conjuntos reutilizados, con fecha de última sincronización visible | Bajo | Medio |
| 13 | Sin versión legible para todos de normativa y ordenanzas | Documentos PDF | Resúmenes de ordenanzas (terrazas, fiscales, ORA) y "qué cambia" con cada modificación | Medio | Medio |
| 14 | Datos de empleo público solo en bases PDF | Oferta de empleo | Calendario de oposiciones municipales, provinciales y autonómicas en Salamanca | Bajo | Medio |

## Prioridad sugerida (primeros 90 días)

1. **Movilidad (7)** y **agenda (6)**: ya hay datos en el repositorio y el coste es bajo.
2. **Presupuestos (2)**: diferencial claro frente al portal oficial.
3. **Calendario de ayudas (5)**: alto valor para autónomos y asociaciones.
4. **Guía de trámites (1)**: mayor tráfico potencial (búsquedas de utilidad).

## Pendiente de verificar

- Microsites revisados el 2026-11-24: salvo `espanolensalamanca.com` (carga dinámica, pendiente de revisión manual), ya se ha leído su contenido. Ninguno ofrece datos descargables ni API.
- Webs del bus urbano, ORA, Policía Local y Bomberos: no se localizaron como páginas oficiales. Para ORA solo apareció un dataset de aparcamientos en el catálogo de datos abiertos; las tarifas que circulan vienen de guías de terceros y no están verificadas. Un directorio de trámites de terceros (papelea.com) también aparece en los resultados y no es fuente oficial.
- Oportunidad añadida: la agenda de `salamancadenoche.com` y el calendario del Palacio de Congresos son dos fuentes más de eventos para unificar (propuesta 6).
- Licencia y frecuencia de actualización de cada conjunto del catálogo de datos abiertos.
- Si la Diputación mantiene un portal propio de datos abiertos activo.
