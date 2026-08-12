import json
import tempfile
import unittest
from pathlib import Path

from aigc_director_kit import __version__
from aigc_director_kit.verification import find_project_root, run_public_example_verification


ROOT = Path(__file__).resolve().parents[1]


class PublicExampleVerificationTests(unittest.TestCase):
    def test_verifies_all_public_examples_without_local_paths(self) -> None:
        report = run_public_example_verification(ROOT)

        self.assertTrue(report["valid"])
        self.assertEqual(report["version"], __version__)
        self.assertEqual(report["summary"], {"check_count": 11, "passed_check_count": 11})
        self.assertNotIn(str(ROOT), json.dumps(report, ensure_ascii=False))
        self.assertTrue(all(check["valid"] for check in report["checks"]))

    def test_accepts_an_explicit_checkout_root(self) -> None:
        self.assertEqual(find_project_root(ROOT), ROOT)

    def test_missing_checkout_has_a_safe_error_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(FileNotFoundError, "CineThread source checkout"):
                find_project_root(Path(temp_dir))

    def test_failed_verification_does_not_expose_the_checkout_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_root = Path(temp_dir)
            (temporary_root / "pyproject.toml").write_text("", encoding="utf-8")
            (temporary_root / "examples").mkdir()

            report = run_public_example_verification(temporary_root)

            self.assertFalse(report["valid"])
            self.assertNotIn(str(temporary_root), json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
