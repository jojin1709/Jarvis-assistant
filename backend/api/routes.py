import json
import re
import threading
import time

from flask import Blueprint, Response, current_app, jsonify, request, send_file, stream_with_context

from api.ai_provider import ask_ai, ask_ai_code_project, provider_label
from api.approvals import resolve_approval
from api.browser_automation import browser_operator
from api.context_awareness import context_snapshot
from api.code_writer import (
    create_code_project,
    create_portfolio_project,
    extract_code_request,
    is_portfolio_request,
)
from api.execution import add_log, execute_agent_task, execute_recorded_workflow, execution_logs, preview_execution_plan
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
    recent_memories,
    remember_conversation,
    setup_memory_storage,
)
from api.wake_words import wake_command_from as parse_wake_command
from agents.orchestrator import execute_autonomous_goal
from automation.workflow_recorder import load_workflow, recorder_state, start_recording, stop_recording
from automation.workflow_recorder import record_action
from coding.agent import analyze_project, run_project_script
from community.community_sync import community_state
from context.context_manager import multimodal_context
from core.autonomous_runtime import run_autonomous_runtime
from core.cognitive_core import cognitive_core_status, prepare_goal
from decision_engine.strategy_selector import choose_strategy
from desktop.automation import desktop_automation
from distributed.worker_manager import worker_status
from docs.auto_doc_generator import generate_docs
from environment.runtime_analyzer import runtime_analysis
from events.event_bus import recent_events
from explainability.action_trace import action_trace
from legal.consent_manager import consent_state, update_consents
from legal.policy_renderer import legal_documents
from execution.control import cancel_execution, execution_control_state, pause_execution, resume_execution
from execution.thinking import thinking_timeline
from agents.message_bus import message_bus
from knowledge.document_indexer import index_path
from knowledge.semantic_search import search_knowledge
from marketplace.skill_registry import marketplace_skills
from marketplace.workflow_registry import marketplace_workflows
from mobile_companion.api import mobile_state, push_mobile_notification
from observability.telemetry import telemetry_snapshot
from optimization.async_runtime_optimizer import async_runtime_plan
from optimization.browser_pool import browser_pool_status
from optimization.memory_optimizer import memory_pressure, optimize_memory
from optimization.performance_manager import performance_status
from platform_core.execution_loop import execute_platform_goal
from platform_core.intelligence import build_intelligence_snapshot
from platform_core.state_store import platform_history, platform_state
from plugins.registry import install_local_plugin, list_plugins, set_plugin_enabled
from providers.registry import (
    list_provider_status,
    ollama_model_list,
    remove_provider_key,
    set_provider_key,
    test_provider,
    update_provider_settings,
)
from providers.provider_router import browser_provider_status, open_provider_login, ask_with_orchestration
from release_security.code_signing_manager import signing_command, signing_config
from release_security.release_validator import validate_release_artifact
from remote.distributed_runtime import distributed_runtime_status
from research.article_parser import fetch_article
from research.search_engine import web_search
from research.summarizer import summarize_text
from recovery.environment_restore import restore_readiness
from sandbox.executor import run_in_docker
from scheduler.task_scheduler import scheduler
from self_improvement.engine import analyze_execution_quality
from simulation.dry_run_engine import dry_run_goal
from skills.registry import list_skills, select_skills
from state_machine.workflow_state_manager import current_state
from sync.sync_manager import configure_provider, connect_provider, provider_auth_url, restore_sync_backup, run_backup_sync, sync_status
from telemetry.analytics_engine import analytics_snapshot, diagnostic_bundle, update_telemetry_config
from vision.screenshot import capture_screen
from workflows.workflow_engine import execute_workflow_graph
from workflows.workflow_store import list_workflow_definitions, load_workflow_definition, save_workflow_definition
from workspace.code_map import build_code_map
from api.permissions import (
    evaluate_permission,
    guard_action,
    permission_activity,
    permissions_state,
    update_permissions,
)
from api.system_tasks import (
    TASKS,
    app_icon_file,
    extract_file_search,
    extract_google_search,
    extract_youtube_search,
    list_available_apps,
    match_system_command,
    open_google_search,
    run_close_target_action,
    run_open_target_action,
    run_system_task,
    scan_app_folder,
    run_local_file_action,
    search_user_files,
    search_youtube,
)
from app.config import _startup_warnings, settings
from terminal.service import terminal_service
from voice.microphone_manager import list_microphones, update_voice_preferences
from voice.voice_orchestrator import push_to_talk
from voice.recognizer import VoiceRecognizer
from voice.speaker import EdgeSpeaker
from voice.voice_runtime import voice_runtime

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


def shutdown_runtime() -> dict:
    cancelled_jobs = terminal_service.shutdown()
    try:
        browser_operator.close()
    except Exception as error:
        add_log(f"Browser cleanup warning: {error}", "warning")
    try:
        voice_runtime.stop()
    except Exception as error:
        add_log(f"Voice cleanup warning: {error}", "warning")
    set_state("offline", "JX JARVIS is closing.")
    return {"status": "closing", "terminalCancelled": len(cancelled_jobs)}


@router.post("/shutdown")
def shutdown():
    return jsonify(shutdown_runtime())


@router.get("/health")
def health():
    return jsonify(
        status="online",
        detail="Backend link established.",
        profile=profile_summary(settings.owner_name),
        provider=settings.ai_provider,
        port=settings.backend_port,
        warnings=_startup_warnings,
    )


@router.get("/memory")
def memory():
    return jsonify(profile=profile_summary(settings.owner_name), context=memory_context(), recent=recent_memories(limit=40))


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


@router.get("/voice/runtime")
def voice_runtime_state():
    return jsonify(runtime=voice_runtime.status())


@router.patch("/voice/runtime")
def voice_runtime_update():
    payload = request.get_json(silent=True) or {}
    if "enabled" in payload:
        result = voice_runtime.start() if bool(payload.get("enabled")) else voice_runtime.stop()
    elif "muted" in payload:
        result = voice_runtime.mute(bool(payload.get("muted")))
    elif payload.get("mode"):
        result = voice_runtime.set_mode(str(payload.get("mode")))
    else:
        update_voice_preferences(payload)
        result = voice_runtime.status()
    return jsonify(runtime=result)


@router.get("/voice/microphones")
def voice_microphones():
    return jsonify(microphones=list_microphones())


@router.post("/voice/push-to-talk")
def voice_push_to_talk():
    payload = request.get_json(silent=True) or {}
    decision = evaluate_permission("voice.listen", "use push-to-talk voice activation")
    if not decision.allowed:
        return jsonify(transcript="", response=decision.message, audio_file=None, status="blocked"), 403
    language_mode = normalize_language_mode(payload.get("language", "auto"))
    speak_response = bool(payload.get("speak", True))
    result = push_to_talk(run_text_command, language=language_mode, speak_response=speak_response, source=str(payload.get("source") or "api"))
    if result.get("transcript"):
        remember_conversation(str(result.get("transcript") or ""), str(result.get("response") or ""), {"source": "global-voice"})
    return jsonify(result), 200 if result.get("status") not in {"error"} else 500


@router.post("/voice/interrupt")
def voice_interrupt():
    return jsonify(runtime=voice_runtime.mark("idle", "Voice interaction interrupted by user."))


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


@router.post("/terminal/run")
def terminal_run():
    payload = request.get_json(silent=True) or {}
    command = str(payload.get("command") or "").strip()
    cwd = str(payload.get("cwd") or "").strip() or None
    if not command:
        return jsonify(error="Terminal command is required."), 400
    decision = evaluate_permission("terminal.run", f"run terminal command: {command}", path=cwd, command=command)
    if not decision.allowed:
        return jsonify(error=decision.message), 403
    if decision.requires_confirmation:
        return jsonify(error=f"Approval required before running terminal command: {command}"), 403
    job = terminal_service.enqueue(command, cwd=cwd)
    add_log(f"Terminal job queued: {command}", "running")
    return jsonify(job.as_dict())


@router.get("/terminal/jobs")
def terminal_jobs():
    return jsonify(jobs=terminal_service.history())


@router.post("/terminal/jobs/<job_id>/cancel")
def terminal_cancel(job_id):
    add_log(f"Terminal cancellation requested: {job_id}", "warning")
    return jsonify(terminal_service.cancel(job_id))


@router.get("/context")
def context():
    return jsonify(context=context_snapshot())


@router.post("/context/multimodal")
def context_multimodal():
    payload = request.get_json(silent=True) or {}
    goal = str(payload.get("goal") or "").strip()
    include_vision = bool(payload.get("includeVision", False))
    return jsonify(multimodal_context(goal=goal, include_vision=include_vision))


@router.get("/dashboard")
def autonomous_dashboard():
    return jsonify(
        context=multimodal_context(),
        telemetry=telemetry_snapshot(),
        agents={"messages": message_bus.recent()},
        workflows={"definitions": list_workflow_definitions(), "scheduler": scheduler.list()},
        platform={"state": platform_state(), "history": platform_history(limit=40), "intelligence": build_intelligence_snapshot()},
        core={"status": cognitive_core_status(), "executionState": current_state(), "events": recent_events(limit=40)},
        production={
            "sync": sync_status(),
            "telemetry": analytics_snapshot(),
            "performance": performance_status(),
            "remote": distributed_runtime_status(),
            "legal": consent_state(),
        },
    )


@router.get("/core/status")
def core_status():
    return jsonify(core=cognitive_core_status(), runtime=runtime_analysis(), workers=worker_status(), recovery=restore_readiness())


@router.post("/core/prepare")
def core_prepare():
    payload = request.get_json(silent=True) or {}
    goal = str(payload.get("goal") or "").strip()
    if not goal:
        return jsonify(error="Goal is required."), 400
    return jsonify(prepare_goal(goal, include_vision=bool(payload.get("includeVision", False)), dry_run=bool(payload.get("dryRun", False))))


@router.post("/core/dry-run")
def core_dry_run():
    payload = request.get_json(silent=True) or {}
    goal = str(payload.get("goal") or "").strip()
    if not goal:
        return jsonify(error="Goal is required."), 400
    return jsonify(dry_run_goal(goal))


@router.post("/platform/intelligence")
def platform_intelligence():
    payload = request.get_json(silent=True) or {}
    return jsonify(build_intelligence_snapshot(str(payload.get("goal") or ""), include_vision=bool(payload.get("includeVision", False))))


@router.post("/platform/execute")
def platform_execute():
    payload = request.get_json(silent=True) or {}
    goal = str(payload.get("goal") or payload.get("text") or "").strip()
    if not goal:
        return jsonify(error="Goal is required."), 400
    decision = evaluate_permission("automation.run", f"execute platform goal: {goal}", command=goal)
    if not decision.allowed:
        return jsonify(error=decision.message), 403
    if decision.requires_confirmation:
        return jsonify(error=f"Approval required before executing platform goal: {goal}"), 403
    if bool(payload.get("dryRun", False)):
        return jsonify(run_autonomous_runtime(goal, include_vision=bool(payload.get("includeVision", False)), dry_run=True))
    return jsonify(execute_platform_goal(goal, include_vision=bool(payload.get("includeVision", False))))


@router.get("/events")
def events_state():
    return jsonify(events=recent_events())


@router.get("/explainability/action-trace")
def explainability_action_trace():
    return jsonify(trace=action_trace())


@router.get("/skills")
def internal_skills():
    goal = str(request.args.get("goal") or "")
    return jsonify(skills=list_skills(), selected=select_skills(goal) if goal else [])


@router.get("/marketplace")
def marketplace_state():
    return jsonify(skills=marketplace_skills(), workflows=marketplace_workflows())


@router.get("/distributed/workers")
def distributed_workers():
    return jsonify(worker_status())


@router.get("/sync/status")
def cloud_sync_status():
    return jsonify(sync_status())


@router.post("/sync/providers/<provider>/configure")
def cloud_sync_configure(provider):
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(configure_provider(provider, payload))
    except ValueError as error:
        return jsonify(error=str(error)), 400


@router.post("/sync/providers/<provider>/auth-url")
def cloud_sync_auth_url(provider):
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(provider_auth_url(provider, str(payload.get("redirectUri") or ""), str(payload.get("clientId") or "")))
    except ValueError as error:
        return jsonify(error=str(error)), 400


@router.post("/sync/providers/<provider>/connect")
def cloud_sync_connect(provider):
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(connect_provider(provider, payload))
    except ValueError as error:
        return jsonify(error=str(error)), 400


@router.post("/sync/backup")
def cloud_sync_backup():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(run_backup_sync(payload.get("provider"), payload.get("scope") if isinstance(payload.get("scope"), list) else None))
    except Exception as error:
        return jsonify(error=f"Sync backup failed: {error}"), 400


@router.post("/sync/restore")
def cloud_sync_restore():
    payload = request.get_json(silent=True) or {}
    path = str(payload.get("path") or "").strip()
    if not path:
        return jsonify(error="Backup path is required."), 400
    try:
        return jsonify(restore_sync_backup(path, str(payload.get("target") or "").strip() or None))
    except Exception as error:
        return jsonify(error=f"Sync restore failed: {error}"), 400


@router.get("/telemetry")
def telemetry_state():
    return jsonify(analytics_snapshot())


@router.patch("/telemetry")
def telemetry_update():
    payload = request.get_json(silent=True) or {}
    return jsonify(update_telemetry_config(payload))


@router.get("/telemetry/diagnostics")
def telemetry_diagnostics():
    return jsonify(diagnostic_bundle())


@router.get("/legal")
def legal_state():
    return jsonify(consent=consent_state(), documents=legal_documents())


@router.patch("/legal/consent")
def legal_consent_update():
    payload = request.get_json(silent=True) or {}
    return jsonify(update_consents(payload))


@router.get("/optimization/status")
def optimization_status():
    return jsonify(performance=performance_status(), memory=memory_pressure(), browserPool=browser_pool_status(), asyncRuntime=async_runtime_plan())


@router.post("/optimization/memory")
def optimization_memory():
    return jsonify(optimize_memory())


@router.get("/release/security")
def release_security_state():
    artifact = str(request.args.get("artifact") or "").strip()
    result = {"signing": signing_config()}
    if artifact:
        result["artifact"] = validate_release_artifact(artifact)
        result["signCommand"] = signing_command(artifact)
    return jsonify(result)


@router.post("/docs/generate")
def docs_generate():
    return jsonify(generate_docs(current_app))


@router.get("/community")
def community_platform_state():
    return jsonify(community_state())


@router.get("/remote/status")
def remote_status():
    return jsonify(distributed_runtime_status())


@router.post("/decision/strategy")
def decision_strategy():
    payload = request.get_json(silent=True) or {}
    goal = str(payload.get("goal") or "").strip()
    return jsonify(choose_strategy(goal, payload.get("context") or {}))


@router.post("/vision/screenshot")
def vision_screenshot():
    result = capture_screen()
    if not result.get("ok"):
        return jsonify(result), 500
    return jsonify(result)


@router.post("/desktop/action")
def desktop_action():
    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action") or "").strip()
    if action == "move":
        result = desktop_automation.move_mouse(int(payload.get("x") or 0), int(payload.get("y") or 0), float(payload.get("duration") or 0.1))
    elif action == "click":
        result = desktop_automation.click(payload.get("x"), payload.get("y"))
    elif action == "type":
        result = desktop_automation.type_text(str(payload.get("text") or ""))
    elif action == "hotkey":
        result = desktop_automation.hotkey(list(payload.get("keys") or []))
    else:
        return jsonify(error="Unsupported desktop action."), 400
    return jsonify(result.as_dict()), 200 if result.ok else 400


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
    api_key = str(payload.get("apiKey") or payload.get("api_key") or "").strip()
    if not provider or not api_key:
        return jsonify(error="Provider and API key are required."), 400
    set_provider_key(provider, api_key)
    update_provider_settings({"enabled": {provider: True}})
    add_log(f"AI provider key updated: {provider}", "success")
    return jsonify(list_provider_status())


@router.post("/providers/save-key")
def providers_save_key_compat():
    return providers_key_set()


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


@router.get("/providers/orchestration")
def providers_orchestration_status():
    return jsonify(browser_provider_status())


@router.post("/providers/orchestration/login/<provider_id>")
def providers_orchestration_login(provider_id):
    result = open_provider_login(provider_id)
    status = 200 if result.ok else 400
    return jsonify(result.__dict__), status


@router.post("/providers/orchestration/test")
def providers_orchestration_test():
    payload = request.get_json(silent=True) or {}
    provider = str(payload.get("provider") or "").strip() or None
    prompt = str(payload.get("prompt") or "Reply with exactly: JX browser provider online").strip()
    result = ask_with_orchestration(
        [{"role": "user", "content": prompt}],
        task_type="chat",
        preferred_provider=provider,
        multi_provider=bool(payload.get("multiProvider", False)),
    )
    status = 200 if result.ok else 400
    return jsonify(result.__dict__), status


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
    add_log(f"Replaying workflow: {workflow.get('name', workflow_id)}", "running")
    result = execute_recorded_workflow(workflow)
    if result.get("response") == "This workflow has no replayable actions yet.":
        return jsonify(error=result["response"]), 400
    return jsonify(result)


@router.get("/workflows/graphs")
def workflow_graphs():
    return jsonify(workflows=list_workflow_definitions())


@router.post("/workflows/graphs")
def workflow_graph_save():
    payload = request.get_json(silent=True) or {}
    result = save_workflow_definition(payload)
    return jsonify(result), 200 if result.get("ok") else 400


@router.post("/workflows/graphs/<workflow_id>/run")
def workflow_graph_run(workflow_id):
    workflow = load_workflow_definition(workflow_id)
    if not workflow:
        return jsonify(error="Workflow was not found."), 404
    return jsonify(execute_workflow_graph(workflow))


@router.get("/scheduler")
def scheduler_state():
    scheduler.start()
    return jsonify(scheduler.list())


@router.post("/scheduler")
def scheduler_upsert():
    payload = request.get_json(silent=True) or {}
    scheduler.start()
    return jsonify(task=scheduler.upsert(payload), scheduler=scheduler.list())


@router.delete("/scheduler/<task_id>")
def scheduler_delete(task_id):
    return jsonify(ok=scheduler.remove(task_id), scheduler=scheduler.list())


@router.get("/coding/analyze")
def coding_analyze():
    path = request.args.get("path")
    return jsonify(analyze_project(path))


@router.post("/coding/run-script")
def coding_run_script():
    payload = request.get_json(silent=True) or {}
    return jsonify(run_project_script(payload.get("path"), str(payload.get("script") or "build")))


def _stream_task(task_fn, *args, **kwargs):
    result_holder = {}
    error_holder = {}

    def run():
        try:
            result_holder["data"] = task_fn(*args, **kwargs)
        except Exception as error:
            error_holder["error"] = str(error)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    elapsed = 0
    while thread.is_alive():
        yield f"data: {json.dumps({'type': 'progress', 'elapsed': elapsed})}\n\n"
        time.sleep(1)
        elapsed += 1

    if error_holder:
        yield f"data: {json.dumps({'type': 'error', 'error': error_holder['error']})}\n\n"
    else:
        yield f"data: {json.dumps({'type': 'done', 'result': result_holder.get('data', {})})}\n\n"


@router.post("/coding/run-script/stream")
def coding_run_script_stream():
    payload = request.get_json(silent=True) or {}
    return Response(
        stream_with_context(_stream_task(run_project_script, payload.get("path"), str(payload.get("script") or "build"))),
        mimetype="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


@router.get("/browser/state")
def browser_state():
    return jsonify(browser_operator.state())


@router.post("/browser/run")
def browser_run():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify(error="Browser task text is required."), 400
    decision = evaluate_permission("browser.automation", f"run browser automation: {text}", command=text)
    if not decision.allowed:
        return jsonify(error=decision.message), 403
    if decision.requires_confirmation:
        return jsonify(error=f"Approval required before running browser automation: {text}"), 403
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
            result = execute_platform_goal(text)["result"] if _should_use_autonomous_orchestrator(text) else execute_agent_task(text)
        except RuntimeError as error:
            result = {"response": str(error), "plan": [], "logs": execution_logs()}
            add_log(str(error), "warning")
        return str(result.get("response", "Done."))

    guarded = guard_action("automation.run", f"run autonomous task: {text}", run)
    if result is None:
        result = {"response": guarded, "plan": [], "logs": execution_logs()}
    remember_conversation(text, str(result.get("response") or ""), {"source": "agent-execute"})
    set_state("online", "Awaiting next command.")
    return jsonify(result)


@router.get("/workspace/code-map")
def workspace_code_map():
    path = request.args.get("path") or "."
    return jsonify(build_code_map(path))


@router.post("/knowledge/index")
def knowledge_index():
    payload = request.get_json(silent=True) or {}
    path = str(payload.get("path") or ".")
    return jsonify(index_path(path, source=str(payload.get("source") or "workspace")))


@router.get("/knowledge/search")
def knowledge_search():
    query = str(request.args.get("q") or "").strip()
    if not query:
        return jsonify(error="Query is required."), 400
    return jsonify(search_knowledge(query, limit=int(request.args.get("limit") or 8)))


@router.get("/research/search")
def research_search():
    query = str(request.args.get("q") or "").strip()
    if not query:
        return jsonify(error="Query is required."), 400
    return jsonify(web_search(query))


@router.post("/research/summarize")
def research_summarize():
    payload = request.get_json(silent=True) or {}
    if payload.get("url"):
        article = fetch_article(str(payload.get("url")))
        return jsonify({**article, "summary": summarize_text(article.get("text", ""))})
    return jsonify(summarize_text(str(payload.get("text") or "")))


@router.post("/sandbox/run")
def sandbox_run():
    payload = request.get_json(silent=True) or {}
    command = str(payload.get("command") or "").strip()
    workspace = str(payload.get("workspace") or ".").strip() or "."
    if not command:
        return jsonify(ok=False, error="No command provided."), 400
    from sandbox.executor import docker_available

    if not docker_available():
        return jsonify(ok=False, error="Docker is not installed. Install Docker Desktop to use the sandbox.", sandbox="docker"), 503
    return jsonify(run_in_docker(command, workspace, image=str(payload.get("image") or "python:3.11-slim")))


@router.get("/self-improvement")
def self_improvement_state():
    return jsonify(analyze_execution_quality())


@router.get("/agents/messages")
def agent_messages():
    return jsonify(messages=message_bus.recent())


@router.get("/mobile/state")
def mobile_companion_state():
    return jsonify(mobile_state())


@router.post("/mobile/notify")
def mobile_notify():
    payload = request.get_json(silent=True) or {}
    return jsonify(notification=push_mobile_notification(str(payload.get("title") or "Jarvis"), str(payload.get("body") or ""), str(payload.get("level") or "info"), payload.get("action") or {}))


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
    payload = request.get_json(silent=True) or {}
    speak_response = bool(payload.get("speak", False))
    response = startup_greeting()
    set_state("speaking", "Startup greeting active.")
    audio_file = None
    if speak_response:
        try:
            audio_file = str(speaker.speak(response))
        except Exception as error:
            add_log(f"Startup voice unavailable: {error}", "error")
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
    if _looks_like_simple_open_target(normalized):
        return None
    browser_verbs = ("navigate to", "go to", "open website", "click ", "scroll", "summarize page", "summarise page")
    if any(phrase in normalized for phrase in browser_verbs):
        return text
    return None


def _looks_like_simple_open_target(normalized: str) -> bool:
    open_match = re.search(r"\b(?:open|launch|start)\s+(.+)$", normalized)
    if not open_match:
        return False
    target = re.sub(r"\b(?:please|for me|bro|broh|now)\b", "", open_match.group(1)).strip(" .")
    return target in {
        "youtube",
        "google",
        "gmail",
        "github",
        "whatsapp",
        "chrome",
        "edge",
        "notepad",
        "calculator",
        "file explorer",
        "explorer",
        "vs code",
        "vscode",
        "visual studio code",
    }


def _conversation_history_context(history: list[dict] | None) -> str:
    if not isinstance(history, list):
        return ""
    lines: list[str] = []
    for item in history[-8:]:
        if not isinstance(item, dict):
            continue
        transcript = re.sub(r"\s+", " ", str(item.get("transcript") or "")).strip()
        response = re.sub(r"\s+", " ", str(item.get("response") or "")).strip()
        if not transcript or response.lower() in {"thinking...", "planning and executing..."}:
            continue
        lines.append(f"User: {transcript}")
        if response:
            lines.append(f"Jarvis: {response}")
    return "\n".join(lines)


def _is_short_follow_up(text: str) -> bool:
    normalized = " ".join(text.lower().strip().split())
    return normalized in {
        "ok",
        "okay",
        "ok do it",
        "okay do it",
        "do it",
        "yes",
        "yes do it",
        "sure",
        "go ahead",
        "please do",
        "proceed",
        "continue",
    }


def _extract_weather_location(text: str) -> str:
    patterns = (
        r"\bweather\s+(?:in|for|at)\s+([a-zA-Z][a-zA-Z\s,.-]{1,60})",
        r"\bweather search for\s+([a-zA-Z][a-zA-Z\s,.-]{1,60})",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            location = re.sub(r"\s+", " ", match.group(1)).strip(" .,-")
            location = re.split(r"\b(?:i can|i cannot|for you|please|now)\b", location, maxsplit=1, flags=re.IGNORECASE)[0]
            return location.strip(" .,-")
    return ""


def extract_weather_search(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())
    if "weather" not in normalized:
        return None

    blocked_contexts = (
        "weather app",
        "weather application",
    )
    if any(context in normalized for context in blocked_contexts) and not any(verb in normalized for verb in ("open", "launch", "start")):
        return None

    location = _extract_weather_location(text)
    if location:
        return f"weather in {location}"

    if re.search(r"\b(?:tell me|show me|check|what is|what's|current|today|now|search|google|find|look up|lookup|open|launch|start)\b", normalized):
        return "current weather"

    if normalized in {"weather", "the weather"}:
        return "current weather"

    return None


def resolve_contextual_follow_up(command_text: str, history: list[dict] | None) -> str:
    if not _is_short_follow_up(command_text) or not isinstance(history, list) or not history:
        return command_text

    recent_items = [item for item in history[-3:] if isinstance(item, dict)]
    recent_text = " ".join(
        str(value or "")
        for item in recent_items
        for value in (item.get("transcript"), item.get("response"))
    )
    lowered = recent_text.lower()

    if "weather" in lowered and (
        "open a browser" in lowered
        or "weather search" in lowered
        or "search" in lowered
        or "weather application" in lowered
        or "weather app" in lowered
    ):
        location = ""
        for item in reversed(recent_items):
            location = _extract_weather_location(str(item.get("transcript") or "")) or _extract_weather_location(str(item.get("response") or ""))
            if location:
                break
        return f"search Google for weather in {location}" if location else "search Google for current weather"

    search_match = re.search(r"\bsearch(?: google)? for\s+([^.;]+)", recent_text, flags=re.IGNORECASE)
    if search_match and ("open a browser" in lowered or "search" in lowered):
        query = re.sub(r"\s+", " ", search_match.group(1)).strip(" .,-")
        if query:
            return f"search Google for {query}"

    return command_text


def run_text_command(
    text: str,
    speak_response: bool = True,
    speak_limit: int | None = None,
    language_mode: str = "auto",
    conversation_history: list[dict] | None = None,
) -> dict[str, str | None]:
    language = resolve_language(text, language_mode)
    command_text = normalize_command_to_english(text, language)
    command_text = resolve_contextual_follow_up(command_text, conversation_history)
    add_log(f"Understanding command: {command_text}", "info")
    record_action("text_command", command_text, {"source": "assistant.chat"})

    if _should_use_autonomous_orchestrator(command_text):
        set_state("executing", "Running autonomous multi-agent workflow.")
        result = execute_autonomous_goal(command_text)
        for item in result.get("logs", [])[-20:]:
            add_log(str(item.get("message") or ""), str(item.get("level") or "info"))
        return finish_response(
            str(result.get("response") or "Autonomous workflow complete."),
            language,
            speak_response,
            speak_limit=900,
        )

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

    local_file_response = run_local_file_action(command_text)
    if local_file_response:
        set_state("executing", "Running local file action.")
        add_log(local_file_response, "success" if "could not" not in local_file_response.lower() else "error")
        return finish_response(local_file_response, language, speak_response, speak_limit=450)

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

    weather_query = extract_weather_search(command_text)
    if weather_query:
        set_state("executing", f"Searching weather in Chrome: {weather_query}.")
        response = open_google_search(weather_query)
        add_log(response, "success" if "searching google" in response.lower() or "opened" in response.lower() else "error")
        return finish_response(response, language, speak_response, speak_limit=240)

    youtube_query = extract_youtube_search(command_text)
    if youtube_query:
        set_state("executing", f"Visually searching YouTube for: {youtube_query}.")
        response = browser_operator.run_async(f"open YouTube and search {youtube_query}")["response"]
        return finish_response(response, language, speak_response)

    google_query = extract_google_search(command_text)
    if google_query:
        set_state("executing", f"Searching Google in Chrome: {google_query}.")
        response = open_google_search(google_query)
        add_log(response, "success" if "searching google" in response.lower() or "opened" in response.lower() else "error")
        return finish_response(response, language, speak_response, speak_limit=240)

    browser_command = visual_browser_command(command_text)
    if browser_command:
        set_state("executing", "Running visual browser automation.")
        response = browser_operator.run_async(browser_command)["response"]
        return finish_response(response, language, speak_response, speak_limit=320)

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
    history_context = _conversation_history_context(conversation_history)
    history_block = (
        ""
        if not history_context
        else f"Recent messages in this same chat thread. Use this to understand follow-ups and pronouns:\n{history_context}\n\n"
    )
    prompt = (
        f"{profile_line}\nResponse style: {personality}\n\n{history_block}User command:\n{text}"
        if not memories
        else f"{profile_line}\nResponse style: {personality}\nSaved local memories about the current user:\n{memories}\n\n{history_block}User command:\n{text}"
    )
    response = ask_ai(prompt, language_instruction=command_language_instruction(language))
    return finish_response(response, language, speak_response, speak_limit=speak_limit)


def _should_use_autonomous_orchestrator(text: str) -> bool:
    normalized = " ".join(text.lower().strip().split())
    full_stack = any(term in normalized for term in ("mern", "full stack", "full-stack", "react and node", "express", "mongodb"))
    bug_bounty = any(term in normalized for term in ("bug bounty", "find bugs", "recon", "vulnerability scan", "scan target"))
    platform_terms = any(
        term in normalized
        for term in (
            "workflow",
            "desktop",
            "screen",
            "screenshot",
            "docker",
            "deploy",
            "research",
            "codebase",
            "architecture",
            "refactor",
            "debug project",
        )
    )
    return full_stack or bug_bounty or platform_terms


@router.post("/assistant/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    speak_response = bool(payload.get("speak", False))
    language_mode = normalize_language_mode(payload.get("language", "auto"))
    conversation_history = payload.get("history")
    if not isinstance(conversation_history, list):
        conversation_history = []

    if not text:
        return jsonify(error="Text command is required."), 400

    result = run_text_command(
        text,
        speak_response=speak_response,
        language_mode=language_mode,
        conversation_history=conversation_history,
    )
    remember_conversation(text, str(result["response"] or ""), {"source": "chat"})
    return jsonify(
        transcript=text,
        response=result["response"],
        audio_file=result["audio_file"],
        status="complete",
    )


@router.post("/assistant/chat/stream")
def chat_stream():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    language_mode = normalize_language_mode(payload.get("language", "auto"))
    conversation_history = payload.get("history")
    if not isinstance(conversation_history, list):
        conversation_history = []

    if not text:
        return jsonify(error="Text command is required."), 400

    def emit(event: dict) -> str:
        return json.dumps(event, ensure_ascii=False) + "\n"

    @stream_with_context
    def generate():
        yield emit({"type": "status", "message": "Thinking..."})
        result = run_text_command(
            text,
            speak_response=False,
            language_mode=language_mode,
            conversation_history=conversation_history,
        )
        response = str(result.get("response") or "")
        for chunk in re.findall(r".{1,96}(?:\s+|$)", response, flags=re.DOTALL):
            if chunk:
                yield emit({"type": "chunk", "text": chunk})
                time.sleep(0.015)
        remember_conversation(text, response, {"source": "chat-stream"})
        yield emit({"type": "done", "response": response, "audio_file": None, "status": "complete"})

    return Response(generate(), mimetype="application/x-ndjson")


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
    awakened, command = parse_wake_command(transcript)

    if not awakened:
        set_state("online", "Wake word monitor standing by.")
        return jsonify(awakened=False, transcript=transcript, response="", audio_file=None, status="standby")

    add_log("Wake word detected.", "success")
    if not command:
        language = resolve_language(transcript, language_mode)
        response = "അതെ, ഞാൻ കേൾക്കുന്നു." if language == "ml" else f"Yes, {user_display_name(settings.owner_name)}. I am listening."
        if language == "ml":
            response = "അതെ, ഞാൻ കേൾക്കുന്നു."
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


@router.post("/system/apps/scan-folder")
def system_apps_scan_folder():
    payload = request.get_json(silent=True) or {}
    folder_path = str(payload.get("path") or "").strip()
    if not folder_path:
        return jsonify(error="Choose a folder to scan."), 400
    return jsonify(apps=scan_app_folder(folder_path))


@router.get("/system/app-icon")
def system_app_icon():
    label = str(request.args.get("label") or "app")
    source_path = str(request.args.get("path") or "")
    icon = app_icon_file(label, source_path)
    if not icon:
        return jsonify(error="Icon not available."), 404
    return send_file(icon, mimetype="image/x-icon", max_age=86400)


@router.post("/system/task")
def system_task():
    payload = request.get_json(silent=True) or {}
    task_id = str(payload.get("task", "")).strip()
    if task_id not in TASKS:
        return jsonify(error="Unsupported system task."), 400
    decision = evaluate_permission("app.system", f"run system task: {task_id}", command=task_id)
    if not decision.allowed:
        return jsonify(error=decision.message), 403
    if decision.requires_confirmation:
        return jsonify(error=f"Approval required before running system task: {task_id}"), 403

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
