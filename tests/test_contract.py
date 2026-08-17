import json
import unittest
from pathlib import Path

from aigc_director_kit.contract import validate_plan, validate_plan_file


ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_example_plan_is_valid(self) -> None:
        result = validate_plan_file(ROOT / "examples" / "shot_plan.json")
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.summary["shot_count"], 2)
        self.assertEqual(result.summary["total_frames"], 168)
        self.assertEqual(result.warnings, [])

    def test_bad_camera_keyframe_is_rejected(self) -> None:
        plan = json.loads((ROOT / "examples" / "shot_plan.json").read_text(encoding="utf-8"))
        plan["shots"][0]["camera"]["path"][1]["time_s"] = 5
        result = validate_plan(plan)
        self.assertFalse(result.valid)
        self.assertTrue(any("time_s" in error for error in result.errors))
        issue = next(item for item in result.issues if item["path"].endswith("time_s"))
        self.assertEqual(issue["severity"], "error")
        self.assertEqual(issue["code"], "out_of_range")
        self.assertEqual(issue["path"], "shots[0].camera.path[1].time_s")

    def test_state_mismatch_is_a_warning_not_an_error(self) -> None:
        plan = json.loads((ROOT / "examples" / "shot_plan.json").read_text(encoding="utf-8"))
        plan["shots"][1]["entry_state"]["screen_axis"] = "right-to-left"
        result = validate_plan(plan)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("S01 -> S02", result.warnings[0])
        self.assertEqual(result.issues[0]["severity"], "warning")
        self.assertEqual(result.issues[0]["code"], "continuity_warning")
        self.assertIsNone(result.issues[0]["path"])

    def test_validation_result_keeps_legacy_fields_and_adds_issues(self) -> None:
        result = validate_plan({})
        payload = result.as_dict()
        self.assertEqual(
            list(payload),
            ["contract", "version", "valid", "errors", "warnings", "issues", "summary"],
        )
        self.assertEqual(payload["errors"], result.errors)
        self.assertEqual(payload["warnings"], result.warnings)
        self.assertEqual(payload["issues"], result.issues)
        self.assertTrue(all(set(issue) == {"severity", "code", "path", "message"} for issue in result.issues))

    def test_duplicate_shot_id_is_rejected(self) -> None:
        plan = json.loads((ROOT / "examples" / "shot_plan.json").read_text(encoding="utf-8"))
        plan["shots"][1]["id"] = "S01"
        result = validate_plan(plan)
        self.assertFalse(result.valid)
        self.assertTrue(any("duplicated" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
