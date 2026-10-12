#!/usr/bin/env python3
"""Finds the project's engine and searches its source (27.4, precedence rule 1).

    python standards/tooling/claude/scripts/ue_engine.py root
    python standards/tooling/claude/scripts/ue_engine.py grep "DeriveGameplayCueTagFromAssetName" --in Engine/Plugins/Runtime/GameplayAbilities

Every engine claim in the standard is checked against engine source, and so is any claim made while
working. This prints the engine root and exact version - the version a verified claim is recorded
against - and greps the source with file:line results. It uses ripgrep when installed; otherwise it
walks the folder given by --in, which should be narrow, because the full engine tree is very large.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ue_common  # noqa: E402

SOURCE_SUFFIXES = {".h", ".hpp", ".inl", ".cpp", ".cs", ".ini", ".py", ".usf", ".ush"}


def grep(engine: Path, pattern: str, within: str, suffixes: set[str], limit: int) -> list[str]:
    root = engine / within
    if shutil.which("rg"):
        globs = [arg for suffix in sorted(suffixes) for arg in ("-g", f"*{suffix}")]
        result = subprocess.run(["rg", "-n", "--no-heading", "-S", *globs, "-e", pattern, str(root)],
                                capture_output=True, text=True, errors="replace")
        hits = result.stdout.splitlines()
    else:
        regex = re.compile(pattern)
        hits = []
        for path in root.rglob("*"):
            if path.suffix not in suffixes or not path.is_file():
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                if regex.search(line):
                    hits.append(f"{path}:{number}:{line}")
                    if len(hits) >= limit * 4:
                        break
    return [shorten(hit, engine) for hit in hits[:limit]]


# path:line:text - the path is matched lazily up to the first ':<digits>:', so a drive letter survives
HIT = re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?P<text>.*)$")


def shorten(hit: str, engine: Path) -> str:
    """'C:/.../Engine/Source/X.cpp:12:  code' -> 'Engine/Source/X.cpp:12: code'."""
    match = HIT.match(hit)
    if not match:
        return hit
    try:
        path = Path(match.group("path")).resolve().relative_to(engine.resolve()).as_posix()
    except ValueError:
        path = match.group("path").replace("\\", "/")
    return f"{path}:{match.group('line')}: {match.group('text').strip()}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Find the engine and search its source.")
    parser.add_argument("command", choices=["root", "grep"])
    parser.add_argument("pattern", nargs="?")
    parser.add_argument("--in", dest="within", default="Engine", help="folder under the engine root to search")
    parser.add_argument("--ext", nargs="+", help="file extensions to search, such as .h .cpp")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    project = ue_common.find_project(args.project)
    if not project:
        print("No .uproject found - run from inside the project or pass --project.")
        return 2
    association = ue_common.engine_association(project)
    engine = ue_common.resolve_engine(association)
    if not engine:
        print(f"Engine '{association}' not found - set UE_ROOT to the engine folder.")
        return 2

    print(f"Engine {ue_common.engine_version(engine)} at {engine.as_posix()}")
    if args.command == "root":
        return 0
    if not args.pattern:
        print("grep needs a pattern.")
        return 2
    suffixes = {ext if ext.startswith(".") else f".{ext}" for ext in args.ext} if args.ext else SOURCE_SUFFIXES
    hits = grep(engine, args.pattern, args.within, suffixes, args.limit)
    for hit in hits:
        print(hit)
    print(f"{len(hits)} hit(s) shown (limit {args.limit})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
