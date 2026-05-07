from groq import Groq

from app.config import settings


SYSTEM_PROMPT = """
You are JX JARVIS, a cinematic desktop AI assistant.
Personality: intelligent, calm, precise, friendly, futuristic, and concise.
Style: sound like an advanced onboard assistant, but do not overdo theatrics.
When useful, give direct steps. Keep spoken responses natural and brief.
Do not dump full source code in chat for build/create/write-code requests.
If a coding command reaches this chat path, answer briefly: "I should create that in VS Code. Try again with: write code for <project>."
"""

CODE_PROJECT_PROMPT = """
You are JX JARVIS writing code directly into a local VS Code workspace.
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
- Create a small, runnable starter project for the user's request.
- Include complete code, not placeholders.
- Prefer plain HTML/CSS/JS for websites and small apps unless the user asks for another stack.
- Prefer Python for scripts unless the user asks for another language.
- Keep it focused: 1 to 6 files.
- Add comments only where they help.
- Never include secrets, malware, destructive scripts, credential theft, or hidden persistence.
"""


def ask_groq(user_text: str, language_instruction: str = "Reply in English.") -> str:
    if not settings.groq_api_key:
        return (
            "GROQ API key is not configured. Add GROQ_API_KEY to your .env file, "
            "then restart JX JARVIS."
        )

    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=settings.groq_model,
        temperature=0.72,
        max_tokens=700,
        messages=[
            {"role": "system", "content": f"{SYSTEM_PROMPT.strip()}\n{language_instruction}".strip()},
            {"role": "user", "content": user_text},
        ],
    )
    return completion.choices[0].message.content.strip()


def ask_groq_code_project(user_text: str) -> str:
    if not settings.groq_api_key:
        return (
            '{"project_name":"missing-groq-key","summary":"Groq API key is not configured.",'
            '"files":[{"path":"README.md","content":"Add GROQ_API_KEY to .env, restart JX JARVIS, then ask again."}]}'
        )

    client = Groq(api_key=settings.groq_api_key)
    messages = [
        {"role": "system", "content": CODE_PROJECT_PROMPT.strip()},
        {"role": "user", "content": user_text},
    ]
    try:
        completion = client.chat.completions.create(
            model=settings.groq_model,
            temperature=0.35,
            max_tokens=2600,
            response_format={"type": "json_object"},
            messages=messages,
        )
    except Exception as error:
        if "response_format" not in str(error).lower() and "json" not in str(error).lower():
            raise
        completion = client.chat.completions.create(
            model=settings.groq_model,
            temperature=0.35,
            max_tokens=2600,
            messages=messages,
        )
    return completion.choices[0].message.content.strip()
