from __future__ import annotations

from pathlib import Path

from app.config import BACKEND_DIR
from docs.architecture_docs import architecture_markdown
from docs.developer_guides import developer_guide_markdown
from docs.plugin_docs import plugin_markdown
from docs.workflow_docs import workflow_markdown


OUTPUT_DIR = BACKEND_DIR / "runtime" / "generated_docs"


def generate_docs(app=None) -> dict:
    from docs.api_docs import api_markdown

    docs = {
        "architecture.md": architecture_markdown(),
        "api.md": api_markdown(app),
        "workflows.md": workflow_markdown(),
        "plugins.md": plugin_markdown(),
        "developer-guide.md": developer_guide_markdown(),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in docs.items():
        path = OUTPUT_DIR / name
        path.write_text(content, encoding="utf-8")
        written.append(str(path))
    return {"ok": True, "files": written}
