import json
import unittest
from pathlib import Path

from aigc_director_kit.actions import load_action_library
from aigc_director_kit.integration import (
    validate_skill_integration,
    validate_skill_integration_files,
)


ROOT = Path(__file__).resolve().parents[1]


class SkillIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter_path = ROOT / "examples" / "local_skill_adapter_case.json"
        cls.workflow_path = ROOT / "examples" / "skill_workflow_case.json"
        cls.library_path = ROOT / "examples" / "action_library.json"
        cls.library = load_action_library(cls.library_path)

    def load_examples(self) -> tuple[dict, dict]:
        adapter = json.loads(self.adapter_path.read_text(encoding="utf-8"))
        workflow = json.loads(self.workflow_path.read_text(encoding="utf-8"))
        return adapter, workflow

    def test_public_adapter_and_workflow_are_compatible(self) -> None:
        result = validate_skill_integration_files(
            self.adapter_path,
            self.workflow_path,
            self.library_path,
        )

        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.summary["matched_stage_count"], 3)
        self.assertEqual(
            result.summary["unused_adapter_stage_ids"],
            ["prompt-contract", "quality-evidence"],
        )
        self.assertEqual(result.summary["public_safety_issue_count"], 0)
        self.assertTrue(result.summary["manual_privacy_review_required"])

    def test_integration_without_action_library_keeps_an_explicit_warning(self) -> None:
        result = validate_skill_integration_files(self.adapter_path, self.workflow_path)

        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.summary["compiled_action_count"], 0)
        self.assertTrue(any("was not compiled" in warning for warning in result.warnings))

    def test_skill_label_mismatch_is_rejected(self) -> None:
        adapter, workflow = self.load_examples()
        workflow["stages"][0]["skill"] = "another-director"

        result = validate_skill_integration(adapter, workflow, self.library)

        self.assertFalse(result.valid)
        self.assertTrue(any("Skill label" in error for error in result.errors))

    def test_output_and_evidence_mismatches_are_rejected(self) -> None:
        adapter, workflow = self.load_examples()
        workflow["stages"][0]["output"] = "custom-shot-plan"
        workflow["stages"][1]["evidence"] = "designed"

        result = validate_skill_integration(adapter, workflow, self.library)

        self.assertFalse(result.valid)
        self.assertTrue(any("output contract" in error for error in result.errors))
        self.assertTrue(any("evidence semantics" in error for error in result.errors))

    def test_action_request_must_use_an_action_producer(self) -> None:
        adapter, workflow = self.load_examples()
        workflow["action_requests"][0]["stage_id"] = "direction"

        result = validate_skill_integration(adapter, workflow, self.library)

        self.assertFalse(result.valid)
        self.assertTrue(any("action_requests[0].stage_id" in error for error in result.errors))

    def test_undeclared_workflow_stage_is_rejected(self) -> None:
        adapter, workflow = self.load_examples()
        workflow["stages"].append(
            {
                "id": "private-stage",
                "skill": "private-skill",
                "role": "Private stage must not bypass the public adapter.",
                "output": "private-output",
                "evidence": "designed",
                "status": "validated",
            }
        )

        result = validate_skill_integration(adapter, workflow, self.library)

        self.assertFalse(result.valid)
        self.assertTrue(any("not declared by the adapter" in error for error in result.errors))

    def test_required_workflow_producer_cannot_be_omitted(self) -> None:
        adapter, workflow = self.load_examples()
        workflow["stages"] = [stage for stage in workflow["stages"] if stage["id"] != "coordination"]

        result = validate_skill_integration(adapter, workflow, self.library)

        self.assertFalse(result.valid)
        self.assertTrue(
            any("aigc-director-skill-workflow" in error for error in result.errors)
        )

    def test_local_path_is_rejected_without_echoing_its_value(self) -> None:
        adapter, workflow = self.load_examples()
        workflow["handoff"]["constraints"].append(r"Read Z:\redacted\brief.md")

        result = validate_skill_integration(adapter, workflow, self.library)

        errors = "\n".join(result.errors)
        self.assertFalse(result.valid)
        self.assertIn("local or network path", errors)
        self.assertNotIn(r"Z:\redacted\brief.md", errors)

    def test_credential_field_and_email_are_rejected(self) -> None:
        adapter, workflow = self.load_examples()
        adapter["stages"][0]["role"] = "Contact editor@example.com before export."
        workflow["api_key"] = "not-a-real-key"

        result = validate_skill_integration(adapter, workflow, self.library)

        errors = "\n".join(result.errors)
        self.assertFalse(result.valid)
        self.assertIn("credential-bearing field", errors)
        self.assertIn("email address", errors)
        self.assertNotIn("not-a-real-key", errors)
        self.assertNotIn("editor@example.com", errors)

        issue_codes = {issue["code"] for issue in result.issues}
        self.assertIn("public_safety_credential", issue_codes)
        self.assertIn("public_safety_email", issue_codes)
        self.assertTrue(all(issue["severity"] == "error" for issue in result.issues))


if __name__ == "__main__":
    unittest.main()
