from api.ai_provider import ask_ai_code_project
from api.code_writer import create_code_project, extract_code_request


def run_code_generation(text: str) -> str | None:
    request = extract_code_request(text)
    if not request:
        return None

    model_response = ask_ai_code_project(request)
    return create_code_project(request, model_response)
