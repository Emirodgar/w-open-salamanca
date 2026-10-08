// Red de seguridad de los workflows diarios de actualización: GitHub Actions
// pierde a veces los disparos de `schedule`, así que este Worker (con crons de
// Cloudflare, mucho más fiables) lanza cada workflow por `workflow_dispatch`
// si hoy (hora de Madrid) todavía no se ha actualizado su fichero de control.
//
// Para añadir otro workflow, añade una entrada a JOBS:
//   repo       propietario/repositorio
//   workflow   fichero del workflow en .github/workflows (debe tener workflow_dispatch)
//   ref        rama por defecto del repo
//   comprobar  fichero que SOLO ese workflow commitea (si hoy ya tiene commit, no se lanza)
//   desdeHora  hora de Madrid a partir de la cual puede lanzarse (por defecto 7)
// Un dispatch se salta la lógica "solo si toca" de cada workflow, por eso la
// comprobación la hace este Worker.
const JOBS = [
  { repo: "Emirodgar/w-open-salamanca", workflow: "actualidad.yml", ref: "main", comprobar: "actualidad.json" },
  { repo: "Emirodgar/w-emirodgar-es", workflow: "actualidad.yml", ref: "master", comprobar: "actualidad/datos/latest.json" },
  { repo: "Emirodgar/w-mejor-imposible", workflow: "actualiza-tendencias-rss.yml", ref: "main", comprobar: ".claude/state/tendencias-rss-seen.json" },
];

const API = "https://api.github.com";

const fechaMadrid = (d) => new Intl.DateTimeFormat("sv-SE", { timeZone: "Europe/Madrid" }).format(d); // YYYY-MM-DD
const horaMadrid = (d) =>
  Number(new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Madrid", hour: "2-digit", hour12: false }).format(d)) % 24;

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

async function disparar(env, job) {
  const ahora = new Date();
  const hoy = fechaMadrid(ahora);
  const etiqueta = `${job.repo}/${job.workflow}`;

  if (horaMadrid(ahora) < (job.desdeHora ?? 7)) return `${etiqueta}: aún no son las ${job.desdeHora ?? 7}:00 en Madrid.`;

  const commits = await gh(env, `/repos/${job.repo}/commits?path=${encodeURIComponent(job.comprobar)}&sha=${job.ref}&per_page=1`);
  if (!commits.ok) throw new Error(`${etiqueta}: no pude leer commits (${commits.status})`);
  const [ultimo] = await commits.json();
  const fechaUltimo = ultimo ? fechaMadrid(new Date(ultimo.commit.committer.date)) : null;
  if (fechaUltimo === hoy) return `${etiqueta}: ya actualizado hoy (${hoy}).`;

  // Si ya hay una ejecución en marcha o en cola, no apilamos otra.
  const runs = await gh(env, `/repos/${job.repo}/actions/workflows/${job.workflow}/runs?per_page=5`);
  if (runs.ok) {
    const { workflow_runs } = await runs.json();
    if (workflow_runs.some((r) => r.status !== "completed" && fechaMadrid(new Date(r.created_at)) === hoy)) {
      return `${etiqueta}: hay una ejecución en curso hoy.`;
    }
  }

  const res = await gh(env, `/repos/${job.repo}/actions/workflows/${job.workflow}/dispatches`, {
    method: "POST",
    body: JSON.stringify({ ref: job.ref }),
  });
  if (res.status !== 204) throw new Error(`${etiqueta}: dispatch falló (${res.status} ${await res.text()})`);
  return `${etiqueta}: lanzado (último commit: ${fechaUltimo ?? "ninguno"}, hoy: ${hoy}).`;
}

// Cada trabajo es independiente: que uno falle no impide lanzar los demás.
async function dispararTodos(env) {
  const res = await Promise.allSettled(JOBS.map((j) => disparar(env, j)));
  return res.map((r) => (r.status === "fulfilled" ? r.value : `ERROR ${r.reason.message}`));
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(dispararTodos(env).then((m) => console.log(m.join("\n"))));
  },
  // GET manual para probar (requiere ?clave=<TRIGGER_KEY> si se define ese secret).
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!env.TRIGGER_KEY || url.searchParams.get("clave") !== env.TRIGGER_KEY) {
      return new Response("No autorizado", { status: 401 });
    }
    return new Response((await dispararTodos(env)).join("\n"));
  },
};
