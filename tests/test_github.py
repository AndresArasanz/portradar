import io
import json
import urllib.error

import pytest

from collector import github
from collector.github import GitHubClient, GitHubError


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code):
    return urllib.error.HTTPError("https://api.github.com/x", code, "err", {}, io.BytesIO(b""))


@pytest.fixture
def calls(monkeypatch):
    recorded = []
    responses = []

    def fake_urlopen(request, timeout):
        recorded.append(request)
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return FakeResponse(result)

    monkeypatch.setattr(github.urllib.request, "urlopen", fake_urlopen)
    return recorded, responses


def test_get_repo_sends_token_and_parses_json(calls):
    recorded, responses = calls
    responses.append(json.dumps({"full_name": "a/b"}).encode())

    result = GitHubClient(token="tkn").get_repo("a/b")

    assert result == {"full_name": "a/b"}
    assert recorded[0].full_url == "https://api.github.com/repos/a/b"
    assert recorded[0].get_header("Authorization") == "Bearer tkn"


def test_no_token_sends_no_auth_header(calls):
    recorded, responses = calls
    responses.append(b"{}")

    GitHubClient(token=None).get_repo("a/b")

    assert recorded[0].get_header("Authorization") is None


def test_404_returns_none(calls):
    _, responses = calls
    responses.append(_http_error(404))

    assert GitHubClient().get_repo("a/b") is None


def test_other_http_errors_raise(calls):
    _, responses = calls
    responses.append(_http_error(500))

    with pytest.raises(GitHubError):
        GitHubClient().get_repo("a/b")


def test_network_errors_raise(calls):
    _, responses = calls
    responses.append(urllib.error.URLError("down"))

    with pytest.raises(GitHubError):
        GitHubClient().get_repo("a/b")


def test_releases_missing_repo_returns_empty_list(calls):
    _, responses = calls
    responses.append(_http_error(404))

    assert GitHubClient().get_releases("a/b") == []


def test_releases_uses_newest_first_endpoint(calls):
    recorded, responses = calls
    responses.append(b"[]")

    GitHubClient().get_releases("a/b")

    assert recorded[0].full_url == "https://api.github.com/repos/a/b/releases?per_page=1"


def test_readme_returns_raw_text_or_none(calls):
    recorded, responses = calls
    responses.extend(["# Hola ñ".encode(), _http_error(404)])

    assert GitHubClient().get_readme("a/b") == "# Hola ñ"
    assert GitHubClient().get_readme("a/b") is None
    assert recorded[0].get_header("Accept") == "application/vnd.github.raw"


def test_search_returns_items_and_excludes_forks_in_query(calls):
    recorded, responses = calls
    responses.append(json.dumps({"items": [{"full_name": "a/b"}]}).encode())

    items = GitHubClient().search_repos("ps4 pc port")

    assert items == [{"full_name": "a/b"}]
    assert "fork%3Afalse" in recorded[0].full_url
    assert "ps4+pc+port" in recorded[0].full_url


@pytest.mark.parametrize("exc", [TimeoutError("t"), ConnectionResetError("r"), github.http.client.IncompleteRead(b"")])
def test_low_level_network_errors_raise_github_error(calls, exc):
    _, responses = calls
    responses.append(exc)

    with pytest.raises(GitHubError):
        GitHubClient().get_repo("a/b")


def test_invalid_json_raises_github_error(calls):
    _, responses = calls
    responses.append(b"<html>no json</html>")

    with pytest.raises(GitHubError):
        GitHubClient().get_repo("a/b")
