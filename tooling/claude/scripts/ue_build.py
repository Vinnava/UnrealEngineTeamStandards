#!/usr/bin/env python3
"""Builds a project target and prints only what needs fixing (27.4).

    python standards/tooling/claude/scripts/ue_build.py [--target ZWSEditor] [--config Development]

A UnrealBuildTool log runs to thousands of lines; this prints the result, every error, and the
warnings in the project's own files, with paths relative to the project. The full log is kept in
Saved/Claude/ue_build.log for when the summary is not enough.

Header, delegate, constructor and new-class changes need an editor-closed build (15, item 1). If
Live Coding is holding the target, this says so instead of burying it in the log.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ue_common  # noqa: E402

# MSVC: path(12): error C2065: ...   clang: path:12:5: error: ...
COMPILER = re.compile(r"^\s*(?P<path>[^\s(][^(]*?)(?:\((?P<line>\d+)(?:,\d+)?\)|:(?P<cline>\d+)(?::\d+)?)\s*:\s*"
                      r"(?:fatal )?(?P<kind>error|warning)\s*(?P<code>[A-Z]+\d+)?\s*:\s*(?P<text>.*)$", re.I)
# Linker, UnrealHeaderTool and UnrealBuildTool lines that carry no source position
TOOL_ERROR = re.compile(r"(error LNK\d+|fatal error LNK\d+|\bLINK : fatal error|: Error: |^ERROR: |^Error: |"
                        r"UnrealHeaderTool failed|error : )")
LIVE_CODING = re.compile(r"Live Coding|live coding is active", re.I)
RESULT = re.compile(r"^\s*Result:\s*(\w+)", re.I)


def summarise(lines: list[str], project: Path) -> tuple[list[str], list[str], str | None, bool]:
    """Splits build output into (errors, project warnings, result word, live-coding blocked)."""
    errors, warnings, result, live_coding = [], [], None, False
    for raw in lines:
        line = raw.rstrip()
        found = RESULT.match(line)
        if found:
            result = found.group(1)
        if LIVE_CODING.search(line) and "unable" in line.lower():
            live_coding = True
        match = COMPILER.match(line)
        if match:
            path = ue_common.relative_to(match.group("path").strip(), project)
            where = f"{path}:{match.group('line') or match.group('cline')}"
            code = f"{match.group('code')}: " if match.group("code") else ""
            entry = f"{where}  {code}{match.group('text').strip()}"
            if match.group("kind").lower() == "error":
                errors.append(entry)
            elif not Path(path).is_absolute() and not path.startswith(".."):
                warnings.append(entry)
            continue
        if TOOL_ERROR.search(line):
            errors.append(ue_common.strip_log_prefix(line))
    return errors, warnings, result, live_coding


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a target and print only what needs fixing.")
    parser.add_argument("--project", type=Path, help="the project folder; found from the cwd if omitted")
    parser.add_argument("--target", help="the target to build; defaults to the project's Editor target")
    parser.add_argument("--platform", default=ue_common.host_platform())
    parser.add_argument("--config", default="Development")
    parser.add_argument("--limit", type=int, default=30, help="most lines of each kind to print")
    args = parser.parse_args()

    project = ue_common.find_project(args.project)
    if not project:
        print("No .uproject found - run from inside the project or pass --project.")
        return 2
    engine = ue_common.resolve_engine(ue_common.engine_association(project))
    if not engine:
        print(f"Engine '{ue_common.engine_association(project)}' not found - set UE_ROOT to the engine folder.")
        return 2
    target = args.target or ue_common.target_name(project)
    if not target:
        print("No Editor target in Source/*.Target.cs - pass --target.")
        return 2

    batch = engine / "Engine/Build/BatchFiles"
    tool = batch / "Build.bat" if sys.platform == "win32" else batch / ("Mac" if sys.platform == "darwin" else "Linux") / "Build.sh"
    command = [str(tool), target, args.platform, args.config, f"-Project={ue_common.uproject_file(project)}", "-WaitMutex"]
    log = ue_common.kit_log(project, "ue_build.log")
    code, lines, seconds = ue_common.run_logged(command, log, project)

    errors, warnings, result, live_coding = summarise(lines, project)
    verdict = "succeeded" if code == 0 else f"FAILED (exit {code})"
    print(f"Build {target} {args.platform} {args.config}: {verdict} in {seconds:.0f}s"
          + (f" - UBT result {result}" if result else ""))
    if live_coding:
        print("Live Coding is holding the target: close the editor for a full build (15, item 1), "
              "or press Ctrl+Alt+F11 for a body-only change.")
    for title, entries in (("error", errors), ("warning", warnings)):
        shown, hidden = ue_common.compact(entries, args.limit)
        for entry in shown:
            print(f"{title}  {entry}")
        if hidden:
            print(f"... {hidden} more {title}s")
    if code != 0 and not errors and not live_coding:
        print("No error lines recognised - read the end of the full log.")
    print(f"Full log: {ue_common.relative_to(str(log), project)}")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
