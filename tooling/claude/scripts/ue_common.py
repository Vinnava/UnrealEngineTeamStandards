"""Shared helpers for the Claude kit's scripts and hooks (27.4). Standard library only.

Finding the project and the engine is the part every script repeats, and the part that differs per
machine: a launcher install, a source build, a Linux install file. One place does it for all of them.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# tooling/claude/scripts/ue_common.py -> the pinned copy of the standard
STANDARDS = Path(__file__).resolve().parents[3]

# Unreal's own log line prefix: [2026.10.12-10.11.12:123][  0]
LOG_PREFIX = re.compile(r"^\[[^\]]*\]\[[^\]]*\]")


def find_project(start: Path | None = None) -> Path | None:
    """The folder holding the .uproject, searching up from start (a file or folder), then the cwd."""
    for origin in (start, Path(os.environ.get("CLAUDE_PROJECT_DIR", "")) if os.environ.get("CLAUDE_PROJECT_DIR") else None,
                   Path.cwd()):
        if origin is None:
            continue
        folder = origin.resolve()
        if folder.is_file():
            folder = folder.parent
        for candidate in (folder, *folder.parents):
            if any(candidate.glob("*.uproject")):
                return candidate
    return None


def uproject_file(project: Path) -> Path:
    return sorted(project.glob("*.uproject"))[0]


def engine_association(project: Path) -> str:
    return json.loads(uproject_file(project).read_text(encoding="utf-8-sig")).get("EngineAssociation", "")


def _launcher_installs() -> dict[str, Path]:
    """AppName -> install folder, from the Epic launcher's own list (Windows)."""
    listing = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "Epic/UnrealEngineLauncher/LauncherInstalled.dat"
    try:
        data = json.loads(listing.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {item.get("AppName", ""): Path(item.get("InstallLocation", "")) for item in data.get("InstallationList", [])}


def _registry_value(hive: str, key: str, name: str | None) -> str | None:
    """A registry value, or None off Windows or when it is absent. name=None reads every value as 'n=v' lines."""
    if sys.platform != "win32":
        return None
    import winreg
    root = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}[hive]
    try:
        with winreg.OpenKey(root, key) as handle:
            if name is not None:
                return str(winreg.QueryValueEx(handle, name)[0])
            values, index = [], 0
            while True:
                try:
                    value_name, value, _ = winreg.EnumValue(handle, index)
                except OSError:
                    break
                values.append(f"{value_name}={value}")
                index += 1
            return "\n".join(values)
    except OSError:
        return None


def resolve_engine(association: str) -> Path | None:
    """The engine root for a .uproject's EngineAssociation - a version such as '5.8', or a source build's GUID.

    Order: the UE_ROOT variable, the launcher's install list (the registry can miss a launcher install),
    the launcher registry key, source builds registered by the editor, then Linux and Mac Install.ini.
    """
    candidates = []
    if os.environ.get("UE_ROOT"):
        candidates.append(Path(os.environ["UE_ROOT"]))
    candidates.append(_launcher_installs().get(f"UE_{association}"))
    installed = _registry_value("HKLM", rf"SOFTWARE\EpicGames\Unreal Engine\{association}", "InstalledDirectory")
    candidates.append(Path(installed) if installed else None)
    builds = _registry_value("HKCU", r"Software\Epic Games\Unreal Engine\Builds", None) or ""
    for line in builds.splitlines():
        name, _, value = line.partition("=")
        if name.strip("{}").lower() == association.strip("{}").lower():
            candidates.append(Path(value))
    for ini in (Path.home() / ".config/Epic/UnrealEngine/Install.ini",
                Path.home() / "Library/Application Support/Epic/UnrealEngine/Install.ini"):
        if ini.is_file():
            for line in ini.read_text(encoding="utf-8", errors="replace").splitlines():
                name, _, value = line.partition("=")
                if name.strip().strip("{}").lower() == association.strip("{}").lower():
                    candidates.append(Path(value.strip()))
    if sys.platform == "win32":
        candidates.append(Path(f"C:/Program Files/Epic Games/UE_{association}"))
    for candidate in candidates:
        if candidate and (candidate / "Engine/Build/Build.version").is_file():
            return candidate
    return None


def engine_version(engine: Path) -> str:
    data = json.loads((engine / "Engine/Build/Build.version").read_text(encoding="utf-8"))
    return f"{data.get('MajorVersion')}.{data.get('MinorVersion')}.{data.get('PatchVersion')}"


def target_name(project: Path, kind: str = "Editor") -> str | None:
    """The project's target of this TargetType, from Source/*.Target.cs - 'ZWSEditor' for Editor."""
    for path in sorted((project / "Source").glob("*.Target.cs")):
        if re.search(rf"TargetType\.{kind}\b", path.read_text(encoding="utf-8", errors="replace")):
            return path.name[: -len(".Target.cs")]
    return None


def host_platform() -> str:
    return {"win32": "Win64", "darwin": "Mac"}.get(sys.platform, "Linux")


def kit_log(project: Path, name: str) -> Path:
    """Where a script keeps the full output it summarised. Saved/ is never committed (14.3)."""
    folder = project / "Saved" / "Claude"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / name


def run_logged(command: list[str], log: Path, cwd: Path) -> tuple[int, list[str], float]:
    """Runs a command, keeps everything it printed in log, and returns the exit code, lines and seconds."""
    started = time.monotonic()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, errors="replace")
    output = (result.stdout or "") + (result.stderr or "")
    log.write_text(output, encoding="utf-8")
    return result.returncode, output.splitlines(), time.monotonic() - started


def strip_log_prefix(line: str) -> str:
    return LOG_PREFIX.sub("", line).strip()


def compact(lines: list[str], limit: int) -> tuple[list[str], int]:
    """De-duplicates lines in first-seen order, counting repeats, and caps the list. Returns (shown, hidden)."""
    counts: dict[str, int] = {}
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    shown = [f"{line}  (x{count})" if count > 1 else line for line, count in counts.items()]
    return shown[:limit], max(0, len(shown) - limit)


def relative_to(path_text: str, project: Path) -> str:
    """A path printed relative to the project when it is inside it, so output stays short."""
    try:
        return Path(path_text).resolve().relative_to(project).as_posix()
    except (ValueError, OSError):
        return path_text.replace("\\", "/")
