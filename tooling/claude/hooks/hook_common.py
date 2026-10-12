"""Shared code for the Claude kit's hooks (27.4). Standard library only.

Every hook is a command hook: it runs outside the model, so it costs no tokens unless it prints a
finding (27.4). Each one reads the event as JSON on stdin and answers in the JSON Claude Code expects.
"""

import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

# tooling/claude/hooks/hook_common.py -> the pinned copy of the standard
STANDARDS = Path(__file__).resolve().parents[3]
SOURCE_SUFFIXES = {".h", ".hpp", ".inl", ".cpp", ".cs"}
STATE_DIR = Path(tempfile.gettempdir()) / "claude-ue-kit"
STATE_MAX_AGE_SECONDS = 7 * 24 * 3600


def read_event() -> dict:
    try:
        return json.load(sys.stdin)
    except ValueError:
        return {}


def emit(payload: dict) -> None:
    print(json.dumps(payload))


def edited_path(event: dict) -> Path | None:
    """The absolute path an Edit, Write or MultiEdit call touches; Claude Code always sends it absolute."""
    path = (event.get("tool_input") or {}).get("file_path")
    return Path(path) if path else None


def project_root(start: Path | None, event: dict) -> Path | None:
    """The folder holding the .uproject, searching up from the edited file, then the session's project."""
    origins = [start, os.environ.get("CLAUDE_PROJECT_DIR"), event.get("cwd")]
    for origin in origins:
        if not origin:
            continue
        folder = Path(origin)
        folder = folder.parent if folder.suffix else folder
        for candidate in (folder, *folder.parents):
            if any(candidate.glob("*.uproject")):
                return candidate
    return None


def load_check_project():
    spec = importlib.util.spec_from_file_location("check_project", STANDARDS / "tooling" / "check-project.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_files(root: Path, files: list[Path]) -> tuple[list[str], list[str]]:
    """check-project's findings for these files only: (errors, warnings)."""
    check_project = load_check_project()
    chosen = check_project.selected_files(root.resolve(), files)
    if not chosen:
        return [], []
    report = check_project.run(root.resolve(), files=chosen)
    return report.errors, report.warnings


def _state_file(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "unknown")
    return STATE_DIR / f"{safe}.json"


def remember_edit(session_id: str, path: Path) -> None:
    """Records a source file this session edited, so the Stop gate can re-check it (27.4)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = _state_file(session_id)
    try:
        edited = set(json.loads(state.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        edited = set()
    edited.add(str(path))
    state.write_text(json.dumps(sorted(edited)), encoding="utf-8")
    _prune_old_state()


def edits_this_session(session_id: str) -> list[Path]:
    try:
        return [Path(p) for p in json.loads(_state_file(session_id).read_text(encoding="utf-8")) if Path(p).is_file()]
    except (OSError, ValueError):
        return []


def _prune_old_state() -> None:
    cutoff = time.time() - STATE_MAX_AGE_SECONDS
    for old in STATE_DIR.glob("*.json"):
        try:
            if old.stat().st_mtime < cutoff:
                old.unlink()
        except OSError:
            pass


def format_findings(findings: list[str], limit: int = 15) -> str:
    shown = findings[:limit]
    more = f"\n... {len(findings) - limit} more" if len(findings) > limit else ""
    return "\n".join(f"- {line}" for line in shown) + more
