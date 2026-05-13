from __future__ import annotations

from collections.abc import Callable

from api.permissions import evaluate_permission
from events.event_bus import emit_event
from governance.safety_governor import evaluate_action
from voice.audio_router import play_activation_sound, play_error_sound
from voice.microphone_manager import voice_preferences
from voice.speech_to_text import SpeechToTextEngine
from voice.text_to_speech import TextToSpeechEngine
from voice.voice_runtime import voice_runtime


stt_engine = SpeechToTextEngine()
tts_engine = TextToSpeechEngine()


def push_to_talk(command_handler: Callable[..., dict], language: str = "auto", speak_response: bool = True, source: str = "push_to_talk") -> dict:
    runtime = voice_runtime.status()
    if not runtime.get("enabled"):
        return {"ok": False, "status": "disabled", "response": "Voice runtime is disabled."}

    decision = evaluate_permission("voice.listen", "global push-to-talk voice activation")
    if not decision.allowed:
        return {"ok": False, "status": "blocked", "response": decision.message}

    preferences = voice_preferences()
    voice_runtime.mark("activating", "Push-to-talk hotkey received.")
    play_activation_sound()
    voice_runtime.mark("listening", "Microphone input active.")

    try:
        transcript_result = stt_engine.transcribe_once(float(preferences.get("listenDurationSeconds") or 6), language=language or preferences.get("language", "auto"))
        transcript = str(transcript_result.get("transcript") or "").strip()
        if not transcript:
            play_error_sound()
            voice_runtime.mark("idle", "No speech detected.")
            return {"ok": False, "status": "no_speech", "transcript": "", "response": "I could not hear a command."}

        voice_runtime.mark("thinking", "Routing voice command into cognitive orchestration.", transcript=transcript)
        safety = evaluate_action("automation.run", f"voice command: {transcript}", command=transcript)
        if not safety.get("allowed"):
            response = f"Voice command blocked: {safety.get('reason')}"
            voice_runtime.mark("blocked", response, transcript=transcript, response=response)
            return {"ok": False, "status": "blocked", "transcript": transcript, "response": response, "safety": safety}
        if safety.get("requiresApproval"):
            response = f"Confirmation required before running: {transcript}"
            voice_runtime.mark("waiting", response, transcript=transcript, response=response)
            return {"ok": False, "status": "needs_confirmation", "transcript": transcript, "response": response, "safety": safety}

        result = command_handler(transcript, speak_response=False, language_mode=language or preferences.get("language", "auto"))
        response = str(result.get("response") or "Done.")
        voice_runtime.mark("speaking" if speak_response and not preferences.get("silentMode") else "idle", "Voice workflow complete.", transcript=transcript, response=response)
        speech = None
        if speak_response and not preferences.get("silentMode"):
            speech = tts_engine.speak(response[:900], silent=bool(preferences.get("silentMode")))
        voice_runtime.mark("idle", "Awaiting next voice command.", transcript=transcript, response=response)
        emit_event("voice.command_completed", {"source": source, "transcript": transcript})
        return {"ok": True, "status": "complete", "transcript": transcript, "response": response, "speech": speech, "stt": transcript_result}
    except Exception as error:
        play_error_sound()
        voice_runtime.mark("error", str(error))
        emit_event("voice.command_failed", {"source": source, "error": str(error)}, level="error")
        return {"ok": False, "status": "error", "response": str(error)}
