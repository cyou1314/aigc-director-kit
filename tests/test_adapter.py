import json
import unittest
from pathlib import Path

from aigc_director_kit.adapter import (
    ADAPTER_CONTRACT,
    validate_local_skill_adapter,
    validate_local_skill_adapter_file,
)


ROOT = Path(__file__).resolve().parents[1]


class LocalSkillAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter_path = ROOT / "examples" / "local_skill_adapter_case.json"

    def test_public_metadata_only_example_is_valid(self) -> None:
        result = validate_local_skill_adapter_file(self.adapter_path)

        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.summary["stage_count"], 5)
        self.assertEqual(result.summary["visibility"], "public-metadata-only")
        self.assertEqual(result.summary["source_access"], "local-only")
        self.assertIn("aigc-output-qc", result.summary["skill_labels"])

    def test_unknown_content_fields_are_rejected(self) -> None:
        adapter = json.loads(self.adapter_path.read_text(encoding="utf-8"))
        adapter["stages"][0]["prompt_text"] = "private prompt must not be published"

        result = validate_local_skill_adapter(adapter)

        self.assertFalse(result.valid)
        self.assertTrue(any("unsupported fields" in error for error in result.errors))

    def test_local_paths_are_rejected_even_in_an_allowed_text_field(self) -> None:
        adapter = json.loads(self.adapter_path.read_text(encoding="utf-8"))
        adapter["stages"][0]["role"] = r"Reads D:\private\brief.md before emitting metadata."

        result = validate_local_skill_adapter(adapter)

        self.assertFalse(result.valid)
        self.assertTrue(any("credential or local source path" in error for error in result.errors))

    def test_adapter_requires_the_public_metadata_boundary(self) -> None:
        adapter = json.loads(self.adapter_path.read_text(encoding="utf-8"))
        adapter["contract"] = "wrong-contract"
        adapter["visibility"] = "private-export"

        result = validate_local_skill_adapter(adapter)

        self.assertFalse(result.valid)
        self.assertEqual(ADAPTER_CONTRACT, "aigc-director-local-skill-adapter")
        self.assertTrue(any("visibility" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
