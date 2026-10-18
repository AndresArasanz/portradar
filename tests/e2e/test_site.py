import base64
import functools
import http.server
import json
import subprocess
import threading
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
REPO_API = "https://api.github.com/repos/AndresArasanz/portradar"

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def site_url(tmp_path_factory):
    site = tmp_path_factory.mktemp("site")
    subprocess.run([str(ROOT / "scripts" / "build_site.sh"), str(site)], check=True, capture_output=True)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
    handler.log_message = lambda *a: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    pg = context.new_page()
    pg.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=""))
    pg.route("**/actions/workflows/update.yml/runs**",
             lambda r: r.fulfill(status=200, json={"workflow_runs": [{"updated_at": "2099-01-01T00:00:00Z"}]}))
    pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
    yield pg
    context.close()


def _contents(name):
    raw = (DATA / name).read_bytes()
    return {"sha": f"sha-{name}", "content": base64.b64encode(raw).decode()}


def _fake_github(page, puts):
    def handle(route):
        req = route.request
        if req.method == "PUT":
            puts.append((req.url, json.loads(req.post_data)))
            return route.fulfill(status=200, json={})
        if "/contents/data/" in req.url:
            name = req.url.split("/contents/data/")[1].split("?")[0]
            return route.fulfill(status=200, json=_contents(name))
        return route.fulfill(status=200, json={"permissions": {"push": True}})

    page.route(f"{REPO_API}**", handle)


def test_all_tab_lists_every_port_read_only(page, site_url):
    page.goto(site_url)
    page.get_by_role("tab", name="Todos").click()

    ports = json.loads((DATA / "ports.json").read_text())["ports"]
    expect(page.locator("#rows tr")).to_have_count(len(ports))
    expect(page.locator(".star")).to_have_count(0)
    expect(page.locator("#warning")).to_be_in_viewport()
    assert page.errors == []


def test_following_tab_shows_only_followed(page, site_url):
    page.goto(site_url)

    follows = json.loads((DATA / "follows.json").read_text())["follows"]
    expect(page.locator("#rows tr")).to_have_count(len(follows))
    assert sorted(page.locator("#rows tr").evaluate_all("rs => rs.map(r => r.dataset.id)")) == sorted(follows)


def test_search_filters_rows(page, site_url):
    page.goto(site_url)
    page.get_by_role("tab", name="Todos").click()
    page.fill("#q", "hayatog")

    expect(page.locator("#rows tr")).to_have_count(3)


def test_author_status_is_shown(page, site_url):
    page.goto(site_url)
    page.get_by_role("tab", name="Todos").click()

    expect(page.locator('tr[data-id="ctr-nitro-fueled"] .author-status')).to_contain_text("playable")


def test_review_tab_lists_candidates_without_actions(page, site_url):
    page.goto(site_url)
    page.get_by_role("tab", name="Sin revisar").click()

    expect(page.locator(".card").first).to_be_visible()
    expect(page.locator("#panel-table")).to_be_hidden()
    expect(page.get_by_role("button", name="Aceptar")).to_have_count(0)


def test_fork_badge_names_the_parent(page, site_url):
    page.goto(site_url)

    expect(page.locator('tr[data-id="bloodborne"] .badge')).to_contain_text("fork de deadinside28/bloodborne_pc")


def test_follow_with_token_commits_follows_json(page, site_url):
    puts = []
    _fake_github(page, puts)
    page.add_init_script("localStorage.setItem('portradar-token', 'github_pat_fake')")
    page.goto(site_url)
    page.get_by_role("tab", name="Todos").click()

    with page.expect_request(lambda r: r.method == "PUT"):
        page.get_by_role("button", name="Seguir P.T.").click()

    expect(page.get_by_role("button", name="Dejar de seguir P.T.")).to_be_enabled()
    url, body = puts[0]
    assert url.endswith("/contents/data/follows.json")
    assert "pt" in json.loads(base64.b64decode(body["content"]))["follows"]
    assert body["sha"] == "sha-follows.json"


def test_dismiss_candidate_commits_review_json(page, site_url):
    puts = []
    _fake_github(page, puts)
    page.add_init_script("localStorage.setItem('portradar-token', 'github_pat_fake')")
    page.goto(site_url)
    page.get_by_role("tab", name="Sin revisar").click()
    first = page.locator(".card").first
    repo = first.get_attribute("data-repo")

    with page.expect_request(lambda r: r.method == "PUT"):
        first.get_by_role("button", name="Descartar").click()

    expect(page.locator(f'.card[data-repo="{repo}"]')).to_have_count(0)
    url, body = puts[0]
    assert url.endswith("/contents/data/review.json")
    assert repo in json.loads(base64.b64decode(body["content"]))["dismissed"]


def test_failed_write_reverts_and_shows_error(page, site_url):
    page.route(f"{REPO_API}/contents/**", lambda r: r.fulfill(status=403, json={"message": "nope"})
               if r.request.method == "PUT" else r.fulfill(status=200, json=_contents(r.request.url.split("/contents/data/")[1].split("?")[0])))
    page.add_init_script("localStorage.setItem('portradar-token', 'github_pat_fake')")
    page.goto(site_url)
    page.get_by_role("tab", name="Todos").click()

    page.get_by_role("button", name="Seguir P.T.").click()

    expect(page.locator("#error")).to_contain_text("403")
    expect(page.get_by_role("button", name="Seguir P.T.")).to_be_visible()


def test_failed_write_only_reverts_its_own_change(page, site_url):
    def handle(route):
        req = route.request
        if req.method == "PUT":
            follows = json.loads(base64.b64decode(json.loads(req.post_data)["content"]))["follows"]
            ok = "uncharted" in follows
            return route.fulfill(status=200 if ok else 403, json={} if ok else {"message": "nope"})
        return route.fulfill(status=200, json=_contents(req.url.split("/contents/data/")[1].split("?")[0]))

    page.route(f"{REPO_API}/contents/**", handle)
    page.add_init_script("localStorage.setItem('portradar-token', 'github_pat_fake')")
    page.goto(site_url)
    page.get_by_role("tab", name="Todos").click()

    page.get_by_role("button", name="Seguir P.T.").click()
    page.get_by_role("button", name="Seguir Uncharted: The Nathan Drake Collection").click()

    expect(page.locator("#error")).to_contain_text("403")
    expect(page.get_by_role("button", name="Seguir P.T.")).to_be_visible()
    expect(page.get_by_role("button", name="Dejar de seguir Uncharted: The Nathan Drake Collection")).to_be_visible()


def test_csp_allows_the_page_to_work(page, site_url):
    page.goto(site_url)

    expect(page.locator("#rows tr").first).to_be_visible()
    assert not [e for e in page.errors if "Content Security Policy" in e]


def test_header_shows_last_check_from_workflow_runs(page, site_url):
    page.goto(site_url)

    expect(page.locator("#snap")).to_contain_text("Comprobado en GitHub")


def test_header_falls_back_to_data_date_when_runs_api_fails(page, site_url):
    page.route("**/actions/workflows/update.yml/runs**", lambda r: r.fulfill(status=403, json={}))
    page.goto(site_url)

    expect(page.locator("#snap")).to_contain_text("Datos de GitHub actualizados")
