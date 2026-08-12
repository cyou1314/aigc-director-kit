import json
import unittest
from pathlib import Path

from aigc_director_kit.actions import load_action_library
from aigc_director_kit.workflow import validate_workflow, validate_workflow_file


ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow_path = ROOT / "examples" / "skill_workflow_case.json"
        cls.library = load_action_library(ROOT / "examples" / "action_library.json")

    def test_example_is_structurally_valid_without_library(self) -> None:
        result = validate_workflow_file(self.workflow_path)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.summary["stage_count"], 3)
        self.assertEqual(result.summary["shot_count"], 1)
        self.assertEqual(result.summary["compiled_action_count"], 0)
        self.assertTrue(result.warnings)

    def test_example_compiles_action_handoff(self) -> None:
        result = validate_workflow_file(
            self.workflow_path,
            ROOT / "examples" / "action_library.json",
        )
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.summary["compiled_action_count"], 1)
        self.assertEqual(result.summary["matched_action_ids"], ["run_quick_stop"])
        self.assertEqual(result.warnings, [])

    def test_unknown_action_is_rejected(self) -> None:
        workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        workflow["action_requests"][0]["text"] = "invent a flying sword choreography"
        result = validate_workflow(workflow, self.library)
        self.assertFalse(result.valid)
        self.assertTrue(any("could not be compiled" in error for error in result.errors))

    def test_action_request_must_reference_a_known_shot(self) -> None:
        workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        workflow["action_requests"][0]["shot_id"] = "S99"
        result = validate_workflow(workflow, self.library)
        self.assertFalse(result.valid)
        self.assertTrue(any("shot_id" in error for error in result.errors))

    def test_optional_prompt_and_qc_layers_are_validated(self) -> None:
        workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        workflow["prompt_pack"] = json.loads(
            (ROOT / "examples" / "prompt_pack_case.json").read_text(encoding="utf-8")
        )
        workflow["prompt_pack"]["project"] = workflow["project"]
        workflow["prompt_pack"]["shots"][0]["source_shot_id"] = "S01"
        workflow["prompt_pack"]["shots"][0]["duration_s"] = 4.0
        workflow["qc_report"] = json.loads(
            (ROOT / "examples" / "qc_report_unverified_case.json").read_text(encoding="utf-8")
        )
        workflow["qc_report"]["project"] = workflow["project"]
        result = validate_workflow(workflow, self.library)
        self.assertTrue(result.valid, result.errors)
        self.assertTrue(result.summary["prompt_pack_present"])
        self.assertEqual(result.summary["qc_report_status"], "unverified")

    def test_invalid_embedded_qc_layer_rejects_workflow(self) -> None:
        workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        workflow["qc_report"] = {
            "contract": "aigc-director-qc-report",
            "version": 1,
            "project": workflow["project"],
            "artifact": {"label": "missing", "available": False},
            "overall_status": "pass",
            "checks": [
                {
                    "id": "continuity",
                    "status": "pass",
                    "evidence": "inferred",
                    "notes": "Not inspected.",
                }
            ],
        }
        result = validate_workflow(workflow, self.library)
        self.assertFalse(result.valid)
        self.assertTrue(any("qc_report" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
