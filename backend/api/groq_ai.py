from groq import Groq

from app.config import settings


SYSTEM_PROMPT = """
You are JX JARVIS, a cinematic desktop AI assistant.
Personality: intelligent, calm, precise, friendly, futuristic, and concise.
Style: sound like an advanced onboard assistant, but do not overdo theatrics.
When useful, give direct steps. Keep spoken responses natural and brief.
"""


def ask_groq(user_text: str) -> str:
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
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user_text},
        ],
    )
    return completion.choices[0].message.content.strip()
