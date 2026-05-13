from __future__ import annotations

from urllib.request import Request, urlopen


def inspect_github_repo(owner: str, repo: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        request = Request(url, headers={"User-Agent": "JX-Jarvis/1.0"})
        with urlopen(request, timeout=12) as response:
            import json

            data = json.loads(response.read().decode("utf-8"))
        return {
            "ok": True,
            "repo": f"{owner}/{repo}",
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "openIssues": data.get("open_issues_count"),
            "language": data.get("language"),
            "description": data.get("description"),
            "updatedAt": data.get("updated_at"),
        }
    except Exception as error:
        return {"ok": False, "repo": f"{owner}/{repo}", "error": str(error)}
