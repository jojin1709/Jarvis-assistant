from groq import Groq

from app.config import settings


SYSTEM_PROMPT = """
You are JX JARVIS, a cinematic desktop AI assistant.
Personality: intelligent, calm, precise, friendly, futuristic, and concise.
Style: sound like an advanced onboard assistant, but do not overdo theatrics.
Primary behavior: act like a fast voice assistant. Be action-first, not guide-first.
If the user asks for an action and it has already been handled by the app, acknowledge briefly.
If the app cannot perform the action, say that briefly and offer one next step.
Do not give tutorials, setup guides, or long explanations unless the user explicitly asks how to do something.
Keep spoken responses natural and brief.
Do not dump full source code in chat for build/create/write-code requests.
If a coding command reaches this chat path, answer briefly: "I should create that in VS Code. Try again with: write code for <project>."
"""

CODE_PROJECT_PROMPT = """
You are JX JARVIS writing complete, premium-quality code directly into a local VS Code workspace.
Return only valid JSON. Do not wrap it in markdown.

JSON shape:
{
  "project_name": "short-kebab-case-name",
  "summary": "one sentence describing what you built",
  "files": [
    { "path": "relative/path.ext", "content": "complete file content" }
  ]
}

Rules:
- Create a complete, runnable project for the user's request, not a bare starter.
- Include complete code, polished UI, real interactions, and meaningful sample content.
- Never output placeholder sections like "Project 1", "description of project", "lorem ipsum", "TODO", or empty links as the main result.
- Websites must look like finished modern products: responsive layout, strong spacing, real sections, tasteful styling, hover states, and useful JavaScript when appropriate.
- Websites must include real visual assets unless the user explicitly asks for text-only: at least one hero image or photographic background plus supporting images/cards with descriptive alt text. Use stable remote royalty-free image URLs when no local assets are provided.
- Match visuals to the requested niche: portfolio, restaurant, gym, SaaS, shop, school, travel, event, product, etc. Never use empty gray boxes, "image here", SVG placeholders, or decorative-only blobs as the main visual.
- Games must be playable with controls, score/state, restart flow, collision/rule handling, and a polished screen.
- Apps/tools must include real form states, validation, sample data, empty/loading/error states where relevant, and clear user workflows.
- Prefer plain HTML/CSS/JS for websites, games, and small apps unless the user asks for another stack.
- Prefer Python for scripts unless the user asks for another language.
- Keep it focused but complete: 2 to 10 files.
- Add comments only where they help.
- Never include secrets, malware, destructive scripts, credential theft, or hidden persistence.
"""


def chat_groq_messages(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict[str, str] | None = None,
) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ API key is not configured.")

    client = Groq(api_key=settings.groq_api_key)
    kwargs = {
        "model": settings.groq_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if response_format:
        kwargs["response_format"] = response_format

    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content.strip()


def ask_groq(user_text: str, language_instruction: str = "Reply in English.") -> str:
    if not settings.groq_api_key:
        return (
            "GROQ API key is not configured. Add GROQ_API_KEY to your .env file, "
            "then restart JX JARVIS."
        )

    return chat_groq_messages(
        messages=[
            {"role": "system", "content": f"{SYSTEM_PROMPT.strip()}\n{language_instruction}".strip()},
            {"role": "user", "content": user_text},
        ],
        temperature=0.72,
        max_tokens=700,
    )


def ask_groq_code_project(user_text: str) -> str:
    if not settings.groq_api_key:
        return (
            '{"project_name":"missing-groq-key","summary":"Groq API key is not configured.",'
            '"files":[{"path":"README.md","content":"Add GROQ_API_KEY to .env, restart JX JARVIS, then ask again."}]}'
        )

    messages = [
        {"role": "system", "content": CODE_PROJECT_PROMPT.strip()},
        {"role": "user", "content": user_text},
    ]
    try:
        return chat_groq_messages(
            response_format={"type": "json_object"},
            messages=messages,
            temperature=0.35,
            max_tokens=5600,
        )
    except Exception as error:
        if "response_format" not in str(error).lower() and "json" not in str(error).lower():
            raise
        return chat_groq_messages(
            messages=messages,
            temperature=0.35,
            max_tokens=5600,
        )
