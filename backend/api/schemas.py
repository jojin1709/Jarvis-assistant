from dataclasses import dataclass


@dataclass
class ChatRequest:
    text: str
    speak: bool = True


@dataclass
class SpeakRequest:
    text: str


@dataclass
class AssistantResponse:
    transcript: str
    response: str
    audio_file: str | None = None
    status: str = "online"


@dataclass
class StatusResponse:
    status: str
    detail: str
