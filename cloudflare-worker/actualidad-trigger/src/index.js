// Red de seguridad del workflow "Actualizar actualidad": GitHub Actions pierde
// a veces los disparos de `schedule`, así que este Worker (con crons de
// Cloudflare, mucho más fiables) lanza el workflow por `workflow_dispatch`
// si hoy (hora de Madrid) todavía no se ha actualizado actualidad.json.

const API = "https://api.github.com";

function fechaMadrid(d) {
  return new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Madrid" }).format(d); // YYYY-MM-DD
}

async function gh(env, path, init = {}) {
  return fetch(`${API}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "opensalamanca-actualidad-trigger",
      ...(init.headers || {}),
    },
  });
}

async function disparar(env) {
  const hoy = fechaMadrid(new Date());

  const commits = await gh(env, `/repos/${env.REPO}/commits?path=actualidad.json&sha=${env.REF}&per_page=1`);
  if (!commits.ok) throw new Error(`No pude leer commits: ${commits.status}`);
  const [ultimo] = await commits.json();
  const fechaUltimo = ultimo ? fechaMadrid(new Date(ultimo.commit.committer.date)) : null;
  if (fechaUltimo === hoy) return `Ya actualizado hoy (${hoy}): no hago nada.`;

  // Si ya hay una ejecución en marcha o en cola, no apilamos otra.
  const runs = await gh(env, `/repos/${env.REPO}/actions/workflows/${env.WORKFLOW}/runs?per_page=5`);
  if (runs.ok) {
    const { workflow_runs } = await runs.json();
    if (workflow_runs.some((r) => r.status !== "completed" && fechaMadrid(new Date(r.created_at)) === hoy)) {
      return "Hay una ejecución en curso hoy: no apilo otra.";
    }
  }

  const res = await gh(env, `/repos/${env.REPO}/actions/workflows/${env.WORKFLOW}/dispatches`, {
    method: "POST",
    body: JSON.stringify({ ref: env.REF }),
  });
  if (res.status !== 204) throw new Error(`Dispatch falló: ${res.status} ${await res.text()}`);
  return `Workflow lanzado (último commit: ${fechaUltimo ?? "ninguno"}, hoy: ${hoy}).`;
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(disparar(env).then((m) => console.log(m)));
  },
  // GET manual para probar (requiere ?clave=<TRIGGER_KEY> si se define ese secret).
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!env.TRIGGER_KEY || url.searchParams.get("clave") !== env.TRIGGER_KEY) {
      return new Response("No autorizado", { status: 401 });
    }
    try {
      return new Response(await disparar(env));
    } catch (e) {
      return new Response(String(e), { status: 500 });
    }
  },
};
