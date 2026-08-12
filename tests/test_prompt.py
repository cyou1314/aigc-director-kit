import json
import unittest
from pathlib import Path

from aigc_director_kit.contract import load_json
from aigc_director_kit.prompt import validate_prompt_pack, validate_prompt_pack_file


ROOT = Path(__file__).resolve().parents[1]


class PromptPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompt_path = ROOT / "examples" / "prompt_pack_case.json"
        cls.plan_path = ROOT / "examples" / "one_take_previs_case.json"

    def test_example_matches_source_plan(self) -> None:
        result = validate_prompt_pack_file(self.prompt_path, self.plan_path)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.summary["prompt_shot_count"], 1)
        self.assertEqual(result.summary["source_shot_count"], 1)
        self.assertEqual(result.warnings, [])

    def test_duration_drift_is_a_warning(self) -> None:
        prompt_pack = json.loads(self.prompt_path.read_text(encoding="utf-8"))
        prompt_pack["shots"][0]["duration_s"] = 3.5
        result = validate_prompt_pack(prompt_pack, load_json(self.plan_path))
        self.assertTrue(result.valid, result.errors)
        self.assertTrue(any("duration_s differs" in warning for warning in result.warnings))

    def test_action_causality_is_required(self) -> None:
        prompt_pack = json.loads(self.prompt_path.read_text(encoding="utf-8"))
        del prompt_pack["shots"][0]["action_causality"]
        result = validate_prompt_pack(prompt_pack)
        self.assertFalse(result.valid)
        self.assertTrue(any("action_causality" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
