#!/usr/bin/env python3
"""Checks a game project against the rules in the team standard that a text scan can decide.

    python check-project.py <project-root> [--warn-only]

check-standard.py checks this repository; this one checks a project. It scans the project's
Source/ and Plugins/*/Source/ trees and reports, per rule:

    error    TAtomic (10.8), LogTemp (6.2), a synchronous load in gameplay code (10.3),
             an emoji or U+FFFD (5.5), THREADING-CANDIDATE markers that disagree with the
             registry in CLAUDE.md (10.10)
    warning  a mutable static (3.7), UE_LOG in a file that also uses UE_LOGFMT (6.5)

Warnings are the checks with known false positives; they print but never fail the build.
--warn-only reports errors as warnings and exits 0 - the retrofit mode 18.4 asks for, so a
backlog can be seen before the gate is switched on.

Code in a prototype module (1.6) is held only to the safety checks: TAtomic and encoding.
"""

import argparse
import re
import sys
from pathlib import Path

SOURCE_SUFFIXES = {".h", ".hpp", ".inl", ".cpp", ".cs"}
SKIPPED_DIRS = {"Intermediate", "Binaries", "Saved", "ThirdParty", "DerivedDataCache", ".git", ".vs"}

# Emoji blocks, plus the variation selector that turns a plain symbol into an emoji
EMOJI_RANGES = ((0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0xFE0F, 0xFE0F))
REPLACEMENT_CHAR = chr(0xFFFD)

TATOMIC = re.compile(r"\bTAtomic\s*<")
LOG_TEMP = re.compile(r"\bLogTemp\b")
SYNC_LOAD = re.compile(r"\b(LoadSynchronous|StaticLoadObject|LoadObject)\s*[<(]")
SYNC_LOAD_OK = "sync-load-ok:"
UE_LOG = re.compile(r"\bUE_LOG\s*\(")
UE_LOGFMT = re.compile(r"\bUE_LOGFMT\s*\(")
STATIC_DECL = re.compile(r"^\s*(?:thread_local\s+)?static\s+(.*)$")
CANDIDATE_MARKER = "THREADING-CANDIDATE"
CLASS_DECL = re.compile(r"^\s*(?:class|struct)\s+(?:[A-Z0-9_]+_API\s+)?([A-Za-z_]\w*)")


class Report:
    def __init__(self, warn_only: bool) -> None:
        self.warn_only = warn_only
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, message: str) -> None:
        (self.warnings if self.warn_only else self.errors).append(f"{where}: {message}")

    def warning(self, where: str, message: str) -> None:
        self.warnings.append(f"{where}: {message}")


def strip_comments_and_strings(text: str) -> str:
    """Blank out comments and string/char literals, keeping line breaks so line numbers survive.

    A rule about code must not fire on a comment that mentions it - "// never use LogTemp" is
    not a use of LogTemp.
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "/" and nxt == "*":
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            i += 2
        elif c in "\"'":
            quote = c
            out.append(" ")
            i += 1
            while i < n and text[i] != quote and text[i] != "\n":
                if text[i] == "\\":
                    i += 1
                i += 1
            i += 1
            out.append(" ")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def is_mutable_static_variable(declaration: str) -> bool:
    """True for 'static int32 counter = 0;', false for a function, a constant or a CVar.

    Heuristic, which is why this check only warns. A parenthesis before any '=' means a function
    declaration - which also, deliberately, lets through the engine's file-scope console variable
    idiom 'static TAutoConsoleVariable<int32> CVarX(TEXT(...), ...);'.
    """
    head = declaration.split("=")[0]
    if set(re.findall(r"[A-Za-z_]\w*", head)) & {"const", "constexpr", "consteval", "constinit"}:
        return False
    return "(" not in head and declaration.rstrip().endswith(";")


def is_prototype(path: Path) -> bool:
    return any("Prototype" in part for part in path.parts)


def is_editor_module(path: Path) -> bool:
    """An editor module may load synchronously (10.3). By convention its folder ends in Editor."""
    return any(part.endswith("Editor") for part in path.parts)


def contains_emoji(line: str) -> bool:
    return any(lo <= ord(c) <= hi for c in line for lo, hi in EMOJI_RANGES)


def source_files(root: Path) -> list[Path]:
    trees = [root / "Source"] + sorted((root / "Plugins").glob("*/Source"))
    found = []
    for tree in trees:
        if not tree.is_dir():
            continue
        for path in tree.rglob("*"):
            if path.suffix in SOURCE_SUFFIXES and not (set(path.parts) & SKIPPED_DIRS) and path.is_file():
                found.append(path)
    return sorted(found)


def check_file(path: Path, root: Path, report: Report) -> list[str]:
    """Runs the per-line checks and returns the classes this file marks as threading candidates."""
    rel = path.relative_to(root).as_posix()
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw_lines = raw.splitlines()
    code_lines = strip_comments_and_strings(raw).splitlines()
    prototype = is_prototype(path.relative_to(root))

    for number, line in enumerate(raw_lines, start=1):
        if REPLACEMENT_CHAR in line:
            report.error(f"{rel}:{number}", "contains U+FFFD, the mark of a mangled encoding (5.5)")
        if contains_emoji(line):
            report.error(f"{rel}:{number}", "contains an emoji (5.5)")

    uses_logfmt = any(UE_LOGFMT.search(line) for line in code_lines)
    for number, code in enumerate(code_lines, start=1):
        where = f"{rel}:{number}"
        if TATOMIC.search(code):
            report.error(where, "TAtomic is deprecated in a comment only, so the compiler never warns - use std::atomic (10.8)")
        if prototype:
            continue
        if LOG_TEMP.search(code):
            report.error(where, "LogTemp in committed code - declare a Log<Project><Domain> category (6.2)")
        if SYNC_LOAD.search(code) and not is_editor_module(path.relative_to(root)):
            here = raw_lines[number - 1] if number - 1 < len(raw_lines) else ""
            above = raw_lines[number - 2] if number >= 2 else ""
            if SYNC_LOAD_OK not in here and SYNC_LOAD_OK not in above:
                report.error(where, f"synchronous load in gameplay code - load asynchronously, or mark an allowed "
                                    f"exception with '// {SYNC_LOAD_OK} <reason>' (10.3)")
        if uses_logfmt and UE_LOG.search(code):
            report.warning(where, "UE_LOG in a file that already uses UE_LOGFMT - new and modified lines use UE_LOGFMT (6.5)")
        match = STATIC_DECL.match(code)
        if match and is_mutable_static_variable(match.group(1)):
            report.warning(where, "mutable static - it survives between PIE sessions and races under threading (3.7)")

    marked = []
    for number, line in enumerate(raw_lines):
        if CANDIDATE_MARKER in line:
            for later in code_lines[number:number + 15]:
                declared = CLASS_DECL.match(later)
                if declared:
                    marked.append(declared.group(1))
                    break
    return marked


def registered_candidates(claude_md: Path) -> list[str] | None:
    """System names from the 'Threading candidates' table in CLAUDE.md; None if the section is absent."""
    if not claude_md.is_file():
        return None
    lines = claude_md.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip().lower() == "## threading candidates")
    except StopIteration:
        return None
    names = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
            continue
        first = line.strip("|").split("|")[0].strip().strip("`")
        if first and first.lower() != "system":
            names.append(first)
    return names


def check_registry(marked: list[str], root: Path, report: Report) -> None:
    registered = registered_candidates(root / "CLAUDE.md")
    if registered is None:
        if marked:
            report.error("CLAUDE.md", f"{len(marked)} class(es) are marked {CANDIDATE_MARKER} but CLAUDE.md has no "
                                      f"'## Threading candidates' table (10.10)")
        return
    for name in sorted(set(marked) - set(registered)):
        report.error("CLAUDE.md", f"{name} is marked {CANDIDATE_MARKER} but is not in the registry (10.10)")
    for name in sorted(set(registered) - set(marked)):
        report.error("CLAUDE.md", f"{name} is in the registry but no class is marked {CANDIDATE_MARKER} (10.10)")


def run(root: Path, warn_only: bool = False) -> Report:
    report = Report(warn_only)
    marked = []
    for path in source_files(root):
        marked += check_file(path, root, report)
    check_registry(marked, root, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a game project against the team standard.")
    parser.add_argument("project", type=Path, help="the project root - the folder holding the .uproject")
    parser.add_argument("--warn-only", action="store_true", help="report errors as warnings and exit 0 (18.4)")
    args = parser.parse_args()

    root = args.project.resolve()
    if not (root / "Source").is_dir():
        print(f"{root} has no Source/ folder - pass the project root.")
        return 2

    report = run(root, args.warn_only)
    for warning in report.warnings:
        print(f"warning: {warning}")
    for error in report.errors:
        print(f"error: {error}")
    print(f"\n{len(source_files(root))} source files, {len(report.errors)} errors, {len(report.warnings)} warnings")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
