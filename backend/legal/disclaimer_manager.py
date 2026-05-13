from __future__ import annotations


def safe_execution_disclaimer() -> dict:
    return {
        "title": "Safe autonomous execution",
        "body": "Jarvis can run terminal, browser, desktop, coding, and security workflows. Destructive commands, unsafe filesystem operations, credential access, and external scans require explicit user permission and should only be run against systems you own or are authorized to test.",
        "requiresConsent": ["desktopAutomation", "browserAutomation", "securityTooling", "pluginExecution"],
    }


def browser_automation_disclosure() -> dict:
    return {
        "title": "Browser automation disclosure",
        "body": "Jarvis may control a persistent browser profile only after the user enables this capability. It must not bypass captchas, evade anti-bot systems, automate account creation, or extract raw cookies.",
    }
