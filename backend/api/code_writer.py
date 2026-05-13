import json
import os
import re
import socket
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path, PurePosixPath

from api.permissions import evaluate_permission, guard_action
from api.memory_storage import remember_project


CODE_ROOT = Path.home() / "Desktop" / "JX-JARVIS-Code"
MAX_FILES = 10
MAX_FILE_CHARS = 60000
READY_RESPONSE = "Yes sir, it is ready."
_RECENT_GENERATIONS: dict[str, tuple[float, str]] = {}
_GENERATION_DEDUP_SECONDS = 8


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

    if has_code_intent and any(phrase in normalized for phrase in ("website for", "portfolio for", "landing page for", "web app for")):
        return True

    if normalized.startswith(("website ", "portfolio ", "landing page ", "web app ")):
        return True

    return False

def is_portfolio_request(text: str) -> bool:
    normalized = text.lower()
    return "portfolio" in normalized and any(word in normalized for word in ("website", "site", "web", "page", "app"))


def create_portfolio_project(user_request: str) -> str:
    from api.ai_provider import ask_ai_code_project

    model_response = ask_ai_code_project(user_request)
    return create_code_project(user_request, model_response)


def create_code_project(user_request: str, model_response: str) -> str:
    return guard_action(
        "code.generate",
        "create code project",
        lambda: _create_code_project(user_request, model_response),
        path=CODE_ROOT,
    )


def _create_code_project(user_request: str, model_response: str) -> str:
    dedup_key = " ".join(user_request.lower().split())
    now = datetime.now().timestamp()
    previous = _RECENT_GENERATIONS.get(dedup_key)
    if previous and now - previous[0] < _GENERATION_DEDUP_SECONDS:
        return previous[1]

    result = _create_code_project_from_response(user_request, model_response, allow_retry=True)
    _RECENT_GENERATIONS[dedup_key] = (now, result)
    return result


def _create_code_project_from_response(user_request: str, model_response: str, allow_retry: bool) -> str:
    spec = _parse_project_spec(model_response)
    files = spec.get("files") if isinstance(spec.get("files"), list) else []
    if _is_generation_error(spec, files):
        return str(spec.get("summary") or "The AI provider failed to generate project files. Try a stronger coding provider in Settings.")

    if not files:
        if allow_retry:
            from api.ai_provider import ask_ai_code_project

            retry_response = ask_ai_code_project(_retry_code_request(user_request, "The response did not include any writable files.", files))
            return _create_code_project_from_response(user_request, retry_response, allow_retry=False)
        repaired = _validated_repair_website_files(user_request, "The provider did not return any writable files.")
        if repaired:
            spec = {"project_name": _safe_project_name(user_request), "summary": "Repaired by generating project files one by one.", "files": repaired}
            files = repaired
        else:
            return "The AI provider did not return writable project files. No project was created."

    if not _has_usable_file_content(files):
        if allow_retry:
            from api.ai_provider import ask_ai_code_project

            retry_response = ask_ai_code_project(_retry_code_request(user_request, "The file entries had empty code content.", files))
            return _create_code_project_from_response(user_request, retry_response, allow_retry=False)
        repaired = _validated_repair_website_files(user_request, "The provider returned file names with empty code content.")
        if repaired:
            spec = {"project_name": _safe_project_name(user_request), "summary": "Repaired by generating project files one by one.", "files": repaired}
            files = repaired
        else:
            return "The AI returned file entries, but none had usable code content. No project files were written."

    quality_warning = None
    try:
        _validate_generated_project(user_request, files)
    except RuntimeError as error:
        if allow_retry:
            from api.ai_provider import ask_ai_code_project

            retry_response = ask_ai_code_project(_retry_code_request(user_request, str(error), files))
            return _create_code_project_from_response(user_request, retry_response, allow_retry=False)
        repaired = _validated_repair_website_files(user_request, str(error))
        if repaired:
            spec = {"project_name": _safe_project_name(user_request), "summary": "Repaired by generating stronger project files one by one.", "files": repaired}
            files = repaired
            quality_warning = "The first AI output was incomplete, so Jarvis regenerated the files one by one."
        else:
            return f"The AI generated files, but they did not match your requested UI/theme: {error}"

    project_name = _safe_project_name(spec.get("project_name") or user_request)

    project_dir = _new_project_dir(project_name)
    written = _write_files(project_dir, files)

    if not written:
        return "The AI returned file entries, but none had usable code content. No project files were written."

    summary_text = spec.get("summary")
    if quality_warning:
        summary_text = f"{summary_text or 'Generated by configured AI provider.'} Quality warning: {quality_warning}"
    _write_project_readme(project_dir, user_request, summary_text, written)
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


def _fallback_project_spec(user_request: str, reason: str) -> dict:
    brief = _fallback_site_brief(user_request)
    project_name = _safe_project_name(brief["brand"] or user_request)
    return {
        "project_name": project_name,
        "summary": f"Built a prompt-specific fallback website because: {reason}",
        "files": _fallback_website_files(user_request, brief),
    }


def _fallback_site_brief(user_request: str) -> dict:
    normalized = user_request.lower()
    if any(word in normalized for word in ("restaurant", "cafe", "food", "hotel", "menu", "dining")):
        return {
            "brand": _extract_named_brand(user_request) or "Restaurant Website",
            "initials": "RW",
            "eyebrow": "Premium restaurant website",
            "headline": "Bring your dining experience online.",
            "description": "A responsive restaurant website with a hero section, menu highlights, reservation-focused contact form, smooth animations, and a premium visual style.",
            "primaryCta": "Reserve a table",
            "secondaryCta": "View menu",
            "cardText": "Menu cards, chef highlights, opening hours, and contact flow are arranged for real restaurant visitors.",
            "featureHeading": "Built around menu, mood, and bookings.",
            "features": [
                {"icon": "🍽", "title": "Menu showcase", "body": "Highlight signature dishes, pricing cues, ingredients, and chef recommendations in polished cards."},
                {"icon": "✦", "title": "Reservation flow", "body": "A styled contact form guides visitors to request tables, events, or private dining."},
                {"icon": "⌁", "title": "Atmosphere-first design", "body": "Dark luxury colors, smooth reveals, and premium spacing create a memorable dining mood."},
            ],
            "aboutHeading": "A restaurant presence that feels premium.",
            "aboutText": "This fallback follows your restaurant prompt instead of using a generic startup page. It includes restaurant-friendly sections, mobile navigation, responsive cards, and simple JavaScript interactions.",
            "contactHeading": "Ready for bookings and enquiries.",
            "contactMessage": "Tell us your date, time, guests, or event details",
        }
    if any(word in normalized for word in ("portfolio", "resume", "developer", "designer", "personal site")):
        return {
            "brand": _extract_named_brand(user_request) or "Portfolio Website",
            "initials": "PW",
            "eyebrow": "Modern portfolio website",
            "headline": "Show your work with confidence.",
            "description": "A responsive portfolio website with a bold hero, project cards, skill tags, about section, and a clean contact flow.",
            "primaryCta": "Contact me",
            "secondaryCta": "View work",
            "cardText": "Project sections, skill highlights, and contact prompts are designed for showcasing real work.",
            "featureHeading": "Built to present skills and projects.",
            "features": [
                {"icon": "▣", "title": "Project cards", "body": "Feature standout work with compact summaries, tags, and hover interactions."},
                {"icon": "◆", "title": "Skill story", "body": "Use sharp tags and metrics to make capabilities easy to scan."},
                {"icon": "✉", "title": "Contact ready", "body": "A polished form gives visitors a clear way to reach out."},
            ],
            "aboutHeading": "A polished personal brand surface.",
            "aboutText": "This fallback is tuned for a portfolio prompt with work-focused sections, responsive layout, subtle motion, and separated HTML, CSS, and JavaScript.",
            "contactHeading": "Start a conversation.",
            "contactMessage": "Tell me about the role, project, or collaboration",
        }
    if any(word in normalized for word in ("shop", "store", "ecommerce", "e-commerce", "product")):
        return {
            "brand": _extract_named_brand(user_request) or "Shop Website",
            "initials": "SW",
            "eyebrow": "Modern ecommerce website",
            "headline": "Make products feel irresistible.",
            "description": "A product-focused website with featured items, benefit cards, conversion CTAs, smooth hover states, and a mobile-friendly layout.",
            "primaryCta": "Shop now",
            "secondaryCta": "See products",
            "cardText": "Product grids, trust badges, and CTA sections are arranged for shopping and conversion.",
            "featureHeading": "Built around products and trust.",
            "features": [
                {"icon": "◈", "title": "Product highlights", "body": "Showcase items with clean cards, pricing cues, and premium hover feedback."},
                {"icon": "✓", "title": "Trust signals", "body": "Add delivery, support, and quality promises that help shoppers decide."},
                {"icon": "↗", "title": "Conversion flow", "body": "Clear CTAs guide visitors from discovery to action."},
            ],
            "aboutHeading": "A storefront that feels clear and modern.",
            "aboutText": "This fallback follows ecommerce prompts with product sections, responsive design, animated cards, and a styled contact/order enquiry form.",
            "contactHeading": "Ask about an order.",
            "contactMessage": "Tell us the product or order details",
        }
    if any(word in normalized for word in ("gym", "fitness", "trainer", "workout", "yoga")):
        return {
            "brand": _extract_named_brand(user_request) or "Fitness Website",
            "initials": "FW",
            "eyebrow": "High-energy fitness website",
            "headline": "Turn energy into memberships.",
            "description": "A bold fitness website with program cards, class highlights, coaching sections, animated CTAs, and mobile-first structure.",
            "primaryCta": "Join now",
            "secondaryCta": "View programs",
            "cardText": "Programs, trainers, schedules, and membership actions are built into a premium responsive layout.",
            "featureHeading": "Built for classes, coaching, and signups.",
            "features": [
                {"icon": "↯", "title": "Program cards", "body": "Display strength, cardio, yoga, and personal coaching offers clearly."},
                {"icon": "●", "title": "Trainer focus", "body": "Show expertise, results, and social proof in a modern visual flow."},
                {"icon": "➜", "title": "Signup CTAs", "body": "Guide visitors toward trials, memberships, and contact requests."},
            ],
            "aboutHeading": "A fitness brand with movement.",
            "aboutText": "This fallback follows fitness prompts with energetic copy, responsive panels, motion, contact validation, and separated files.",
            "contactHeading": "Book a trial session.",
            "contactMessage": "Tell us your fitness goal",
        }
    if any(word in normalized for word in ("school", "college", "academy", "education", "course")):
        return {
            "brand": _extract_named_brand(user_request) or "Education Website",
            "initials": "EW",
            "eyebrow": "Modern education website",
            "headline": "Make learning easy to explore.",
            "description": "An education website with course highlights, admission CTAs, program cards, and responsive sections for students and parents.",
            "primaryCta": "Apply now",
            "secondaryCta": "View courses",
            "cardText": "Course blocks, admission prompts, learning outcomes, and enquiry sections are ready to customize.",
            "featureHeading": "Built for programs and admissions.",
            "features": [
                {"icon": "□", "title": "Course sections", "body": "Present programs, outcomes, and learning paths in clear responsive cards."},
                {"icon": "◇", "title": "Admissions focus", "body": "Guide students and parents toward enquiry or application actions."},
                {"icon": "✦", "title": "Trust layout", "body": "Use outcomes, faculty, and campus highlights to build confidence."},
            ],
            "aboutHeading": "A clearer way to present education.",
            "aboutText": "This fallback follows education prompts with admissions-focused structure, responsive layout, and interactive JavaScript sections.",
            "contactHeading": "Ask about admissions.",
            "contactMessage": "Tell us the course or program you want",
        }
    return {
        "brand": _extract_named_brand(user_request) or "Custom Website",
        "initials": "CW",
        "eyebrow": "Prompt-specific website",
        "headline": _fallback_headline(user_request),
        "description": "A responsive website generated from your prompt with separated HTML, CSS, and JavaScript files, modern sections, animations, and a styled contact flow.",
        "primaryCta": "Get started",
        "secondaryCta": "Explore",
        "cardText": "The layout is built from the current prompt and can be edited directly in VS Code.",
        "featureHeading": "Built from the request you typed.",
        "features": [
            {"icon": "✦", "title": "Prompt-first layout", "body": "Sections and copy are based on the current website request instead of a saved template."},
            {"icon": "◈", "title": "Responsive structure", "body": "Navbar, hero, cards, about, contact, and footer adapt across screen sizes."},
            {"icon": "↯", "title": "Interactive details", "body": "Mobile menu, reveal animations, hover effects, typing headline, and form validation are included."},
        ],
        "aboutHeading": "A custom starting point for this prompt.",
        "aboutText": "This fallback is only used when the AI provider fails to return usable files. It still follows the current prompt and creates editable code.",
        "contactHeading": "Send an enquiry.",
        "contactMessage": "Tell us what you want to build",
    }


def _extract_named_brand(user_request: str) -> str:
    patterns = (
        r"\b(?:called|named|brand(?:ed)? as|name is)\s+([A-Za-z0-9 &'-]{2,36})",
        r"\bfor\s+([A-Z][A-Za-z0-9 &'-]{2,36})",
    )
    blocked = {"restaurant", "website", "portfolio", "shop", "store", "gym", "school", "landing page"}
    for pattern in patterns:
        match = re.search(pattern, user_request)
        if not match:
            continue
        brand = re.sub(r"\s+", " ", match.group(1)).strip(" .,-")
        if brand.lower() not in blocked:
            return brand[:36]
    return ""


def _fallback_headline(user_request: str) -> str:
    normalized = user_request.lower()
    if "dashboard" in normalized:
        return "See every important signal clearly."
    if "app" in normalized or "tool" in normalized:
        return "Launch a clean interactive experience."
    if "landing page" in normalized:
        return "Turn first impressions into action."
    return "Build a website that matches your idea."


def _html_escape(value: object) -> str:
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _fallback_restaurant_files(user_request: str, brief: dict) -> list[dict[str, str]]:
    brand = _html_escape(brief.get("brand") or "Restaurant Website")
    initials = _html_escape(brief.get("initials") or "RW")
    primary_cta = _html_escape(brief.get("primaryCta") or "Reserve a table")
    request_text = _html_escape(re.sub(r"\s+", " ", user_request).strip())

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{brand}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="topbar">
    <a href="#home" class="brand"><span>{initials}</span>{brand}</a>
    <button class="menu-button" data-menu-button aria-label="Open menu">Menu</button>
    <nav class="nav" data-nav>
      <a href="#menu">Menu</a>
      <a href="#story">Story</a>
      <a href="#gallery">Gallery</a>
      <a href="#reserve">Reserve</a>
    </nav>
  </header>

  <main>
    <section class="hero" id="home">
      <div class="hero-media" aria-hidden="true">
        <div class="plate plate-one"></div>
        <div class="plate plate-two"></div>
        <div class="steam steam-one"></div>
        <div class="steam steam-two"></div>
      </div>
      <div class="hero-content">
        <p class="kicker">Fine dining • Fresh ingredients • Memorable nights</p>
        <h1>Restaurant experiences that guests remember.</h1>
        <p class="lead">{request_text}</p>
        <div class="hero-actions">
          <a class="btn primary" href="#reserve">{primary_cta}</a>
          <a class="btn secondary" href="#menu">Explore menu</a>
        </div>
      </div>
      <aside class="hours-card">
        <span>Open today</span>
        <strong>12:00 PM - 11:30 PM</strong>
        <p>Chef tasting menu, family tables, and private dining available.</p>
      </aside>
    </section>

    <section class="menu-section" id="menu">
      <div class="section-title">
        <p class="kicker">Signature menu</p>
        <h2>Curated dishes with rich flavor and premium plating.</h2>
      </div>
      <div class="menu-filters" data-menu-filters></div>
      <div class="menu-grid" data-menu-grid></div>
    </section>

    <section class="story-section" id="story">
      <div>
        <p class="kicker">Our story</p>
        <h2>Warm ambience, precise service, and food made for slow evenings.</h2>
      </div>
      <p>
        This restaurant website is structured around real dining needs: menu discovery, table reservation,
        opening hours, chef specials, ambience photos, and quick contact. The design uses a luxury restaurant
        mood instead of a tech startup layout.
      </p>
      <div class="stats">
        <div><strong>24</strong><span>Signature dishes</span></div>
        <div><strong>4.8</strong><span>Guest rating</span></div>
        <div><strong>7</strong><span>Days open</span></div>
      </div>
    </section>

    <section class="gallery-section" id="gallery">
      <div class="gallery-card wide"><span>Chef's table</span></div>
      <div class="gallery-card"><span>Fresh pasta</span></div>
      <div class="gallery-card"><span>Grill specials</span></div>
      <div class="gallery-card tall"><span>Private dining</span></div>
    </section>

    <section class="reserve-section" id="reserve">
      <div class="section-title">
        <p class="kicker">Reservations</p>
        <h2>Book a table or plan a private dining night.</h2>
      </div>
      <form class="reservation-form" data-reservation-form>
        <label>Name<input name="name" type="text" placeholder="Your name" required /></label>
        <label>Email<input name="email" type="email" placeholder="you@example.com" required /></label>
        <label>Guests<input name="guests" type="number" min="1" max="24" value="2" required /></label>
        <label>Date<input name="date" type="date" required /></label>
        <label class="full">Notes<textarea name="notes" placeholder="Time, occasion, seating preference"></textarea></label>
        <button class="btn primary" type="submit">Request reservation</button>
        <p class="form-status" data-form-status></p>
      </form>
    </section>
  </main>

  <footer class="footer">
    <p>{brand} • Premium restaurant website</p>
    <div><a href="#menu">Menu</a><a href="#reserve">Reserve</a><a href="#home">Back top</a></div>
  </footer>

  <script src="script.js"></script>
</body>
</html>
"""

    css = """* {
  box-sizing: border-box;
}

:root {
  color-scheme: dark;
  --bg: #110d0a;
  --panel: #1d1510;
  --cream: #fff0d2;
  --muted: #c9ac86;
  --gold: #d59b43;
  --ember: #bb3f24;
  --wine: #501c1c;
  --line: rgba(255, 240, 210, .16);
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: Inter, system-ui, sans-serif;
  color: var(--cream);
  background:
    radial-gradient(circle at 12% 18%, rgba(187, 63, 36, .28), transparent 28%),
    radial-gradient(circle at 82% 8%, rgba(213, 155, 67, .18), transparent 24%),
    linear-gradient(135deg, #110d0a 0%, #21120d 48%, #0e0b09 100%);
}

a {
  color: inherit;
  text-decoration: none;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(1160px, calc(100% - 32px));
  margin: 18px auto;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(17, 13, 10, .78);
  backdrop-filter: blur(18px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
}

.brand span {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--gold);
  color: #1a1009;
}

.nav {
  display: flex;
  gap: 8px;
}

.nav a {
  padding: 10px 14px;
  border-radius: 999px;
  color: var(--muted);
}

.nav a:hover {
  background: rgba(255, 240, 210, .08);
  color: var(--cream);
}

.menu-button {
  display: none;
}

.hero {
  position: relative;
  width: min(1160px, calc(100% - 32px));
  min-height: 720px;
  margin: 0 auto 28px;
  display: grid;
  grid-template-columns: 1.05fr .95fr;
  align-items: center;
  gap: 40px;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 2;
}

.kicker {
  margin: 0 0 14px;
  color: var(--gold);
  text-transform: uppercase;
  letter-spacing: .15em;
  font-size: 12px;
  font-weight: 800;
}

h1, h2 {
  font-family: "Playfair Display", Georgia, serif;
  line-height: .98;
  letter-spacing: 0;
}

h1 {
  max-width: 720px;
  margin: 0;
  font-size: clamp(58px, 8.5vw, 118px);
}

h2 {
  margin: 0;
  font-size: clamp(36px, 5vw, 72px);
}

.lead {
  max-width: 620px;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.btn {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 14px 20px;
  font-weight: 800;
  cursor: pointer;
  transition: transform .2s ease, background .2s ease;
}

.btn:hover {
  transform: translateY(-2px);
}

.btn.primary {
  background: var(--gold);
  color: #1a1009;
}

.btn.secondary {
  color: var(--cream);
  background: rgba(255, 240, 210, .08);
}

.hero-media {
  position: relative;
  min-height: 560px;
}

.plate {
  position: absolute;
  border-radius: 50%;
  background:
    radial-gradient(circle at 50% 50%, #2a1710 0 22%, #f0d19a 23% 27%, #553021 28% 54%, #190f0b 55% 100%);
  box-shadow: 0 38px 90px rgba(0,0,0,.46);
}

.plate-one {
  width: 420px;
  height: 420px;
  top: 40px;
  right: 20px;
}

.plate-two {
  width: 230px;
  height: 230px;
  left: 20px;
  bottom: 60px;
  opacity: .85;
}

.steam {
  position: absolute;
  width: 90px;
  height: 180px;
  border-left: 3px solid rgba(255, 240, 210, .22);
  border-radius: 50%;
  animation: steam 3.8s ease-in-out infinite;
}

.steam-one { top: 8px; right: 200px; }
.steam-two { top: 36px; right: 125px; animation-delay: -1.4s; }

.hours-card {
  position: absolute;
  right: 28px;
  bottom: 38px;
  max-width: 330px;
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: 24px;
  background: rgba(29, 21, 16, .78);
  backdrop-filter: blur(18px);
}

.hours-card span, .hours-card p {
  color: var(--muted);
}

.hours-card strong {
  display: block;
  margin: 8px 0;
  font-size: 24px;
}

.menu-section, .story-section, .reserve-section, .gallery-section {
  width: min(1160px, calc(100% - 32px));
  margin: 30px auto;
  padding: clamp(30px, 5vw, 68px);
  border: 1px solid var(--line);
  border-radius: 34px;
  background: rgba(29, 21, 16, .72);
}

.section-title {
  max-width: 820px;
  margin-bottom: 28px;
}

.menu-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 22px;
}

.filter-button {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 10px 14px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}

.filter-button.active {
  background: var(--cream);
  color: #1a1009;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.dish-card {
  min-height: 260px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  border: 1px solid var(--line);
  border-radius: 28px;
  background:
    linear-gradient(to top, rgba(17,13,10,.95), rgba(17,13,10,.12)),
    radial-gradient(circle at 50% 25%, rgba(213,155,67,.32), transparent 36%),
    var(--wine);
  transition: transform .22s ease, border-color .22s ease;
}

.dish-card:hover {
  transform: translateY(-8px);
  border-color: rgba(213,155,67,.75);
}

.dish-card h3 {
  margin: 0 0 8px;
  font-size: 24px;
}

.dish-card p {
  color: var(--muted);
  line-height: 1.6;
}

.dish-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--gold);
  font-weight: 800;
}

.story-section {
  display: grid;
  grid-template-columns: .9fr 1.1fr;
  gap: 40px;
  align-items: center;
}

.story-section > p {
  color: var(--muted);
  font-size: 18px;
  line-height: 1.9;
}

.stats {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.stats div {
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 24px;
  background: rgba(255,240,210,.06);
}

.stats strong {
  display: block;
  font-family: "Playfair Display", Georgia, serif;
  font-size: 48px;
}

.stats span {
  color: var(--muted);
}

.gallery-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 220px;
  gap: 16px;
}

.gallery-card {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  background-image:
    linear-gradient(to top, rgba(17,13,10,.9), transparent),
    radial-gradient(circle at 50% 30%, rgba(213,155,67,.36), transparent 35%),
    linear-gradient(135deg, #442115, #130d0a);
}

.gallery-card.wide {
  grid-column: span 2;
}

.gallery-card.tall {
  grid-row: span 2;
}

.gallery-card span {
  position: absolute;
  left: 18px;
  bottom: 18px;
  font-weight: 800;
}

.reservation-form {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.reservation-form label {
  display: grid;
  gap: 8px;
  color: var(--muted);
  font-weight: 700;
}

.reservation-form .full {
  grid-column: 1 / -1;
}

input, textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: rgba(17,13,10,.64);
  color: var(--cream);
  padding: 14px 15px;
  font: inherit;
  outline: none;
}

textarea {
  min-height: 120px;
  resize: vertical;
}

input:focus, textarea:focus {
  border-color: var(--gold);
  box-shadow: 0 0 0 4px rgba(213,155,67,.12);
}

.form-status {
  min-height: 22px;
  color: var(--gold);
}

.footer {
  width: min(1160px, calc(100% - 32px));
  margin: 30px auto 42px;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  color: var(--muted);
}

.footer div {
  display: flex;
  gap: 16px;
}

@keyframes steam {
  0%, 100% { transform: translateY(20px) scale(.9); opacity: .15; }
  50% { transform: translateY(-18px) scale(1.1); opacity: .55; }
}

@media (max-width: 860px) {
  .topbar {
    border-radius: 24px;
    align-items: flex-start;
  }

  .menu-button {
    display: block;
    border: 1px solid var(--line);
    border-radius: 999px;
    background: transparent;
    color: var(--cream);
    padding: 10px 14px;
  }

  .nav {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    right: 0;
    display: none;
    flex-direction: column;
    padding: 14px;
    border: 1px solid var(--line);
    border-radius: 24px;
    background: rgba(17,13,10,.96);
  }

  .nav.open {
    display: flex;
  }

  .hero, .story-section {
    grid-template-columns: 1fr;
  }

  .hero {
    min-height: auto;
    padding-top: 30px;
  }

  .hero-media {
    min-height: 360px;
    order: -1;
  }

  .plate-one {
    width: 320px;
    height: 320px;
  }

  .hours-card {
    position: static;
    margin-top: 18px;
  }

  .menu-grid, .stats, .reservation-form {
    grid-template-columns: 1fr;
  }

  .gallery-section {
    grid-template-columns: 1fr;
  }

  .gallery-card.wide, .gallery-card.tall {
    grid-column: auto;
    grid-row: auto;
  }

  .footer {
    flex-direction: column;
  }
}
"""

    js = """const dishes = [
  { category: "Starters", name: "Charred Paneer Skewers", price: "₹280", detail: "Smoked spices, mint yoghurt, pickled onion." },
  { category: "Starters", name: "Crispy Calamari", price: "₹360", detail: "Lemon aioli, chilli dust, fresh herbs." },
  { category: "Mains", name: "Truffle Mushroom Risotto", price: "₹520", detail: "Arborio rice, parmesan, roasted mushrooms." },
  { category: "Mains", name: "Coastal Grill Platter", price: "₹740", detail: "Seasonal seafood, herb butter, grilled vegetables." },
  { category: "Desserts", name: "Saffron Panna Cotta", price: "₹260", detail: "Pistachio crumb, rose syrup, citrus zest." },
  { category: "Drinks", name: "Smoked Citrus Cooler", price: "₹190", detail: "Orange, lime, soda, smoked rosemary." },
];

const nav = document.querySelector("[data-nav]");
const menuButton = document.querySelector("[data-menu-button]");
const filters = document.querySelector("[data-menu-filters]");
const menuGrid = document.querySelector("[data-menu-grid]");
const form = document.querySelector("[data-reservation-form]");
const statusText = document.querySelector("[data-form-status]");

menuButton?.addEventListener("click", () => nav?.classList.toggle("open"));
document.querySelectorAll(".nav a").forEach((link) => link.addEventListener("click", () => nav?.classList.remove("open")));

function renderFilters() {
  const categories = ["All", ...new Set(dishes.map((dish) => dish.category))];
  filters.innerHTML = categories.map((category, index) => `
    <button class="filter-button ${index === 0 ? "active" : ""}" type="button" data-category="${category}">${category}</button>
  `).join("");

  filters.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      filters.querySelectorAll("button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      renderMenu(button.dataset.category);
    });
  });
}

function renderMenu(category = "All") {
  const visible = category === "All" ? dishes : dishes.filter((dish) => dish.category === category);
  menuGrid.innerHTML = visible.map((dish) => `
    <article class="dish-card">
      <div class="dish-meta"><span>${dish.category}</span><span>${dish.price}</span></div>
      <h3>${dish.name}</h3>
      <p>${dish.detail}</p>
    </article>
  `).join("");
}

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const name = String(data.get("name") || "").trim();
  const email = String(data.get("email") || "").trim();
  const guests = Number(data.get("guests") || 0);
  const date = String(data.get("date") || "").trim();

  if (!name || !email.includes("@") || guests < 1 || !date) {
    statusText.textContent = "Please add a valid name, email, guest count, and date.";
    return;
  }

  form.reset();
  statusText.textContent = `Reservation request received for ${name}. We will confirm by email.`;
});

renderFilters();
renderMenu();
"""

    return [
        {"path": "index.html", "content": html},
        {"path": "style.css", "content": css},
        {"path": "script.js", "content": js},
    ]


def _fallback_website_files(user_request: str, brief: dict) -> list[dict[str, str]]:
    if "restaurant" in str(brief.get("eyebrow", "")).lower():
        return _fallback_restaurant_files(user_request, brief)

    request_text = re.sub(r"\s+", " ", user_request).strip()
    safe_request = _html_escape(request_text)
    features_json = json.dumps(brief["features"], ensure_ascii=False)
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__BRAND__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <div class="loading-screen" data-loader>
    <div class="loader-ring"></div>
    <span>Initializing interface</span>
  </div>

  <header class="site-header">
    <a href="#home" class="brand" aria-label="__BRAND__ home">
      <span class="brand-mark">__INITIALS__</span>
      <span>__BRAND__</span>
    </a>
    <button class="menu-toggle" data-menu-toggle aria-label="Toggle navigation">
      <span></span><span></span><span></span>
    </button>
    <nav class="nav-links" data-nav>
      <a href="#home">Home</a>
      <a href="#features">Features</a>
      <a href="#about">About</a>
      <a href="#contact">Contact</a>
    </nav>
  </header>

  <main>
    <section class="hero section-panel" id="home">
      <div class="orb orb-one"></div>
      <div class="orb orb-two"></div>
      <div class="hero-copy reveal">
        <p class="eyebrow">__EYEBROW__</p>
        <h1><span data-typing></span><span class="cursor">|</span></h1>
        <p class="hero-description">
          __DESCRIPTION__
        </p>
        <div class="hero-actions">
          <a class="button primary" href="#contact">__PRIMARY_CTA__</a>
          <a class="button ghost" href="#features">__SECONDARY_CTA__</a>
        </div>
      </div>
      <div class="hero-card reveal">
        <div class="card-toolbar"><span></span><span></span><span></span></div>
        <div class="signal-grid">
          <div><strong>98%</strong><span>UI polish</span></div>
          <div><strong>24ms</strong><span>Motion feel</span></div>
          <div><strong>3x</strong><span>Launch speed</span></div>
        </div>
        <div class="glow-line"></div>
        <p>__CARD_TEXT__</p>
      </div>
    </section>

    <section class="section-panel features" id="features">
      <div class="section-heading reveal">
        <p class="eyebrow">Feature system</p>
        <h2>__FEATURE_HEADING__</h2>
      </div>
      <div class="feature-grid" data-feature-grid></div>
    </section>

    <section class="section-panel about" id="about">
      <div class="about-copy reveal">
        <p class="eyebrow">About</p>
        <h2>__ABOUT_HEADING__</h2>
        <p>
          __ABOUT_TEXT__
        </p>
        <div class="skill-tags">
          <button>HTML</button><button>CSS Grid</button><button>JavaScript</button><button>Animations</button><button>Responsive</button>
        </div>
      </div>
      <div class="about-meter reveal">
        <div class="meter-row"><span>Design</span><strong>95</strong></div>
        <div class="meter"><span style="width:95%"></span></div>
        <div class="meter-row"><span>Speed</span><strong>91</strong></div>
        <div class="meter"><span style="width:91%"></span></div>
        <div class="meter-row"><span>Conversion</span><strong>88</strong></div>
        <div class="meter"><span style="width:88%"></span></div>
      </div>
    </section>

    <section class="section-panel contact" id="contact">
      <div class="section-heading reveal">
        <p class="eyebrow">Contact</p>
        <h2>__CONTACT_HEADING__</h2>
      </div>
      <form class="contact-form reveal" data-contact-form>
        <label>Name<input name="name" type="text" placeholder="Your name" required /></label>
        <label>Email<input name="email" type="email" placeholder="you@example.com" required /></label>
        <label>Message<textarea name="message" placeholder="__CONTACT_MESSAGE__" required></textarea></label>
        <button class="button primary" type="submit">Submit request</button>
        <p class="form-status" data-form-status></p>
      </form>
    </section>
  </main>

  <footer class="site-footer">
    <p>Copyright 2026 __BRAND__. Built by JX Jarvis.</p>
    <div><a href="#home">Top</a><a href="#features">Features</a><a href="#contact">Contact</a></div>
  </footer>

  <script src="script.js"></script>
</body>
</html>
"""
    replacements = {
        "__REQUEST__": safe_request,
        "__BRAND__": _html_escape(brief["brand"]),
        "__INITIALS__": _html_escape(brief["initials"]),
        "__EYEBROW__": _html_escape(brief["eyebrow"]),
        "__DESCRIPTION__": _html_escape(brief["description"]),
        "__PRIMARY_CTA__": _html_escape(brief["primaryCta"]),
        "__SECONDARY_CTA__": _html_escape(brief["secondaryCta"]),
        "__CARD_TEXT__": _html_escape(brief["cardText"]),
        "__FEATURE_HEADING__": _html_escape(brief["featureHeading"]),
        "__ABOUT_HEADING__": _html_escape(brief["aboutHeading"]),
        "__ABOUT_TEXT__": _html_escape(brief["aboutText"]),
        "__CONTACT_HEADING__": _html_escape(brief["contactHeading"]),
        "__CONTACT_MESSAGE__": _html_escape(brief["contactMessage"]),
    }
    for source, target in replacements.items():
        html = html.replace(source, target)

    css = """* {
  box-sizing: border-box;
}

:root {
  color-scheme: dark;
  --bg: #050713;
  --panel: rgba(255, 255, 255, 0.075);
  --panel-strong: rgba(255, 255, 255, 0.12);
  --line: rgba(255, 255, 255, 0.16);
  --text: #f5f7fb;
  --muted: #a7b2c7;
  --cyan: #18e3ff;
  --pink: #ff4ecd;
  --green: #6dffb3;
  --shadow: 0 26px 80px rgba(0, 0, 0, 0.42);
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--text);
  background-color: var(--bg);
  background-image:
    radial-gradient(circle at 15% 8%, rgba(24, 227, 255, 0.22), transparent 28%),
    radial-gradient(circle at 82% 12%, rgba(255, 78, 205, 0.18), transparent 25%),
    linear-gradient(135deg, #050713 0%, #0b1326 52%, #070816 100%);
  overflow-x: hidden;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
  background-size: 58px 58px;
  mask-image: linear-gradient(to bottom, black, transparent 75%);
}

a {
  color: inherit;
  text-decoration: none;
}

.loading-screen {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  gap: 16px;
  background: #050713;
  transition: opacity .55s ease, visibility .55s ease;
}

.loading-screen.hidden {
  opacity: 0;
  visibility: hidden;
}

.loader-ring {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  border: 3px solid rgba(255,255,255,.12);
  border-top-color: var(--cyan);
  animation: spin 1s linear infinite;
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(1180px, calc(100% - 32px));
  margin: 18px auto 0;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 22px;
  background: rgba(8, 12, 27, .68);
  backdrop-filter: blur(18px);
  box-shadow: var(--shadow);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--cyan), var(--pink));
  color: #06101d;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-links a {
  padding: 10px 13px;
  border-radius: 14px;
  color: var(--muted);
  transition: color .2s ease, background .2s ease;
}

.nav-links a:hover {
  color: var(--text);
  background: rgba(255,255,255,.08);
}

.menu-toggle {
  display: none;
  width: 42px;
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(255,255,255,.06);
}

.menu-toggle span {
  display: block;
  width: 18px;
  height: 2px;
  margin: 4px auto;
  background: var(--text);
}

.section-panel {
  position: relative;
  width: min(1180px, calc(100% - 32px));
  margin: 22px auto;
  padding: clamp(34px, 6vw, 80px);
  border: 1px solid var(--line);
  border-radius: 28px;
  background: linear-gradient(145deg, rgba(255,255,255,.095), rgba(255,255,255,.035));
  box-shadow: var(--shadow);
  overflow: hidden;
}

.hero {
  min-height: 720px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(300px, .8fr);
  align-items: center;
  gap: 42px;
}

.eyebrow {
  margin: 0 0 12px;
  color: var(--green);
  text-transform: uppercase;
  letter-spacing: .16em;
  font-size: 12px;
  font-weight: 800;
}

h1, h2 {
  margin: 0;
  letter-spacing: 0;
  line-height: 1.02;
}

h1 {
  min-height: 174px;
  font-size: clamp(52px, 8vw, 104px);
}

h2 {
  font-size: clamp(34px, 5vw, 64px);
}

.cursor {
  color: var(--cyan);
  animation: blink .8s infinite;
}

.hero-description, .about-copy p {
  max-width: 690px;
  color: var(--muted);
  font-size: 18px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 0 18px;
  border: 1px solid var(--line);
  border-radius: 16px;
  font-weight: 800;
  transition: transform .2s ease, box-shadow .2s ease, background .2s ease;
}

.button:hover {
  transform: translateY(-2px);
}

.button.primary {
  background: linear-gradient(135deg, var(--cyan), var(--pink));
  color: #06101d;
  box-shadow: 0 18px 46px rgba(24, 227, 255, .18);
}

.button.ghost {
  background: rgba(255,255,255,.055);
  color: var(--text);
}

.hero-card {
  min-height: 360px;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 24px;
  background: rgba(2, 8, 23, .46);
  backdrop-filter: blur(22px);
}

.card-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 30px;
}

.card-toolbar span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--cyan);
}

.card-toolbar span:nth-child(2) { background: var(--pink); }
.card-toolbar span:nth-child(3) { background: var(--green); }

.signal-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.signal-grid div, .feature-card, .about-meter, .contact-form {
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255,255,255,.06);
}

.signal-grid div {
  padding: 16px;
}

.signal-grid strong {
  display: block;
  font-size: 28px;
}

.signal-grid span, .hero-card p {
  color: var(--muted);
}

.glow-line {
  height: 3px;
  margin: 30px 0;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--cyan), var(--pink), var(--green));
  box-shadow: 0 0 30px rgba(24,227,255,.45);
}

.orb {
  position: absolute;
  width: 210px;
  height: 210px;
  border-radius: 999px;
  filter: blur(6px);
  opacity: .55;
  animation: float 8s ease-in-out infinite;
}

.orb-one {
  top: 80px;
  right: 18%;
  background: radial-gradient(circle, rgba(24,227,255,.45), transparent 68%);
}

.orb-two {
  bottom: 70px;
  left: 10%;
  background: radial-gradient(circle, rgba(255,78,205,.36), transparent 68%);
  animation-delay: -3s;
}

.section-heading {
  max-width: 760px;
  margin-bottom: 28px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.feature-card {
  padding: 24px;
  min-height: 230px;
  transition: transform .24s ease, border-color .24s ease, background .24s ease;
}

.feature-card:hover {
  transform: translateY(-8px);
  border-color: rgba(24,227,255,.55);
  background: rgba(24,227,255,.08);
}

.feature-icon {
  display: grid;
  place-items: center;
  width: 50px;
  height: 50px;
  margin-bottom: 20px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(24,227,255,.22), rgba(255,78,205,.18));
  font-size: 24px;
}

.feature-card p {
  color: var(--muted);
  line-height: 1.7;
}

.about {
  display: grid;
  grid-template-columns: 1fr .82fr;
  gap: 34px;
  align-items: center;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.skill-tags button {
  border: 1px solid var(--line);
  border-radius: 999px;
  background: rgba(255,255,255,.06);
  color: var(--text);
  padding: 10px 14px;
}

.about-meter {
  padding: 24px;
}

.meter-row {
  display: flex;
  justify-content: space-between;
  margin: 18px 0 8px;
}

.meter {
  height: 12px;
  border-radius: 999px;
  background: rgba(255,255,255,.08);
  overflow: hidden;
}

.meter span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--cyan), var(--pink));
}

.contact-form {
  display: grid;
  gap: 16px;
  padding: 24px;
}

.contact-form label {
  display: grid;
  gap: 8px;
  color: var(--muted);
  font-weight: 700;
}

.contact-form input, .contact-form textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(0,0,0,.22);
  color: var(--text);
  padding: 14px 15px;
  font: inherit;
  outline: none;
}

.contact-form textarea {
  min-height: 130px;
  resize: vertical;
}

.contact-form input:focus, .contact-form textarea:focus {
  border-color: var(--cyan);
  box-shadow: 0 0 0 4px rgba(24,227,255,.1);
}

.form-status {
  min-height: 24px;
  margin: 0;
  color: var(--green);
}

.site-footer {
  display: flex;
  justify-content: space-between;
  width: min(1180px, calc(100% - 32px));
  margin: 18px auto 32px;
  color: var(--muted);
}

.site-footer div {
  display: flex;
  gap: 16px;
}

.reveal {
  opacity: 0;
  transform: translateY(22px);
  transition: opacity .65s ease, transform .65s ease;
}

.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes blink { 50% { opacity: 0; } }
@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-22px) scale(1.04); }
}

@media (max-width: 860px) {
  .site-header {
    align-items: flex-start;
  }
  .menu-toggle {
    display: block;
  }
  .nav-links {
    position: absolute;
    top: calc(100% + 10px);
    left: 0;
    right: 0;
    display: none;
    flex-direction: column;
    align-items: stretch;
    padding: 14px;
    border: 1px solid var(--line);
    border-radius: 20px;
    background: rgba(8, 12, 27, .94);
  }
  .nav-links.open {
    display: flex;
  }
  .hero, .about {
    grid-template-columns: 1fr;
  }
  .feature-grid {
    grid-template-columns: 1fr;
  }
  h1 {
    min-height: 150px;
  }
  .site-footer {
    flex-direction: column;
    gap: 10px;
  }
}
"""

    js = """const features = __FEATURES_JSON__;

const loader = document.querySelector("[data-loader]");
const nav = document.querySelector("[data-nav]");
const menuToggle = document.querySelector("[data-menu-toggle]");
const typingTarget = document.querySelector("[data-typing]");
const featureGrid = document.querySelector("[data-feature-grid]");
const contactForm = document.querySelector("[data-contact-form]");
const formStatus = document.querySelector("[data-form-status]");
const headline = __HEADLINE_JSON__;

window.addEventListener("load", () => {
  setTimeout(() => loader?.classList.add("hidden"), 550);
});

menuToggle?.addEventListener("click", () => {
  nav?.classList.toggle("open");
  menuToggle.classList.toggle("active");
});

document.querySelectorAll("a[href^='#']").forEach((link) => {
  link.addEventListener("click", () => nav?.classList.remove("open"));
});

function typeHeadline(index = 0) {
  if (!typingTarget) return;
  typingTarget.textContent = headline.slice(0, index);
  if (index < headline.length) {
    window.setTimeout(() => typeHeadline(index + 1), 46);
  }
}

function renderFeatures() {
  if (!featureGrid) return;
  featureGrid.innerHTML = features
    .filter((feature) => feature.title && feature.body)
    .map((feature) => `
      <article class="feature-card reveal" data-title="${feature.title}">
        <div class="feature-icon">${feature.icon}</div>
        <h3>${feature.title}</h3>
        <p>${feature.body}</p>
      </article>
    `)
    .join("");

  featureGrid.querySelectorAll(".feature-card").forEach((card) => {
    card.addEventListener("click", () => {
      featureGrid.querySelectorAll(".feature-card").forEach((item) => item.classList.remove("selected"));
      card.classList.add("selected");
    });
  });
}

function setupRevealAnimations() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.18 },
  );

  document.querySelectorAll(".reveal").forEach((item) => observer.observe(item));
}

contactForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(contactForm);
  const name = String(data.get("name") || "").trim();
  const email = String(data.get("email") || "").trim();
  const message = String(data.get("message") || "").trim();

  if (!name || !email.includes("@") || message.length < 8) {
    formStatus.textContent = "Add a valid name, email, and project message.";
    formStatus.style.color = "#ff8ba7";
    return;
  }

  contactForm.reset();
  formStatus.style.color = "#6dffb3";
  formStatus.textContent = `Thanks ${name}. Your request is ready to send.`;
});

renderFeatures();
typeHeadline();
requestAnimationFrame(setupRevealAnimations);
""".replace("__FEATURES_JSON__", features_json).replace("__HEADLINE_JSON__", json.dumps(brief["headline"]))

    return [
        {"path": "index.html", "content": html},
        {"path": "style.css", "content": css},
        {"path": "script.js", "content": js},
    ]


def _retry_code_request(user_request: str, reason: str, files: list[dict]) -> str:
    file_summary = ", ".join(str(item.get("path") or "unknown") for item in files[:6] if isinstance(item, dict))
    return (
        f"{user_request}\n\n"
        "The previous code output was rejected by validation and must be rebuilt from scratch.\n"
        f"Validation reason: {reason}\n"
        f"Previous files: {file_summary or 'none'}\n\n"
        "Return a complete replacement project as valid JSON only. For websites, build a finished dynamic page with "
        "data-rendered sections, filtering/search or tabs, form validation, responsive CSS, "
        "real content, and real visual treatment. Do not use Project 1/Project 2/sample content, picsum.photos, "
        "placeholder images, empty links, tiny starter code, or generic reusable templates. Match the user's exact niche and visual request.\n\n"
        f"Visual contract:\n{_prompt_style_contract(user_request)}"
    )


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

        normalized = _normalize_file_item(item)
        relative_path = _safe_relative_path(normalized["path"])
        content = normalized["content"][:MAX_FILE_CHARS]
        if not content.strip():
            continue

        file_path = project_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8", newline="\n")
        written.append(file_path)
    return written


def _has_usable_file_content(files: list[dict]) -> bool:
    for item in files:
        if not isinstance(item, dict):
            continue
        content = _normalize_file_item(item)["content"].strip()
        if len(content) >= 40:
            return True
    return False


def _repair_website_files_with_ai(user_request: str, reason: str) -> list[dict[str, str]]:
    if not _is_website_request(user_request.lower()) and "html" not in user_request.lower():
        return []

    try:
        return [
            {"path": "index.html", "content": _generate_single_project_file(user_request, reason, "index.html", _html_file_instruction(user_request))},
            {"path": "style.css", "content": _generate_single_project_file(user_request, reason, "style.css", _css_file_instruction(user_request))},
            {"path": "script.js", "content": _generate_single_project_file(user_request, reason, "script.js", _js_file_instruction(user_request))},
        ]
    except Exception:
        return []


def _validated_repair_website_files(user_request: str, reason: str) -> list[dict[str, str]]:
    repaired = _repair_website_files_with_ai(user_request, reason)
    if not repaired:
        return []
    try:
        _validate_generated_project(user_request, repaired)
        return repaired
    except RuntimeError as error:
        stronger_reason = (
            f"{reason}\n\nThe first repair still failed visual validation: {error}\n"
            "Regenerate with a noticeably custom visual system that matches the user's exact prompt."
        )
        repaired = _repair_website_files_with_ai(user_request, stronger_reason)
        if not repaired:
            return []
        try:
            _validate_generated_project(user_request, repaired)
            return repaired
        except RuntimeError:
            return []


def _generate_single_project_file(user_request: str, reason: str, path: str, instruction: str) -> str:
    from api.ai_provider import chat_ai_messages

    raw = chat_ai_messages(
        task_type="coding",
        temperature=0.28,
        max_tokens=5200,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are JX Jarvis generating exactly one project file for a local website build. "
                    "Return only the complete file content. Do not use markdown fences. Do not explain. "
                    "Do not return an empty file. Do not use generic reusable templates. Follow the user's exact niche, style, and feature request. "
                    "Reject plain browser-default output: no default blue link nav, no bullet menus, no unstyled white cards, "
                    "no broken image URLs, and no overlapping text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original user request:\n{user_request}\n\n"
                    f"Repair reason:\n{reason}\n\n"
                    f"Generate this file only: {path}\n\n"
                    f"File requirements:\n{instruction}"
                ),
            },
        ],
    )
    content = _strip_code_fence(raw).strip()
    if len(content) < 40:
        raise RuntimeError(f"{path} came back empty.")
    return content


def _strip_code_fence(text: str) -> str:
    match = re.search(r"```[^\n`]*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def _html_file_instruction(user_request: str) -> str:
    return (
        "Create complete semantic HTML for the requested website. Link to style.css and script.js. "
        "Include real sections matching the prompt, not generic placeholders. Include nav, hero, feature/product/service sections as relevant, "
        "contact/booking/cart area as relevant, and accessible text. Do not inline CSS or JS except tiny unavoidable attributes. "
        + _prompt_style_contract(user_request)
    )


def _css_file_instruction(user_request: str) -> str:
    return (
        "Create polished responsive CSS matching the prompt's visual style. Include desktop and mobile layouts, meaningful typography, "
        "hover states, animations, and niche-appropriate colors. Do not reuse a generic cyan-purple startup layout unless the user asked for that exact style. "
        "Style every nav/list/form/card so the page never looks like raw HTML. "
        + _prompt_style_contract(user_request)
    )


def _js_file_instruction(user_request: str) -> str:
    return (
        "Create JavaScript for real interactions matching the prompt: render dynamic cards/data when useful, menu toggle, filters/tabs/cart/gallery/booking validation as relevant, "
        "smooth scrolling helpers, and visible UI state updates. Do not use localStorage unless the user explicitly asks to save data. "
        + _prompt_style_contract(user_request)
    )


def _normalize_file_item(item: dict) -> dict[str, str]:
    path = str(
        item.get("path")
        or item.get("filename")
        or item.get("file")
        or item.get("name")
        or item.get("filepath")
        or item.get("file_path")
        or "main.txt"
    )
    content = str(
        item.get("content")
        or item.get("code")
        or item.get("source")
        or item.get("text")
        or item.get("body")
        or ""
    )
    return {"path": path, "content": content}


def _validate_generated_project(user_request: str, files: list[dict]) -> None:
    normalized = user_request.lower()
    issues: list[str] = []

    if _is_website_request(normalized):
        if _is_weak_generated_project(files, minimum_chars=7600):
            issues.append("the project has too little complete website code")
        if not _has_website_visual_assets(files):
            issues.append("it is missing real visual treatment such as images, rich backgrounds, or generated visual panels")
        if not _has_professional_website_css(files):
            issues.append("the CSS is too plain and still looks like default browser HTML")
        issues.extend(_prompt_theme_issues(normalized, files))
        if _expects_dynamic_site(normalized) and not _has_dynamic_website_behavior(files):
            issues.append("the prompt asked for interactive/dynamic behavior, but the JavaScript is too weak")
    elif _is_snake_game_request(normalized) and _is_weak_generated_project(files, minimum_chars=5200):
        issues.append("the game project is too incomplete")
    elif _is_app_or_tool_request(normalized) and _is_weak_generated_project(files, minimum_chars=4200):
        issues.append("the app/tool project is too incomplete")

    if issues:
        raise RuntimeError("The generated project failed validation: " + "; ".join(issues[:6]) + ".")


def _is_generation_error(spec: dict, files: list[dict]) -> bool:
    project_name = str(spec.get("project_name") or "").lower()
    summary = str(spec.get("summary") or "").lower()
    if not files and ("failed" in project_name or "missing-provider" in project_name):
        return True
    failure_markers = (
        "request failed",
        "no configured ai provider",
        "add a key",
        "missing provider",
        "missing-provider",
    )
    return not files and any(marker in summary or marker in project_name for marker in failure_markers)


def _is_website_request(normalized: str) -> bool:
    return any(word in normalized for word in ("website", "web site", "webpage", "web page", "landing page", "portfolio"))


def _is_snake_game_request(normalized: str) -> bool:
    return "snake" in normalized and any(word in normalized for word in ("game", "website", "web", "app", "code"))


def _prompt_style_contract(user_request: str) -> str:
    normalized = user_request.lower()
    rules = [
        "The final page must look custom-built for this exact prompt, not like a saved template.",
        "Avoid raw HTML defaults: no blue link menu, bullet navigation, tiny unstyled inputs, broken images, or overlapping content.",
    ]

    if _has_any(normalized, ("dark", "black", "night", "cinematic", "luxury")):
        rules.append("Use a visibly dark visual system with light text, layered backgrounds, and strong contrast.")
    if _has_any(normalized, ("luxury", "premium", "elegant")):
        rules.append("Add premium typography, careful spacing, and refined accent colors instead of a basic startup look.")
    if _has_any(normalized, ("glass", "glassmorphism", "blur")):
        rules.append("Use translucent panels with rgba backgrounds, border highlights, and backdrop-filter blur.")
    if _has_any(normalized, ("neon", "glow", "glowing")):
        rules.append("Use glow effects through box-shadow/text-shadow/filter while keeping readability clean.")
    if _has_any(normalized, ("animated", "animation", "smooth", "parallax", "cinematic")):
        rules.append("Include CSS animations/transitions and JavaScript scroll or reveal behavior where useful.")
    if _has_any(normalized, ("food", "restaurant", "delivery", "menu", "dish")):
        rules.append("Use food/restaurant-specific sections, menu cards, order/booking flows, and appetizing visual language.")
    if _has_any(normalized, ("ecommerce", "e-commerce", "shop", "shopping", "product", "cart")):
        rules.append("Use product cards, prices, cart state, checkout/order controls, and store-focused layout.")
    if _has_any(normalized, ("travel", "destination", "booking", "gallery", "agency")):
        rules.append("Use destination cards, cinematic travel imagery/panels, gallery, itinerary/booking sections.")
    if _has_any(normalized, ("gym", "fitness", "workout", "trainer")):
        rules.append("Use workout plans, trainer cards, energetic fitness typography, and strong action-focused sections.")

    return " ".join(f"{index}. {rule}" for index, rule in enumerate(rules, start=1))


def _combined_files_text(files: list[dict]) -> str:
    return "\n".join(_normalize_file_item(item)["content"] for item in files if isinstance(item, dict))


def _file_content_by_suffix(files: list[dict], suffixes: tuple[str, ...]) -> str:
    chunks: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        normalized = _normalize_file_item(item)
        if normalized["path"].lower().endswith(suffixes):
            chunks.append(normalized["content"])
    return "\n".join(chunks)


def _has_website_visual_assets(files: list[dict]) -> bool:
    combined = _combined_files_text(files).lower()
    if not combined.strip():
        return False

    visual_markers = (
        "<img",
        "<picture",
        "background-image:",
        "image-set(",
        "images.unsplash.com",
        "images.pexels.com",
        "linear-gradient",
        "radial-gradient",
        "conic-gradient",
        "canvas",
        "svg",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".avif",
    )
    blocked_placeholders = (
        "image here",
        "placeholder image",
        "picsum.photos",
        "placehold.co",
        "placeholder.com",
        "your image",
        "gray box",
        "grey box",
    )
    return any(marker in combined for marker in visual_markers) and not any(
        placeholder in combined for placeholder in blocked_placeholders
    )


def _expects_dynamic_site(normalized: str) -> bool:
    return any(word in normalized for word in ("dynamic", "interactive", "filter", "search", "dashboard", "app-like", "cart", "booking", "gallery", "menu toggle"))


def _has_dynamic_website_behavior(files: list[dict]) -> bool:
    combined = _combined_files_text(files).lower()
    dynamic_markers = (
        "addeventlistener",
        "localstorage",
        "sessionstorage",
        "queryselector",
        "createelement",
        ".map(",
        ".filter(",
        "dataset",
        "formdata",
        "intersectionobserver",
        "classlist",
    )
    return sum(marker in combined for marker in dynamic_markers) >= 4


def _has_professional_website_css(files: list[dict]) -> bool:
    css = _file_content_by_suffix(files, (".css",)).lower()
    html = _file_content_by_suffix(files, (".html", ".htm")).lower()
    combined = (css + "\n" + html).lower()
    if len(css) < 2400:
        return False

    layout_markers = ("display: flex", "display:flex", "display: grid", "display:grid", "grid-template", "minmax(")
    responsive_markers = ("@media", "clamp(", "min(", "max(")
    polish_markers = ("transition", ":hover", "@keyframes", "animation", "transform", "box-shadow", "backdrop-filter")
    reset_markers = ("box-sizing", "margin: 0", "margin:0", "list-style", "text-decoration")

    if not any(marker in css for marker in layout_markers):
        return False
    if not any(marker in css for marker in responsive_markers):
        return False
    if sum(marker in css for marker in polish_markers) < 2:
        return False
    if sum(marker in css for marker in reset_markers) < 2:
        return False
    if "<ul" in html and "list-style" not in css and "nav" not in css:
        return False
    if "<form" in html and not any(marker in css for marker in ("input", "textarea", "select", "form-control")):
        return False
    if "body {" in css and "background: #fff" in css and not any(marker in combined for marker in ("dark", "luxury", "gradient", "image", "hero")):
        return False
    return True


def _prompt_theme_issues(normalized: str, files: list[dict]) -> list[str]:
    combined = _combined_files_text(files).lower()
    css = _file_content_by_suffix(files, (".css",)).lower()
    issues: list[str] = []

    if _has_any(normalized, ("dark", "black", "night", "cinematic")) and not _has_any(
        css,
        ("#0", "#111", "#121", "#151", "#171", "rgb(0", "rgb(1", "rgb(2", "color-scheme: dark", "linear-gradient", "radial-gradient"),
    ):
        issues.append("the prompt asked for a dark/cinematic theme, but the CSS does not create one")
    if _has_any(normalized, ("luxury", "premium", "elegant")) and not _has_any(
        combined,
        ("gold", "#d4", "#c9", "#f5d", "serif", "playfair", "cinzel", "letter-spacing", "premium", "luxury"),
    ):
        issues.append("the prompt asked for a premium/luxury feel, but the styling lacks premium visual cues")
    if _has_any(normalized, ("glass", "glassmorphism", "blur")) and not _has_any(css, ("backdrop-filter", "rgba(", "blur(")):
        issues.append("the prompt asked for glassmorphism, but the CSS lacks translucent blur panels")
    if _has_any(normalized, ("neon", "glow", "glowing")) and not _has_any(css, ("box-shadow", "text-shadow", "drop-shadow", "glow")):
        issues.append("the prompt asked for glowing/neon UI, but no glow styling is present")
    if _has_any(normalized, ("animated", "animation", "smooth", "parallax", "cinematic")) and not _has_any(
        combined,
        ("@keyframes", "animation", "transition", "intersectionobserver", "parallax", "requestanimationframe", "transform"),
    ):
        issues.append("the prompt asked for animations/smooth effects, but the files lack animation behavior")
    if _has_any(normalized, ("food", "restaurant", "delivery", "dish", "menu")) and not _has_any(
        combined,
        ("menu", "dish", "chef", "order", "delivery", "restaurant", "flavor", "meal"),
    ):
        issues.append("the content does not match the requested food/restaurant website")
    if _has_any(normalized, ("ecommerce", "e-commerce", "shop", "shopping", "product", "cart")) and not (
        "product" in combined and "cart" in combined
    ):
        issues.append("the prompt asked for ecommerce, but product/cart UI is missing")
    if _has_any(normalized, ("travel", "destination", "booking", "gallery", "agency")) and not _has_any(
        combined,
        ("destination", "travel", "gallery", "booking", "itinerary", "journey", "escape"),
    ):
        issues.append("the content does not match the requested travel website")
    if _has_any(normalized, ("gym", "fitness", "workout", "trainer")) and not _has_any(
        combined,
        ("workout", "trainer", "fitness", "gym", "program", "strength"),
    ):
        issues.append("the content does not match the requested gym/fitness website")

    return issues


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


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

    normalized_items = [_normalize_file_item(item) for item in files if isinstance(item, dict)]
    paths = [item["path"].lower() for item in normalized_items]
    contents = [item["content"] for item in normalized_items]
    combined = "\n".join(contents).lower()

    placeholder_terms = (
        "project 1",
        "project 2",
        "project 3",
        "sample project",
        "another sample project",
        "this is a description",
        "welcome to my portfolio",
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
            return _normalize_project_spec(parsed)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return _normalize_project_spec(parsed)
        except json.JSONDecodeError:
            pass

    files = _extract_fenced_files(text)

    return {
        "project_name": "jarvis-code",
        "summary": "Generated code from the assistant response.",
        "files": files,
    }


def _normalize_project_spec(spec: dict) -> dict:
    normalized = dict(spec)
    raw_files = spec.get("files")
    files: list[dict[str, str]] = []

    if isinstance(raw_files, list):
        for item in raw_files:
            if isinstance(item, dict):
                files.append(_normalize_file_item(item))
    elif isinstance(raw_files, dict):
        for path, content in raw_files.items():
            files.append({"path": str(path), "content": str(content or "")})

    top_level_map = {
        "html": "index.html",
        "index_html": "index.html",
        "index.html": "index.html",
        "css": "style.css",
        "style_css": "style.css",
        "styles_css": "styles.css",
        "style.css": "style.css",
        "styles.css": "styles.css",
        "js": "script.js",
        "javascript": "script.js",
        "script_js": "script.js",
        "script.js": "script.js",
        "app.js": "app.js",
    }
    existing = {item["path"].lower().replace("\\", "/") for item in files}
    for key, path in top_level_map.items():
        value = spec.get(key)
        if value and path.lower() not in existing:
            files.append({"path": path, "content": str(value)})
            existing.add(path.lower())

    normalized["files"] = _merge_duplicate_file_blocks(files)
    return normalized


def _extract_fenced_files(text: str) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    used_paths: set[str] = set()
    blocks = list(re.finditer(r"```([^\n`]*)\n(.*?)```", text, re.DOTALL))
    for index, block in enumerate(blocks, start=1):
        info = block.group(1).strip()
        content = block.group(2).strip()
        if not content:
            continue
        before = text[max(0, block.start() - 180) : block.start()]
        path = _path_from_code_block(info, before, content, index, used_paths)
        used_paths.add(path.lower().replace("\\", "/"))
        files.append({"path": path, "content": content})
    return _merge_duplicate_file_blocks(files)


def _path_from_code_block(info: str, before: str, content: str, index: int, used_paths: set[str]) -> str:
    candidate = _extract_path_candidate(info) or _extract_path_candidate(before)
    if candidate:
        return candidate

    language = info.split()[0].lower() if info else ""
    extension = LANGUAGE_EXTENSIONS.get(language)
    lowered = content.lower()
    if not extension:
        if "<!doctype" in lowered or "<html" in lowered:
            extension = "html"
        elif "{" in content and (":" in content or ";" in content) and any(marker in lowered for marker in ("body", "color", "display", "font-")):
            extension = "css"
        elif any(marker in lowered for marker in ("document.", "queryselector", "addeventlistener", "const ", "let ")):
            extension = "js"
        else:
            extension = "txt"

    preferred = {
        "html": "index.html",
        "css": "style.css",
        "js": "script.js",
        "javascript": "script.js",
        "json": "data.json",
        "md": "README.md",
    }.get(extension, f"main-{index}.{extension}")
    if preferred.lower() not in used_paths:
        return preferred
    return f"main-{index}.{extension}"


def _extract_path_candidate(text: str) -> str | None:
    patterns = (
        r"(?:path|file|filename)\s*[:=]\s*[`'\"]?([A-Za-z0-9_.\-/\\ ]+\.[A-Za-z0-9]{1,8})",
        r"[`'\"]([A-Za-z0-9_.\-/\\ ]+\.[A-Za-z0-9]{1,8})[`'\"]",
        r"\b([A-Za-z0-9_.\-/\\ ]+\.(?:html|css|js|jsx|ts|tsx|json|md|py))\b",
    )
    for pattern in patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for match in reversed(matches):
            path = " ".join(match.group(1).strip().split())
            if path and not path.lower().startswith(("http:", "https:")):
                return path.replace("\\", "/")
    return None


def _merge_duplicate_file_blocks(files: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for item in files:
        path = str(item.get("path") or "main.txt")
        key = path.lower().replace("\\", "/")
        if key not in merged:
            merged[key] = item
            order.append(key)
            continue
        if len(str(item.get("content") or "")) > len(str(merged[key].get("content") or "")):
            merged[key] = item
    return [merged[key] for key in order]


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
            port = _find_free_port()
            if _start_static_server(project_dir, port):
                webbrowser.open(f"http://127.0.0.1:{port}/{name}")
                return True
            webbrowser.open(candidate.resolve().as_uri())
            return True
    return False


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_static_server(project_dir: Path, port: int) -> bool:
    try:
        subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
            cwd=project_dir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW) if os.name == "nt" else 0,
        )
        return True
    except (FileNotFoundError, OSError):
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
