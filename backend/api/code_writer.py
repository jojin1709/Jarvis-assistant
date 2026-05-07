import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path, PurePosixPath


CODE_ROOT = Path.home() / "Desktop" / "JX-JARVIS-Code"
MAX_FILES = 8
MAX_FILE_CHARS = 30000


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
    "make code for",
    "make me code for",
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


def create_portfolio_project(user_request: str) -> str:
    project_dir = _new_project_dir("super-portfolio-website")
    files = _portfolio_files()
    written = _write_files(project_dir, files)
    _write_project_readme(project_dir, user_request, "Premium responsive portfolio website.", written)
    validation = validate_code_project(project_dir)
    preview = _open_preview(project_dir)
    opened = _open_in_vscode(project_dir)
    open_text = "I opened it in a new VS Code window." if opened else "VS Code was not found in PATH, but the files are ready."
    preview_text = " Browser preview opened." if preview else ""
    return f"Super portfolio website created: {project_dir}. Files: index.html, styles.css, script.js. Validation: {validation}. {open_text}{preview_text}"


def create_code_project(user_request: str, model_response: str) -> str:
    spec = _parse_project_spec(model_response)
    project_name = _safe_project_name(spec.get("project_name") or user_request)
    project_dir = _new_project_dir(project_name)

    files = spec.get("files") if isinstance(spec.get("files"), list) else []
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

    open_text = "I opened it in a new VS Code window." if opened else "VS Code was not found in PATH, but the files are ready."
    preview_text = " Browser preview opened." if preview else ""
    return f"Code workspace created: {project_dir}. Files: {file_list}. Validation: {validation}. {open_text}{preview_text}"


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
      <button class="theme-toggle" type="button" aria-label="Toggle theme">◐</button>
    </header>

    <main>
      <section id="home" class="hero section">
        <div class="hero-copy reveal">
          <p class="eyebrow">Full-stack developer • UI engineer • Problem solver</p>
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
          <div class="avatar">JX</div>
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
            <span class="tag">AI Desktop App</span>
            <h3>Jarvis Assistant</h3>
            <p>Electron + Python assistant with voice commands, bilingual support, local actions, and code generation.</p>
            <div class="stack"><span>Electron</span><span>React</span><span>Python</span></div>
          </article>
          <article class="project-card reveal">
            <span class="tag">Web Platform</span>
            <h3>Portfolio System</h3>
            <p>A responsive personal brand website with smooth sections, premium cards, and conversion-focused contact.</p>
            <div class="stack"><span>HTML</span><span>CSS</span><span>JavaScript</span></div>
          </article>
          <article class="project-card reveal">
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
        <h2>Let’s build something excellent.</h2>
        <p>Replace these links with your real email, GitHub, LinkedIn, and resume.</p>
        <div class="contact-actions">
          <a class="button primary" href="mailto:you@example.com">Email Me</a>
          <a class="button ghost" href="#" target="_blank" rel="noreferrer">GitHub</a>
          <a class="button ghost" href="#" target="_blank" rel="noreferrer">LinkedIn</a>
        </div>
      </section>
    </main>

    <footer>© <span id="year"></span> Your Name. Built with focus.</footer>
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
.avatar {
  width: 112px;
  height: 112px;
  border-radius: 32px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #ffffff, var(--accent-2) 38%, var(--accent));
  color: #080a12;
  font-size: 2.3rem;
  font-weight: 900;
}
.status { color: #77f7c9; font-weight: 800; }

.section-heading { max-width: 760px; margin-bottom: 2rem; }
.project-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.project-card { min-height: 280px; border-radius: 28px; padding: 1.4rem; display: flex; flex-direction: column; justify-content: space-between; transition: transform .2s ease, border-color .2s ease; }
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
    CODE_ROOT.mkdir(parents=True, exist_ok=True)
    opened = _open_in_vscode(CODE_ROOT)
    if opened:
        return f"Opened code workspace folder: {CODE_ROOT}"
    return f"Code workspace folder is ready: {CODE_ROOT}. VS Code was not found."


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

    opened = _open_in_vscode(project)
    preview = _open_preview(project)
    if opened and preview:
        return f"Opened latest code project in VS Code and browser: {project}"
    if opened:
        return f"Opened latest code project in VS Code: {project}"
    return f"Latest code project is ready: {project}. VS Code was not found."


def test_latest_code_project() -> str:
    project = latest_code_project()
    if not project:
        return "No generated code projects found yet."
    return f"Latest code project test result for {project.name}: {validate_code_project(project)}"


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
    for name in ("index.html", "app.html"):
        candidate = project_dir / name
        if candidate.exists():
            webbrowser.open(candidate.resolve().as_uri())
            return True
    return False


def _open_in_vscode(path: Path) -> bool:
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
