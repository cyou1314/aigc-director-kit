import unittest
from pathlib import Path

from aigc_director_kit.contract import validate_plan_file


ROOT = Path(__file__).resolve().parents[1]


class PublicCaseTests(unittest.TestCase):
    def test_sanitized_workflow_cases_are_valid(self) -> None:
        case_names = (
            "shot_plan.json",
            "one_take_previs_case.json",
            "film_contract_handoff_case.json",
            "multi_actor_prop_case.json",
        )
        for case_name in case_names:
            with self.subTest(case=case_name):
                result = validate_plan_file(ROOT / "examples" / case_name)
                self.assertTrue(result.valid, result.errors)
                self.assertEqual(result.summary["shot_count"], 1 if case_name != "shot_plan.json" else 2)


if __name__ == "__main__":
    unittest.main()
