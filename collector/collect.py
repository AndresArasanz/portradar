"""Lógica pura del recolector: transforma respuestas de la API de GitHub en registros."""
import re

STATUS_MAX_LEN = 280
STATUS_CHANGE_FIELDS = ("status_text",)

_BOLD_STATUS = re.compile(r"^\*\*Status(?: [^:*]+)?:\s*(.*)$", re.IGNORECASE)
_STATUS_HEADING = re.compile(r"^#{1,4}\s*Status\b", re.IGNORECASE)
_HEADING = re.compile(r"^#{1,6}\s")
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_HTML_TAG = re.compile(r"<[^>]+>")


def _clean(text):
    text = _IMAGE.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _HTML_TAG.sub("", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text):
    if len(text) <= STATUS_MAX_LEN:
        return text
    cut = text[: STATUS_MAX_LEN - 1].rsplit(" ", 1)[0].rstrip(" ,;:")
    return cut + "…"


def _paragraph(lines, start):
    """Devuelve las líneas desde `start` hasta la siguiente línea vacía o encabezado."""
    out = []
    for line in lines[start:]:
        if not line.strip() or _HEADING.match(line):
            break
        out.append(line.strip())
    return out


def _table_to_text(lines):
    """Convierte una tabla markdown en 'celda1: celda2 · …' omitiendo cabecera y separador."""
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines]
    body = [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r if c)]
    return " · ".join(": ".join(c for c in r if c) for r in body)


def _paragraph_text(lines):
    if lines and lines[0].startswith("|"):
        return _clean(_table_to_text(lines))
    return _clean(" ".join(lines))


def extract_status(readme):
    """Extrae el párrafo de estado que publica el autor en su README, o None."""
    if not readme:
        return None
    lines = readme.splitlines()
    for i, line in enumerate(lines):
        bold = _BOLD_STATUS.match(line.strip())
        if bold:
            text = _clean(" ".join([bold.group(1), *_paragraph(lines, i + 1)]))
            return _truncate(text) if text else None
        if _STATUS_HEADING.match(line):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines) or _HEADING.match(lines[j]):
                return None
            text = _paragraph_text(_paragraph(lines, j))
            return _truncate(text) if text else None
    return None


def build_record(requested_repo, repo_json, releases, readme):
    """Registro automático de un repo a partir de las respuestas de la API."""
    latest = releases[0] if releases else None
    published = (latest or {}).get("published_at") or ""
    full_name = repo_json["full_name"]
    return {
        "stars": repo_json["stargazers_count"],
        "pushed_at": repo_json["pushed_at"],
        "archived": repo_json["archived"],
        "fork": repo_json["fork"],
        "missing": False,
        "renamed_to": None if full_name.lower() == requested_repo.lower() else full_name,
        "release_tag": latest["tag_name"] if latest else None,
        "release_date": published[:10] or None,
        "status_text": extract_status(readme),
    }


_EMPTY_RECORD = {
    "stars": None,
    "pushed_at": None,
    "archived": False,
    "fork": False,
    "renamed_to": None,
    "release_tag": None,
    "release_date": None,
    "status_text": None,
    "status_changed_at": None,
}


def merge_record(prev, new, today):
    """Combina el registro nuevo con el anterior sin mutar ninguno.

    `new` es None cuando el repo ya no existe: se conservan los datos previos.
    """
    if new is None:
        return {**_EMPTY_RECORD, **(prev or {}), "missing": True}
    if prev is None:
        return {**new, "status_changed_at": None}
    changed = any(prev.get(f) != new.get(f) for f in STATUS_CHANGE_FIELDS)
    return {**new, "status_changed_at": today if changed else prev.get("status_changed_at")}


def filter_candidates(items, known, dismissed, previous, today):
    """Repos nuevos sin revisar: excluye forks, conocidos y descartados.

    Conserva los candidatos previos (y su fecha de detección) mientras no se revisen.
    """
    excluded = {r.lower() for r in known} | {r.lower() for r in dismissed}
    result = {k: v for k, v in previous.items() if k.lower() not in excluded}
    for item in items:
        key = item["full_name"].lower()
        if item["fork"] or key in excluded or key in result:
            continue
        result[key] = {
            "repo": item["full_name"],
            "url": item["html_url"],
            "description": item.get("description") or "",
            "stars": item["stargazers_count"],
            "pushed_at": item["pushed_at"],
            "found_at": today,
        }
    return result
