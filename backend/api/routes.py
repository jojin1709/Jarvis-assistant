from flask import Blueprint, jsonify, request

from api.ai_provider import ask_ai, ask_ai_code_project, provider_label
from api.approvals import resolve_approval
from api.code_writer import create_code_project, create_portfolio_project, extract_code_request, is_portfolio_request
from api.file_ingest import save_and_analyze
from api.language import (
    command_language_instruction,
    detect_language,
    localize_response,
    normalize_command_to_english,
    normalize_language_mode,
    resolve_language,
)
from api.memory import handle_memory_command, memory_context, profile_summary, user_display_name
from api.system_tasks import (
    TASKS,
    extract_file_search,
    extract_google_search,
    extract_youtube_search,
    match_system_command,
    open_google_search,
    run_open_target_action,
    run_system_task,
    run_local_file_action,
    search_user_files,
    search_youtube,
)
from app.config import settings
from voice.recognizer import VoiceRecognizer
from voice.speaker import EdgeSpeaker

router = Blueprint("api", __name__, url_prefix="/api")
recognizer = VoiceRecognizer()
speaker = EdgeSpeaker()

state = {
    "status": "online",
    "detail": "JX JARVIS core systems online.",
}


def set_state(status: str, detail: str) -> None:
    state["status"] = status
    state["detail"] = detail


@router.get("/health")
def health():
    return jsonify(status="online", detail="Backend link established.", profile=profile_summary(settings.owner_name))


@router.get("/status")
def status():
    return jsonify(status=state["status"], detail=state["detail"])


def startup_greeting() -> str:
    hour = __import__("datetime").datetime.now().hour
    if 4 <= hour < 12:
        period = "Good morning"
    elif 12 <= hour < 17:
        period = "Good afternoon"
    elif 17 <= hour < 23:
        period = "Good evening"
    else:
        period = "Good night"

    return (
        f"{period}, {user_display_name(settings.owner_name)}. JX JARVIS is online. "
        f"Voice systems, Malayalam and English input, file intake, {provider_label()} intelligence, "
        "and desktop operations are ready."
    )


@router.post("/assistant/greet")
def greet():
    response = startup_greeting()
    set_state("speaking", "Startup greeting active.")
    audio_file = str(speaker.speak(response))
    set_state("online", "Awaiting next command.")
    return jsonify(transcript="startup greeting", response=response, audio_file=audio_file, status="complete")


def wake_command_from(text: str) -> tuple[bool, str]:
    normalized = " ".join(text.lower().strip().split())
    wake_phrases = (
        "hey jarvis",
        "hi jarvis",
        "hello jarvis",
        "ok jarvis",
        "okay jarvis",
        "jarvis",
        "ഹേ ജാർവിസ്",
        "ഹായ് ജാർവിസ്",
        "ജാർവിസ്",
        "ജാര്‍വിസ്",
    )

    for phrase in wake_phrases:
        if phrase in normalized:
            command = normalized.split(phrase, 1)[1].strip(" ,:.-")
            return True, command
    return False, ""


def finish_response(response: str, language: str, speak_response: bool, speak_limit: int | None = None) -> dict[str, str | None]:
    localized = localize_response(response, language)
    audio_file = None
    if speak_response:
        set_state("speaking", "Voice response active.")
        speech_text = localized[:speak_limit] if speak_limit else localized
        audio_file = str(speaker.speak(speech_text, language=language))
    set_state("online", "Awaiting next command.")
    return {"response": localized, "audio_file": audio_file}


def run_text_command(
    text: str,
    speak_response: bool = True,
    speak_limit: int | None = None,
    language_mode: str = "auto",
) -> dict[str, str | None]:
    language = resolve_language(text, language_mode)
    command_text = normalize_command_to_english(text, language)

    approval_response = resolve_approval(command_text)
    if approval_response:
        set_state("executing", "Confirmed action executed.")
        return finish_response(approval_response, language, speak_response, speak_limit=450)

    memory_response = handle_memory_command(command_text)
    if memory_response:
        set_state("memory", "Memory updated.")
        return finish_response(memory_response, language, speak_response, speak_limit=450)

    code_request = extract_code_request(command_text)
    if code_request:
        set_state("coding", "Generating code workspace and opening VS Code.")
        if is_portfolio_request(code_request):
            response = create_portfolio_project(code_request)
        else:
            model_response = ask_ai_code_project(code_request)
            response = create_code_project(code_request, model_response)
        return finish_response(response, language, speak_response, speak_limit=450)

    youtube_query = extract_youtube_search(command_text)
    if youtube_query:
        set_state("executing", f"Searching YouTube for: {youtube_query}.")
        response = search_youtube(youtube_query)
        return finish_response(response, language, speak_response)

    google_query = extract_google_search(command_text)
    if google_query:
        set_state("executing", f"Searching Google for: {google_query}.")
        response = open_google_search(google_query)
        return finish_response(response, language, speak_response)

    local_file_response = run_local_file_action(command_text)
    if local_file_response:
        set_state("executing", "Running local file action.")
        return finish_response(local_file_response, language, speak_response, speak_limit=450)

    open_target_response = run_open_target_action(command_text)
    if open_target_response:
        set_state("executing", "Opening requested target.")
        return finish_response(open_target_response, language, speak_response, speak_limit=240)

    file_query = extract_file_search(command_text)
    if file_query:
        set_state("executing", f"Searching user files for: {file_query}.")
        response = search_user_files(file_query)
        return finish_response(response, language, speak_response, speak_limit=700)

    task_id = match_system_command(command_text)
    if task_id:
        set_state("executing", f"Running safe system task: {task_id}.")
        response = run_system_task(task_id)
        return finish_response(response, language, speak_response)

    set_state("thinking", f"Processing command through {provider_label()} neural core.")
    memories = memory_context()
    user_name = user_display_name(settings.owner_name)
    profile_line = f"Current user name: {user_name}"
    prompt = (
        f"{profile_line}\n\nUser command:\n{text}"
        if not memories
        else f"{profile_line}\nSaved local memories about the current user:\n{memories}\n\nUser command:\n{text}"
    )
    response = ask_ai(prompt, language_instruction=command_language_instruction(language))
    return finish_response(response, language, speak_response, speak_limit=speak_limit)


@router.post("/assistant/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    speak_response = bool(payload.get("speak", True))
    language_mode = normalize_language_mode(payload.get("language", "auto"))

    if not text:
        return jsonify(error="Text command is required."), 400

    result = run_text_command(text, speak_response=speak_response, language_mode=language_mode)
    return jsonify(
        transcript=text,
        response=result["response"],
        audio_file=result["audio_file"],
        status="complete",
    )


@router.post("/assistant/listen")
def listen():
    payload = request.get_json(silent=True) or {}
    language_mode = normalize_language_mode(payload.get("language", "auto"))

    set_state("listening", "Microphone input active.")
    transcript = recognizer.listen_once(language_mode=language_mode)

    result = run_text_command(transcript, speak_response=True, language_mode=language_mode)
    return jsonify(
        transcript=transcript,
        response=result["response"],
        audio_file=result["audio_file"],
        status="complete",
    )


@router.post("/assistant/wake-listen")
def wake_listen():
    payload = request.get_json(silent=True) or {}
    duration = float(payload.get("duration", 3.2))
    language_mode = normalize_language_mode(payload.get("language", "auto"))

    set_state("wake", "Wake word monitor active.")
    transcript = recognizer.listen_once(duration=duration, language_mode=language_mode)
    awakened, command = wake_command_from(transcript)

    if not awakened:
        set_state("online", "Wake word monitor standing by.")
        return jsonify(awakened=False, transcript=transcript, response="", audio_file=None, status="standby")

    if not command:
        language = resolve_language(transcript, language_mode)
        response = "അതെ, ഞാൻ കേൾക്കുന്നു." if language == "ml" else f"Yes, {user_display_name(settings.owner_name)}. I am listening."
        set_state("speaking", "Wake word acknowledged.")
        audio_file = str(speaker.speak(response, language=language))
        set_state("online", "Awaiting next command.")
        return jsonify(awakened=True, transcript=transcript, response=response, audio_file=audio_file, status="awake")

    result = run_text_command(command, speak_response=True, speak_limit=900, language_mode=language_mode)
    return jsonify(
        awakened=True,
        transcript=transcript,
        command=command,
        response=result["response"],
        audio_file=result["audio_file"],
        status="complete",
    )


@router.post("/assistant/speak")
def speak():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify(error="Text is required."), 400

    set_state("speaking", "Speaking supplied text.")
    audio_file = speaker.speak(text, language=detect_language(text))
    set_state("online", "Awaiting next command.")
    return jsonify(audio_file=str(audio_file), status="complete")


@router.get("/system/tasks")
def system_tasks():
    return jsonify(
        tasks=[
            {"id": "open_notepad", "label": "Notepad"},
            {"id": "open_calculator", "label": "Calculator"},
            {"id": "open_explorer", "label": "Explorer"},
            {"id": "list_desktop", "label": "Desktop Scan"},
            {"id": "system_status", "label": "System Status"},
            {"id": "create_note", "label": "Create Note"},
            {"id": "open_youtube", "label": "YouTube"},
            {"id": "open_google", "label": "Google"},
            {"id": "open_gmail", "label": "Gmail"},
            {"id": "open_github", "label": "GitHub"},
            {"id": "open_whatsapp", "label": "WhatsApp"},
            {"id": "open_chrome", "label": "Chrome"},
            {"id": "open_edge", "label": "Edge"},
            {"id": "open_vscode", "label": "VS Code"},
            {"id": "open_latest_code", "label": "Latest Code"},
            {"id": "test_latest_code", "label": "Test Code"},
            {"id": "take_screenshot", "label": "Screenshot"},
            {"id": "play_music", "label": "Music"},
            {"id": "current_time", "label": "Time"},
            {"id": "current_date", "label": "Date"},
        ]
    )


@router.post("/system/task")
def system_task():
    payload = request.get_json(silent=True) or {}
    task_id = str(payload.get("task", "")).strip()
    if task_id not in TASKS:
        return jsonify(error="Unsupported system task."), 400

    set_state("executing", f"Running safe system task: {task_id}.")
    response = run_system_task(task_id)
    set_state("online", "Awaiting next command.")
    return jsonify(response=response, status="complete", task=task_id)


@router.post("/files/upload")
def upload_file():
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify(error="No file was uploaded."), 400

    set_state("indexing", "Receiving and indexing uploaded file.")
    result = save_and_analyze(uploaded)
    set_state("online", "Awaiting next command.")
    return jsonify(result)
