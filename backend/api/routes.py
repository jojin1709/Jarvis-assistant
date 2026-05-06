from flask import Blueprint, jsonify, request

from api.file_ingest import save_and_analyze
from api.groq_ai import ask_groq
from api.system_tasks import (
    TASKS,
    extract_file_search,
    extract_google_search,
    match_system_command,
    open_google_search,
    run_system_task,
    search_user_files,
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
    return jsonify(status="online", detail="Backend link established.")


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
        f"{period}, {settings.owner_name}. JX JARVIS is online. "
        "Voice systems, file intake, Groq intelligence, and desktop operations are ready."
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
    wake_phrases = ("hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis", "jarvis")

    for phrase in wake_phrases:
        if phrase in normalized:
            command = normalized.split(phrase, 1)[1].strip(" ,:.-")
            return True, command
    return False, ""


def run_text_command(text: str, speak_response: bool = True, speak_limit: int | None = None) -> dict[str, str | None]:
    google_query = extract_google_search(text)
    if google_query:
        set_state("executing", f"Searching Google for: {google_query}.")
        response = open_google_search(google_query)
        audio_file = None
        if speak_response:
            set_state("speaking", "Voice response active.")
            audio_file = str(speaker.speak(response))
        set_state("online", "Awaiting next command.")
        return {"response": response, "audio_file": audio_file}

    file_query = extract_file_search(text)
    if file_query:
        set_state("executing", f"Searching user files for: {file_query}.")
        response = search_user_files(file_query)
        audio_file = None
        if speak_response:
            set_state("speaking", "Voice response active.")
            audio_file = str(speaker.speak(response[:700]))
        set_state("online", "Awaiting next command.")
        return {"response": response, "audio_file": audio_file}

    task_id = match_system_command(text)
    if task_id:
        set_state("executing", f"Running safe system task: {task_id}.")
        response = run_system_task(task_id)
        audio_file = None
        if speak_response:
            set_state("speaking", "Voice response active.")
            audio_file = str(speaker.speak(response))
        set_state("online", "Awaiting next command.")
        return {"response": response, "audio_file": audio_file}

    set_state("thinking", "Processing command through Groq neural core.")
    response = ask_groq(text)
    audio_file = None
    if speak_response:
        set_state("speaking", "Generating Edge-TTS voice response.")
        speech_text = response[:speak_limit] if speak_limit else response
        audio_file = str(speaker.speak(speech_text))
    set_state("online", "Awaiting next command.")
    return {"response": response, "audio_file": audio_file}


@router.post("/assistant/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    speak_response = bool(payload.get("speak", True))

    if not text:
        return jsonify(error="Text command is required."), 400

    result = run_text_command(text, speak_response=speak_response)
    return jsonify(
        transcript=text,
        response=result["response"],
        audio_file=result["audio_file"],
        status="complete",
    )


@router.post("/assistant/listen")
def listen():
    set_state("listening", "Microphone input active.")
    transcript = recognizer.listen_once()

    result = run_text_command(transcript, speak_response=True)
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

    set_state("wake", "Wake word monitor active.")
    transcript = recognizer.listen_once(duration=duration)
    awakened, command = wake_command_from(transcript)

    if not awakened:
        set_state("online", "Wake word monitor standing by.")
        return jsonify(awakened=False, transcript=transcript, response="", audio_file=None, status="standby")

    if not command:
        response = f"Yes, {settings.owner_name}. I am listening."
        set_state("speaking", "Wake word acknowledged.")
        audio_file = str(speaker.speak(response))
        set_state("online", "Awaiting next command.")
        return jsonify(awakened=True, transcript=transcript, response=response, audio_file=audio_file, status="awake")

    result = run_text_command(command, speak_response=True, speak_limit=900)
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
    audio_file = speaker.speak(text)
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
