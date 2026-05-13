from __future__ import annotations

from legal.disclaimer_manager import browser_automation_disclosure, safe_execution_disclaimer
from legal.privacy_policy_generator import generate_privacy_policy


def legal_documents() -> dict:
    return {
        "privacyPolicy": generate_privacy_policy(),
        "safeExecution": safe_execution_disclaimer(),
        "browserAutomation": browser_automation_disclosure(),
        "pluginSecurity": "Plugins run under Jarvis permission scopes and should be reviewed before enabling. Untrusted plugins must not receive filesystem, terminal, browser, or credential access.",
        "localStorage": "Local runtime data is kept under backend/runtime and can be cleared or backed up by the user.",
    }
