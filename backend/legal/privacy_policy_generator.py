from __future__ import annotations


def generate_privacy_policy() -> str:
    return """# Jarvis Privacy Policy

Jarvis is local-first. Core workflows, memory, browser profiles, provider sessions, logs, and skills are stored on the user's machine unless the user explicitly enables optional integrations.

Optional cloud sync uses user-owned providers such as Google Drive, Dropbox, or OneDrive. Jarvis does not require centralized Jarvis cloud infrastructure.

Jarvis must not sync raw browser cookies, plaintext credentials, provider key stores, `.env` files, virtual environments, or operating-system secrets. Sensitive backup bundles are encrypted before upload.

Telemetry is optional, disabled by default, and user-controlled. Local diagnostics can be reviewed before sharing.
"""
