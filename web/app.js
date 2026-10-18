// Interfaz: carga data/*.json, pinta pestañas y, con token, guarda cambios en el repo.
import {
  acceptCandidate, buildRows, candidateList, dismissRepo, filterRows,
  isRecent, relativeTime, sortRows, toggleFollow,
} from "./logic.js";
import { createStore } from "./store.js";

const REPO = "AndresArasanz/portradar";
const TOKEN_KEY = "portradar-token";
const TAB_KEY = "portradar-tab";
const STALE_HOURS = 48;
const CHANGED_DAYS = 7;
const STATUS = { play: ["Jugable", "s-play"], alpha: ["Alfa", "s-alpha"], early: ["Temprano", "s-early"] };

const $ = id => document.getElementById(id);
const state = {
  ports: { ports: [] }, github: { repos: {} }, candidates: { candidates: {} },
  follows: { follows: [] }, review: { dismissed: [] },
  tab: storageGet(TAB_KEY) || "following", query: "", sortKey: "pushedAt", sortDir: -1,
  token: storageGet(TOKEN_KEY), busy: new Set(),
};

function storageGet(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function storageSet(key, value) {
  try { value === null ? localStorage.removeItem(key) : localStorage.setItem(key, value); } catch { /* sin almacenamiento */ }
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  node.append(...children.filter(c => c !== null && c !== undefined && c !== false));
  return node;
}

function showError(message) {
  $("error").textContent = message || "";
  $("error").hidden = !message;
}

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return res.json();
}

async function load() {
  const [ports, github, candidates, follows, review] = await Promise.all(
    ["ports", "github", "candidates", "follows", "review"].map(n => fetchJson(`data/${n}.json`)));
  Object.assign(state, { ports, github, candidates, follows, review });
  if (state.token) await loadFresh();
}

// Con token se leen del repo los ficheros que cambia la web, para no ver una versión antigua de Pages.
async function loadFresh() {
  const store = createStore({ repo: REPO, token: state.token });
  try {
    const [ports, follows, review] = await Promise.all(
      ["ports", "follows", "review"].map(n => store.readJson(`data/${n}.json`)));
    Object.assign(state, { ports: ports.data, follows: follows.data, review: review.data });
  } catch (err) {
    showError(`No se pudo leer del repo con tu token (${err.message}). Se muestran los datos publicados.`);
  }
}

function badges(row, now) {
  const list = [
    row.fork && [row.forkOf ? `fork de ${row.forkOf}` : "fork", ""],
    row.missing && ["no encontrado", "b-missing"],
    row.archived && ["archivado", ""],
    row.renamedTo && [`renombrado → ${row.renamedTo}`, ""],
    isRecent(row.statusChangedAt, now, CHANGED_DAYS) && ["estado cambiado", "b-changed"],
  ].filter(Boolean);
  return list.length ? el("div", { class: "badges" }, ...list.map(([t, c]) => el("span", { class: `badge ${c}` }, t))) : null;
}

function gameCell(row, now) {
  return el("td", {},
    el("div", { class: "game" }, row.game),
    el("a", { class: "repo", href: row.url, target: "_blank", rel: "noopener" }, row.renamedTo || row.repo),
    badges(row, now),
    row.reach && el("div", { class: "reach" }, `Hasta dónde llega: ${row.reach}`),
    row.note && el("div", { class: "note" }, row.note),
    row.statusText && el("div", { class: "author-status" }, `Según el autor: ${row.statusText} `,
      el("a", { href: `${row.url}#readme`, target: "_blank", rel: "noopener" }, "ver README")));
}

function followCell(row) {
  if (!state.token) return el("td");
  const busy = state.busy.has(row.id);
  return el("td", {}, el("button", {
    class: "star", type: "button", "aria-pressed": String(row.followed),
    "aria-label": row.followed ? `Dejar de seguir ${row.game}` : `Seguir ${row.game}`,
    title: row.followed ? "Dejar de seguir" : "Seguir",
    ...(busy ? { disabled: "" } : {}),
    onclick: () => onToggleFollow(row),
  }, row.followed ? "★" : "☆"));
}

function rowElement(row, now) {
  const [label, cls] = STATUS[row.status];
  const stale = !row.pushedAt || (now - new Date(row.pushedAt)) / 36e5 > STALE_HOURS;
  return el("tr", { class: row.followed ? "followed" : "", "data-id": row.id },
    gameCell(row, now),
    el("td", {}, row.os || "—"),
    el("td", {}, el("span", { class: `pill ${cls}` }, label)),
    el("td", { class: "num" }, row.releaseTag || "—"),
    el("td", { class: "num" }, row.releaseDate ? row.releaseDate.split("-").reverse().slice(0, 2).join("/") : "—"),
    el("td", { class: "num" }, row.stars === null ? "—" : row.stars.toLocaleString("es-ES")),
    el("td", {}, el("span", { class: "fresh" }, el("span", { class: `dot${stale ? " stale" : ""}` }),
      el("span", { class: "num" }, relativeTime(row.pushedAt, now)))),
    followCell(row));
}

function renderTable(rows, now) {
  const visible = sortRows(filterRows(rows, { tab: state.tab, query: state.query }), state.sortKey, state.sortDir);
  const empty = state.tab === "following" && !state.query
    ? "Aún no sigues ningún juego. Márcalos con ☆ en la pestaña Todos."
    : "Ningún port coincide con la búsqueda.";
  $("rows").replaceChildren(...(visible.length ? visible.map(r => rowElement(r, now))
    : [el("tr", {}, el("td", { colspan: "8", class: "empty" }, empty))]));
}

function candidateCard(c) {
  const busy = state.busy.has(c.repo);
  const url = `https://github.com/${c.repo}`;
  return el("li", { class: "card", "data-repo": c.repo },
    el("a", { class: "repo", href: url, target: "_blank", rel: "noopener" }, c.repo),
    el("p", {}, c.description || "Sin descripción"),
    el("p", { class: "meta" }, `★ ${c.stars ?? 0} · detectado ${c.found_at || "—"}`),
    state.token && el("div", { class: "actions" },
      el("button", { class: "chip primary", type: "button", ...(busy ? { disabled: "" } : {}), onclick: () => onAccept(c) }, "Aceptar"),
      el("button", { class: "chip", type: "button", ...(busy ? { disabled: "" } : {}), onclick: () => onDismiss(c) }, "Descartar")));
}

function renderCandidates(list) {
  const items = list.map(candidateCard);
  $("review-hint").hidden = Boolean(state.token) || !list.length;
  $("candidates").replaceChildren(...(items.length ? items : [el("li", { class: "empty" }, "No hay repos nuevos pendientes.")]));
}

function render() {
  const now = new Date();
  const rows = buildRows(state.ports.ports, state.github, state.follows.follows);
  const candidates = candidateList(state.candidates, state.ports.ports, state.review);
  $("count-following").textContent = rows.filter(r => r.followed).length;
  $("count-all").textContent = rows.length;
  $("count-review").textContent = candidates.length;
  document.querySelectorAll(".tab").forEach(t => t.setAttribute("aria-selected", String(t.dataset.tab === state.tab)));
  $("panel-table").hidden = state.tab === "review";
  $("panel-review").hidden = state.tab !== "review";
  $("token-btn").textContent = state.token ? "Conectado ✓" : "Conectar";
  const updated = state.github.updated_at;
  $("snap").textContent = updated ? `Datos de GitHub actualizados ${relativeTime(updated, now)} (${new Date(updated).toLocaleString("es-ES")})` : "";
  if (state.tab === "review") renderCandidates(candidates);
  else renderTable(rows, now);
}

async function withWrite(key, optimistic, write) {
  const backup = { ports: state.ports, follows: state.follows, review: state.review };
  state.busy.add(key);
  optimistic();
  render();
  try {
    await write(createStore({ repo: REPO, token: state.token }));
    showError(null);
  } catch (err) {
    Object.assign(state, backup);
    showError(`No se pudo guardar: ${err.message}`);
  } finally {
    state.busy.delete(key);
    render();
  }
}

function onToggleFollow(row) {
  withWrite(row.id,
    () => { state.follows = { follows: toggleFollow(state.follows.follows, row.id) }; },
    async store => {
      const saved = await store.updateJson("data/follows.json",
        d => ({ ...d, follows: toggleFollow(d.follows, row.id) }),
        `${row.followed ? "Deja de seguir" : "Sigue"} ${row.game}`);
      state.follows = saved;
    });
}

function onAccept(c) {
  withWrite(c.repo,
    () => { state.ports = acceptCandidate(state.ports, c); },
    async store => { state.ports = await store.updateJson("data/ports.json", d => acceptCandidate(d, c), `Acepta ${c.repo}`); });
}

function onDismiss(c) {
  withWrite(c.repo,
    () => { state.review = dismissRepo(state.review, c.repo); },
    async store => { state.review = await store.updateJson("data/review.json", d => dismissRepo(d, c.repo), `Descarta ${c.repo}`); });
}

function setupTokenDialog() {
  const dialog = $("token-dialog");
  $("token-btn").addEventListener("click", () => {
    $("token-input").value = "";
    $("token-error").hidden = true;
    $("token-forget").hidden = !state.token;
    dialog.showModal();
  });
  $("token-cancel").addEventListener("click", () => dialog.close());
  $("token-forget").addEventListener("click", () => {
    storageSet(TOKEN_KEY, null);
    state.token = null;
    dialog.close();
    render();
  });
  $("token-form").addEventListener("submit", async ev => {
    ev.preventDefault();
    const token = $("token-input").value.trim();
    if (!token) return;
    $("token-save").disabled = true;
    const ok = await createStore({ repo: REPO, token }).checkToken().catch(() => false);
    $("token-save").disabled = false;
    if (!ok) {
      $("token-error").textContent = "El token no es válido o no tiene acceso de escritura a este repositorio.";
      $("token-error").hidden = false;
      return;
    }
    storageSet(TOKEN_KEY, token);
    state.token = token;
    dialog.close();
    await loadFresh();
    render();
  });
}

function setupControls() {
  document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => {
    state.tab = t.dataset.tab;
    storageSet(TAB_KEY, state.tab);
    render();
  }));
  $("q").addEventListener("input", e => { state.query = e.target.value; render(); });
  document.querySelectorAll("th[data-k]").forEach(th => th.addEventListener("click", () => {
    const key = th.dataset.k;
    state.sortDir = state.sortKey === key ? -state.sortDir : (key === "game" || key === "os" ? 1 : -1);
    state.sortKey = key;
    document.querySelectorAll("th").forEach(h => h.removeAttribute("data-sort-dir"));
    th.setAttribute("data-sort-dir", state.sortDir > 0 ? "↑" : "↓");
    render();
  }));
}

setupControls();
setupTokenDialog();
load().then(render).catch(err => showError(`No se pudieron cargar los datos: ${err.message}`));
