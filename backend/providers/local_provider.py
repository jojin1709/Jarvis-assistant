from providers.openai_provider import chat as openai_compatible_chat
from providers.base_provider import ProviderResult


def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None, base_url: str = "http://127.0.0.1:8080/v1") -> tuple[str, float]:
    return openai_compatible_chat(
        messages,
        api_key or "local",
        model,
        temperature,
        max_tokens,
        response_format=response_format,
        base_url=base_url,
    )


class LocalModelProvider:
    id = "local_model"
    label = "Local Model"

    def ask(self, messages: list[dict[str, str]], model: str, base_url: str, temperature: float, max_tokens: int) -> ProviderResult:
        try:
            content, latency = chat(messages, "local", model, temperature, max_tokens, base_url=base_url)
            return ProviderResult(ok=True, provider=self.id, response=content, latency_ms=latency, source="local")
        except Exception as error:
            return ProviderResult(ok=False, provider=self.id, error=str(error), source="local")
