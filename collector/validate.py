"""Validación de los ficheros de datos editados a mano o desde la web."""
import re

ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
STATUSES = {"play", "alpha", "early"}
TEXT_FIELDS = ("os", "reach", "note")


def _validate_port(i, port, seen):
    if not isinstance(port, dict):
        return [f"ports[{i}]: debe ser un objeto"]
    errors = []
    pid = port.get("id")
    if not isinstance(pid, str) or not ID_PATTERN.match(pid):
        errors.append(f"ports[{i}]: id inválido {pid!r} (kebab-case)")
    elif pid in seen:
        errors.append(f"ports[{i}]: id duplicado '{pid}'")
    if not isinstance(port.get("game"), str) or not port["game"].strip():
        errors.append(f"ports[{i}]: falta game")
    if not isinstance(port.get("repo"), str) or not REPO_PATTERN.match(port["repo"]):
        errors.append(f"ports[{i}]: repo inválido {port.get('repo')!r}")
    if port.get("status") not in STATUSES:
        errors.append(f"ports[{i}]: status {port.get('status')!r} no es uno de {sorted(STATUSES)}")
    errors += [f"ports[{i}]: {f} debe ser texto" for f in TEXT_FIELDS if not isinstance(port.get(f), str)]
    return errors


def validate_ports(data):
    ports = data.get("ports")
    if not isinstance(ports, list):
        return ["ports: falta la lista 'ports'"]
    errors, seen = [], set()
    for i, port in enumerate(ports):
        errors += _validate_port(i, port, seen)
        if isinstance(port, dict):
            seen.add(port.get("id"))
    return errors


def validate_follows(data, port_ids):
    follows = data.get("follows")
    if not isinstance(follows, list):
        return ["follows: falta la lista 'follows'"]
    return [f"follows: id desconocido '{f}'" for f in follows if f not in port_ids]


def validate_review(data):
    dismissed = data.get("dismissed")
    if not isinstance(dismissed, list):
        return ["review: falta la lista 'dismissed'"]
    return [f"review: repo inválido '{r}'" for r in dismissed
            if not isinstance(r, str) or not REPO_PATTERN.match(r)]
