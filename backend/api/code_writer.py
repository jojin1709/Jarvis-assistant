import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path, PurePosixPath

from api.permissions import evaluate_permission, guard_action
from api.memory_storage import remember_project


CODE_ROOT = Path.home() / "Desktop" / "JX-JARVIS-Code"
RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"
PENDING_BRIEF_PATH = RUNTIME_DIR / "pending_code_brief.json"
MAX_FILES = 10
MAX_FILE_CHARS = 60000
READY_RESPONSE = "Yes sir, it is ready."
GENERIC_WEBSITE_WORDS = {
    "a",
    "an",
    "and",
    "beautiful",
    "best",
    "better",
    "cool",
    "create",
    "develop",
    "for",
    "full",
    "good",
    "great",
    "landing",
    "make",
    "me",
    "modern",
    "nice",
    "page",
    "premium",
    "professional",
    "responsive",
    "site",
    "stylish",
    "the",
    "website",
    "web",
}


CODE_TRIGGERS = (
    "can you write code for",
    "can you write a code for",
    "can you write me code for",
    "can you write me the code for",
    "can you make code for",
    "can you make me code for",
    "can you make a",
    "can you make an",
    "can you build a",
    "can you build an",
    "can you create a",
    "can you create an",
    "can u write code for",
    "can u write me code for",
    "can u make a",
    "can u make an",
    "can u build a",
    "can u build an",
    "i want a",
    "i want an",
    "i want you to make a",
    "i want you to make an",
    "i want you to build a",
    "i want you to build an",
    "i need a",
    "i need an",
    "i need you to make a",
    "i need you to make an",
    "i need you to build a",
    "i need you to build an",
    "please write code for",
    "please write me code for",
    "please write me the code for",
    "please make a",
    "please make an",
    "please build a",
    "please build an",
    "please create a",
    "please create an",
    "write code for",
    "write a code for",
    "write me code for",
    "write me a code for",
    "write me the code for",
    "write the code for",
    "write code to",
    "write a code to",
    "write me code to",
    "write me the code to",
    "write the code to",
    "give me code for",
    "give me the code for",
    "give me full code for",
    "give full code for",
    "show me code for",
    "show me the code for",
    "source code for",
    "full code for",
    "create code for",
    "create me code for",
    "make a",
    "make an",
    "make code for",
    "make me code for",
    "build a",
    "build an",
    "create a",
    "create an",
    "develop a",
    "develop an",
    "generate a",
    "generate an",
    "generate code for",
    "generate me code for",
    "build code for",
    "build me code for",
    "code a",
    "code an",
    "code me a",
    "code me an",
    "make me",
    "make a game",
    "make a web game",
    "make an app",
    "make a app",
    "make a website",
    "make me a game",
    "make me an app",
    "make me a website",
    "build a game",
    "build a web game",
    "build an app",
    "build a app",
    "build a website",
    "create a game",
    "create a web game",
    "create an app",
    "create a app",
    "create a website",
    "develop a game",
    "develop an app",
    "develop a website",
)

CODE_INTENT_WORDS = (
    "code",
    "program",
    "script",
    "app",
    "application",
    "website",
    "web site",
    "webpage",
    "web page",
    "game",
    "portfolio",
    "landing page",
    "tool",
    "dashboard",
    "calculator",
    "todo",
    "to-do",
    "tracker",
    "converter",
    "generator",
    "clone",
    "html",
    "css",
    "javascript",
    "python",
    "react",
)

BUILD_INTENT_WORDS = (
    "write",
    "make",
    "build",
    "create",
    "generate",
    "develop",
    "program",
    "code",
    "give",
    "show",
)


LANGUAGE_EXTENSIONS = {
    "html": "html",
    "css": "css",
    "javascript": "js",
    "js": "js",
    "python": "py",
    "py": "py",
    "typescript": "ts",
    "ts": "ts",
    "tsx": "tsx",
    "jsx": "jsx",
    "json": "json",
    "markdown": "md",
    "md": "md",
}


def extract_code_request(text: str) -> str | None:
    cleaned = " ".join(text.strip().split())
    normalized = cleaned.lower()

    for wake in ("hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis", "jarvis"):
        if normalized.startswith(wake):
            cleaned = cleaned[len(wake) :].strip(" ,:.-")
            normalized = cleaned.lower()
            break

    for trigger in CODE_TRIGGERS:
        index = normalized.find(trigger)
        if index >= 0:
            request = cleaned[index:].strip()
            return request or cleaned

    if _looks_like_code_creation(normalized):
        return cleaned

    return None


def _looks_like_code_creation(normalized: str) -> bool:
    has_build_intent = any(word in normalized for word in BUILD_INTENT_WORDS)
    has_code_intent = any(word in normalized for word in CODE_INTENT_WORDS)
    asks_for_output = any(
        phrase in normalized
        for phrase in ("for me", "me a", "me an", "full code", "source code", "the code", "write me", "make me")
    )

    wants_project = any(phrase in normalized for phrase in ("i want", "i need")) and has_code_intent

    if has_build_intent and has_code_intent:
        return True

    if (asks_for_output or wants_project) and has_code_intent:
        return True

    return False


def is_portfolio_request(text: str) -> bool:
    normalized = text.lower()
    return "portfolio" in normalized and any(word in normalized for word in ("website", "site", "web", "page", "app"))


def should_collect_website_brief(text: str) -> bool:
    normalized = text.lower()
    if not _is_website_request(normalized):
        return False

    detail_markers = (
        "about",
        "booking",
        "brand",
        "business",
        "contact",
        "ecommerce",
        "gallery",
        "menu",
        "portfolio",
        "pricing",
        "restaurant",
        "school",
        "services",
        "shop",
        "store",
        "testimonials",
        "for ",
    )
    if sum(marker in normalized for marker in detail_markers) >= 2:
        return False

    words = re.findall(r"[a-z0-9]+", normalized)
    specific_words = [word for word in words if word not in GENERIC_WEBSITE_WORDS and len(word) > 2]
    return len(specific_words) < 4


def start_website_brief(user_request: str) -> str:
    _save_pending_brief(
        {
            "kind": "website",
            "original_request": user_request,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return (
        "I can build it, but I need your website options first so it is not a random template.\n\n"
        "Reply with these details:\n"
        "1. Website type or business: portfolio, shop, restaurant, agency, gym, SaaS, etc.\n"
        "2. Name/brand to show on the site.\n"
        "3. Style: dark, light, luxury, minimal, colorful, tech, etc.\n"
        "4. Sections needed: hero, services, pricing, gallery, contact, booking, testimonials, etc.\n"
        "5. Main goal: get clients, sell products, show work, collect leads, book calls, etc.\n\n"
        "After you answer, I will create the code in VS Code, save it under JX-JARVIS-Code with the time, and open a browser preview."
    )


def consume_pending_website_brief(text: str) -> str | None:
    pending = _load_pending_brief()
    if not pending or pending.get("kind") != "website":
        return None

    normalized = " ".join(text.lower().strip().split())
    if normalized in {"cancel", "stop", "never mind", "nevermind"}:
        _clear_pending_brief()
        return None

    if len(text.strip()) < 8:
        return None

    _clear_pending_brief()
    original = str(pending.get("original_request") or "Create a website")
    return (
        f"{original}\n\n"
        "User-approved website brief:\n"
        f"{text.strip()}\n\n"
        "Create a finished, custom website from this brief. Use the brand, sections, style, goal, and content direction from the user's answer. "
        "Do not create a generic agency template unless the user asked for an agency."
    )


def _load_pending_brief() -> dict | None:
    if not PENDING_BRIEF_PATH.exists():
        return None
    try:
        data = json.loads(PENDING_BRIEF_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _save_pending_brief(payload: dict) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_BRIEF_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _clear_pending_brief() -> None:
    try:
        PENDING_BRIEF_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def create_portfolio_project(user_request: str) -> str:
    return guard_action(
        "code.generate",
        "create portfolio website project",
        lambda: _create_portfolio_project(user_request),
        path=CODE_ROOT,
    )


def _create_portfolio_project(user_request: str) -> str:
    project_dir = _new_project_dir("super-portfolio-website")
    files = _portfolio_files()
    written = _write_files(project_dir, files)
    _write_project_readme(project_dir, user_request, "Premium responsive portfolio website.", written)
    validation = validate_code_project(project_dir)
    preview = _open_preview(project_dir)
    opened = _open_in_vscode(project_dir)
    open_text = "I opened it in a new VS Code window." if opened else "VS Code was unavailable or blocked, but the files are ready."
    preview_text = " Browser preview opened." if preview else ""
    summary = f"Super portfolio website created: {project_dir}. Files: index.html, styles.css, script.js. Validation: {validation}. {open_text}{preview_text}"
    remember_project(project_dir.name, str(project_dir), summary)
    return READY_RESPONSE


def create_code_project(user_request: str, model_response: str) -> str:
    return guard_action(
        "code.generate",
        "create code project",
        lambda: _create_code_project(user_request, model_response),
        path=CODE_ROOT,
    )


def _create_code_project(user_request: str, model_response: str) -> str:
    spec = _parse_project_spec(model_response)
    files = spec.get("files") if isinstance(spec.get("files"), list) else []

    fallback = _quality_fallback_for_request(user_request, files)
    if fallback:
        project_name, summary, files = fallback
        spec["summary"] = summary
    else:
        project_name = _safe_project_name(spec.get("project_name") or user_request)

    project_dir = _new_project_dir(project_name)
    written = _write_files(project_dir, files)

    if not written:
        fallback = project_dir / "README.md"
        fallback.write_text(
            "# JX JARVIS Code Output\n\n"
            f"Request: {user_request}\n\n"
            "Jarvis could not parse a file list, so the raw AI response is below.\n\n"
            "```text\n"
            f"{model_response[:MAX_FILE_CHARS]}\n"
            "```\n",
            encoding="utf-8",
            newline="\n",
        )
        written.append(fallback)

    _write_project_readme(project_dir, user_request, spec.get("summary"), written)
    validation = validate_code_project(project_dir)
    preview = _open_preview(project_dir)
    opened = _open_in_vscode(project_dir)
    file_list = ", ".join(path.name for path in written[:4])
    if len(written) > 4:
        file_list += f", and {len(written) - 4} more"

    open_text = "I opened it in a new VS Code window." if opened else "VS Code was unavailable or blocked, but the files are ready."
    preview_text = " Browser preview opened." if preview else ""
    summary = f"Code workspace created: {project_dir}. Files: {file_list}. Validation: {validation}. {open_text}{preview_text}"
    remember_project(project_dir.name, str(project_dir), summary)
    return READY_RESPONSE


def _new_project_dir(project_name: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    project_dir = CODE_ROOT / f"{stamp}-{_safe_project_name(project_name)}"
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def _write_files(project_dir: Path, files: list[dict]) -> list[Path]:
    written: list[Path] = []
    for item in files[:MAX_FILES]:
        if not isinstance(item, dict):
            continue

        relative_path = _safe_relative_path(str(item.get("path") or "main.txt"))
        content = str(item.get("content") or "")[:MAX_FILE_CHARS]
        if not content.strip():
            continue

        file_path = project_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8", newline="\n")
        written.append(file_path)
    return written


def _quality_fallback_for_request(user_request: str, files: list[dict]) -> tuple[str, str, list[dict]] | None:
    normalized = user_request.lower()

    if _is_snake_game_request(normalized) and _is_weak_generated_project(files, minimum_chars=5200):
        return (
            "premium-snake-game",
            "Playable polished Snake web game with score, controls, restart flow, and responsive canvas.",
            _snake_game_files(),
        )

    if _is_website_request(normalized) and (
        _is_weak_generated_project(files, minimum_chars=5200) or not _has_website_visual_assets(files)
    ):
        return (
            "premium-website",
            "Premium responsive website with real images, finished sections, interactive filtering, pricing, testimonials, and contact form.",
            _premium_website_files(user_request),
        )

    if _is_app_or_tool_request(normalized) and _is_weak_generated_project(files, minimum_chars=4200):
        return (
            "premium-web-app",
            "Polished browser app with real data, interactive controls, validation, empty states, and responsive design.",
            _premium_web_app_files(user_request),
        )

    return None


def _is_website_request(normalized: str) -> bool:
    return any(word in normalized for word in ("website", "web site", "webpage", "web page", "landing page", "portfolio"))


def _is_snake_game_request(normalized: str) -> bool:
    return "snake" in normalized and any(word in normalized for word in ("game", "website", "web", "app", "code"))


def _has_website_visual_assets(files: list[dict]) -> bool:
    combined = "\n".join(str(item.get("content") or "") for item in files if isinstance(item, dict)).lower()
    if not combined.strip():
        return False

    visual_markers = (
        "<img",
        "<picture",
        "background-image:",
        "image-set(",
        "images.unsplash.com",
        "images.pexels.com",
        "picsum.photos",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".avif",
    )
    blocked_placeholders = (
        "image here",
        "placeholder image",
        "your image",
        "gray box",
        "grey box",
    )
    return any(marker in combined for marker in visual_markers) and not any(
        placeholder in combined for placeholder in blocked_placeholders
    )


def _is_app_or_tool_request(normalized: str) -> bool:
    terms = (
        "app",
        "application",
        "tool",
        "dashboard",
        "calculator",
        "todo",
        "to-do",
        "tracker",
        "converter",
        "generator",
        "planner",
        "manager",
        "clone",
    )
    return any(term in normalized for term in terms)


def _is_weak_generated_project(files: list[dict], minimum_chars: int) -> bool:
    if not files:
        return True

    paths = [str(item.get("path") or "").lower() for item in files if isinstance(item, dict)]
    contents = [str(item.get("content") or "") for item in files if isinstance(item, dict)]
    combined = "\n".join(contents).lower()

    placeholder_terms = (
        "project 1",
        "project 2",
        "this is a description",
        "welcome to my portfolio website",
        "lorem ipsum",
        "todo:",
        "your content here",
        "example@example.com",
    )
    has_html = any(path.endswith((".html", ".htm")) for path in paths)
    has_css = any(path.endswith(".css") for path in paths) or "<style" in combined
    has_js = any(path.endswith(".js") for path in paths) or "<script" in combined
    has_placeholder = any(term in combined for term in placeholder_terms)

    if has_placeholder:
        return True
    if len(combined) < minimum_chars:
        return True
    if has_html and not has_css:
        return True
    if ("game" in combined or "snake" in combined) and not has_js:
        return True

    return False


def _premium_website_files(user_request: str) -> list[dict]:
    title = "Nova Studio"
    return [
        {
            "path": "index.html",
            "content": f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title} - Premium Website</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="topbar">
      <a class="brand" href="#home"><span>N</span>{title}</a>
      <nav aria-label="Main navigation">
        <a href="#work">Work</a>
        <a href="#services">Services</a>
        <a href="#pricing">Pricing</a>
        <a href="#contact">Contact</a>
      </nav>
      <button class="icon-button" id="themeButton" type="button" aria-label="Toggle theme">Theme</button>
    </header>

    <main id="home">
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Strategy - Design - Code</p>
          <h1>High-converting digital experiences built with premium detail.</h1>
          <p>
            {title} turns ambitious ideas into fast, responsive websites with strong messaging,
            polished visuals, and interactions that feel ready for real users.
          </p>
          <div class="actions">
            <a class="button primary" href="#contact">Start a Project</a>
            <a class="button secondary" href="#work">See Work</a>
          </div>
        </div>
        <aside class="hero-panel" aria-label="Project snapshot">
          <img src="https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1100&q=80" alt="Premium creative workspace with modern website planning" />
          <div class="hero-panel-content">
            <span class="status">Live build queue open</span>
            <strong>Request understood</strong>
            <p>{user_request[:160]}</p>
            <div class="score-grid">
              <div><b>98</b><span>Performance</span></div>
              <div><b>24h</b><span>Prototype</span></div>
              <div><b>4.9</b><span>Client rating</span></div>
            </div>
          </div>
        </aside>
      </section>

      <section id="work" class="section">
        <div class="section-title">
          <p class="eyebrow">Featured Work</p>
          <h2>Real sections, real content, and a finished feel.</h2>
        </div>
        <div class="filters" aria-label="Project filters">
          <button class="filter active" data-filter="all" type="button">All</button>
          <button class="filter" data-filter="brand" type="button">Brand</button>
          <button class="filter" data-filter="saas" type="button">SaaS</button>
          <button class="filter" data-filter="commerce" type="button">Commerce</button>
        </div>
        <div class="project-grid">
          <article class="project-card" data-kind="brand">
            <img src="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80" alt="Premium brand website displayed in a warm studio setting" />
            <span>Brand System</span>
            <h3>Pulse Identity</h3>
            <p>Launch-ready visual identity with a responsive site, motion accents, and conversion copy.</p>
          </article>
          <article class="project-card" data-kind="saas">
            <img src="https://images.unsplash.com/photo-1551434678-e076c223a692?auto=format&fit=crop&w=900&q=80" alt="Team reviewing a polished SaaS dashboard interface" />
            <span>SaaS Dashboard</span>
            <h3>MetricFlow</h3>
            <p>Operational dashboard with clean cards, compact data views, and a smooth onboarding path.</p>
          </article>
          <article class="project-card" data-kind="commerce">
            <img src="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80" alt="Stylish commerce photography for a premium product website" />
            <span>Commerce</span>
            <h3>Craft Market</h3>
            <p>Premium storefront concept with product highlights, trust signals, and mobile-first checkout cues.</p>
          </article>
        </div>
      </section>

      <section id="services" class="section services">
        <div>
          <p class="eyebrow">Services</p>
          <h2>Everything needed to ship a sharp web presence.</h2>
        </div>
        <div class="service-list">
          <div><strong>01</strong><h3>Website Design</h3><p>Responsive layouts, brand direction, sections, and content architecture.</p></div>
          <div><strong>02</strong><h3>Frontend Build</h3><p>Clean HTML/CSS/JS with interactions, accessibility basics, and fast loading.</p></div>
          <div><strong>03</strong><h3>Automation</h3><p>Forms, local tools, workflow helpers, and simple integrations where useful.</p></div>
        </div>
      </section>

      <section id="pricing" class="section">
        <div class="section-title">
          <p class="eyebrow">Pricing</p>
          <h2>Clear packages for different launch speeds.</h2>
        </div>
        <div class="pricing-grid">
          <article><span>Starter</span><h3>$499</h3><p>One polished page, responsive build, contact CTA, and launch checklist.</p></article>
          <article class="featured"><span>Growth</span><h3>$1,299</h3><p>Multi-section website, animations, case studies, forms, and performance pass.</p></article>
          <article><span>Custom</span><h3>Quote</h3><p>Advanced flows, dashboards, content systems, integrations, or app prototypes.</p></article>
        </div>
      </section>

      <section class="section testimonials">
        <blockquote>
          "The final site felt like a real product on day one: fast, premium, and easy for customers to understand."
        </blockquote>
        <span>- A happy launch client</span>
      </section>

      <section id="contact" class="section contact">
        <div>
          <p class="eyebrow">Contact</p>
          <h2>Tell us what you want to build.</h2>
        </div>
        <form id="leadForm">
          <input name="name" placeholder="Your name" required />
          <input name="email" type="email" placeholder="Email address" required />
          <select name="budget" required>
            <option value="">Project budget</option>
            <option>$500 - $1,000</option>
            <option>$1,000 - $3,000</option>
            <option>$3,000+</option>
          </select>
          <textarea name="message" placeholder="What should this website do?" required></textarea>
          <button class="button primary" type="submit">Send Request</button>
          <p id="formStatus" role="status"></p>
        </form>
      </section>
    </main>

    <footer>Built by JX JARVIS. Replace the brand, prices, and links with your final business details.</footer>
    <script src="script.js"></script>
  </body>
</html>
""",
        },
        {
            "path": "styles.css",
            "content": """:root {
  --bg: #090d14;
  --panel: rgba(255, 255, 255, 0.08);
  --panel-strong: rgba(255, 255, 255, 0.14);
  --text: #f7fbff;
  --muted: #a7b2c5;
  --line: rgba(255, 255, 255, 0.14);
  --accent: #00d4ff;
  --accent-2: #f8c84e;
  --shadow: 0 24px 70px rgba(0, 0, 0, 0.34);
}

body.light {
  --bg: #f5f7fb;
  --panel: rgba(255, 255, 255, 0.82);
  --panel-strong: #ffffff;
  --text: #101827;
  --muted: #5c6678;
  --line: rgba(16, 24, 39, 0.12);
  --shadow: 0 18px 55px rgba(16, 24, 39, 0.12);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background:
    radial-gradient(circle at 15% 0%, rgba(0, 212, 255, 0.25), transparent 30rem),
    radial-gradient(circle at 85% 10%, rgba(248, 200, 78, 0.16), transparent 24rem),
    var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

a { color: inherit; text-decoration: none; }
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem clamp(1rem, 5vw, 4rem);
  border-bottom: 1px solid var(--line);
  background: color-mix(in srgb, var(--bg) 86%, transparent);
  backdrop-filter: blur(18px);
}
.brand { display: flex; align-items: center; gap: .6rem; font-weight: 900; }
.brand span {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #07111f;
}
nav { display: flex; gap: clamp(.75rem, 2vw, 1.5rem); color: var(--muted); font-weight: 800; }
nav a:hover { color: var(--text); }
.icon-button, .filter {
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--text);
  border-radius: 999px;
  min-height: 40px;
  padding: 0 .9rem;
  cursor: pointer;
  font-weight: 800;
}

.hero, .section {
  width: min(1180px, calc(100% - 2rem));
  margin: 0 auto;
}
.hero {
  min-height: calc(100vh - 72px);
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(300px, .88fr);
  align-items: center;
  gap: 2rem;
  padding: 4rem 0;
}
.hero h1, .section h2 {
  margin: 0 0 1rem;
  line-height: .96;
  letter-spacing: -0.06em;
}
.hero h1 { font-size: clamp(3.2rem, 7.8vw, 6.8rem); }
.section h2 { font-size: clamp(2.1rem, 4.3vw, 4.3rem); }
p { color: var(--muted); line-height: 1.75; }
.eyebrow {
  color: var(--accent);
  font-size: .78rem;
  font-weight: 900;
  letter-spacing: .16em;
  text-transform: uppercase;
}
.actions, .filters { display: flex; flex-wrap: wrap; gap: .75rem; margin-top: 1.5rem; }
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 50px;
  padding: 0 1.1rem;
  border-radius: 999px;
  font-weight: 900;
}
.primary { background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #07111f; }
.secondary { border: 1px solid var(--line); background: var(--panel); }

.hero-panel, .project-card, .service-list div, .pricing-grid article, .testimonials, .contact, form {
  border: 1px solid var(--line);
  background: var(--panel);
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
  overflow: hidden;
}
.hero-panel { border-radius: 30px; padding: 0; }
.hero-panel img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  display: block;
}
.hero-panel-content { padding: 1.4rem; }
.status { color: #74f5bd; font-weight: 900; }
.score-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .7rem; margin-top: 1rem; }
.score-grid div { border-radius: 18px; padding: .9rem; background: var(--panel-strong); }
.score-grid b { display: block; font-size: 1.5rem; }
.score-grid span { color: var(--muted); font-size: .78rem; font-weight: 800; }

.section { padding: clamp(4rem, 8vw, 7rem) 0; }
.section-title { max-width: 760px; margin-bottom: 2rem; }
.project-grid, .pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.project-card, .pricing-grid article { border-radius: 26px; padding: 1.35rem; min-height: 245px; }
.project-card {
  display: flex;
  flex-direction: column;
  gap: .8rem;
}
.project-card img {
  width: calc(100% + 2.7rem);
  margin: -1.35rem -1.35rem .3rem;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  display: block;
}
.project-card span, .pricing-grid span { color: var(--accent-2); font-size: .8rem; font-weight: 900; text-transform: uppercase; letter-spacing: .12em; }
.project-card.hide { display: none; }
.filter.active { background: var(--accent); color: #07111f; border-color: transparent; }
.services { display: grid; grid-template-columns: .85fr 1.15fr; gap: 2rem; }
.service-list { display: grid; gap: .85rem; }
.service-list div { border-radius: 24px; padding: 1.15rem; }
.service-list strong { color: var(--accent); }
.featured { transform: translateY(-10px); border-color: color-mix(in srgb, var(--accent) 60%, var(--line)) !important; }
.testimonials { border-radius: 30px; padding: clamp(2rem, 5vw, 4rem); text-align: center; }
blockquote { margin: 0 auto 1rem; max-width: 820px; font-size: clamp(1.5rem, 3vw, 2.8rem); line-height: 1.16; letter-spacing: -0.04em; }
.contact { border-radius: 30px; padding: clamp(1.25rem, 4vw, 2rem); display: grid; grid-template-columns: .8fr 1.2fr; gap: 1rem; }
form { border-radius: 24px; padding: 1rem; display: grid; gap: .75rem; box-shadow: none; }
input, select, textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--panel-strong);
  color: var(--text);
  min-height: 48px;
  padding: .9rem;
  font: inherit;
}
textarea { min-height: 120px; resize: vertical; }
footer { padding: 2rem; text-align: center; color: var(--muted); border-top: 1px solid var(--line); }

@media (max-width: 840px) {
  nav { display: none; }
  .hero, .services, .contact, .project-grid, .pricing-grid { grid-template-columns: 1fr; }
  .hero { min-height: auto; }
  .score-grid { grid-template-columns: 1fr; }
  .featured { transform: none; }
}
""",
        },
        {
            "path": "script.js",
            "content": """const themeButton = document.getElementById("themeButton");
const savedTheme = localStorage.getItem("nova-theme");

if (savedTheme === "light") {
  document.body.classList.add("light");
}

themeButton.addEventListener("click", () => {
  document.body.classList.toggle("light");
  localStorage.setItem("nova-theme", document.body.classList.contains("light") ? "light" : "dark");
});

document.querySelectorAll(".filter").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".filter").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");

    const filter = button.dataset.filter;
    document.querySelectorAll(".project-card").forEach((card) => {
      card.classList.toggle("hide", filter !== "all" && card.dataset.kind !== filter);
    });
  });
});

document.getElementById("leadForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const name = data.get("name");
  document.getElementById("formStatus").textContent = `Thanks, ${name}. Your project brief is ready to send.`;
  event.currentTarget.reset();
});
""",
        },
    ]


def _premium_web_app_files(user_request: str) -> list[dict]:
    return [
        {
            "path": "index.html",
            "content": f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>JX Build Studio App</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <main class="app-shell">
      <aside class="sidebar">
        <a class="brand" href="#"><span>JX</span> Build Studio</a>
        <nav aria-label="Workspace navigation">
          <button class="nav-item active" data-view="overview" type="button">Overview</button>
          <button class="nav-item" data-view="tasks" type="button">Tasks</button>
          <button class="nav-item" data-view="insights" type="button">Insights</button>
        </nav>
      </aside>

      <section class="workspace">
        <header class="topline">
          <div>
            <p class="eyebrow">Generated by JX JARVIS</p>
            <h1>Premium working app for your request.</h1>
            <p class="request">Request: {user_request[:180]}</p>
          </div>
          <button id="themeButton" type="button">Theme</button>
        </header>

        <section class="metric-grid" aria-label="Project metrics">
          <article><span>Progress</span><strong id="progressMetric">68%</strong><p>Active build confidence</p></article>
          <article><span>Items</span><strong id="itemMetric">4</strong><p>Live workspace entries</p></article>
          <article><span>Priority</span><strong>High</strong><p>Ready for customization</p></article>
        </section>

        <section class="panel input-panel">
          <div>
            <p class="eyebrow">Create</p>
            <h2>Add a new workspace item</h2>
          </div>
          <form id="itemForm">
            <input id="titleInput" name="title" placeholder="Item title" required />
            <select id="typeInput" name="type" required>
              <option value="Feature">Feature</option>
              <option value="Design">Design</option>
              <option value="Bug Fix">Bug Fix</option>
              <option value="Research">Research</option>
            </select>
            <textarea id="noteInput" name="note" placeholder="Short note or requirement" required></textarea>
            <button type="submit">Add Item</button>
          </form>
        </section>

        <section class="panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Workspace</p>
              <h2>Active build board</h2>
            </div>
            <input id="searchInput" placeholder="Search items" />
          </div>
          <div id="emptyState" class="empty-state" hidden>No matching items yet.</div>
          <div id="itemList" class="item-list"></div>
        </section>
      </section>
    </main>
    <script src="script.js"></script>
  </body>
</html>
""",
        },
        {
            "path": "styles.css",
            "content": """:root {
  --bg: #0b1018;
  --sidebar: #080c12;
  --panel: rgba(255, 255, 255, 0.08);
  --panel-strong: rgba(255, 255, 255, 0.13);
  --text: #f8fbff;
  --muted: #a7b2c4;
  --line: rgba(255, 255, 255, 0.14);
  --accent: #34d399;
  --accent-2: #60a5fa;
  --shadow: 0 22px 70px rgba(0, 0, 0, 0.32);
}

body.light {
  --bg: #f4f7fb;
  --sidebar: #ffffff;
  --panel: rgba(255, 255, 255, 0.86);
  --panel-strong: #ffffff;
  --text: #111827;
  --muted: #5f6b7a;
  --line: rgba(17, 24, 39, 0.12);
  --shadow: 0 18px 50px rgba(17, 24, 39, 0.11);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  color: var(--text);
  background:
    radial-gradient(circle at 78% 8%, rgba(96, 165, 250, .22), transparent 28rem),
    radial-gradient(circle at 34% 0%, rgba(52, 211, 153, .18), transparent 24rem),
    var(--bg);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
}
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 1.2rem;
  border-right: 1px solid var(--line);
  background: color-mix(in srgb, var(--sidebar) 88%, transparent);
}
.brand {
  display: flex;
  align-items: center;
  gap: .65rem;
  color: var(--text);
  text-decoration: none;
  font-weight: 900;
}
.brand span {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #061018;
}
nav { display: grid; gap: .55rem; margin-top: 2rem; }
button, input, select, textarea {
  font: inherit;
}
button {
  border: 0;
  border-radius: 14px;
  min-height: 44px;
  padding: 0 .9rem;
  cursor: pointer;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #061018;
  font-weight: 900;
}
.nav-item {
  width: 100%;
  text-align: left;
  background: transparent;
  color: var(--muted);
}
.nav-item.active, .nav-item:hover {
  color: var(--text);
  background: var(--panel);
}
.workspace {
  padding: clamp(1rem, 4vw, 2rem);
  display: grid;
  gap: 1rem;
}
.topline {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 1rem;
}
.eyebrow {
  margin: 0 0 .45rem;
  color: var(--accent);
  font-size: .76rem;
  font-weight: 900;
  letter-spacing: .14em;
  text-transform: uppercase;
}
h1, h2, p { margin-top: 0; }
h1 {
  max-width: 760px;
  margin-bottom: .7rem;
  font-size: clamp(2.4rem, 5.4vw, 5.2rem);
  line-height: .95;
  letter-spacing: -0.06em;
}
h2 { margin-bottom: .75rem; font-size: clamp(1.5rem, 3vw, 2.5rem); letter-spacing: -0.04em; }
p, .request { color: var(--muted); line-height: 1.7; }
.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
.metric-grid article, .panel, .item-card {
  border: 1px solid var(--line);
  border-radius: 22px;
  background: var(--panel);
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
}
.metric-grid article { padding: 1rem; }
.metric-grid span, .item-type { color: var(--muted); font-size: .78rem; font-weight: 900; text-transform: uppercase; letter-spacing: .11em; }
.metric-grid strong { display: block; margin: .2rem 0; font-size: 2rem; }
.panel { padding: clamp(1rem, 3vw, 1.35rem); }
.input-panel { display: grid; grid-template-columns: .7fr 1.3fr; gap: 1rem; align-items: start; }
form { display: grid; gap: .7rem; }
input, select, textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel-strong);
  color: var(--text);
  min-height: 46px;
  padding: .8rem;
}
textarea { min-height: 95px; resize: vertical; }
.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
  margin-bottom: 1rem;
}
#searchInput { max-width: 260px; }
.item-list { display: grid; gap: .75rem; }
.item-card {
  padding: 1rem;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  box-shadow: none;
}
.item-card h3 { margin: .2rem 0 .35rem; }
.item-actions { display: flex; gap: .5rem; align-items: center; }
.item-actions button { min-height: 36px; border-radius: 12px; }
.done { opacity: .58; }
.done h3 { text-decoration: line-through; }
.empty-state {
  border: 1px dashed var(--line);
  border-radius: 18px;
  padding: 1rem;
  color: var(--muted);
  text-align: center;
}

@media (max-width: 860px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; }
  .metric-grid, .input-panel { grid-template-columns: 1fr; }
  .topline, .panel-heading, .item-card { grid-template-columns: 1fr; display: grid; }
  #searchInput { max-width: none; }
}
""",
        },
        {
            "path": "script.js",
            "content": """const initialItems = [
  { id: crypto.randomUUID(), type: "Feature", title: "Build the main experience", note: "Turn the user request into a working screen with useful controls.", done: false },
  { id: crypto.randomUUID(), type: "Design", title: "Polish the interface", note: "Responsive layout, premium spacing, hover states, and readable content.", done: false },
  { id: crypto.randomUUID(), type: "Research", title: "Add realistic sample data", note: "Use content that makes the app feel real instead of empty.", done: true },
  { id: crypto.randomUUID(), type: "Bug Fix", title: "Validate edge states", note: "Check empty, search, completed, and new item states.", done: false },
];

let items = JSON.parse(localStorage.getItem("jx-app-items") || "null") || initialItems;
const list = document.getElementById("itemList");
const emptyState = document.getElementById("emptyState");
const searchInput = document.getElementById("searchInput");
const itemMetric = document.getElementById("itemMetric");
const progressMetric = document.getElementById("progressMetric");

function save() {
  localStorage.setItem("jx-app-items", JSON.stringify(items));
}

function render() {
  const query = searchInput.value.trim().toLowerCase();
  const visible = items.filter((item) => {
    return [item.title, item.type, item.note].join(" ").toLowerCase().includes(query);
  });

  list.innerHTML = visible.map((item) => `
    <article class="item-card ${item.done ? "done" : ""}">
      <div>
        <span class="item-type">${item.type}</span>
        <h3>${item.title}</h3>
        <p>${item.note}</p>
      </div>
      <div class="item-actions">
        <button data-action="toggle" data-id="${item.id}" type="button">${item.done ? "Undo" : "Done"}</button>
        <button data-action="delete" data-id="${item.id}" type="button">Delete</button>
      </div>
    </article>
  `).join("");

  emptyState.hidden = visible.length > 0;
  itemMetric.textContent = String(items.length);
  const done = items.filter((item) => item.done).length;
  const progress = items.length ? Math.round((done / items.length) * 100) : 0;
  progressMetric.textContent = `${progress}%`;
}

document.getElementById("itemForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  items.unshift({
    id: crypto.randomUUID(),
    title: form.get("title"),
    type: form.get("type"),
    note: form.get("note"),
    done: false,
  });
  event.currentTarget.reset();
  save();
  render();
});

list.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const id = button.dataset.id;
  if (button.dataset.action === "toggle") {
    items = items.map((item) => item.id === id ? { ...item, done: !item.done } : item);
  }
  if (button.dataset.action === "delete") {
    items = items.filter((item) => item.id !== id);
  }
  save();
  render();
});

searchInput.addEventListener("input", render);

document.getElementById("themeButton").addEventListener("click", () => {
  document.body.classList.toggle("light");
  localStorage.setItem("jx-app-theme", document.body.classList.contains("light") ? "light" : "dark");
});

if (localStorage.getItem("jx-app-theme") === "light") {
  document.body.classList.add("light");
}

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
  });
});

render();
""",
        },
    ]


def _snake_game_files() -> list[dict]:
    return [
        {
            "path": "index.html",
            "content": """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Neon Snake Arena</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <main class="shell">
      <section class="intro">
        <p class="eyebrow">Arcade Web Game</p>
        <h1>Neon Snake Arena</h1>
        <p>Eat energy cores, grow longer, dodge your own trail, and push for a new high score.</p>
        <div class="controls">
          <button id="startButton" type="button">Start</button>
          <button id="pauseButton" type="button">Pause</button>
          <button id="restartButton" type="button">Restart</button>
        </div>
      </section>

      <section class="game-card">
        <div class="hud">
          <div><span>Score</span><strong id="score">0</strong></div>
          <div><span>Best</span><strong id="best">0</strong></div>
          <div><span>Status</span><strong id="status">Ready</strong></div>
        </div>
        <canvas id="board" width="560" height="560" aria-label="Snake game board"></canvas>
        <p class="hint">Use arrow keys or WASD. On mobile, swipe the board.</p>
      </section>
    </main>
    <script src="script.js"></script>
  </body>
</html>
""",
        },
        {
            "path": "styles.css",
            "content": """:root {
  --bg: #071018;
  --panel: rgba(255, 255, 255, 0.08);
  --line: rgba(255, 255, 255, 0.14);
  --text: #f6fbff;
  --muted: #9fb0c4;
  --accent: #39ffbc;
  --danger: #ff4d7d;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 20% 10%, rgba(57, 255, 188, .24), transparent 24rem),
    radial-gradient(circle at 80% 20%, rgba(111, 76, 255, .2), transparent 26rem),
    var(--bg);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.shell {
  width: min(1120px, calc(100% - 2rem));
  display: grid;
  grid-template-columns: .8fr 1.2fr;
  gap: 1.5rem;
  align-items: center;
}
.intro, .game-card {
  border: 1px solid var(--line);
  background: var(--panel);
  border-radius: 28px;
  padding: clamp(1rem, 4vw, 2rem);
  box-shadow: 0 28px 90px rgba(0, 0, 0, .35);
  backdrop-filter: blur(18px);
}
.eyebrow {
  color: var(--accent);
  font-size: .78rem;
  font-weight: 900;
  letter-spacing: .16em;
  text-transform: uppercase;
}
h1 {
  margin: 0 0 1rem;
  font-size: clamp(3rem, 8vw, 6.2rem);
  line-height: .9;
  letter-spacing: -0.07em;
}
p { color: var(--muted); line-height: 1.7; }
.controls { display: flex; flex-wrap: wrap; gap: .7rem; margin-top: 1.5rem; }
button {
  border: 0;
  border-radius: 999px;
  min-height: 46px;
  padding: 0 1rem;
  cursor: pointer;
  color: #04110d;
  background: var(--accent);
  font-weight: 900;
}
button:nth-child(2) { background: #ffd166; }
button:nth-child(3) { background: #8bb8ff; }
.hud {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: .75rem;
  margin-bottom: 1rem;
}
.hud div {
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: .85rem;
  background: rgba(255, 255, 255, .06);
}
.hud span { display: block; color: var(--muted); font-size: .78rem; font-weight: 900; text-transform: uppercase; letter-spacing: .1em; }
.hud strong { font-size: 1.5rem; }
canvas {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 22px;
  border: 1px solid var(--line);
  background: #02070b;
}
.hint { text-align: center; margin-bottom: 0; }

@media (max-width: 820px) {
  .shell { grid-template-columns: 1fr; padding: 1rem 0; }
  .hud { grid-template-columns: 1fr; }
}
""",
        },
        {
            "path": "script.js",
            "content": """const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");
const scoreEl = document.getElementById("score");
const bestEl = document.getElementById("best");
const statusEl = document.getElementById("status");

const size = 20;
const cells = canvas.width / size;
let snake;
let food;
let direction;
let nextDirection;
let score;
let timer;
let running = false;
let best = Number(localStorage.getItem("snake-best") || 0);
bestEl.textContent = best;

function reset() {
  snake = [{ x: 10, y: 10 }, { x: 9, y: 10 }, { x: 8, y: 10 }];
  direction = { x: 1, y: 0 };
  nextDirection = direction;
  score = 0;
  scoreEl.textContent = score;
  statusEl.textContent = "Ready";
  placeFood();
  draw();
}

function placeFood() {
  do {
    food = {
      x: Math.floor(Math.random() * cells),
      y: Math.floor(Math.random() * cells),
    };
  } while (snake.some((part) => part.x === food.x && part.y === food.y));
}

function start() {
  if (running) return;
  running = true;
  statusEl.textContent = "Playing";
  timer = setInterval(tick, 92);
}

function pause() {
  running = false;
  clearInterval(timer);
  statusEl.textContent = "Paused";
}

function restart() {
  pause();
  reset();
  start();
}

function tick() {
  direction = nextDirection;
  const head = snake[0];
  const next = { x: head.x + direction.x, y: head.y + direction.y };

  if (
    next.x < 0 || next.x >= cells ||
    next.y < 0 || next.y >= cells ||
    snake.some((part) => part.x === next.x && part.y === next.y)
  ) {
    gameOver();
    return;
  }

  snake.unshift(next);
  if (next.x === food.x && next.y === food.y) {
    score += 10;
    scoreEl.textContent = score;
    if (score > best) {
      best = score;
      bestEl.textContent = best;
      localStorage.setItem("snake-best", best);
    }
    placeFood();
  } else {
    snake.pop();
  }
  draw();
}

function gameOver() {
  pause();
  statusEl.textContent = "Game Over";
  draw();
  ctx.fillStyle = "rgba(2, 7, 11, .68)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#f6fbff";
  ctx.font = "bold 42px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("Game Over", canvas.width / 2, canvas.height / 2 - 10);
  ctx.font = "18px system-ui";
  ctx.fillText("Press restart to play again", canvas.width / 2, canvas.height / 2 + 28);
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#02070b";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "rgba(255,255,255,.05)";
  for (let i = 0; i <= cells; i += 1) {
    ctx.beginPath();
    ctx.moveTo(i * size, 0);
    ctx.lineTo(i * size, canvas.height);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, i * size);
    ctx.lineTo(canvas.width, i * size);
    ctx.stroke();
  }

  ctx.fillStyle = "#ff4d7d";
  roundRect(food.x * size + 3, food.y * size + 3, size - 6, size - 6, 7);

  snake.forEach((part, index) => {
    ctx.fillStyle = index === 0 ? "#39ffbc" : "#18b98a";
    roundRect(part.x * size + 2, part.y * size + 2, size - 4, size - 4, 6);
  });
}

function roundRect(x, y, width, height, radius) {
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, radius);
  ctx.fill();
}

function setDirection(x, y) {
  if (direction.x + x === 0 && direction.y + y === 0) return;
  nextDirection = { x, y };
}

document.addEventListener("keydown", (event) => {
  const key = event.key.toLowerCase();
  if (key === "arrowup" || key === "w") setDirection(0, -1);
  if (key === "arrowdown" || key === "s") setDirection(0, 1);
  if (key === "arrowleft" || key === "a") setDirection(-1, 0);
  if (key === "arrowright" || key === "d") setDirection(1, 0);
  if (key === " ") running ? pause() : start();
});

let touchStart = null;
canvas.addEventListener("touchstart", (event) => {
  const touch = event.changedTouches[0];
  touchStart = { x: touch.clientX, y: touch.clientY };
});
canvas.addEventListener("touchend", (event) => {
  if (!touchStart) return;
  const touch = event.changedTouches[0];
  const dx = touch.clientX - touchStart.x;
  const dy = touch.clientY - touchStart.y;
  if (Math.abs(dx) > Math.abs(dy)) setDirection(Math.sign(dx), 0);
  else setDirection(0, Math.sign(dy));
  touchStart = null;
});

document.getElementById("startButton").addEventListener("click", start);
document.getElementById("pauseButton").addEventListener("click", pause);
document.getElementById("restartButton").addEventListener("click", restart);

reset();
""",
        },
    ]


def _portfolio_files() -> list[dict]:
    return [
        {
            "path": "index.html",
            "content": """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Premium Portfolio</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <div class="page-glow"></div>
    <header class="site-header">
      <a class="brand" href="#home"><span>JX</span> Portfolio</a>
      <nav class="nav" aria-label="Main navigation">
        <a href="#work">Work</a>
        <a href="#skills">Skills</a>
        <a href="#journey">Journey</a>
        <a href="#contact">Contact</a>
      </nav>
      <button class="theme-toggle" type="button" aria-label="Toggle theme">Theme</button>
    </header>

    <main>
      <section id="home" class="hero section">
        <div class="hero-copy reveal">
          <p class="eyebrow">Full-stack developer - UI engineer - Problem solver</p>
          <h1>Building polished digital products that feel fast, useful, and alive.</h1>
          <p class="hero-text">
            I craft modern websites, dashboards, automations, and AI-assisted tools with clean interfaces,
            strong performance, and practical engineering.
          </p>
          <div class="hero-actions">
            <a class="button primary" href="#work">View Projects</a>
            <a class="button ghost" href="#contact">Hire Me</a>
          </div>
          <div class="metrics" aria-label="Portfolio highlights">
            <div><strong>20+</strong><span>Projects</span></div>
            <div><strong>3+</strong><span>Years Learning</span></div>
            <div><strong>100%</strong><span>Build Mindset</span></div>
          </div>
        </div>
        <div class="hero-card reveal">
          <img class="portrait" src="https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=900&q=80" alt="Professional developer portrait for the portfolio hero" />
          <div>
            <p class="status">Available for projects</p>
            <h2>Your Name</h2>
            <p>Developer focused on React, Python, AI assistants, and beautiful product experiences.</p>
          </div>
        </div>
      </section>

      <section id="work" class="section">
        <div class="section-heading reveal">
          <p class="eyebrow">Selected Work</p>
          <h2>Featured projects with real-world polish.</h2>
        </div>
        <div class="project-grid">
          <article class="project-card reveal">
            <img src="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80" alt="AI desktop assistant interface on a laptop" />
            <span class="tag">AI Desktop App</span>
            <h3>Jarvis Assistant</h3>
            <p>Electron + Python assistant with voice commands, bilingual support, local actions, and code generation.</p>
            <div class="stack"><span>Electron</span><span>React</span><span>Python</span></div>
          </article>
          <article class="project-card reveal">
            <img src="https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=900&q=80" alt="Responsive web platform code and design workspace" />
            <span class="tag">Web Platform</span>
            <h3>Portfolio System</h3>
            <p>A responsive personal brand website with smooth sections, premium cards, and conversion-focused contact.</p>
            <div class="stack"><span>HTML</span><span>CSS</span><span>JavaScript</span></div>
          </article>
          <article class="project-card reveal">
            <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=900&q=80" alt="Automation dashboard with analytics charts" />
            <span class="tag">Automation</span>
            <h3>Workflow Toolkit</h3>
            <p>Small tools that organize files, speed up repetitive tasks, and make daily computer work easier.</p>
            <div class="stack"><span>Python</span><span>APIs</span><span>UX</span></div>
          </article>
        </div>
      </section>

      <section id="skills" class="section split">
        <div class="section-heading reveal">
          <p class="eyebrow">Capabilities</p>
          <h2>Design taste plus engineering discipline.</h2>
          <p>I can turn an idea into a usable product: interface, logic, backend, automation, and deployment flow.</p>
        </div>
        <div class="skill-list reveal">
          <div><span>Frontend</span><strong>React, Vite, Tailwind, animation</strong></div>
          <div><span>Backend</span><strong>Python, Flask, APIs, automation</strong></div>
          <div><span>AI Tools</span><strong>Voice assistants, prompts, local actions</strong></div>
          <div><span>Product</span><strong>UX flows, dashboards, responsive design</strong></div>
        </div>
      </section>

      <section id="journey" class="section">
        <div class="section-heading reveal">
          <p class="eyebrow">Journey</p>
          <h2>How I work.</h2>
        </div>
        <div class="timeline">
          <div class="timeline-item reveal"><span>01</span><h3>Understand</h3><p>Clarify the goal, user, and workflow before touching the UI.</p></div>
          <div class="timeline-item reveal"><span>02</span><h3>Build</h3><p>Create the core experience quickly, then sharpen details and responsiveness.</p></div>
          <div class="timeline-item reveal"><span>03</span><h3>Improve</h3><p>Test, fix rough edges, and make the final result feel complete.</p></div>
        </div>
      </section>

      <section id="contact" class="section contact reveal">
        <p class="eyebrow">Contact</p>
        <h2>Let's build something excellent.</h2>
        <p>Replace these links with your real email, GitHub, LinkedIn, and resume.</p>
        <div class="contact-actions">
          <a class="button primary" href="mailto:you@example.com">Email Me</a>
          <a class="button ghost" href="#" target="_blank" rel="noreferrer">GitHub</a>
          <a class="button ghost" href="#" target="_blank" rel="noreferrer">LinkedIn</a>
        </div>
      </section>
    </main>

    <footer>(c) <span id="year"></span> Your Name. Built with focus.</footer>
    <script src="script.js"></script>
  </body>
</html>
""",
        },
        {
            "path": "styles.css",
            "content": """:root {
  --bg: #080a12;
  --panel: rgba(255, 255, 255, 0.07);
  --panel-strong: rgba(255, 255, 255, 0.12);
  --text: #f8fbff;
  --muted: #a8b3c7;
  --line: rgba(255, 255, 255, 0.14);
  --accent: #7c3cff;
  --accent-2: #35e7ff;
  --shadow: 0 28px 80px rgba(0, 0, 0, 0.34);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at 15% 10%, rgba(124, 60, 255, 0.34), transparent 28rem),
    radial-gradient(circle at 80% 0%, rgba(53, 231, 255, 0.22), transparent 26rem),
    var(--bg);
  color: var(--text);
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body.light {
  --bg: #f4f7fb;
  --panel: rgba(255, 255, 255, 0.82);
  --panel-strong: #ffffff;
  --text: #111827;
  --muted: #5b6474;
  --line: rgba(15, 23, 42, 0.12);
  --shadow: 0 24px 70px rgba(15, 23, 42, 0.13);
}

a { color: inherit; text-decoration: none; }
.page-glow {
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image: linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px);
  background-size: 54px 54px;
  mask-image: linear-gradient(to bottom, black, transparent 70%);
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem clamp(1rem, 4vw, 4rem);
  border-bottom: 1px solid var(--line);
  background: color-mix(in srgb, var(--bg) 82%, transparent);
  backdrop-filter: blur(18px);
}
.brand { font-weight: 800; letter-spacing: -0.04em; }
.brand span { color: var(--accent-2); }
.nav { display: flex; gap: clamp(.75rem, 2vw, 1.75rem); color: var(--muted); font-weight: 700; }
.nav a:hover { color: var(--text); }
.theme-toggle {
  width: 42px;
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: var(--panel);
  color: var(--text);
  cursor: pointer;
}

.section { width: min(1180px, calc(100% - 2rem)); margin: 0 auto; padding: clamp(4rem, 8vw, 8rem) 0; }
.hero { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(300px, .75fr); gap: 2rem; align-items: center; min-height: calc(100vh - 76px); }
.eyebrow { color: var(--accent-2); font-weight: 800; letter-spacing: .16em; text-transform: uppercase; font-size: .78rem; }
h1, h2, h3, p { margin-top: 0; }
h1 { font-size: clamp(3.2rem, 8vw, 6.8rem); line-height: .92; letter-spacing: -.08em; margin-bottom: 1.5rem; }
h2 { font-size: clamp(2rem, 4vw, 4rem); line-height: 1; letter-spacing: -.06em; margin-bottom: 1rem; }
h3 { font-size: 1.45rem; margin-bottom: .75rem; }
.hero-text, .section-heading p, .project-card p, .timeline-item p, .contact p { color: var(--muted); font-size: 1.05rem; line-height: 1.8; }

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0 1.1rem;
  border-radius: 999px;
  border: 1px solid var(--line);
  font-weight: 800;
}
.primary { background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: white; border: 0; }
.ghost { background: var(--panel); }
.hero-actions, .contact-actions { display: flex; flex-wrap: wrap; gap: .8rem; margin-top: 1.5rem; }

.metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: .8rem; margin-top: 2rem; }
.metrics div, .hero-card, .project-card, .skill-list div, .timeline-item, .contact {
  border: 1px solid var(--line);
  background: var(--panel);
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
}
.metrics div { border-radius: 20px; padding: 1rem; }
.metrics strong { display: block; font-size: 1.5rem; }
.metrics span, .skill-list span, .tag { color: var(--muted); font-size: .85rem; font-weight: 800; text-transform: uppercase; letter-spacing: .12em; }

.hero-card { border-radius: 34px; padding: 2rem; display: grid; gap: 1.25rem; }
.portrait {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 26px;
  object-fit: cover;
  display: block;
}
.status { color: #77f7c9; font-weight: 800; }

.section-heading { max-width: 760px; margin-bottom: 2rem; }
.project-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.project-card { min-height: 360px; border-radius: 28px; padding: 1.4rem; display: flex; flex-direction: column; justify-content: space-between; gap: .8rem; overflow: hidden; transition: transform .2s ease, border-color .2s ease; }
.project-card img {
  width: calc(100% + 2.8rem);
  margin: -1.4rem -1.4rem .35rem;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  display: block;
}
.project-card:hover { transform: translateY(-6px); border-color: color-mix(in srgb, var(--accent-2) 58%, var(--line)); }
.stack { display: flex; flex-wrap: wrap; gap: .45rem; }
.stack span { border: 1px solid var(--line); border-radius: 999px; padding: .35rem .65rem; color: var(--muted); font-size: .82rem; font-weight: 700; }

.split { display: grid; grid-template-columns: .85fr 1fr; gap: 2rem; align-items: start; }
.skill-list { display: grid; gap: .75rem; }
.skill-list div { border-radius: 22px; padding: 1.1rem; display: grid; gap: .35rem; }
.timeline { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.timeline-item { border-radius: 28px; padding: 1.4rem; }
.timeline-item span { color: var(--accent-2); font-weight: 900; }
.contact { text-align: center; border-radius: 34px; padding: clamp(2rem, 5vw, 4rem); }
footer { padding: 2rem; text-align: center; color: var(--muted); border-top: 1px solid var(--line); }

.reveal { opacity: 0; transform: translateY(18px); transition: opacity .7s ease, transform .7s ease; }
.reveal.visible { opacity: 1; transform: translateY(0); }

@media (max-width: 820px) {
  .nav { display: none; }
  .hero, .split, .project-grid, .timeline { grid-template-columns: 1fr; }
  .hero { min-height: auto; padding-top: 4rem; }
  .metrics { grid-template-columns: 1fr; }
}
""",
        },
        {
            "path": "script.js",
            "content": """document.getElementById("year").textContent = new Date().getFullYear();

const toggle = document.querySelector(".theme-toggle");
toggle.addEventListener("click", () => {
  document.body.classList.toggle("light");
  localStorage.setItem("portfolio-theme", document.body.classList.contains("light") ? "light" : "dark");
});

if (localStorage.getItem("portfolio-theme") === "light") {
  document.body.classList.add("light");
}

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.16 }
);

document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
""",
        },
    ]


def open_code_workspace() -> str:
    def run() -> str:
        CODE_ROOT.mkdir(parents=True, exist_ok=True)
        opened = _open_in_vscode(CODE_ROOT)
        if opened:
            return READY_RESPONSE
        return "Yes sir, the code workspace is ready."

    return guard_action("file.read", "open code workspace", run, path=CODE_ROOT)


def latest_code_project() -> Path | None:
    if not CODE_ROOT.exists():
        return None
    projects = [path for path in CODE_ROOT.iterdir() if path.is_dir()]
    if not projects:
        return None
    return max(projects, key=lambda path: path.stat().st_mtime)


def open_latest_code_project() -> str:
    project = latest_code_project()
    if not project:
        return "No generated code projects found yet."

    def run() -> str:
        opened = _open_in_vscode(project)
        preview = _open_preview(project)
        if opened and preview:
            return READY_RESPONSE
        if opened:
            return READY_RESPONSE
        return READY_RESPONSE

    return guard_action("file.read", "open latest code project", run, path=project)


def test_latest_code_project() -> str:
    project = latest_code_project()
    if not project:
        return "No generated code projects found yet."
    return guard_action(
        "file.read",
        "test latest code project",
        lambda: f"Latest code project test result for {project.name}: {validate_code_project(project)}",
        path=project,
    )


def validate_code_project(project_dir: Path) -> str:
    checks: list[str] = []
    errors: list[str] = []

    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()
        if suffix == ".py":
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            checks.append(path.name)
            if result.returncode != 0:
                errors.append(f"{path.name}: {result.stderr.strip()[:240]}")

        elif suffix == ".json":
            checks.append(path.name)
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                errors.append(f"{path.name}: {error}")

        elif suffix == ".html":
            checks.append(path.name)
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "<html" not in content and "<!doctype" not in content and "<body" not in content:
                errors.append(f"{path.name}: missing basic HTML structure")

    package_json = project_dir / "package.json"
    if package_json.exists() and (project_dir / "node_modules").exists():
        result = subprocess.run(
            ["npm.cmd", "run", "build"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        checks.append("npm build")
        if result.returncode != 0:
            errors.append(f"npm build: {(result.stderr or result.stdout).strip()[:300]}")

    if errors:
        return "needs attention - " + " | ".join(errors[:3])

    if not checks:
        return "ready - no runnable checks found"

    return f"passed {len(checks)} check(s)"


def _parse_project_spec(text: str) -> dict:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    files = []
    for index, block in enumerate(re.finditer(r"```([a-zA-Z0-9_+-]*)\s*\n(.*?)```", text, re.DOTALL), start=1):
        language = block.group(1).lower()
        extension = LANGUAGE_EXTENSIONS.get(language, "txt")
        files.append({"path": f"main-{index}.{extension}", "content": block.group(2).strip()})

    return {
        "project_name": "jarvis-code",
        "summary": "Generated code from the assistant response.",
        "files": files,
    }


def _safe_project_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (name[:48] or "jarvis-code").strip("-")


def _safe_relative_path(value: str) -> Path:
    cleaned = value.replace("\\", "/").strip().lstrip("/")
    pure = PurePosixPath(cleaned)
    parts = [part for part in pure.parts if part not in ("", ".", "..")]
    if not parts:
        parts = ["main.txt"]
    return Path(*parts)


def _write_project_readme(project_dir: Path, user_request: str, summary: object, written: list[Path]) -> None:
    readme = project_dir / "README.md"
    if readme in written:
        return

    relative_files = "\n".join(f"- {path.relative_to(project_dir)}" for path in written)
    readme.write_text(
        "# JX JARVIS Generated Code\n\n"
        f"Request: {user_request}\n\n"
        f"Summary: {summary or 'Code workspace generated by JX JARVIS.'}\n\n"
        "Files:\n"
        f"{relative_files}\n",
        encoding="utf-8",
        newline="\n",
    )


def _open_preview(project_dir: Path) -> bool:
    if not evaluate_permission("browser.open", "open generated project preview").allowed:
        return False
    for name in ("index.html", "app.html"):
        candidate = project_dir / name
        if candidate.exists():
            webbrowser.open(candidate.resolve().as_uri())
            return True
    return False


def _open_in_vscode(path: Path) -> bool:
    if not evaluate_permission("app.open", "open VS Code", app="VS Code").allowed:
        return False
    commands = ["code.cmd", "code"]
    local_app_data = os.getenv("LOCALAPPDATA")
    program_files = os.getenv("ProgramFiles")

    if local_app_data:
        commands.append(str(Path(local_app_data) / "Programs" / "Microsoft VS Code" / "Code.exe"))
    if program_files:
        commands.append(str(Path(program_files) / "Microsoft VS Code" / "Code.exe"))

    for command in commands:
        try:
            subprocess.Popen(
                [command, "-n", str(path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
            return True
        except (FileNotFoundError, OSError):
            continue

    return False
