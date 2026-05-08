from api.browser_automation import browser_operator
from api.system_tasks import extract_google_search, extract_youtube_search


def run_browser_command(text: str) -> str | None:
    youtube_query = extract_youtube_search(text)
    if youtube_query:
        result = browser_operator.run_async(f"open YouTube and search {youtube_query}")
        return result["response"]

    google_query = extract_google_search(text)
    if google_query:
        result = browser_operator.run_async(f"search Google for {google_query}")
        return result["response"]

    lowered = text.lower()
    if any(phrase in lowered for phrase in ("open website", "navigate to", "go to", "click ", "scroll", "summarize page")):
        result = browser_operator.run_async(text)
        return result["response"]

    return None
