"""Recolector diario: actualiza data/github.json y data/candidates.json.

Uso: python -m collector.main [data_dir]   (GITHUB_TOKEN opcional en el entorno)
Sale con código 0 y escribe `changed=true|false` en $GITHUB_OUTPUT si existe.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from collector.collect import build_record, filter_candidates, merge_record
from collector.github import GitHubClient, GitHubError
from collector.validate import validate_follows, validate_ports, validate_review

SEARCH_QUERIES = ("ps4 pc port", "ps4 native port", "ps4 recomp", "ps4 recompilation")


def _load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def _write_if_changed(path, data):
    text = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if path.exists() and path.read_text() == text:
        return False
    path.write_text(text)
    return True


def _log(msg):
    print(msg, file=sys.stderr)


def _load_validated(data_dir):
    ports = _load(data_dir / "ports.json", {})
    follows = _load(data_dir / "follows.json", {"follows": []})
    review = _load(data_dir / "review.json", {"dismissed": []})
    port_ids = {p.get("id") for p in ports.get("ports", []) if isinstance(p, dict)}
    errors = validate_ports(ports) + validate_follows(follows, port_ids) + validate_review(review)
    if errors:
        raise ValueError("Datos inválidos:\n" + "\n".join(errors))
    return ports["ports"], set(review["dismissed"])


def _collect_repo(client, repo, prev, today):
    try:
        repo_json = client.get_repo(repo)
        if repo_json is None:
            return merge_record(prev, None, today)
        new = build_record(repo, repo_json, client.get_releases(repo), client.get_readme(repo))
        return merge_record(prev, new, today)
    except GitHubError as err:
        _log(f"AVISO {repo}: {err} — se conservan los datos anteriores")
        return prev


def _search(client):
    items = []
    for query in SEARCH_QUERIES:
        try:
            items += client.search_repos(query)
        except GitHubError as err:
            _log(f"AVISO búsqueda '{query}': {err}")
    return items


def run(client, data_dir, today, now_iso):
    data_dir = Path(data_dir)
    ports, dismissed = _load_validated(data_dir)
    previous = _load(data_dir / "github.json", {"repos": {}})

    repos = {}
    for repo in dict.fromkeys(p["repo"] for p in ports):
        key = repo.lower()
        record = _collect_repo(client, repo, previous["repos"].get(key), today)
        if record is not None:
            repos[key] = record

    known = set(repos) | {r["renamed_to"] for r in repos.values() if r.get("renamed_to")}
    old_candidates = _load(data_dir / "candidates.json", {"candidates": {}})["candidates"]
    candidates = filter_candidates(_search(client), known, dismissed, old_candidates, today)

    repos_changed = repos != previous["repos"]
    github_data = {"repos": repos, "updated_at": now_iso if repos_changed else previous.get("updated_at", now_iso)}
    changed = _write_if_changed(data_dir / "github.json", github_data)
    changed |= _write_if_changed(data_dir / "candidates.json", {"candidates": candidates})
    return changed


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    now = datetime.now(timezone.utc)
    client = GitHubClient(os.environ.get("GITHUB_TOKEN"))
    changed = run(client, data_dir, now.date().isoformat(), now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    print(f"changed={str(changed).lower()}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as out:
            out.write(f"changed={str(changed).lower()}\n")


if __name__ == "__main__":
    main()
