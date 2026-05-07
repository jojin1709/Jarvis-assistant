import secrets
from dataclasses import dataclass
from typing import Callable


@dataclass
class PendingApproval:
    token: str
    label: str
    action: Callable[[], str]


_pending: PendingApproval | None = None


CONFIRM_PHRASES = {
    "yes",
    "yes do it",
    "confirm",
    "confirmed",
    "approve",
    "approved",
    "go ahead",
    "do it",
}

CANCEL_PHRASES = {
    "no",
    "cancel",
    "stop",
    "abort",
    "never mind",
    "nevermind",
}


def request_approval(label: str, action: Callable[[], str]) -> str:
    global _pending
    token = secrets.token_hex(3).upper()
    _pending = PendingApproval(token=token, label=label, action=action)
    return f"Confirmation required for: {label}. Say confirm {token} or type confirm {token}."


def resolve_approval(text: str) -> str | None:
    global _pending
    if not _pending:
        return None

    normalized = " ".join(text.lower().strip().split())
    token = _pending.token.lower()

    if normalized in CANCEL_PHRASES or "cancel" in normalized:
        label = _pending.label
        _pending = None
        return f"Cancelled: {label}."

    if token in normalized or normalized in CONFIRM_PHRASES:
        pending = _pending
        _pending = None
        return pending.action()

    return None


def pending_approval_label() -> str | None:
    return _pending.label if _pending else None
