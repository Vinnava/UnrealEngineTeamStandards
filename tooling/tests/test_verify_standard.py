"""Tests for tooling/verify-standard.py. Run from the repository root:

    python -m unittest discover -s tooling/tests -v

Each test copies the repository the way a project vendors it - no .git - changes it one way, and
asserts the verifier's verdict. A verifier that passes a clean copy proves nothing on its own; these
show it notices an edit, a missing file and a stale manifest, and forgives what 26.4 allows.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from release_copy import copy_release

REPO = Path(__file__).resolve().parents[2]


class VerifyStandardTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name) / "standards"
        copy_release(self.root)

    def tearDown(self) -> None:
        self._dir.cleanup()

    def run_verifier(self, *args: str) -> tuple[int, str]:
        result = subprocess.run([sys.executable, str(self.root / "tooling" / "verify-standard.py"), *args],
                                capture_output=True, text=True, cwd=self.root)
        return result.returncode, result.stdout

    def assertPasses(self, *args: str) -> str:
        code, out = self.run_verifier(*args)
        self.assertEqual(code, 0, out)
        return out

    def assertFails(self, fragment: str, *args: str) -> None:
        code, out = self.run_verifier(*args)
        self.assertEqual(code, 1, f"expected failure, got exit {code}:\n{out}")
        self.assertIn(fragment, out)

    def test_the_real_repository_is_complete(self):
        self.assertPasses("--complete")

    def test_an_edited_file_fails(self):
        path = self.root / "rules/19-audio.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nA local tweak.\n", encoding="utf-8")
        self.assertFails("rules/19-audio.md: edited")

    def test_crlf_line_endings_still_verify(self):
        path = self.root / "rules/19-audio.md"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        self.assertPasses()

    def test_a_missing_rule_file_fails(self):
        (self.root / "rules/19-audio.md").unlink()
        self.assertFails("rules/19-audio.md: missing")

    def test_a_vendored_copy_may_leave_out_the_optional_files(self):
        shutil.rmtree(self.root / ".github")
        shutil.rmtree(self.root / "tooling/tests/validator-harness")
        (self.root / ".gitattributes").unlink()
        out = self.assertPasses()
        self.assertIn("optional files not vendored", out)

    def test_complete_mode_does_not_forgive_an_omission(self):
        shutil.rmtree(self.root / ".github")
        self.assertFails(".github/workflows/standard.yml: missing", "--complete")

    def test_a_projects_own_note_only_warns(self):
        (self.root / "VENDORED.md").write_text("Vendored at v0.0.0.\n", encoding="utf-8")
        out = self.assertPasses()
        self.assertIn("warning: VENDORED.md: not part of the release", out)

    def test_a_file_missing_from_the_manifest_fails_complete(self):
        (self.root / "rules/notes.md").write_text("New.\n", encoding="utf-8")
        self.assertFails("rules/notes.md: not in MANIFEST.sha256", "--complete")

    def test_write_brings_the_manifest_up_to_date(self):
        (self.root / "rules/notes.md").write_text("New.\n", encoding="utf-8")
        self.assertPasses("--write")
        self.assertPasses("--complete")

    def test_a_manifest_for_another_version_fails_complete(self):
        readme = self.root / "README.md"
        text = readme.read_text(encoding="utf-8")
        start = text.index("**Version ") + len("**Version ")
        end = text.index("**", start)
        readme.write_text(text[:start] + "9.9.9" + text[end:], encoding="utf-8")
        self.assertPasses("--write")
        manifest = self.root / "MANIFEST.sha256"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace("9.9.9", "9.9.8", 1), encoding="utf-8")
        self.assertFails("MANIFEST.sha256 is for version 9.9.8, README.md says 9.9.9", "--complete")

    def test_no_manifest_fails(self):
        (self.root / "MANIFEST.sha256").unlink()
        self.assertFails("not found")


if __name__ == "__main__":
    unittest.main()
