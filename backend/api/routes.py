import re

from flask import Blueprint, jsonify, request, send_file

from api.ai_provider import ask_ai, ask_ai_code_project, provider_label
from api.approvals import resolve_approval
from api.browser_automation import browser_operator
from api.context_awareness import context_snapshot
from api.code_writer import create_code_project, create_portfolio_project, extract_code_request, is_portfolio_request
from api.execution import add_log, execute_agent_task, execution_logs, preview_execution_plan
from api.file_ingest import save_and_analyze
from api.language import (
    command_language_instruction,
    detect_language,
    localize_response,
    normalize_command_to_english,
    normalize_language_mode,
    resolve_language,
)
from api.memory import (
    clear_memory,
    export_memory,
    handle_memory_command,
    memory_context,
    profile_summary,
    save_profile,
    save_provider_key,
    user_display_name,
)
from api.memory_storage import (
    backup_memory,
    clear_brain_memory,
    memory_storage_state,
    remember_conversation,
    setup_memory_storage,
)
from automation.workflow_recorder import load_workflow, recorder_state, start_recording, stop_recording
from coding.agent import analyze_project, run_project_script
from execution.control import cancel_execution, execution_control_state, pause_execution, resume_execution
from execution.thinking import thinking_timeline
from plugins.registry import install_local_plugin, list_plugins, set_plugin_enabled
from providers.registry import (
    list_provider_status,
    ollama_model_list,
    remove_provider_key,
    set_provider_key,
    test_provider,
    update_provider_settings,
)
from vision.screenshot import capture_screen
from api.permissions import (
    evaluate_permission,
    guard_action,
    permission_activity,
    permissions_state,
    update_permissions,
)
from api.system_tasks import (
    TASKS,
    extract_file_search,
    extract_google_search,
    extract_youtube_search,
    list_available_apps,
    match_system_command,
    open_google_search,
    run_close_target_action,
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


@router.get("/memory")
def memory():
    return jsonify(profile=profile_summary(settings.owner_name), context=memory_context())


@router.get("/memory/storage")
def memory_storage():
    return jsonify(memory=memory_storage_state())


@router.post("/memory/storage/setup")
def memory_storage_setup():
    payload = request.get_json(silent=True) or {}
    path = str(payload.get("path") or "").strip() or None
    try:
        result = setup_memory_storage(path)
    except OSError as error:
        return jsonify(error=f"Could not set up memory storage: {error}"), 400
    save_profile({"memory_storage_path": result["path"]})
    return jsonify(memory=result, profile=profile_summary(settings.owner_name))


@router.post("/memory/storage/backup")
def memory_storage_backup():
    try:
        return jsonify(backup=backup_memory())
    except OSError as error:
        return jsonify(error=f"Could not back up memory storage: {error}"), 400


@router.post("/memory/storage/clear")
def memory_storage_clear():
    try:
        return jsonify(memory=clear_brain_memory())
    except OSError as error:
        return jsonify(error=f"Could not clear memory storage: {error}"), 400


@router.get("/profile")
def profile():
    return jsonify(profile=profile_summary(settings.owner_name))


@router.patch("/profile")
def profile_update():
    payload = request.get_json(silent=True) or {}
    return jsonify(profile=save_profile(payload))


@router.post("/onboarding/complete")
def onboarding_complete():
    payload = request.get_json(silent=True) or {}
    profile_payload = payload.get("profile") if isinstance(payload.get("profile"), dict) else {}
    permissions_payload = payload.get("permissions") if isinstance(payload.get("permissions"), dict) else {}
    provider_payload = payload.get("provider") if isinstance(payload.get("provider"), dict) else {}

    if permissions_payload:
        update_permissions(permissions_payload)

    memory_payload = payload.get("memory") if isinstance(payload.get("memory"), dict) else {}
    memory_path = str(memory_payload.get("path") or profile_payload.get("memory_storage_path") or "").strip()
    if memory_path:
        storage = setup_memory_storage(memory_path)
        profile_payload["memory_storage_path"] = storage["path"]

    provider = str(provider_payload.get("name") or profile_payload.get("ai_provider") or "").strip()
    api_key = str(provider_payload.get("api_key") or "").strip()
    if provider and api_key:
        save_provider_key(provider, api_key)

    profile_payload["onboarding_complete"] = True
    profile_payload["onboarding_completed_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    saved = save_profile(profile_payload)
    add_log(f"Onboarding completed for {saved.get('user_name', 'User')}.", "success")
    return jsonify(profile=saved, permissions=permissions_state())


@router.post("/memory/clear")
def memory_clear():
    return jsonify(response=clear_memory(), profile=profile_summary(settings.owner_name))


@router.get("/memory/export")
def memory_export():
    decision = evaluate_permission("memory.read", "export Jarvis memory")
    if not decision.allowed:
        return jsonify(error=decision.message), 403
    return jsonify(export_memory())


@router.get("/security/permissions")
def security_permissions():
    return jsonify(permissions=permissions_state())


@router.patch("/security/permissions")
def security_permissions_update():
    payload = request.get_json(silent=True) or {}
    return jsonify(permissions=update_permissions(payload))


@router.get("/security/activity")
def security_activity():
    return jsonify(activity=permission_activity())


@router.get("/status")
def status():
    return jsonify(status=state["status"], detail=state["detail"])


@router.get("/agent/logs")
def agent_logs():
    return jsonify(logs=execution_logs())


@router.get("/agent/thinking")
def agent_thinking():
    return jsonify(thinking=thinking_timeline(), control=execution_control_state())


@router.post("/agent/plan")
def agent_plan():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify(error="Task text is required."), 400
    return jsonify(preview_execution_plan(text))


@router.post("/agent/pause")
def agent_pause():
    add_log("Execution pause requested.", "warning")
    return jsonify(pause_execution())


@router.post("/agent/resume")
def agent_resume():
    add_log("Execution resumed.", "info")
    return jsonify(resume_execution())


@router.post("/agent/cancel")
def agent_cancel():
    add_log("Execution cancellation requested.", "warning")
    return jsonify(cancel_execution())


@router.get("/context")
def context():
    return jsonify(context=context_snapshot())


@router.post("/vision/screenshot")
def vision_screenshot():
    result = capture_screen()
    if not result.get("ok"):
        return jsonify(result), 500
    return jsonify(result)


@router.get("/plugins")
def plugins():
    return jsonify(plugins=list_plugins())


@router.get("/providers")
def providers_status():
    return jsonify(list_provider_status())


@router.patch("/providers/config")
def providers_config_update():
    payload = request.get_json(silent=True) or {}
    update_provider_settings(payload)
    return jsonify(list_provider_status())


@router.post("/providers/key")
def providers_key_set():
    payload = request.get_json(silent=True) or {}
    provider = str(payload.get("provider") or "").strip().lower()
    api_key = str(payload.get("apiKey") or "").strip()
    if not provider or not api_key:
        return jsonify(error="Provider and API key are required."), 400
    set_provider_key(provider, api_key)
    add_log(f"AI provider key updated: {provider}", "success")
    return jsonify(list_provider_status())


@router.delete("/providers/key/<provider>")
def providers_key_remove(provider):
    remove_provider_key(provider)
    add_log(f"AI provider key removed: {provider}", "warning")
    return jsonify(list_provider_status())


@router.post("/providers/test")
def providers_test():
    payload = request.get_json(silent=True) or {}
    provider = str(payload.get("provider") or "").strip().lower()
    model = str(payload.get("model") or "").strip() or None
    if not provider:
        return jsonify(error="Provider is required."), 400
    result = test_provider(provider, model=model)
    add_log(
        f"Provider test {'passed' if result.get('ok') else 'failed'}: {provider}",
        "success" if result.get("ok") else "error",
    )
    return jsonify(result)


@router.get("/providers/ollama/models")
def providers_ollama_models():
    return jsonify(ollama_model_list())


@router.post("/plugins/install")
def plugins_install():
    payload = request.get_json(silent=True) or {}
    return jsonify(plugin=install_local_plugin(payload))


@router.patch("/plugins/<plugin_id>")
def plugins_toggle(plugin_id):
    payload = request.get_json(silent=True) or {}
    plugin = set_plugin_enabled(plugin_id, bool(payload.get("enabled", True)))
    if not plugin:
        return jsonify(error="Only local plugins can be toggled from this endpoint."), 404
    return jsonify(plugin=plugin)


@router.get("/workflows/recorder")
def workflow_recorder_state():
    return jsonify(recorder=recorder_state())


@router.post("/workflows/recorder/start")
def workflow_recorder_start():
    payload = request.get_json(silent=True) or {}
    return jsonify(recorder=start_recording(str(payload.get("name") or "Jarvis workflow")))


@router.post("/workflows/recorder/stop")
def workflow_recorder_stop():
    return jsonify(recorder=stop_recording())


@router.post("/workflows/replay/<workflow_id>")
def workflow_replay(workflow_id):
    workflow = load_workflow(workflow_id)
    if not workflow:
        return jsonify(error="Workflow was not found."), 404
    executable = [
        action.get("label", "")
        for action in workflow.get("actions", [])
        if action.get("kind") == "agent_step" and action.get("label")
    ]
    if not executable:
        return jsonify(error="This workflow has no replayable agent steps yet."), 400
    add_log(f"Replaying workflow: {workflow.get('name', workflow_id)}", "running")
    return jsonify(execute_agent_task(", then ".join(executable)))


@router.get("/coding/analyze")
def coding_analyze():
    path = request.args.get("path")
    return jsonify(analyze_project(path))


@router.post("/coding/run-script")
def coding_run_script():
    payload = request.get_json(silent=True) or {}
    return jsonify(run_project_script(payload.get("path"), str(payload.get("script") or "build")))


@router.get("/browser/state")
def browser_state():
    return jsonify(browser_operator.state())


@router.post("/browser/run")
def browser_run():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify(error="Browser task text is required."), 400
    return jsonify(browser_operator.run_async(text))


@router.post("/browser/stop")
def browser_stop():
    return jsonify(browser_operator.stop())


@router.post("/browser/close")
def browser_close():
    return jsonify(browser_operator.close())


@router.post("/browser/pause")
def browser_pause():
    return jsonify(browser_operator.pause())


@router.post("/browser/resume")
def browser_resume():
    return jsonify(browser_operator.resume())


@router.get("/browser/screenshot")
def browser_screenshot():
    path = browser_operator.screenshot_path()
    if not path.exists():
        return jsonify(error="No browser screenshot is available yet."), 404
    return send_file(path, mimetype="image/png")


@router.post("/agent/execute")
def agent_execute():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify(error="Task text is required."), 400

    set_state("executing", "Autonomous task execution active.")
    result: dict | None = None

    def run() -> str:
        nonlocal result
        try:
            result = execute_agent_task(text)
        except RuntimeError as error:
            result = {"response": str(error), "plan": [], "logs": execution_logs()}
            add_log(str(error), "warning")
        return str(result.get("response", "Done."))

    guarded = guard_action("automation.run", f"run autonomous task: {text}", run)
    if result is None:
        result = {"response": guarded, "plan": [], "logs": execution_logs()}
    set_state("online", "Awaiting next command.")
    return jsonify(result)


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
    try:
        audio_file = str(speaker.speak(response))
    except Exception as error:
        add_log(f"Startup voice unavailable: {error}", "error")
        audio_file = None
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
        try:
            audio_file = str(speaker.speak(speech_text, language=language))
        except Exception as error:
            add_log(f"Voice output unavailable: {error}", "error")
            audio_file = None
    set_state("online", "Awaiting next command.")
    return {"response": localized, "audio_file": audio_file}


def visual_browser_command(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())
    browser_sites = (
        "google",
        "youtube",
        "github",
        "stack overflow",
        "stackoverflow",
        "linkedin",
        "reddit",
    )
    browser_verbs = ("navigate to", "go to", "open website", "click ", "scroll", "summarize page", "summarise page")
    if any(phrase in normalized for phrase in browser_verbs):
        return text
    open_match = re.search(r"\bopen\s+(.+)$", normalized)
    if open_match and open_match.group(1).strip() in browser_sites:
        return text
    return None


def run_text_command(
    text: str,
    speak_response: bool = True,
    speak_limit: int | None = None,
    language_mode: str = "auto",
) -> dict[str, str | None]:
    language = resolve_language(text, language_mode)
    command_text = normalize_command_to_english(text, language)
    add_log(f"Understanding command: {command_text}", "info")

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
        set_state("executing", f"Visually searching YouTube for: {youtube_query}.")
        response = browser_operator.run_async(f"open YouTube and search {youtube_query}")["response"]
        return finish_response(response, language, speak_response)

    google_query = extract_google_search(command_text)
    if google_query:
        set_state("executing", f"Visually searching Google for: {google_query}.")
        response = browser_operator.run_async(f"search Google for {google_query}")["response"]
        return finish_response(response, language, speak_response)

    local_file_response = run_local_file_action(command_text)
    if local_file_response:
        set_state("executing", "Running local file action.")
        add_log(local_file_response, "success" if "could not" not in local_file_response.lower() else "error")
        return finish_response(local_file_response, language, speak_response, speak_limit=450)

    browser_command = visual_browser_command(command_text)
    if browser_command:
        set_state("executing", "Running visual browser automation.")
        response = browser_operator.run_async(browser_command)["response"]
        return finish_response(response, language, speak_response, speak_limit=320)

    close_target_response = run_close_target_action(command_text)
    if close_target_response:
        set_state("executing", "Closing requested target.")
        add_log(close_target_response, "success" if "successfully" in close_target_response.lower() else "error")
        return finish_response(close_target_response, language, speak_response, speak_limit=240)

    open_target_response = run_open_target_action(command_text)
    if open_target_response:
        set_state("executing", "Opening requested target.")
        add_log(open_target_response, "success" if "successfully" in open_target_response.lower() or "opened" in open_target_response.lower() else "error")
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
    profile = profile_summary(settings.owner_name)
    user_name = str(profile.get("user_name") or user_display_name(settings.owner_name))
    personality = str(profile.get("personality") or "professional")
    profile_line = f"Current user name: {user_name}"
    prompt = (
        f"{profile_line}\nResponse style: {personality}\n\nUser command:\n{text}"
        if not memories
        else f"{profile_line}\nResponse style: {personality}\nSaved local memories about the current user:\n{memories}\n\nUser command:\n{text}"
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
    remember_conversation(text, str(result["response"] or ""), {"source": "chat"})
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
    decision = evaluate_permission("voice.listen", "use microphone voice activation")
    if not decision.allowed:
        return jsonify(transcript="", response=decision.message, audio_file=None, status="blocked")

    set_state("listening", "Microphone input active.")
    add_log("Listening for voice command.", "running")
    transcript = recognizer.listen_once(language_mode=language_mode)
    add_log(f"Heard: {transcript}", "info")

    result = run_text_command(transcript, speak_response=True, language_mode=language_mode)
    remember_conversation(transcript, str(result["response"] or ""), {"source": "voice"})
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
    decision = evaluate_permission("voice.background", "background wake word listening")
    if not decision.allowed:
        return jsonify(awakened=False, transcript="", response=decision.message, audio_file=None, status="blocked")

    set_state("wake", "Wake word monitor active.")
    transcript = recognizer.listen_once(duration=duration, language_mode=language_mode)
    awakened, command = wake_command_from(transcript)

    if not awakened:
        set_state("online", "Wake word monitor standing by.")
        return jsonify(awakened=False, transcript=transcript, response="", audio_file=None, status="standby")

    add_log("Wake word detected.", "success")
    if not command:
        language = resolve_language(transcript, language_mode)
        response = "അതെ, ഞാൻ കേൾക്കുന്നു." if language == "ml" else f"Yes, {user_display_name(settings.owner_name)}. I am listening."
        set_state("speaking", "Wake word acknowledged.")
        try:
            audio_file = str(speaker.speak(response, language=language))
        except Exception as error:
            add_log(f"Wake voice unavailable: {error}", "error")
            audio_file = None
        set_state("online", "Awaiting next command.")
        return jsonify(awakened=True, transcript=transcript, response=response, audio_file=audio_file, status="awake")

    add_log(f"Voice command: {command}", "info")
    result = run_text_command(command, speak_response=True, speak_limit=900, language_mode=language_mode)
    remember_conversation(command, str(result["response"] or ""), {"source": "wake"})
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
    try:
        audio_file = speaker.speak(text, language=detect_language(text))
    except Exception as error:
        add_log(f"Voice output unavailable: {error}", "error")
        set_state("online", "Awaiting next command.")
        return jsonify(audio_file=None, status="blocked", error=str(error))
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
            {"id": "lock_pc", "label": "Lock PC"},
            {"id": "play_music", "label": "Music"},
            {"id": "current_time", "label": "Time"},
            {"id": "current_date", "label": "Date"},
        ]
    )


@router.get("/system/apps")
def system_apps():
    return jsonify(apps=list_available_apps())


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
