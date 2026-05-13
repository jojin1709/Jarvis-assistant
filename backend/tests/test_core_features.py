import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agents.task_planner import build_execution_plan
from api.memory_storage import _cosine, _text_embedding
from api.wake_words import wake_command_from
from providers.base_provider import ProviderResult
from providers.provider_router import _route_candidates, aggregate_responses
from release_security.trusted_update_checker import validate_update_manifest
from decision_engine.retry_planner import plan_retry
from decision_engine.execution_scorer import score_execution_plan
from governance.safety_governor import evaluate_action
from knowledge.embedding_engine import cosine as knowledge_cosine, embed_text
from platform_core.service_catalog import tools_for_goal
from reasoning.planning_engine import build_cognitive_plan
from reflection.failure_analyzer import analyze_failure
from simulation.dry_run_engine import dry_run_goal
from state_machine.transition_controller import can_transition
from sync.conflict_resolver import resolve_conflict
from sync.encryption import decrypt_bytes, encrypt_bytes
from telemetry.analytics_engine import analytics_snapshot
from tools.plugin_tool import _command_entries, _matches
from vision.screenshot import _summary
from voice.wake_manager import parse_wake_phrase
from voice.voice_runtime import voice_runtime
from workflows.workflow_parser import execution_order, validate_workflow


class CoreFeatureTests(unittest.TestCase):
    def test_planner_splits_multi_step_commands(self):
        plan = build_execution_plan("open downloads then show system status")
        self.assertEqual([step.label for step in plan], ["open downloads", "show system status"])

    def test_malayalam_wake_phrase_is_supported(self):
        awakened, command = wake_command_from("ഹേ ജാർവിസ് open youtube")
        self.assertTrue(awakened)
        self.assertEqual(command, "open youtube")

    def test_plugin_manifest_command_matching(self):
        plugin = {
            "commands": [
                {
                    "id": "daily-check",
                    "label": "Daily Check",
                    "triggers": ["daily check"],
                    "action": {"type": "response", "text": "Ready."},
                }
            ]
        }
        command = _command_entries(plugin)[0]
        self.assertTrue(_matches(command, "daily check"))
        self.assertTrue(_matches(command, "run daily check"))

    def test_vision_summary_includes_ocr_and_browser_context(self):
        summary = _summary(
            "browser",
            1200,
            800,
            140,
            "#112233",
            "",
            "Welcome to Jarvis",
            [{"name": "top-left", "brightness": 220, "dominantColor": "#ffffff"}],
            {"title": "Jarvis", "url": "https://example.test"},
        )
        self.assertIn("OCR detected readable text", summary)
        self.assertIn("Browser page", summary)

    def test_local_embeddings_are_deterministic(self):
        left = _text_embedding("restaurant menu booking")
        right = _text_embedding("restaurant menu booking")
        self.assertEqual(left, right)
        self.assertGreater(_cosine(left, right), 0.99)

    def test_browser_provider_routes_respect_enabled_map(self):
        candidates = _route_candidates(
            "coding",
            None,
            {
                "enabled": True,
                "enabled_providers": {"chatgpt_web": True, "claude_web": False, "gemini_web": True},
                "routes": {"coding": "claude_web"},
            },
        )
        self.assertEqual(candidates, ["chatgpt_web", "gemini_web"])

    def test_multi_provider_aggregation_tracks_sources(self):
        result = aggregate_responses(
            [
                ProviderResult(ok=True, provider="chatgpt_web", response="First answer", latency_ms=20),
                ProviderResult(ok=True, provider="claude_web", response="Second answer", latency_ms=40),
            ]
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.provider, "multi_provider")
        self.assertEqual(result.metadata["sources"], ["chatgpt_web", "claude_web"])
        self.assertIn("First answer", result.response)

    def test_workflow_graph_validation_and_ordering(self):
        ok, _message, workflow = validate_workflow(
            {
                "name": "Recon to report",
                "nodes": [{"id": "recon", "type": "terminal"}, {"id": "report", "type": "ai"}],
                "edges": [{"from": "recon", "to": "report"}],
            }
        )
        self.assertTrue(ok)
        self.assertEqual([node["id"] for node in execution_order(workflow)], ["recon", "report"])

    def test_decision_retry_planner_routes_build_errors_to_self_heal(self):
        retry = plan_retry("Build failed with SyntaxError", 1)
        self.assertTrue(retry["retry"])
        self.assertEqual(retry["strategy"], "self_heal")

    def test_knowledge_embeddings_are_searchable(self):
        left = embed_text("browser automation playwright selectors")
        right = embed_text("playwright browser selectors")
        self.assertGreater(knowledge_cosine(left, right), 0.2)

    def test_platform_catalog_selects_capability_tools(self):
        tools = tools_for_goal("debug project and inspect browser")
        self.assertIn("coding", tools)
        self.assertIn("browser", tools)

    def test_cognitive_plan_contains_reasoning_trace_and_score(self):
        plan = build_cognitive_plan("debug project and inspect browser", {"context": {"world": {}}})
        self.assertGreaterEqual(plan["taskGraph"]["stepCount"], 1)
        self.assertTrue(plan["reasoningTrace"])
        self.assertGreater(score_execution_plan(plan)["score"], 0)

    def test_reflection_classifies_build_failure(self):
        failure = analyze_failure("Build failed with SyntaxError in src/App.jsx")
        self.assertEqual(failure["category"], "code_or_build")

    def test_state_machine_allows_planning_from_idle(self):
        self.assertTrue(can_transition("IDLE", "PLANNING"))
        self.assertFalse(can_transition("EXECUTING", "PLANNING"))

    def test_dry_run_never_executes(self):
        result = dry_run_goal("build and test a MERN app")
        self.assertTrue(result["ok"])
        self.assertFalse(result["willExecute"])

    def test_governance_blocks_dangerous_command(self):
        result = evaluate_action("terminal.run", "dangerous delete", command="rm -rf /")
        self.assertFalse(result["allowed"])

    def test_sync_encryption_round_trip_and_conflict_resolution(self):
        payload = b"local-first private backup"
        encrypted = encrypt_bytes(payload)
        self.assertNotEqual(encrypted, payload)
        self.assertEqual(decrypt_bytes(encrypted), payload)
        conflict = resolve_conflict({"updatedAt": "2026-01-01T00:00:00"}, {"updatedAt": "2026-01-02T00:00:00"})
        self.assertEqual(conflict["winner"], "remote")

    def test_telemetry_is_disabled_by_default_and_local(self):
        snapshot = analytics_snapshot()
        self.assertFalse(snapshot["config"]["enabled"])
        self.assertTrue(snapshot["localOnly"])

    def test_release_manifest_requires_signature_hash(self):
        result = validate_update_manifest({"version": "1.0.0", "url": "https://example.test/app.exe"})
        self.assertFalse(result["ok"])
        self.assertIn("sha256", result["missing"])

    def test_voice_runtime_exposes_hotkey_and_wake_parser(self):
        status = voice_runtime.set_mode("push_to_talk")
        self.assertEqual(status["hotkey"], "Space+M")
        parsed = parse_wake_phrase("hey jarvis open downloads")
        self.assertTrue(parsed["awakened"])
        self.assertEqual(parsed["command"], "open downloads")


if __name__ == "__main__":
    unittest.main()
