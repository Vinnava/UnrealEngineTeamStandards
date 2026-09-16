#!/usr/bin/env python3
"""Consistency checks for the team standard itself. Run from the repository root:

    python tooling/check-standard.py

Exits non-zero on any error, so it can gate CI (14.5). Checks that section references resolve,
that links are not broken, that checklist items cite the rule they came from, and that the
version and file index agree with reality - the drift a standard accumulates when one rule is
stated in five places.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Engine versions and decimal literals that look like section numbers but are not.
NOT_SECTIONS = {"5.0", "5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8", "5.9"}

# Built from its code point so this file stays ASCII and does not trip its own check.
REPLACEMENT_CHAR = chr(0xFFFD)

errors: list[str] = []
warnings: list[str] = []


def markdown_files() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)


def strip_code(text: str) -> str:
    """Blank out fenced blocks and inline spans so their contents are never parsed as prose."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def known_sections() -> set[str]:
    found = set()
    for path in (ROOT / "rules").glob("*.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^#{2,4}\s+(\d{1,2}\.\d{1,2})\b", line)
            if match:
                found.add(match.group(1))
    return found


def check_section_refs(sections: set[str]) -> None:
    """Every N.M cited in a reference context must be a real heading."""
    for path in markdown_files():
        prose = strip_code(path.read_text(encoding="utf-8"))
        for number, line_no in cited_numbers(prose):
            if number in NOT_SECTIONS or number in sections:
                continue
            errors.append(f"{rel(path)}:{line_no}: reference to section {number}, which does not exist")


def cited_numbers(prose: str):
    """Yield (number, line) for every N.M in a citation context - in parentheses, or after 'section'."""
    for line_no, line in enumerate(prose.splitlines(), start=1):
        if "UE " in line or "Unreal Engine 5" in line:
            continue
        candidates = []
        for group in re.findall(r"\(([^()]*)\)", line):
            # Not a citation: a measurement such as "0.5 ms is typical", or anything starting at 0
            candidates += re.findall(r"\b([1-9]\d?\.\d{1,2})\b(?!\s*(?:ms|s\b|Hz|per))", group)
        for match in re.finditer(r"\b(?:sections?|standard)\s+(\d{1,2}\.\d{1,2})\b", line, re.I):
            candidates.append(match.group(1))
        # Trailing citation form used by the checklists: "- 1.1" at end of a line
        trailing = re.search(r"-\s(\d{1,2}\.\d{1,2})(?:,\s*(\d{1,2}\.\d{1,2}))*\s*$", line)
        if trailing:
            candidates += [g for g in trailing.groups() if g]
        for number in candidates:
            yield number, line_no


def check_links() -> None:
    for path in markdown_files():
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for target in re.findall(r"\]\(([^)]+)\)", line):
                if target.startswith(("http://", "https://", "#")):
                    continue
                resolved = (path.parent / target.split("#")[0]).resolve()
                if not resolved.exists():
                    errors.append(f"{rel(path)}:{line_no}: link to {target}, which does not exist")


def check_encoding() -> None:
    """5.5 - no emojis, no U+FFFD, and nothing non-ASCII that a tool will mangle."""
    for path in sorted(ROOT.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.suffix not in {".md", ".h", ".cpp", ".cs", ".py", ".ini", ".yml", ".clang-tidy", ""}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if REPLACEMENT_CHAR in line:
                errors.append(f"{rel(path)}:{line_no}: contains U+FFFD (5.5)")
            non_ascii = [c for c in line if ord(c) > 127]
            if non_ascii:
                shown = " ".join(f"U+{ord(c):04X}" for c in dict.fromkeys(non_ascii))
                errors.append(f"{rel(path)}:{line_no}: non-ASCII character(s) {shown} (5.5)")


def check_checklist_citations() -> None:
    """Every review-list item names the rule it came from, so a rule change is greppable (17.2)."""
    path = ROOT / "rules" / "13-checklists.md"
    inside = False
    item, item_line = "", 0

    def flush() -> None:
        if item and not re.search(r"\d{1,2}\.\d{1,2}", item):
            warnings.append(f"{rel(path)}:{item_line}: checklist item cites no section")

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith("### 17.2"):
            inside = True
            continue
        if not inside:
            continue
        if line.startswith("### "):
            flush()
            break
        if line.lstrip().startswith("- [ ]"):
            flush()
            item, item_line = line, line_no
        elif item and line.startswith("      "):
            # A wrapped continuation of the item above; its citation often lands here
            item += " " + line.strip()
        elif not line.strip():
            flush()
            item, item_line = "", 0


def check_index() -> None:
    """Every rule file is listed in the README table, and the version matches the changelog."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for path in sorted((ROOT / "rules").glob("*.md")):
        if f"rules/{path.name}" not in readme:
            errors.append(f"README.md: rule file {path.name} is not listed in the index table")

    version = re.search(r"\*\*Version (\d+\.\d+)\*\*", readme)
    changelog = re.search(r"^\*\*(\d+\.\d+)\b", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
    if not version or not changelog:
        errors.append("Could not read the version from README.md or CHANGELOG.md")
    elif version.group(1) != changelog.group(1):
        errors.append(f"README says version {version.group(1)}, changelog's newest entry is {changelog.group(1)}")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    sections = known_sections()
    if not sections:
        print("No sections found - run this from the repository root.")
        return 2

    check_section_refs(sections)
    check_links()
    check_encoding()
    check_checklist_citations()
    check_index()

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")

    print(f"\n{len(sections)} sections, {len(markdown_files())} markdown files, "
          f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
