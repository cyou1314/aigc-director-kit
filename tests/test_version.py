import re
import unittest
from pathlib import Path

from aigc_director_kit import __version__


ROOT = Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def test_runtime_and_project_versions_match(self) -> None:
        project_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        project_version = re.search(r'^version\s*=\s*"([^"]+)"\s*$', project_text, re.MULTILINE)
        self.assertIsNotNone(project_version)
        self.assertEqual(__version__, "0.2.0")
        self.assertEqual(__version__, project_version.group(1))


if __name__ == "__main__":
    unittest.main()
