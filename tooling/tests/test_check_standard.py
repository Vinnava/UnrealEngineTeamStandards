"""Mutation tests for tooling/check-standard.py. Run from the repository root:

    python -m unittest discover -s tooling/tests -v

Each test copies the repository, breaks it in one specific way, and asserts the checker notices.
A consistency checker that passes a clean repository proves nothing on its own: in 1.8 a check
with a backspace character in its regex passed everything, because it matched nothing. These
tests are what caught that, and they stay so it cannot happen quietly again.
"""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class RepoCopy:
    def __init__(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name) / "repo"
        shutil.copytree(REPO, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))

    def edit(self, relative: str, old: str, new: str) -> None:
        path = self.root / relative
        text = path.read_text(encoding="utf-8")
        assert old in text, f"{old!r} not in {relative} - the mutation is out of date"
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def check(self) -> tuple[int, str]:
        result = subprocess.run([sys.executable, str(self.root / "tooling" / "check-standard.py")],
                                capture_output=True, text=True, cwd=self.root)
        return result.returncode, result.stdout

    def close(self) -> None:
        self._dir.cleanup()


class CheckStandardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = RepoCopy()

    def tearDown(self) -> None:
        self.repo.close()

    def assertFails(self, *fragments: str) -> None:
        code, out = self.repo.check()
        self.assertEqual(code, 1, f"expected failure, got exit {code}:\n{out}")
        for fragment in fragments:
            self.assertIn(fragment, out)

    def test_the_real_repository_is_clean(self):
        code, out = self.repo.check()
        self.assertEqual(code, 0, out)
        self.assertIn("0 errors", out)

    def test_reference_to_a_missing_section(self):
        self.repo.edit("rules/19-audio.md", "(3.5)", "(3.99)")
        self.assertFails("section 3.99, which does not exist")

    def test_broken_relative_link(self):
        self.repo.edit("README.md", "(rules/19-audio.md)", "(rules/19-audio-gone.md)")
        self.assertFails("19-audio-gone.md, which does not exist")

    def test_non_ascii_character(self):
        self.repo.edit("rules/19-audio.md", "Audio naming", "Audio " + chr(0x2014) + " naming")
        self.assertFails("U+2014")

    def test_readme_version_drifts_from_changelog(self):
        version = re.search(r"\*\*Version ([\d.]+)\*\*", (REPO / "README.md").read_text(encoding="utf-8")).group(1)
        self.repo.edit("README.md", f"**Version {version}**", "**Version 9.9.9**")
        self.assertFails("README says version 9.9.9")

    def test_template_version_drifts_from_readme(self):
        text = (REPO / "tooling/project-template/CLAUDE.md").read_text(encoding="utf-8")
        pinned = re.search(r"Standard version: ([\d.]+)", text).group(1)
        self.repo.edit("tooling/project-template/CLAUDE.md", f"Standard version: {pinned}", "Standard version: 0.1.0")
        self.assertFails("project-template/CLAUDE.md says standard version 0.1.0")

    def test_section_heading_moved_into_the_wrong_file(self):
        self.repo.edit("rules/19-audio.md", "### 19.1 ", "### 23.1 ")
        self.assertFails("19-audio.md: holds section(s) ['23'] that its name does not claim")

    def test_file_renamed_away_from_its_sections(self):
        (self.repo.root / "rules/21-online.md").rename(self.repo.root / "rules/16-online.md")
        self.assertFails("16-online.md: holds section(s) ['21']")

    def test_always_loaded_set_over_budget(self):
        padding = "\n" + ("Padding sentence that exists only to push the file over budget. " * 2000) + "\n"
        path = self.repo.root / "rules/09-architecture.md"
        path.write_text(path.read_text(encoding="utf-8") + padding, encoding="utf-8")
        self.assertFails("always-loaded set is")

    def _release(self, version: str, bullet: str) -> None:
        """Adds a changelog entry above the current one and moves README and template to match."""
        self.repo.edit("CHANGELOG.md", "# Changelog\n", f"# Changelog\n\n**{version} - 2099-01-01**\n\n- {bullet}\n\n")
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.repo.edit("README.md", re.search(r"\*\*Version [\d.]+\*\*", readme).group(0), f"**Version {version}**")
        template = (REPO / "tooling/project-template/CLAUDE.md").read_text(encoding="utf-8")
        self.repo.edit("tooling/project-template/CLAUDE.md",
                       re.search(r"Standard version: [\d.]+", template).group(0), f"Standard version: {version}")

    def _next(self, bump: str) -> str:
        major, minor, _ = (int(part) for part in re.search(
            r"\*\*Version (\d+)\.(\d+)\.(\d+)\*\*", (REPO / "README.md").read_text(encoding="utf-8")).groups())
        return f"{major + 1}.0.0" if bump == "major" else f"{major}.{minor + 1}.0"

    def test_rule_change_in_a_minor_release_fails(self):
        self._release(self._next("minor"), "**Rule change: something now means something else.**")
        self.assertFails("changes a rule's meaning", "major")

    def test_rule_change_in_a_major_release_passes(self):
        self._release(self._next("major"), "**Rule change: something now means something else.**")
        code, out = self.repo.check()
        self.assertEqual(code, 0, out)

    def test_minor_release_without_a_rule_change_passes(self):
        self._release(self._next("minor"), "**New section on something.**")
        code, out = self.repo.check()
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
