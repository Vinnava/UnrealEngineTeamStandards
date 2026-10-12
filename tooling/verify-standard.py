#!/usr/bin/env python3
"""Proves a pinned copy of the standard is the release it claims to be (26.4).

In a project, from the project root, against the copy in standards/:

    python standards/tooling/verify-standard.py

In this repository:

    python tooling/verify-standard.py --write       regenerate MANIFEST.sha256 after any change
    python tooling/verify-standard.py --complete    CI: the manifest lists exactly the files, unedited

Exits non-zero when a file was edited or a required file is missing, so a project's CI can gate on it.
It works the same whatever source control the project uses: it reads files, not history.
"""

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = "MANIFEST.sha256"
HEADER = "# Unreal Engine Team Standards"

# A vendored copy may leave these out (26.4): CI config, the in-engine harnesses, and git's own files
OPTIONAL = (".github/", "tooling/tests/", ".gitattributes", ".gitignore")

# Never part of a release: version-control metadata and Python's bytecode cache
SKIPPED = {".git", "__pycache__"}


def file_hash(path: Path) -> str:
    """SHA-256 with CRLF read as LF, so a checkout that converts line endings still verifies."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def present_files(root: Path) -> list[str]:
    """Every file under root that belongs in a release. In a git checkout, what git would commit."""
    if (root / ".git").exists():
        listed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--deduplicate"],
            cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
        files = [name for name in listed if (root / name).is_file()]
    else:
        files = [path.relative_to(root).as_posix() for path in root.rglob("*")
                 if path.is_file() and not SKIPPED & set(path.relative_to(root).parts) and path.suffix != ".pyc"]
    return sorted(name for name in files if name != MANIFEST)


def readme_version(root: Path) -> str | None:
    readme = root / "README.md"
    if not readme.exists():
        return None
    match = re.search(r"\*\*Version (\d+\.\d+\.\d+)\*\*", readme.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def read_manifest(root: Path) -> tuple[str | None, dict[str, str]]:
    version, entries = None, {}
    for line in (root / MANIFEST).read_text(encoding="utf-8").splitlines():
        if line.startswith(HEADER):
            version = line[len(HEADER):].strip()
        elif line.strip() and not line.startswith("#"):
            digest, name = line.split("  ", 1)
            entries[name] = digest
    return version, entries


def write_manifest(root: Path) -> int:
    version = readme_version(root)
    if not version:
        print("error: no '**Version X.Y.Z**' in README.md")
        return 1
    files = present_files(root)
    lines = [f"{HEADER} {version}",
             "# SHA-256 of every file in the release, CRLF read as LF. Checked by tooling/verify-standard.py (26.4).",
             "# Regenerate after any change: python tooling/verify-standard.py --write"]
    lines += [f"{file_hash(root / name)}  {name}" for name in files]
    (root / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST}: {len(files)} files, version {version}")
    return 0


def verify(root: Path, complete: bool) -> int:
    if not (root / MANIFEST).exists():
        print(f"error: {root / MANIFEST} not found - copy the whole release, manifest included (26.4)")
        return 1

    version, entries = read_manifest(root)
    errors, warnings, omitted, matched = [], [], [], 0
    for name, digest in entries.items():
        path = root / name
        if not path.is_file():
            if name.startswith(OPTIONAL) and not complete:
                omitted.append(name)
            else:
                errors.append(f"{name}: missing")
        elif file_hash(path) != digest:
            errors.append(f"{name}: edited - a deviation is an override in the project's CLAUDE.md, not an edit here")
        else:
            matched += 1

    for name in present_files(root):
        if name in entries:
            continue
        if complete:
            errors.append(f"{name}: not in {MANIFEST} - run: python tooling/verify-standard.py --write")
        else:
            warnings.append(f"{name}: not part of the release")

    if complete and version != readme_version(root):
        errors.append(f"{MANIFEST} is for version {version}, README.md says {readme_version(root)}")

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")
    print(f"\nStandard {version}: {matched} files verified, {len(omitted)} optional files not vendored, "
          f"{len(warnings)} added, {len(errors)} errors")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT,
                        help="the copy to check; defaults to the one this script sits in")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="regenerate the manifest (this repository only)")
    mode.add_argument("--complete", action="store_true",
                      help="also fail on an omitted or unlisted file and on a version mismatch (this repository's CI)")
    args = parser.parse_args()

    root = args.root.resolve()
    return write_manifest(root) if args.write else verify(root, args.complete)


if __name__ == "__main__":
    sys.exit(main())
