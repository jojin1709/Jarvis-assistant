from __future__ import annotations

from api.browser_automation import browser_operator


def browser_context() -> dict:
    state = browser_operator.state()
    dom = state.get("domSummary") or {}
    return {
        "state": state,
        "interactiveElements": {
            "inputs": len(dom.get("inputs") or []),
            "buttons": len(dom.get("buttons") or []),
            "links": len(dom.get("links") or []),
        },
    }
