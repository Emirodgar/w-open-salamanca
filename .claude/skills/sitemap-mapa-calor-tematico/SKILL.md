---
name: sitemap-mapa-calor-tematico
description: >
  Genera y actualiza el contenido de "actualidad" de opensalamanca.es
  analizando el sitemap de La Gaceta de Salamanca (lagacetadesalamanca.es):
  produce el `actualidad.json` semanal que alimenta la página /actualidad y
  el banner de la home, los `actualidad/YYYYMM.json` mensuales que
  alimentan la línea de tiempo en /timeline, y `eventos.json` con los
  próximos eventos con fecha (ferias, fiestas, festivales...) detectados
  esa semana. Úsala SIEMPRE que el usuario pida "actualizar la
  actualidad", "generar el JSON de esta semana/mes", "analizar el sitemap
  de La Gaceta", "qué ha pasado en Salamanca esta semana/mes", "rellenar
  el timeline", "qué eventos hay próximamente en Salamanca", o cualquier
  variación sobre producir o refrescar el resumen de noticias locales o
  el calendario de eventos de este proyecto — aunque no mencionen el
  nombre de la skill ni el fichero JSON explícitamente.
---

# Actualidad, timeline y eventos de Salamanca (opensalamanca.es)

Esta skill es la versión de proyecto, adaptada a este repositorio, de un
analizador genérico de sitemaps de medios digitales. Sirve **tres piezas
del sitio** a la vez:

1. **`actualidad.json`** (raíz del repo) — resumen semanal/quincenal que
   consumen [`actualidad.html`](../../../actualidad.html) y el banner de
   [`index.html`](../../../index.html).
2. **`actualidad/YYYYMM.json`** (uno por mes, p.ej. `actualidad/202608.json`)
   — hitos destacados del mes que consume [`timeline.html`](../../../timeline.html)
   a través del manifiesto autogenerado [`actualidad/index.json`](../../../actualidad/index.json).
3. **`eventos.json`** (raíz del repo) — próximos eventos con fecha
   (ferias, fiestas, festivales, citas deportivas con fecha fija...) que
   aún no han ocurrido. A diferencia de los dos anteriores, no resume lo
   que ya ha pasado sino que mantiene un calendario vivo de lo que está
   por venir.

No hace falta tocar ningún otro fichero del sitio para que el contenido
nuevo aparezca: Jekyll detecta los `.json` nuevos en `actualidad/` solo
(ver `actualidad/index.json`), y las páginas hacen `fetch` con un
parámetro anti-caché (`?v=timestamp`, `cache: 'no-store'`) para no depender
de la caché del navegador.

## Valores por defecto de este proyecto

- **Medio a analizar:** La Gaceta de Salamanca — `--url-base
  "https://www.lagacetadesalamanca.es"`.
- **Secciones a excluir siempre:** `nacional,opinion,tu-gaceta` (agenda
  nacional y columnas de opinión personal no son "actualidad de la
  ciudad"). Si el usuario pide cubrir otro medio o cambiar las
  exclusiones, pregúntalo explícitamente — no lo asumas en silencio.
- **Categorías editoriales del timeline** (usadas también como colores en
  `assets/css/main.css`: `--cat-sucesos`, `--cat-politica`, etc.) — son
  EXACTAMENTE estas 8, no una taxonomía libre:
  `Sucesos`, `Política`, `Economía`, `Cultura`, `Deportes`, `Sociedad`,
  `Educación`, `Urbanismo`. Si un hito no encaja bien en ninguna,
  elige la más cercana antes que inventar una categoría nueva (una
  categoría nueva no tendría color definido en el CSS y el filtro de
  `/timeline` no la mostraría en la lista de botones).

## Paso 1 — Generar el análisis mecánico

Usa el script `scripts/analizar_sitemap.py` (solo librería estándar de
Python):

```bash
python3 .claude/skills/sitemap-mapa-calor-tematico/scripts/analizar_sitemap.py \
  entrada.xml salida.json \
  --url-base "https://www.lagacetadesalamanca.es" \
  --excluir-secciones "nacional,opinion,tu-gaceta"
```

### Obtener el sitemap

- Si el dominio es accesible por red desde `bash` en este entorno, pásale
  la URL del sitemap directamente como `entrada`.
- Si el acceso a internet vía `bash` está restringido, usa la herramienta
  de fetch web para traer el XML, guárdalo en un fichero local, y pasa ese
  fichero como `entrada`.
- El sitemap de un periódico suele ser "rolling" (solo las últimas N URLs).
  El script tolera truncamientos y siempre refleja el periodo real cubierto
  en `periodo_cubierto` / `nota_cobertura` — **no asumas cobertura completa
  sin comprobar ese campo**, e informa al usuario del rango real analizado.

Ver `references/schema_json.md` para el detalle completo de los campos que
produce el script (todos con `resumen` y `ejemplos_redactados` a `null` —
ese es precisamente el trabajo del paso 2, que hace Claude, no el script).

## Paso 2 — Redactar el resumen semanal (obligatorio, lo haces tú)

El script nunca escribe el resumen final ni ejemplos listos para publicar,
solo detecta patrones léxicos. Antes de escribir/actualizar `actualidad.json`:

1. Lee `conceptos_destacados` completo (sube `--top-conceptos` a 12-15 para
   tener margen) junto con su `evidencia`.
2. **Cura la lista**: descarta ruido léxico (una palabra genérica emparejada
   por casualidad — "gente", "turismo", "personas"); si detectas en la
   evidencia una historia real que el algoritmo no agrupó por pocas piezas,
   añádela igualmente si es noticiable.
3. Para cada concepto que conserves, sustituye `evidencia` por
   `ejemplos_redactados`: 1-2 frases en español correcto, con preposiciones
   y verbos conjugados, sin inventar ningún dato que no esté ya implícito en
   la evidencia. Si la evidencia es ambigua, sé más genérico antes que
   inventar un detalle.
4. Escribe `resumen` como un resumen periodístico real de 2-3 párrafos,
   agrupado por bloques temáticos con transiciones naturales — no una
   descripción del análisis (`resumen_borrador` es solo material de apoyo,
   nunca el resultado final).
5. Sobrescribe `actualidad.json` en la raíz del repo con el resultado final
   (con `resumen` y `ejemplos_redactados` ya rellenos, nunca `null`).

## Paso 3 — Generar/actualizar el JSON mensual del timeline

Además del `actualidad.json` semanal, produce (o actualiza) el fichero
mensual correspondiente en `actualidad/YYYYMM.json` (p.ej. `202608.json`
para agosto de 2026):

```json
{
  "mes": "2026-08",
  "titulo_mes": "Agosto 2026",
  "resumen_mes": "1-2 frases con el resumen del mes",
  "hitos": [
    {
      "fecha": "2026-08-15",
      "titulo": "Título breve del hito (menos de 90 caracteres)",
      "categoria": "Sucesos | Política | Economía | Cultura | Deportes | Sociedad | Educación | Urbanismo",
      "descripcion": "1-2 frases explicando qué pasó y por qué es relevante",
      "fuente": "URL real de la noticia, o \"sin fuente directa\" si no se conoce",
      "destacado": true
    }
  ]
}
```

Pasos:

1. **Parte de `conceptos_destacados` ya curado** (con sus
   `ejemplos_redactados` del paso 2) — cada concepto noticiable se
   convierte en un `hito`.
2. **Reclasifica `seccion_principal` en una de las 8 categorías
   editoriales** de arriba, no uses el nombre crudo de la sección del
   sitemap (`deportes`, `sucesos`, `campo`...) directamente salvo que ya
   coincida.
3. **Elige una fecha concreta por hito** (`fecha`, formato `YYYY-MM-DD`):
   un concepto trae `desde`/`hasta` porque puede cubrir varios días; para
   el timeline necesitas un único día representativo (normalmente el de la
   pieza más relevante, o `hasta` si no hay una pieza claramente
   principal). No inventes una fecha fuera del rango real cubierto.
4. **Marca un único hito con `"destacado": true`** por mes: el de mayor
   repercusión (alcance estructural, número de piezas, interés general). El
   resto va con `"destacado": false`.
5. **Limita a 5-8 hitos por mes**, priorizando diversidad de categorías
   sobre volumen.
6. **`fuente`**: usa la URL real de la noticia si la evidencia/el sitemap
   la traen; si no hay una URL fiable para ese concepto, escribe
   `"sin fuente directa"` en vez de inventar un enlace (así lo interpreta
   `timeline.html`: oculta el enlace "Ver noticia original" cuando ve ese
   valor exacto).
7. **No sobrescribas meses ya cerrados con datos incompletos**: como esta
   skill se ejecuta normalmente cada semana y el sitemap solo cubre los
   últimos días, un mes se completa a lo largo de varias ejecuciones. Antes
   de escribir `actualidad/YYYYMM.json`, comprueba si ya existe uno para
   ese mes:
   - Si existe, **fusiona**: añade los hitos nuevos, no dupliques un
     mismo suceso si ya estaba (compara por título/fecha aproximada, no
     por igualdad exacta de texto), y actualiza `resumen_mes` para que
     siga reflejando el mes completo con lo nuevo incorporado.
   - Si el mes ya tiene 8 hitos y aparece uno nuevo más relevante, puedes
     sustituir el más débil, pero nunca borres el `destacado` actual salvo
     que el nuevo hito sea claramente más importante para el mes completo.
8. No hace falta ningún paso de build ni redeploy manual: Jekyll/GitHub
   Pages reconstruye el sitio al hacer commit — basta con dejar los
   ficheros `.json` en su sitio dentro del repo.

## Paso 4 — Generar/actualizar eventos.json (próximos eventos con fecha)

Además de resumir lo ya ocurrido, identifica los `conceptos_destacados`
que hablen de un **evento futuro con fecha propia** (ferias, fiestas,
festivales, exposiciones, citas deportivas con fecha fija...) y mantenlos
en `eventos.json` (raíz del repo), un calendario vivo de lo que está por
venir en Salamanca.

**Importante — esto NO se puede hacer solo con el análisis mecánico.** El
script trabaja a partir del slug de la URL y la fecha de *publicación* de
la noticia, no la fecha de *celebración* del evento — esa fecha vive en el
cuerpo del artículo. Confirmado en la práctica: para tres candidatos reales
("guía práctica de fechas y horarios de Salamaq", "Feria del Caballo de
Ciudad Rodrigo", "Cabrerizos abre inscripción para su feria") hizo falta
abrir el artículo real y leer su `<meta name="description">` /
`articleBody` para encontrar "del 3 al 7 de septiembre", "del 17 al 19 de
septiembre" y "3 de octubre de 2026" respectivamente — ninguna de esas
fechas estaba en la URL ni en la evidencia léxica del script.

Pasos:

1. **Identifica candidatos** entre los `conceptos_destacados` ya curados
   (paso 2): ¿suena a algo con fecha de celebración propia, no solo fecha
   de publicación? Las palabras clave habituales son "feria", "fiesta",
   "festival", "concurso", "exposición", "jornadas", "certamen", o un
   evento deportivo con fecha ya fijada. La mayoría de conceptos de una
   semana normal (sucesos, política, resultados deportivos ya jugados,
   clima) **no** son candidatos — es normal que algunas semanas no den
   ningún evento nuevo.
2. **Abre el artículo real de cada candidato** (la URL está en
   `evidencia`/`fuente` del concepto) y busca una fecha explícita — la
   meta-descripción (`<meta name="description">` u `og:description`) y el
   `articleBody` del JSON-LD suelen traerla en texto plano ("del X al Y de
   [mes]", "el X de [mes]"). Usa `curl`/`WebFetch` para traer el HTML si
   no lo tienes ya.
3. **Si no hay fecha explícita y verificable en el artículo, NO crees el
   evento.** No infieras ni aproximes una fecha a partir de "esta semana",
   "el próximo fin de semana" ni nada parecido — es preferible que
   `eventos.json` se quede corto a que publique una fecha inventada.
4. Para cada evento confirmado, añade una entrada con este esquema:

```json
{
  "generado_en": "2026-09-01T14:30:00+00:00",
  "eventos": [
    {
      "titulo": "SALAMAQ 2026 - 37ª Exposición Internacional de Ganado Puro",
      "categoria": "Cultura",
      "fecha_inicio": "2026-09-03",
      "fecha_fin": "2026-09-07",
      "lugar": "Recinto Ferial de Salamanca",
      "descripcion": "1-2 frases explicando de qué trata el evento",
      "fuente": "URL real del artículo de donde se sacó la fecha"
    }
  ]
}
```

   - `categoria`: misma taxonomía de 8 categorías del timeline (paso 3).
   - `fecha_fin`: `null` si el artículo solo da un día concreto (evento de
     un solo día) en vez de un rango.
   - `lugar`: solo si el artículo lo menciona explícitamente; si no, omite
     el campo antes que inventar una ubicación.
5. **`eventos.json` se acumula, no se sobrescribe.** Antes de escribir,
   lee el fichero existente y:
   - Añade los eventos nuevos que no estuvieran ya (compara por `titulo`
     aproximado, no exacto).
   - **Elimina los eventos cuyo `fecha_fin` (o `fecha_inicio` si no hay
     `fecha_fin`) ya haya pasado** respecto a la fecha de ejecución — es
     un calendario de lo que queda por venir, no un archivo histórico (eso
     ya lo cubre `actualidad/YYYYMM.json`).
   - Si un evento ya existente aparece de nuevo con más detalle (p.ej. se
     confirma el `lugar` que antes no se conocía), actualiza esa entrada
     en vez de duplicarla.
6. Actualiza `generado_en` a la fecha de la ejecución actual.

## Foco local: qué excluir siempre

Además de `nacional`/`opinion`/`tu-gaceta` (excluidas por defecto), vigila
que no se cuelen como "concepto" secciones de contenido no noticioso
(cartas del lector, obituarios, concursos comerciales) si aparecen en el
sitemap — no aportan a un resumen de actualidad de la ciudad.

`construir_conceptos_destacados()` prioriza frases (palabras contiguas en
el slug) y solo baja a co-ocurrencia suelta o palabra individual cuando no
hay una frase clara. Excluye automáticamente titulares casi idénticos
repetidos varios días seguidos (viñetas, boletines fijos) para que no
contaminen los conceptos, aunque sí siguen contando en `por_seccion`/heatmap.
Sigue siendo un agrupamiento léxico, no semántico: si el usuario señala
ruido evidente, añade el término a `STOPWORDS_ES` en el script o sube
`min_frecuencia`/`min_coocurrencia`.

## Limitaciones a comunicar siempre al usuario

- El análisis se basa solo en la URL/slug del sitemap, no en el contenido
  real de la noticia — es una aproximación rápida, no un análisis
  semántico profundo del texto.
- Depende de que la Gaceta mantenga su patrón de URLs actual
  (`/seccion/(subseccion/)*titulo-FECHA-tipo.html`). Si cambian de CMS o de
  estructura de URLs, revisa `analizar_url()` en el script antes de confiar
  en los resultados.
- El periodo cubierto depende de lo que el sitemap contenga en el momento
  de la consulta (puede ser rolling/incremental), no de lo que se pida —
  informa siempre del `periodo_cubierto` real, tanto en el resumen semanal
  como al decidir qué hitos mensuales quedan cubiertos.
- `eventos.json` (paso 4) depende de que el artículo candidato mencione una
  fecha explícita — muchas semanas no darán ningún evento nuevo, y eso es
  el comportamiento correcto, no un fallo. Ningún artículo del sitio
  consume todavía `eventos.json`; si el usuario quiere una página pública
  de "próximos eventos", pregúntaselo aparte, esta skill solo genera el
  fichero de datos.
