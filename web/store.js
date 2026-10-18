// Lectura/escritura de los JSON de data/ en el repo mediante la API de contenidos de GitHub.

const API = "https://api.github.com";
const BRANCH = "main";
const CONFLICT = 409;
const MAX_ATTEMPTS = 3;
const RETRY_DELAY_MS = 700;
const FINE_GRAINED_PREFIX = "github_pat_";
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

export function encodeBase64(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  bytes.forEach(b => { binary += String.fromCharCode(b); });
  return btoa(binary);
}

export function decodeBase64(b64) {
  const binary = atob(b64.replace(/\s/g, ""));
  return new TextDecoder().decode(Uint8Array.from(binary, c => c.charCodeAt(0)));
}

async function failure(res) {
  const body = await res.json().catch(() => ({}));
  return new Error(`GitHub ${res.status}: ${body.message || "error"}`);
}

export function createStore({ repo, token, fetch = globalThis.fetch, wait = sleep }) {
  const headers = { Accept: "application/vnd.github+json", Authorization: `Bearer ${token}` };

  async function readJson(path) {
    const res = await fetch(`${API}/repos/${repo}/contents/${path}?ref=${BRANCH}&t=${Date.now()}`, { headers });
    if (!res.ok) throw await failure(res);
    const body = await res.json();
    return { data: JSON.parse(decodeBase64(body.content)), sha: body.sha };
  }

  async function put(path, data, sha, message) {
    const content = encodeBase64(JSON.stringify(data, null, 2) + "\n");
    return fetch(`${API}/repos/${repo}/contents/${path}`, {
      method: "PUT", headers, body: JSON.stringify({ message, content, sha, branch: BRANCH }),
    });
  }

  // Lee la versión más reciente, aplica `change` y la guarda; si otro commit se adelantó
  // (409) espera un poco y reintenta, porque la API puede tardar en servir el sha nuevo.
  async function updateJson(path, change, message) {
    for (let attempt = 1; ; attempt += 1) {
      const { data, sha } = await readJson(path);
      const next = change(data);
      const res = await put(path, next, sha, message);
      if (res.ok) return next;
      if (res.status !== CONFLICT || attempt >= MAX_ATTEMPTS) throw await failure(res);
      await wait(RETRY_DELAY_MS * attempt);
    }
  }

  // Solo tokens fine-grained: un token clásico u OAuth daría acceso a todos los repos del usuario.
  async function checkToken() {
    if (!token.startsWith(FINE_GRAINED_PREFIX)) return false;
    const res = await fetch(`${API}/repos/${repo}`, { headers });
    if (!res.ok) return false;
    const body = await res.json();
    return Boolean(body.permissions && body.permissions.push);
  }

  return { readJson, updateJson, checkToken };
}
