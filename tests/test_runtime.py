import json
import unittest
from pathlib import Path

from aigc_director_kit.actions import load_action_library
from aigc_director_kit.runtime import build_runtime_handoff, build_runtime_handoff_file


ROOT = Path(__file__).resolve().parents[1]


class RuntimeHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow_path = ROOT / "examples" / "skill_workflow_case.json"
        cls.library_path = ROOT / "examples" / "action_library.json"
        cls.library = load_action_library(cls.library_path)

    def test_builds_dry_run_packet(self) -> None:
        packet = build_runtime_handoff_file(self.workflow_path, self.library_path, adapter_name="blender-previs")
        self.assertTrue(packet["valid"])
        self.assertEqual(packet["contract"], "aigc-director-runtime-handoff")
        self.assertEqual(packet["runtime"]["adapter"], "blender-previs")
        self.assertFalse(packet["runtime"]["executed"])
        self.assertEqual(
            packet["compiled_action_requests"][0]["compiled"]["matched_actions"][0]["id"],
            "run_quick_stop",
        )
        self.assertEqual(packet["evidence"]["render_status"], "not_run")

    def test_invalid_workflow_remains_invalid_in_packet(self) -> None:
        workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        workflow["action_requests"][0]["text"] = "invent an unsupported action"
        packet = build_runtime_handoff(workflow, self.library)
        self.assertFalse(packet["valid"])
        self.assertEqual(packet["evidence"]["contract_validation"], "failed")
        self.assertEqual(packet["compiled_action_requests"], [])

    def test_adapter_name_is_required(self) -> None:
        with self.assertRaises(ValueError):
            build_runtime_handoff({}, self.library, adapter_name=" ")


if __name__ == "__main__":
    unittest.main()
