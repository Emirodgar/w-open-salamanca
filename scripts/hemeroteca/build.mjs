// Genera hemeroteca.json a partir de los sitemaps de la prensa local.
// No resume ni analiza contenido: solo recopila título, fecha, medio y enlace.
//
// Uso: node scripts/hemeroteca/build.mjs
// (se ejecuta desde la raíz del repo, vía .github/workflows/hemeroteca.yml)

import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const OUTPUT_PATH = path.join(REPO_ROOT, 'hemeroteca.json');

const DIAS_VENTANA = 20;
const CONCURRENCIA_TITULOS = 8;
const TIMEOUT_MS = 10000;
const USER_AGENT = 'OpenSalamancaBot/1.0 (+https://opensalamanca.es/hemeroteca)';

const FUENTES = [
	{
		id: 'tribuna',
		medio: 'Tribuna Salamanca',
		sitemap: 'https://www.tribunasalamanca.com/sitemap_last_news.xml',
		formato: 'news', // trae news:title y news:publication_date
	},
	{
		id: 's24h',
		medio: 'Salamanca24Horas',
		sitemap: 'https://www.salamanca24horas.com/sitemaps/news.xml',
		formato: 'news',
	},
	{
		id: 'gaceta',
		medio: 'La Gaceta de Salamanca',
		// El sitemap.incremental.xml del sitio mete de todo (varias semanas,
		// todas las secciones). Usamos su RSS de Portada en su lugar: son solo
		// las noticias que el propio medio destaca en portada, y ya trae título.
		sitemap: 'https://www.lagacetadesalamanca.es/rss/2.0/?section=',
		formato: 'rss',
	},
	{
		id: 'salamancahoy',
		medio: 'Salamancahoy',
		sitemap: 'https://www.salamancahoy.es/sitemap.incremental.xml',
		formato: 'plano',
		sufijosTitulo: [' - Salamancahoy', ' | Salamancahoy', ' - Salamanca24Horas'],
	},
];

function decodeEntities(str) {
	if (!str) return str;
	return str
		.replace(/&amp;/g, '&')
		.replace(/&lt;/g, '<')
		.replace(/&gt;/g, '>')
		.replace(/&quot;/g, '"')
		.replace(/&apos;/g, "'")
		.replace(/&#0*39;/g, "'")
		.replace(/&#x27;/gi, "'")
		.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
		.replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
		.replace(/\s+/g, ' ')
		.trim();
}

async function fetchConTimeout(url, opts = {}) {
	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
	try {
		return await fetch(url, {
			...opts,
			signal: controller.signal,
			headers: { 'User-Agent': USER_AGENT, ...(opts.headers || {}) },
		});
	} finally {
		clearTimeout(timer);
	}
}

function quitarCdata(str) {
	if (!str) return str;
	const m = str.match(/^<!\[CDATA\[([\s\S]*)\]\]>$/);
	return m ? m[1] : str;
}

function parseSitemap(xml, fuente) {
	if (fuente.formato === 'rss') {
		const bloques = xml.match(/<item>[\s\S]*?<\/item>/g) || [];
		const items = [];
		for (const bloque of bloques) {
			const loc = (bloque.match(/<link>([\s\S]*?)<\/link>/) || [])[1];
			const pubDate = (bloque.match(/<pubDate>([\s\S]*?)<\/pubDate>/) || [])[1];
			if (!loc || !pubDate) continue;
			const url = decodeEntities(quitarCdata(loc).trim());
			const tituloBruto = (bloque.match(/<title>([\s\S]*?)<\/title>/) || [])[1] || null;
			items.push({ url, fechaHora: pubDate.trim(), titulo: decodeEntities(quitarCdata(tituloBruto)) });
		}
		return items;
	}

	const bloques = xml.match(/<url>[\s\S]*?<\/url>/g) || [];
	const items = [];
	for (const bloque of bloques) {
		const loc = (bloque.match(/<loc>([^<]+)<\/loc>/) || [])[1];
		if (!loc) continue;
		const url = decodeEntities(loc);

		let fechaHora;
		let titulo = null;

		if (fuente.formato === 'news') {
			fechaHora = (bloque.match(/<news:publication_date>([^<]+)<\/news:publication_date>/) || [])[1];
			titulo = decodeEntities((bloque.match(/<news:title>([^<]*)<\/news:title>/) || [])[1] || null);
		} else {
			fechaHora = (bloque.match(/<lastmod>([^<]+)<\/lastmod>/) || [])[1];
		}
		if (!fechaHora) continue;

		items.push({ url, fechaHora, titulo });
	}
	return items;
}

function tituloDesdeSlug(url) {
	try {
		const { pathname } = new URL(url);
		const slug = pathname.split('/').filter(Boolean).pop() || '';
		const limpio = slug
			.replace(/-\d{10,}-[a-z]{2}\.html?$/i, '')
			.replace(/\.html?$/i, '')
			.replace(/-/g, ' ')
			.trim();
		if (!limpio) return url;
		return limpio.charAt(0).toUpperCase() + limpio.slice(1);
	} catch {
		return url;
	}
}

function extraerAtributo(tag, nombre) {
	// Ojo: el valor del atributo puede contener el otro tipo de comilla
	// (p. ej. content="...un 'apodo'...") así que hay que respetar solo
	// la comilla que realmente abre el atributo, no excluir ambas.
	const regex = new RegExp(`\\b${nombre}=(?:"([^"]*)"|'([^']*)')`, 'i');
	const match = tag.match(regex);
	if (!match) return null;
	return match[1] !== undefined ? match[1] : match[2];
}

function extraerMetaContent(html, propiedad) {
	const tags = html.match(/<meta\s[^>]*>/gi) || [];
	for (const tag of tags) {
		const prop = extraerAtributo(tag, 'property') || extraerAtributo(tag, 'name');
		if (!prop || prop.toLowerCase() !== propiedad) continue;
		const content = extraerAtributo(tag, 'content');
		if (content) return decodeEntities(content);
	}
	return null;
}

function quitarSufijo(titulo, sufijos) {
	for (const sufijo of sufijos || []) {
		if (titulo.toLowerCase().endsWith(sufijo.toLowerCase())) {
			return titulo.slice(0, titulo.length - sufijo.length).trim();
		}
	}
	return titulo;
}

async function obtenerTituloDePagina(url, fuente) {
	try {
		const res = await fetchConTimeout(url);
		if (!res.ok) return tituloDesdeSlug(url);
		const html = await res.text();
		const ogTitulo = extraerMetaContent(html, 'og:title');
		if (ogTitulo) return quitarSufijo(ogTitulo, fuente.sufijosTitulo);
		const match = html.match(/<title[^>]*>([^<]*)<\/title>/i);
		if (match && match[1]) return quitarSufijo(decodeEntities(match[1]), fuente.sufijosTitulo);
		return tituloDesdeSlug(url);
	} catch {
		return tituloDesdeSlug(url);
	}
}

async function conConcurrencia(items, limite, fn) {
	const resultados = new Array(items.length);
	let siguiente = 0;
	async function trabajador() {
		while (siguiente < items.length) {
			const i = siguiente++;
			resultados[i] = await fn(items[i], i);
		}
	}
	await Promise.all(new Array(Math.min(limite, items.length)).fill(0).map(trabajador));
	return resultados;
}

async function cargarExistentes() {
	try {
		const raw = await readFile(OUTPUT_PATH, 'utf8');
		const json = JSON.parse(raw);
		const mapa = new Map();
		for (const n of json.noticias || []) mapa.set(n.url, n);
		return mapa;
	} catch {
		return new Map();
	}
}

async function main() {
	const ahora = Date.now();
	const limiteVentana = ahora - DIAS_VENTANA * 24 * 60 * 60 * 1000;

	const existentes = await cargarExistentes();
	const vistos = new Set();
	const pendientesDeTitulo = [];
	const finales = [];

	for (const fuente of FUENTES) {
		let xml;
		try {
			const res = await fetchConTimeout(fuente.sitemap);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			xml = await res.text();
		} catch (err) {
			console.error(`No se pudo descargar el sitemap de ${fuente.medio}:`, err.message);
			continue;
		}

		const items = parseSitemap(xml, fuente);
		for (const item of items) {
			const t = Date.parse(item.fechaHora);
			if (Number.isNaN(t) || t < limiteVentana) continue;
			vistos.add(item.url);

			const previo = existentes.get(item.url);
			if (previo) {
				finales.push(previo);
				continue;
			}

			if (item.titulo) {
				finales.push({
					url: item.url,
					titulo: item.titulo,
					medio: fuente.medio,
					fecha: new Date(t).toISOString().slice(0, 10),
					fecha_hora: new Date(t).toISOString(),
				});
			} else {
				pendientesDeTitulo.push({ url: item.url, medio: fuente.medio, fecha: t, fuente });
			}
		}
	}

	console.log(`Noticias nuevas sin título (a resolver contra la página): ${pendientesDeTitulo.length}`);
	await conConcurrencia(pendientesDeTitulo, CONCURRENCIA_TITULOS, async (pendiente) => {
		const titulo = await obtenerTituloDePagina(pendiente.url, pendiente.fuente);
		finales.push({
			url: pendiente.url,
			titulo,
			medio: pendiente.medio,
			fecha: new Date(pendiente.fecha).toISOString().slice(0, 10),
			fecha_hora: new Date(pendiente.fecha).toISOString(),
		});
	});

	// Conserva del fichero anterior cualquier noticia que siga dentro de la ventana
	// aunque ahora mismo no aparezca en el sitemap (evita huecos si el medio la retira antes de que la releamos).
	for (const [url, noticia] of existentes) {
		if (vistos.has(url)) continue;
		const t = Date.parse(noticia.fecha_hora || noticia.fecha);
		if (!Number.isNaN(t) && t >= limiteVentana) finales.push(noticia);
	}

	const porUrl = new Map(finales.map((n) => [n.url, n]));
	const noticias = Array.from(porUrl.values()).sort((a, b) => b.fecha_hora.localeCompare(a.fecha_hora));

	const salida = {
		generado_en: new Date(ahora).toISOString(),
		dias_ventana: DIAS_VENTANA,
		total: noticias.length,
		medios: FUENTES.map((f) => f.medio),
		noticias,
	};

	await writeFile(OUTPUT_PATH, JSON.stringify(salida, null, 2) + '\n', 'utf8');
	console.log(`hemeroteca.json actualizado: ${noticias.length} noticias.`);
}

main().catch((err) => {
	console.error(err);
	process.exit(1);
});
