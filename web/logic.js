// Lógica pura de la web: sin DOM ni red, para poder testearla con node --test.

const STATUS_RANK = { play: 3, alpha: 2, early: 1 };
const HOUR_MS = 36e5;
const DAY_MS = 24 * HOUR_MS;

const lower = s => (s || "").toLowerCase();

export function buildRows(ports, github, follows) {
  const repos = (github && github.repos) || {};
  const followed = new Set(follows);
  return ports.map(p => {
    const g = repos[lower(p.repo)] || {};
    return {
      id: p.id, game: p.game, repo: p.repo, os: p.os, status: p.status, reach: p.reach, note: p.note,
      url: `https://github.com/${g.renamed_to || p.repo}`,
      stars: g.stars ?? null,
      pushedAt: g.pushed_at ?? null,
      releaseTag: g.release_tag ?? null,
      releaseDate: g.release_date ?? null,
      archived: Boolean(g.archived),
      fork: Boolean(g.fork),
      forkOf: g.fork_of ?? null,
      missing: Boolean(g.missing),
      renamedTo: g.renamed_to ?? null,
      statusText: g.status_text ?? null,
      statusChangedAt: g.status_changed_at ?? null,
      followed: followed.has(p.id),
    };
  });
}

export function filterRows(rows, { tab, query }) {
  const q = lower(query).trim();
  return rows.filter(r =>
    (tab !== "following" || r.followed) &&
    (!q || lower(`${r.game} ${r.repo}`).includes(q)));
}

function sortValue(row, key) {
  if (key === "status") return STATUS_RANK[row.status] ?? null;
  if (key === "pushedAt") return row.pushedAt ? Date.parse(row.pushedAt) : null;
  return row[key] ?? null;
}

export function sortRows(rows, key, dir) {
  return [...rows].sort((a, b) => {
    const x = sortValue(a, key);
    const y = sortValue(b, key);
    if (x === null || x === "") return y === null || y === "" ? 0 : 1;
    if (y === null || y === "") return -1;
    const cmp = typeof x === "string" ? x.localeCompare(y, "es") : x - y;
    return cmp * dir;
  });
}

export function relativeTime(iso, now) {
  if (!iso) return "—";
  const hours = Math.round((now - new Date(iso)) / HOUR_MS);
  if (hours < 1) return "hace minutos";
  if (hours < 24) return `hace ${hours} h`;
  const days = Math.round(hours / 24);
  return `hace ${days} ${days === 1 ? "día" : "días"}`;
}

export function isRecent(dateStr, now, days) {
  if (!dateStr) return false;
  return now - new Date(dateStr) <= days * DAY_MS;
}

export function toggleFollow(follows, id) {
  return follows.includes(id) ? follows.filter(f => f !== id) : [...follows, id];
}

export function candidateList(candidates, ports, review) {
  const hidden = new Set([...ports.map(p => lower(p.repo)), ...review.dismissed.map(lower)]);
  return Object.values((candidates && candidates.candidates) || {})
    .filter(c => !hidden.has(lower(c.repo)))
    .sort((a, b) => (b.stars || 0) - (a.stars || 0));
}

export function dismissRepo(review, repo) {
  if (review.dismissed.some(r => lower(r) === lower(repo))) return review;
  return { ...review, dismissed: [...review.dismissed, repo] };
}

export function slugify(text) {
  const slug = lower(text).replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return slug || "port";
}

export function acceptCandidate(portsData, candidate) {
  const ports = portsData.ports;
  if (ports.some(p => lower(p.repo) === lower(candidate.repo))) return portsData;
  const name = candidate.repo.split("/")[1];
  const ids = new Set(ports.map(p => p.id));
  const base = slugify(name);
  let id = base;
  for (let n = 2; ids.has(id); n += 1) id = `${base}-${n}`;
  const port = { id, game: name, repo: candidate.repo, os: "", status: "early", reach: "", note: candidate.description || "" };
  return { ...portsData, ports: [...ports, port] };
}
