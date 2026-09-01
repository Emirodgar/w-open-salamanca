// Contador de votos para la sección "Opina" de opensalamanca.es.
// No usa base de datos: guarda un objeto {opcion: numero_de_votos} por
// pregunta en Cloudflare KV (namespace enlazado como OPINA_VOTOS).
//
// Rutas:
//   GET  /votos/:preguntaId        -> devuelve los recuentos actuales
//   POST /votos/:preguntaId        -> body {"opcion": "..."} incrementa esa opción
//                                     (rechazada con 403 si la pregunta está cerrada)
//
// El origen permitido en CORS está fijado al dominio real del sitio para que
// solo opensalamanca.es pueda escribir votos desde el navegador.
//
// Cerrar una pregunta (al archivarla en opina-archivo.json) para que ya no
// admita más votos, aunque alguien intente llamar a la API directamente:
//   wrangler kv key put "closed:<preguntaId>" "1" --namespace-id=<tu-id>

const ORIGEN_PERMITIDO = 'https://opensalamanca.es';

function cabecerasCors(origin) {
	return {
		'Access-Control-Allow-Origin': origin === ORIGEN_PERMITIDO ? origin : ORIGEN_PERMITIDO,
		'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
		'Access-Control-Allow-Headers': 'Content-Type',
		'Content-Type': 'application/json; charset=utf-8'
	};
}

function json(data, status, cabeceras) {
	return new Response(JSON.stringify(data), { status, headers: cabeceras });
}

export default {
	async fetch(request, env) {
		const url = new URL(request.url);
		const cabeceras = cabecerasCors(request.headers.get('Origin') || '');

		if (request.method === 'OPTIONS') {
			return new Response(null, { headers: cabeceras });
		}

		const coincide = url.pathname.match(/^\/votos\/([a-z0-9-]+)$/i);
		if (!coincide) {
			return json({ error: 'Ruta no válida. Usa /votos/:preguntaId' }, 404, cabeceras);
		}
		const preguntaId = coincide[1];
		const clave = `poll:${preguntaId}`;

		if (request.method === 'GET') {
			const guardado = (await env.OPINA_VOTOS.get(clave, { type: 'json' })) || {};
			return json(guardado, 200, cabeceras);
		}

		if (request.method === 'POST') {
			let cuerpo;
			try {
				cuerpo = await request.json();
			} catch (err) {
				return json({ error: 'JSON inválido en el cuerpo de la petición' }, 400, cabeceras);
			}
			const opcion = cuerpo && cuerpo.opcion;
			if (!opcion || typeof opcion !== 'string' || opcion.length > 200) {
				return json({ error: 'Falta el campo "opcion" (texto)' }, 400, cabeceras);
			}

			const cerrada = await env.OPINA_VOTOS.get(`closed:${preguntaId}`);
			if (cerrada) {
				return json({ error: 'Esta pregunta ya está archivada y no admite más votos' }, 403, cabeceras);
			}

			const guardado = (await env.OPINA_VOTOS.get(clave, { type: 'json' })) || {};
			guardado[opcion] = (guardado[opcion] || 0) + 1;
			await env.OPINA_VOTOS.put(clave, JSON.stringify(guardado));

			return json(guardado, 200, cabeceras);
		}

		return json({ error: 'Método no soportado' }, 405, cabeceras);
	}
};
