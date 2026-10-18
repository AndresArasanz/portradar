import json

import pytest

from collector.github import GitHubError
from collector.main import SEARCH_QUERIES, run


class FakeClient:
    def __init__(self, repos=None, releases=None, readmes=None, search=None, fail=()):
        self.repos = repos or {}
        self.releases = releases or {}
        self.readmes = readmes or {}
        self.search_items = search or []
        self.fail = set(fail)
        self.queries = []

    def get_repo(self, repo):
        if repo in self.fail:
            raise GitHubError("500")
        return self.repos.get(repo)

    def get_releases(self, repo):
        return self.releases.get(repo, [])

    def get_readme(self, repo):
        return self.readmes.get(repo)

    def search_repos(self, query):
        self.queries.append(query)
        return self.search_items


def repo_json(name, stars=10, repo_id=1):
    return {"id": repo_id, "full_name": name, "html_url": f"https://github.com/{name}", "stargazers_count": stars,
            "pushed_at": "2026-10-18T00:00:00Z", "archived": False, "fork": False}


@pytest.fixture
def data_dir(tmp_path):
    ports = {"ports": [
        {"id": "bb", "game": "Bloodborne", "repo": "a/bb", "os": "Windows", "status": "play", "reach": "", "note": ""},
        {"id": "uo", "game": "Unicorn Overlord", "repo": "b/uo", "os": "Linux", "status": "early", "reach": "", "note": ""},
        {"id": "os", "game": "Odin Sphere", "repo": "b/uo", "os": "Linux", "status": "early", "reach": "", "note": ""},
    ]}
    (tmp_path / "ports.json").write_text(json.dumps(ports))
    (tmp_path / "follows.json").write_text(json.dumps({"follows": ["bb"]}))
    (tmp_path / "review.json").write_text(json.dumps({"dismissed": ["x/dismissed"]}))
    return tmp_path


def load(d, name):
    return json.loads((d / name).read_text())


def test_run_writes_records_for_each_unique_repo(data_dir):
    client = FakeClient(repos={"a/bb": repo_json("a/bb", 5), "b/uo": repo_json("b/uo")},
                        readmes={"a/bb": "**Status: playable.** Ok\n"})

    changed = run(client, data_dir, "2026-10-18", "2026-10-18T06:00:00Z")

    gh = load(data_dir, "github.json")
    assert changed is True
    assert set(gh["repos"]) == {"a/bb", "b/uo"}
    assert gh["repos"]["a/bb"]["stars"] == 5
    assert gh["repos"]["a/bb"]["status_text"] == "playable. Ok"
    assert gh["updated_at"] == "2026-10-18T06:00:00Z"


def test_run_is_idempotent_and_reports_no_change(data_dir):
    client = FakeClient(repos={"a/bb": repo_json("a/bb"), "b/uo": repo_json("b/uo")})
    run(client, data_dir, "2026-10-18", "2026-10-18T06:00:00Z")
    before = (data_dir / "github.json").read_text()

    changed = run(client, data_dir, "2026-10-19", "2026-10-19T06:00:00Z")

    assert changed is False
    assert (data_dir / "github.json").read_text() == before


def test_run_marks_missing_repo(data_dir):
    client = FakeClient(repos={"b/uo": repo_json("b/uo")})

    run(client, data_dir, "2026-10-18", "2026-10-18T06:00:00Z")

    assert load(data_dir, "github.json")["repos"]["a/bb"]["missing"] is True


def test_run_keeps_previous_record_on_api_error(data_dir):
    run(FakeClient(repos={"a/bb": repo_json("a/bb", 7), "b/uo": repo_json("b/uo")}), data_dir, "2026-10-18", "t1")

    run(FakeClient(repos={"b/uo": repo_json("b/uo")}, fail={"a/bb"}), data_dir, "2026-10-19", "t2")

    record = load(data_dir, "github.json")["repos"]["a/bb"]
    assert record["stars"] == 7
    assert record["missing"] is False


def test_run_detects_status_change(data_dir):
    repos = {"a/bb": repo_json("a/bb"), "b/uo": repo_json("b/uo")}
    run(FakeClient(repos=repos, readmes={"a/bb": "## Status\n\nalpha\n"}), data_dir, "2026-10-18", "t1")

    run(FakeClient(repos=repos, readmes={"a/bb": "## Status\n\nplayable\n"}), data_dir, "2026-10-19", "t2")

    assert load(data_dir, "github.json")["repos"]["a/bb"]["status_changed_at"] == "2026-10-19"


def test_run_writes_new_candidates_excluding_known_and_dismissed(data_dir):
    items = [repo_json("a/bb"), repo_json("x/dismissed"), repo_json("n/new"), {**repo_json("f/fork"), "fork": True}]
    client = FakeClient(repos={"a/bb": repo_json("a/bb"), "b/uo": repo_json("b/uo")}, search=items)

    run(client, data_dir, "2026-10-18", "t1")

    assert list(load(data_dir, "candidates.json")["candidates"]) == ["n/new"]
    assert len(client.queries) == len(SEARCH_QUERIES)


def test_run_treats_renamed_target_as_known(data_dir):
    client = FakeClient(repos={"a/bb": repo_json("a/bb-renamed"), "b/uo": repo_json("b/uo")},
                        search=[repo_json("a/bb-renamed")])

    run(client, data_dir, "2026-10-18", "t1")

    assert load(data_dir, "candidates.json")["candidates"] == {}


def test_run_survives_search_errors(data_dir):
    class Failing(FakeClient):
        def search_repos(self, query):
            raise GitHubError("rate limit")

    run(Failing(repos={"a/bb": repo_json("a/bb"), "b/uo": repo_json("b/uo")}), data_dir, "2026-10-18", "t1")

    assert load(data_dir, "candidates.json")["candidates"] == {}


def test_run_rejects_invalid_data(data_dir):
    (data_dir / "follows.json").write_text(json.dumps({"follows": ["ghost"]}))

    with pytest.raises(ValueError, match="ghost"):
        run(FakeClient(), data_dir, "2026-10-18", "t1")
