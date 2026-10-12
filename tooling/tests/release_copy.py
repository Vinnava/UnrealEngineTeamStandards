"""Shared by the tests: copies this repository the way a release ships it.

In a git checkout that is what git would commit - ignore rules applied - so an IDE folder or a local
scratch file on the developer's machine never reaches the copy a test checks.
"""

import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def copy_release(destination: Path) -> None:
    if not (REPO / ".git").exists():
        shutil.copytree(REPO, destination, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        return
    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                            cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    for name in dict.fromkeys(listed):
        source = REPO / name
        if source.is_file():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
