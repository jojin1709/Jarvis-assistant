from __future__ import annotations

import importlib.util
import logging
from pathlib import Path


log = logging.getLogger(__name__)
_plugins: dict[str, object] = {}


def load_plugins(plugin_dir: Path | None = None) -> dict[str, object]:
    if plugin_dir is None:
        plugin_dir = Path(__file__).resolve().parents[1] / "runtime" / "plugins"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    for file in sorted(plugin_dir.glob("*.py")):
        name = file.stem
        if name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{name}", file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load plugin spec for {file}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _plugins[name] = module
            log.info("Plugin loaded: %s", name)
        except Exception as error:
            log.warning("Plugin failed to load: %s - %s", name, error)

    return dict(_plugins)


def get_plugins() -> dict[str, object]:
    return dict(_plugins)
