import json
import unittest
from pathlib import Path

from aigc_director_kit.qc import validate_qc_report, validate_qc_report_file


ROOT = Path(__file__).resolve().parents[1]


class QcReportTests(unittest.TestCase):
    def test_unverified_example_is_valid(self) -> None:
        result = validate_qc_report_file(ROOT / "examples" / "qc_report_unverified_case.json")
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.summary["observed_check_count"], 0)
        self.assertEqual(result.summary["overall_status"], "unverified")

    def test_pass_requires_observed_artifact_evidence(self) -> None:
        report = {
            "contract": "aigc-director-qc-report",
            "version": 1,
            "project": "qc-test",
            "artifact": {"label": "clip", "available": True},
            "overall_status": "pass",
            "checks": [
                {
                    "id": "continuity",
                    "status": "pass",
                    "evidence": "inferred",
                    "notes": "Not actually inspected.",
                }
            ],
        }
        result = validate_qc_report(report)
        self.assertFalse(result.valid)
        self.assertTrue(any("observed evidence" in error for error in result.errors))

    def test_observed_pass_is_valid_when_artifact_is_available(self) -> None:
        report = {
            "contract": "aigc-director-qc-report",
            "version": 1,
            "project": "qc-test",
            "artifact": {"label": "clip", "available": True},
            "overall_status": "pass",
            "checks": [
                {
                    "id": "continuity",
                    "status": "pass",
                    "evidence": "observed",
                    "notes": "Tail frame matches the next-shot entry contract.",
                }
            ],
        }
        result = validate_qc_report(report)
        self.assertTrue(result.valid, result.errors)

    def test_unavailable_artifact_cannot_have_observed_check(self) -> None:
        report = json.loads(
            (ROOT / "examples" / "qc_report_unverified_case.json").read_text(encoding="utf-8")
        )
        report["checks"][0]["evidence"] = "observed"
        result = validate_qc_report(report)
        self.assertFalse(result.valid)
        self.assertTrue(any("artifact.available" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
