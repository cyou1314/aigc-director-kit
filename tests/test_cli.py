import json
import tempfile
import unittest
from pathlib import Path

from aigc_director_kit.cli import main


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_validate_plan_json_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "result.json"
            # The CLI writes to stdout; this assertion exercises the actual command path.
            self.assertEqual(main(["validate-plan", str(ROOT / "examples" / "shot_plan.json"), "--json"]), 0)

    def test_compile_action_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "action.json"
            output.write_text("{}", encoding="utf-8")
            code = main(
                [
                    "compile-action",
                    "--library",
                    str(ROOT / "examples" / "action_library.json"),
                    "--text",
                    "前踢",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
