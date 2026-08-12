import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from aigc_director_kit import __version__
from aigc_director_kit.cli import main


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_windows_example_runner_has_portable_python_fallbacks(self) -> None:
        runner = (ROOT / "run_examples.bat").read_text(encoding="utf-8")
        self.assertIn("AIGC_DIRECTOR_PYTHON", runner)
        self.assertIn("%LocalAppData%\\Programs\\Python\\Python*\\python.exe", runner)
        self.assertIn("Python 3.10 or newer", runner)
        self.assertIn("verify-examples --root .", runner)

    def test_validate_plan_json_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "result.json"
            # The CLI writes to stdout; this assertion exercises the actual command path.
            self.assertEqual(main(["validate-plan", str(ROOT / "examples" / "shot_plan.json"), "--json"]), 0)

    def test_validate_local_skill_adapter_json_mode(self) -> None:
        self.assertEqual(
            main(
                [
                    "validate-local-skill-adapter",
                    str(ROOT / "examples" / "local_skill_adapter_case.json"),
                    "--json",
                ]
            ),
            0,
        )

    def test_validate_skill_integration_json_mode(self) -> None:
        self.assertEqual(
            main(
                [
                    "validate-skill-integration",
                    str(ROOT / "examples" / "local_skill_adapter_case.json"),
                    str(ROOT / "examples" / "skill_workflow_case.json"),
                    "--library",
                    str(ROOT / "examples" / "action_library.json"),
                    "--json",
                ]
            ),
            0,
        )

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

    def test_verify_examples_json_mode(self) -> None:
        self.assertEqual(
            main(["verify-examples", "--root", str(ROOT), "--json"]),
            0,
        )

    def test_verify_examples_rejects_an_invalid_explicit_root(self) -> None:
        self.assertEqual(main(["verify-examples", "--root", str(ROOT / "missing")]), 1)

    def test_cli_reports_the_package_version(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as result:
                main(["--version"])

        self.assertEqual(result.exception.code, 0)
        self.assertEqual(output.getvalue(), f"aigc-director-kit {__version__}\n")

    def test_verify_examples_writes_a_versioned_report_without_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "cinethread-verify.json"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "verify-examples",
                            "--root",
                            str(ROOT),
                            "--output",
                            str(output_path),
                        ]
                    ),
                    0,
                )

            report = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report["version"], __version__)
            self.assertNotIn(str(ROOT), json.dumps(report, ensure_ascii=False))

    def test_verify_examples_refuses_to_overwrite_a_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "cinethread-verify.json"
            output_path.write_text("{}", encoding="utf-8")
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors):
                self.assertEqual(
                    main(
                        [
                            "verify-examples",
                            "--root",
                            str(ROOT),
                            "--output",
                            str(output_path),
                        ]
                    ),
                    1,
                )

            self.assertIn("Refusing to overwrite existing output", errors.getvalue())
            self.assertNotIn(str(output_path), errors.getvalue())


if __name__ == "__main__":
    unittest.main()
