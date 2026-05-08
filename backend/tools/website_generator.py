from api.ai_provider import ask_ai_code_project
from api.code_writer import create_code_project, create_portfolio_project, extract_code_request, is_portfolio_request


WEBSITE_WORDS = ("website", "web site", "webpage", "web page", "landing page", "portfolio")
BUILD_WORDS = ("build", "create", "make", "generate", "develop", "design")


def run_website_generation(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())
    if not any(word in normalized for word in WEBSITE_WORDS):
        return None
    if not any(word in normalized for word in BUILD_WORDS):
        return None

    request = extract_code_request(text) or text
    if is_portfolio_request(request):
        return create_portfolio_project(request)

    model_response = ask_ai_code_project(request)
    return create_code_project(request, model_response)
