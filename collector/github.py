"""Cliente mínimo de la API REST de GitHub (solo lectura, sin dependencias)."""
import http.client
import json
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
TIMEOUT_S = 20


class GitHubError(Exception):
    """Fallo de la API distinto de 404 (rate limit, red, 5xx…)."""


class GitHubClient:
    def __init__(self, token=None):
        self.token = token

    def _get(self, path, params=None, accept="application/vnd.github+json"):
        url = f"{API}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "portradar"})
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            raise GitHubError(f"{url}: HTTP {err.code}") from err
        except urllib.error.URLError as err:
            raise GitHubError(f"{url}: {err.reason}") from err
        except (OSError, http.client.HTTPException) as err:
            raise GitHubError(f"{url}: {type(err).__name__}") from err

    def _get_json(self, path, params=None):
        body = self._get(path, params)
        if body is None:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError as err:
            raise GitHubError(f"{path}: respuesta no es JSON") from err

    def get_repo(self, repo):
        return self._get_json(f"/repos/{repo}")

    def get_releases(self, repo):
        """La release más reciente (incluye prereleases y nightlies) o lista vacía."""
        return self._get_json(f"/repos/{repo}/releases", {"per_page": 1}) or []

    def get_readme(self, repo):
        body = self._get(f"/repos/{repo}/readme", accept="application/vnd.github.raw")
        return None if body is None else body.decode("utf-8", errors="replace")

    def search_repos(self, query):
        params = {"q": f"{query} fork:false", "sort": "updated", "order": "desc", "per_page": 30}
        return (self._get_json("/search/repositories", params) or {}).get("items", [])
