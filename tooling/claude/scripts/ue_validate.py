#!/usr/bin/env python3
"""Runs the DataValidation commandlet and prints only the findings (27.4).

    python standards/tooling/claude/scripts/ue_validate.py

The same command CI runs (18.2), headless. The commandlet prints every finding twice - once as it
happens and once in its closing summary - so findings are de-duplicated. The full log is kept in
Saved/Claude/ue_validate.log.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ue_common  # noqa: E402

# The standard's validators cite a section; the engine's own validators log under these categories
FINDING = re.compile(r"\(standard \d|no prefix rule|LogContentValidation: (Error|Warning)|"
                     r"LogDataValidation: (Error|Warning)|AssetCheck: (Error|Warning)")
ENSURE = re.compile(r"Ensure condition failed|did not return a validation result")


def findings(lines: list[str]) -> tuple[list[str], list[str]]:
    """(errors, warnings) from commandlet output, prefixes stripped."""
    errors, warnings = [], []
    for raw in lines:
        line = ue_common.strip_log_prefix(raw).replace("LogInit: Display: ", "")
        if ENSURE.search(line):
            errors.append(line)
        elif FINDING.search(line):
            (errors if "Error" in line else warnings).append(line)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run DataValidation and print only the findings.")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--limit", type=int, default=40)
    args = parser.parse_args()

    project = ue_common.find_project(args.project)
    if not project:
        print("No .uproject found - run from inside the project or pass --project.")
        return 2
    engine = ue_common.resolve_engine(ue_common.engine_association(project))
    if not engine:
        print("Engine not found - set UE_ROOT to the engine folder.")
        return 2

    suffix = ".exe" if sys.platform == "win32" else ""
    editor = engine / "Engine/Binaries" / ue_common.host_platform() / f"UnrealEditor-Cmd{suffix}"
    command = [str(editor), str(ue_common.uproject_file(project)), "-run=DataValidation",
               "-unattended", "-nopause", "-nosplash", "-nullrhi", "-stdout"]
    log = ue_common.kit_log(project, "ue_validate.log")
    code, lines, seconds = ue_common.run_logged(command, log, project)

    errors, warnings = findings(lines)
    print(f"DataValidation: {'passed' if code == 0 else f'FAILED (exit {code})'} in {seconds:.0f}s")
    for title, entries in (("error", errors), ("warning", warnings)):
        shown, hidden = ue_common.compact(entries, args.limit)
        for entry in shown:
            print(f"{title}  {entry}")
        if hidden:
            print(f"... {hidden} more {title}s")
    print(f"Full log: {ue_common.relative_to(str(log), project)}")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
