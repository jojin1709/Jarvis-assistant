# Security Policy

## API Keys

Do not commit real API keys to this repository.

Use `.env.example` as the template and keep your real `.env` file local. The `.gitignore` file is configured to ignore `.env` and other secret-style environment files.

If a real key is pushed by mistake:

1. Delete the key from the provider dashboard.
2. Create a new key.
3. Remove the leaked key from Git history before making the repository public.

## Local System Actions

JX JARVIS only runs allowlisted desktop tasks. It does not execute arbitrary shell commands from AI responses.

The allowlist is implemented in:

```text
backend/api/system_tasks.py
```

To disable local desktop actions:

```env
JX_JARVIS_ENABLE_SYSTEM_TASKS=false
```

## Uploaded Files

Uploaded files are stored locally in:

```text
backend/runtime/uploads/
```

This folder is ignored by Git and should not be committed.
