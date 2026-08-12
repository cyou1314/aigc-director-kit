import json
import unittest
from pathlib import Path

from aigc_director_kit.actions import compile_action_request, list_actions, load_action_library


ROOT = Path(__file__).resolve().parents[1]


class ActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.library = load_action_library(ROOT / "examples" / "action_library.json")

    def test_search_matches_aliases_and_tags(self) -> None:
        results = list_actions(self.library, "跑")
        self.assertEqual([item["id"] for item in results], ["run_quick_stop"])

    def test_compile_known_actions_with_modifiers(self) -> None:
        result = compile_action_request("快速跑步然后急停，过渡0.2秒，原地", self.library)
        self.assertTrue(result["valid"])
        self.assertEqual([item["id"] for item in result["matched_actions"]], ["run_quick_stop"])
        self.assertEqual(result["modifiers"]["speed_scale"], 1.25)
        self.assertTrue(result["modifiers"]["in_place"])
        self.assertEqual(result["matched_actions"][0]["root_motion_scale"], 0.0)

    def test_compile_english_action_with_modifiers(self) -> None:
        result = compile_action_request("run quick stop, blend 0.2s, fast, in place", self.library)
        self.assertTrue(result["valid"])
        self.assertEqual([item["id"] for item in result["matched_actions"]], ["run_quick_stop"])
        self.assertEqual(result["modifiers"]["speed_scale"], 1.25)
        self.assertEqual(result["modifiers"]["blend_s"], 0.2)
        self.assertTrue(result["modifiers"]["in_place"])

    def test_compile_two_actions_in_text_order(self) -> None:
        result = compile_action_request("先伸手拿灯笼，再向右走，过渡0.3秒", self.library)
        self.assertTrue(result["valid"])
        self.assertEqual(
            [item["id"] for item in result["matched_actions"]],
            ["reach_lantern", "walk_turn_right"],
        )
        self.assertEqual(result["matched_actions"][1]["blend_s"], 0.3)

    def test_unknown_action_is_rejected_without_invention(self) -> None:
        result = compile_action_request("做一个空翻并抓住飞来的剑", self.library)
        self.assertFalse(result["valid"])
        self.assertIn("No supported action", result["error"])
        self.assertEqual(len(result["available_actions"]), 4)


if __name__ == "__main__":
    unittest.main()
