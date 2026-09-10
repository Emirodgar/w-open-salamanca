---
name: sitemap-mapa-calor-tematico
description: >
  Genera y actualiza el contenido de "actualidad" de opensalamanca.es
  analizando el sitemap de La Gaceta de Salamanca (lagacetadesalamanca.es):
  produce el `actualidad.json` semanal que alimenta la página /actualidad,
  el banner de la home y la fecha de "Última actualización" de la home,
  los `actualidad/YYYYMM.json` mensuales que alimentan la línea de tiempo
  en /timeline, `eventos.json` con los próximos eventos con fecha (ferias,
  fiestas, festivales...) detectados esa semana, y las preguntas de la
  sección "Opina" (`opina.json`, que alimenta tanto la home como /opina) y
  su histórico (`historico.json`). Al terminar, hace commit y push
  automáticamente. Úsala SIEMPRE que el usuario pida "actualizar la
  actualidad", "generar el JSON de esta semana/mes", "analizar el sitemap
  de La Gaceta", "qué ha pasado en Salamanca esta semana/mes", "rellenar
  el timeline", "qué eventos hay próximamente en Salamanca", "actualizar
  las preguntas de Opina", o cualquier variación sobre producir o
  refrescar el resumen de noticias locales, el calendario de eventos o
  las preguntas de opinión de este proyecto — aunque no mencionen el
  nombre de la skill ni el fichero JSON explícitamente.
---

# Actualidad, timeline, eventos y Opina de Salamanca (opensalamanca.es)

Esta skill es la versión de proyecto, adaptada a este repositorio, de un
analizador genérico de sitemaps de medios digitales. Sirve **cinco piezas
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
4. **La fecha de "Última actualización" de la home** (tarjeta junto a
   "Datasets"/"Categorías") — **no requiere ninguna acción tuya**: desde
   [`assets/js/main.js`](../../../assets/js/main.js) (`loadData()` /
   `updateStats()`), esa fecha ya toma automáticamente el más reciente
   entre las fechas de los datasets y `periodo_cubierto.hasta` de
   `actualidad.json`. Basta con que el paso 1 dé un `periodo_cubierto`
   correcto (como ya hace) para que esta tarjeta avance sola en cada
   ejecución de la skill. Solo tendrías que tocar código si algún día
   cambia el nombre de ese campo o el mecanismo de `#lastUpdate`.
5. **`opina.json`** (raíz del repo) y **`historico.json`** — las preguntas
   de la sección "Opina" (mismo fichero alimenta tanto el destacado de la
   home como la lista completa en `/opina`, así que no hace falta tocar
   nada aparte para que aparezcan en ambos sitios) y el archivo de
   preguntas retiradas. Ver el paso 5 más abajo.

No hace falta tocar ningún otro fichero del sitio para que el contenido
nuevo aparezca: Jekyll detecta los `.json` nuevos en `actualidad/` solo
(ver `actualidad/index.json`), y las páginas hacen `fetch` con un
parámetro anti-caché (`?v=timestamp`, `cache: 'no-store'`) para no depender
de la caché del navegador.

## Valores por defecto de este proyecto

- **Medio a analizar:** La Gaceta de Salamanca — `--url-base
  "https://www.lagacetadesalamanca.es"`.
- **Secciones a excluir siempre:** `nacional,opinion,tu-gaceta,gente-estilo,podcast`
  (agenda nacional y columnas de opinión personal no son "actualidad de
  la ciudad"; `gente-estilo` y `podcast` se excluyeron a petición expresa
  del usuario — no aportan al resumen de actualidad). Si el usuario pide
  cubrir otro medio o cambiar las exclusiones, pregúntalo explícitamente —
  no lo asumas en silencio.
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
  --excluir-secciones "nacional,opinion,tu-gaceta,gente-estilo,podcast"
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
3. **Revisa también, siempre, la programación oficial de la Fundación
   Salamanca Ciudad de Cultura y Saberes**
   (`https://ciudaddecultura.org/es/programacion/`) — es una segunda
   fuente independiente del sitemap de La Gaceta, con su propio listado de
   conciertos, teatro y actividades con fecha ya confirmada. Es una página
   que carga su contenido por JavaScript, así que ábrela con el navegador
   (no sirve un `curl` plano) y lee el texto ya renderizado. En vez de
   crear un evento por cada actuación individual (la programación puede
   traer decenas), agrupa el conjunto en un único evento con el nombre del
   ciclo/temporada (p.ej. "Ferias de Salamanca 2026") usando como
   `fecha_inicio`/`fecha_fin` el primer y último día que veas realmente
   programados, y menciona en la `descripcion` 2-4 cabezas de cartel a
   modo de ejemplo. Si en esa programación hay un espectáculo suelto muy
   posterior y desconectado del grueso del programa (p.ej. una única
   fecha semanas después), puedes añadirlo como evento independiente en
   vez de forzarlo dentro del rango del ciclo principal.
4. **Si no hay fecha explícita y verificable en la fuente, NO crees el
   evento.** No infieras ni aproximes una fecha a partir de "esta semana",
   "el próximo fin de semana" ni nada parecido — es preferible que
   `eventos.json` se quede corto a que publique una fecha inventada.
5. Para cada evento confirmado, añade una entrada con este esquema:

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
   - `fuente`: guárdala siempre (sirve para verificar la fecha y para
     detectar duplicados en fusiones futuras), pero **la tabla de eventos
     de la web NO la muestra como enlace** — el título aparece en texto
     plano, sin enlazar a la página externa. No es necesario ni se debe
     intentar "arreglar" esto añadiendo el enlace de vuelta.
6. **`eventos.json` se acumula, no se sobrescribe.** Antes de escribir,
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
7. Actualiza `generado_en` a la fecha de la ejecución actual.

## Paso 5 — Actualizar las preguntas de Opina (home y /opina)

`opina.json` (raíz del repo) contiene el array `preguntas` que se muestra
**tanto en el destacado de la home** (la pregunta con `"destacada": true`,
o la primera si ninguna la tiene) **como en la lista completa de
`/opina`** — es el mismo fichero para las dos superficies, así que un solo
paso de escritura ya cubre "home y /opina" sin nada adicional.

```json
{
  "worker_url": "https://votos.emirodgar.workers.dev/",
  "preguntas": [
    {
      "id": "slug-corto-del-tema",
      "pregunta": "¿Pregunta cerrada, en segunda persona?",
      "opciones": ["Opción A", "Opción B", "Opción C (3-5 opciones en total)"],
      "basado_en": "actualidad.json | eventos.json",
      "fecha_creacion": "2026-09-10",
      "destacada": true
    }
  ]
}
```

### 5.1 — Añadir preguntas nuevas

1. Revisa `conceptos_destacados` (paso 2) y `eventos.json` (paso 4) ya
   curados en esta misma ejecución en busca de algo sobre lo que tenga
   sentido preguntar: un evento próximo con varias opciones reales entre
   las que elegir, una decisión o resultado local con dos posturas
   claras, etc.
2. **Aplica siempre esta barra de calidad, sin excepciones**: solo
   propón una pregunta si la distribución de respuestas puede aportar
   una conclusión con algo de interés real sobre la ciudad. Descarta
   cualquier pregunta de "charla trivial" (tiempo, humor genérico,
   cosas obvias) — es preferible añadir **cero preguntas nuevas** esa
   semana a rellenar el hueco con una pregunta floja. Ante la duda, no
   la añadas y dilo explícitamente en el resumen que le das al usuario.
3. Si añades una, dale un `id` corto en kebab-case (p.ej.
   `ferias-salamanca-2026`), 3-5 `opciones` con redacción neutral (evita
   opciones que induzcan la respuesta), y usa `basado_en` para indicar de
   qué fichero sale ("actualidad.json" o "eventos.json").
4. **Solo una pregunta puede tener `"destacada": true`** a la vez (es la
   que se muestra en la home): si añades una nueva que deba ser la
   protagonista, quita la marca de la que la tenía antes.

### 5.2 — Retirar preguntas que ya no son de actualidad

Una pregunta debe archivarse cuando el evento al que se refería ya ha
pasado o el tema ha quedado resuelto/obsoleto. Sigue este orden exacto
(igual que documenta `cloudflare-worker/opina-votos/README.md`, sección
"Archivar una pregunta"):

1. **Consulta el resultado final** con una petición GET pública (no hace
   falta autenticación ni `wrangler` para esto):
   ```bash
   curl -s "<worker_url sin barra final>/votos/<id-de-la-pregunta>"
   ```
   Devuelve el recuento por opción, p.ej. `{"Opción A": 12, "Opción B": 8}`.
2. **Añade una entrada** a `preguntas_archivadas` en `historico.json` con
   ese recuento, `fecha_archivado` (fecha de esta ejecución) y
   `total_votos` (suma de todas las opciones).
3. **Quita la pregunta** del array `preguntas` de `opina.json`. Si tenía
   `"destacada": true`, pon esa marca en otra pregunta que siga activa
   (o en ninguna si no queda ninguna con sentido de destacar).
4. **Cierre en el Worker (mejor esfuerzo, no bloqueante)**: el paso
   definitivo es `wrangler kv key put "closed:<id>" "1"
   --namespace-id=<id>`, pero requiere la CLI de `wrangler` autenticada
   contra la cuenta de Cloudflare del usuario, que normalmente **no**
   está disponible en este entorno de ejecución. Si `wrangler` no está
   instalado o no hay sesión iniciada, no falles el paso completo por
   esto: la pregunta ya ha desaparecido de `/opina` y de la home en
   cuanto se publica el `opina.json` sin ella (nadie puede votarla desde
   la web), así que el riesgo real es solo alguien llamando a la API
   directamente. Informa al usuario de que ese cierre en KV queda
   pendiente como paso manual (los comandos exactos están en el README
   del Worker) en vez de darlo por hecho.
5. No archives una pregunta solo porque lleve varias semanas activa si
   el tema sigue vigente — el criterio es relevancia, no antigüedad.

## Paso 6 — Commit y push automáticos al terminar

A diferencia de una edición manual cualquiera en este repo, **esta skill
sí debe terminar haciendo commit y push por su cuenta, sin pedir
confirmación en el chat** — es una instrucción permanente del usuario
para las ejecuciones de esta skill en concreto (no una autorización
general para otros cambios en el repo).

1. Antes de tocar nada, comprueba con `git status` que no hay cambios a
   medias de otra tarea sin relación en este repo; si los hay, no los
   mezcles en este commit (usa `git add` con las rutas concretas, nunca
   `git add -A`/`git add .`).
2. Haz `git add` solo de los ficheros que esta skill haya escrito en esta
   ejecución, típicamente algún subconjunto de: `actualidad.json`,
   `actualidad/YYYYMM.json`, `eventos.json`, `opina.json`,
   `historico.json`.
3. Crea un commit con un mensaje breve que resuma el periodo cubierto y
   qué se ha tocado, por ejemplo:
   `Actualiza actualidad, timeline y Opina (8-10 sep 2026)`.
4. Haz `git push` a la rama actual contra su remoto (`origin`, salvo que
   el repo esté configurado de otra forma). No uses `--force` ni
   `--no-verify`; si el push falla (p.ej. la rama remota avanzó), no lo
   resuelvas con un `push --force` — informa al usuario y pide cómo
   proceder.
5. Termina el resumen al usuario indicando explícitamente que ya se ha
   hecho commit y push (con el hash/rango si es fácil obtenerlo), para
   que quede claro que no hace falta un paso manual adicional.

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
- Las preguntas de Opina (paso 5) están sujetas a una barra de calidad
  deliberadamente restrictiva: muchas semanas no darán ninguna pregunta
  nueva, y eso es correcto, no un fallo — no rellenes el hueco con una
  pregunta trivial solo por tener algo que mostrar.
- Archivar una pregunta de Opina (paso 5.2) solo se completa del todo con
  `wrangler` autenticado contra Cloudflare, que normalmente no está
  disponible en este entorno — el cierre en KV (`closed:<id>`) puede
  quedar como paso manual pendiente para el usuario aunque la pregunta ya
  haya desaparecido de la web.
- El commit y push automáticos (paso 6) son una instrucción permanente
  del usuario específica de esta skill — no la generalices como permiso
  para hacer push automático de otros cambios en el repo fuera de este
  flujo.
