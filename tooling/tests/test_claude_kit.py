"""Tests for the Claude kit in tooling/claude/ (27). Run from the repository root:

    python -m unittest discover -s tooling/tests -v

The kit is vendored into a scratch project exactly as a project pins the standard (26.4), then the
installer, the hooks and the scripts are run the way Claude Code and a person run them - hooks as
subprocesses fed the event JSON on stdin. What Claude Code itself does with their output is proven
in a real session, not here (27.7).
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from release_copy import copy_release

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "tooling" / "claude"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


class KitProject:
    """A scratch Unreal project with the standard vendored at standards/."""

    def __init__(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name) / "Game"
        (self.root / "Source" / "Game").mkdir(parents=True)
        (self.root / "Game.uproject").write_text('{"FileVersion": 3, "EngineAssociation": "5.8"}', encoding="utf-8")
        copy_release(self.root / "standards")
        self.temp = Path(self._dir.name) / "tmp"
        self.temp.mkdir()

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def env(self) -> dict:
        return {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root), "TEMP": str(self.temp), "TMP": str(self.temp),
                "TMPDIR": str(self.temp)}

    def install(self, *args: str) -> tuple[int, str]:
        result = subprocess.run([sys.executable, str(self.root / "standards/tooling/claude/install.py"), *args],
                                capture_output=True, text=True, cwd=self.root, env=self.env())
        return result.returncode, result.stdout

    def hook(self, name: str, event: dict) -> dict | None:
        result = subprocess.run([sys.executable, str(self.root / "standards/tooling/claude/hooks" / name)],
                                input=json.dumps(event), capture_output=True, text=True, cwd=self.root, env=self.env())
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout) if result.stdout.strip() else None

    def close(self) -> None:
        self._dir.cleanup()


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = KitProject()
        self.claude = self.project.root / ".claude"

    def tearDown(self) -> None:
        self.project.close()

    def test_install_then_check_passes(self):
        code, out = self.project.install()
        self.assertEqual(code, 0, out)
        code, out = self.project.install("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("0 problems", out)

    def test_install_warns_until_the_project_has_a_clangd_file(self):
        _, out = self.project.install()
        self.assertIn("warning: no .clangd at the project root", out)
        shutil.copy(REPO / "tooling/.clangd", self.project.root / ".clangd")
        _, out = self.project.install()
        self.assertNotIn(".clangd", out)

    def test_rules_are_path_scoped_copies_of_the_standard(self):
        self.project.install()
        rule = (self.claude / "rules/standard/03-cpp.md").read_text(encoding="utf-8")
        self.assertTrue(rule.startswith("---\npaths:\n"))
        self.assertIn('"Source/**/*.{h,hpp,inl,cpp}"', rule)
        self.assertIn((REPO / "rules/03-cpp.md").read_text(encoding="utf-8").strip(), rule)
        self.assertFalse((self.claude / "rules/standard/00-core.md").exists(), "always-loaded rules come from CLAUDE.md")

    def test_skills_embed_their_rule_and_paths_are_filled(self):
        self.project.install()
        skill = (self.claude / "skills/ue-async/SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: ue-async\n"), "frontmatter must stay on the first line")
        self.assertIn("### 10.1 The rule that has no exceptions", skill)
        agent = (self.claude / "agents/ue-engine-source.md").read_text(encoding="utf-8")
        self.assertNotIn("{{", agent)
        self.assertIn("standards/tooling/claude/scripts/ue_engine.py", agent)

    def test_networking_only_when_the_project_replicates_and_the_choice_sticks(self):
        self.project.install()
        self.assertFalse((self.claude / "rules/standard/11-networking.md").exists())
        self.project.install("--replicates")
        self.assertTrue((self.claude / "rules/standard/11-networking.md").exists())
        self.project.install()
        self.assertTrue((self.claude / "rules/standard/11-networking.md").exists(), "a refresh keeps --replicates")
        self.project.install("--no-replicates")
        self.assertFalse((self.claude / "rules/standard/11-networking.md").exists(), "--no-replicates removes it")

    def test_clangd_is_enabled_and_the_editor_connection_is_opt_in(self):
        mcp = "unreal-engine-skills-for-claude-code@claude-plugins-official"
        self.project.install()
        plugins = json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))["enabledPlugins"]
        self.assertEqual(plugins, {"clangd-lsp@claude-plugins-official": True})
        self.project.install("--editor-mcp")
        self.project.install()
        plugins = json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))["enabledPlugins"]
        self.assertTrue(plugins[mcp], "a refresh keeps --editor-mcp")
        self.project.install("--no-editor-mcp")
        plugins = json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))["enabledPlugins"]
        self.assertNotIn(mcp, plugins)
        code, out = self.project.install("--check")
        self.assertEqual(code, 0, out)

    def test_a_hand_edit_fails_the_check(self):
        self.project.install()
        path = self.claude / "skills/ue-gate/SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nlocal tweak\n", encoding="utf-8")
        code, out = self.project.install("--check")
        self.assertEqual(code, 1)
        self.assertIn("skills/ue-gate/SKILL.md: differs from the kit", out)

    def test_settings_merge_keeps_what_the_kit_does_not_own(self):
        self.claude.mkdir()
        (self.claude / "settings.json").write_text(json.dumps({
            "env": {"FOO": "1"},
            "permissions": {"allow": ["Bash(git status)"]},
            "hooks": {"PostToolUse": [{"matcher": "Write", "hooks": [{"type": "command", "command": "mine.sh"}]}]},
            "modelSettings": {"claude-opus-5-5": {"maxEffortLevel": "xhigh"}},
        }), encoding="utf-8")
        self.project.install()
        settings = json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["env"], {"FOO": "1"})
        self.assertEqual(settings["model"], "opusplan")
        self.assertIn("Bash(git status)", settings["permissions"]["allow"])
        self.assertEqual(settings["modelSettings"]["claude-opus-5-5"], {"maxEffortLevel": "xhigh", "effortLevel": "high"})
        commands = [hook.get("command") for group in settings["hooks"]["PostToolUse"] for hook in group["hooks"]]
        self.assertIn("mine.sh", commands)
        self.project.install()
        again = json.loads((self.claude / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(again, settings, "re-installing changes nothing")

    def test_files_from_an_older_kit_are_removed_unless_edited(self):
        self.project.install()
        marker = json.loads((self.claude / "ue-kit.json").read_text(encoding="utf-8"))
        old = self.claude / "skills/ue-retired/SKILL.md"
        old.parent.mkdir(parents=True)
        old.write_text("old\n", encoding="utf-8")
        edited = self.claude / "skills/ue-edited/SKILL.md"
        edited.parent.mkdir(parents=True)
        edited.write_text("changed since\n", encoding="utf-8")
        import hashlib
        marker["files"]["skills/ue-retired/SKILL.md"] = hashlib.sha256(b"old\n").hexdigest()
        marker["files"]["skills/ue-edited/SKILL.md"] = hashlib.sha256(b"original\n").hexdigest()
        (self.claude / "ue-kit.json").write_text(json.dumps(marker), encoding="utf-8")
        code, out = self.project.install()
        self.assertFalse(old.exists())
        self.assertTrue(edited.exists())
        self.assertIn("kept skills/ue-edited/SKILL.md", out)

    def test_no_uproject_refuses(self):
        (self.project.root / "Game.uproject").unlink()
        code, out = self.project.install("--project", str(self.project.root))
        self.assertEqual(code, 2)


class HookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = KitProject()

    def tearDown(self) -> None:
        self.project.close()

    def edit_event(self, path: Path, session: str = "s1") -> dict:
        return {"session_id": session, "hook_event_name": "PostToolUse", "tool_name": "Write",
                "cwd": str(self.project.root), "tool_input": {"file_path": str(path)}}

    def test_post_edit_blocks_on_an_error(self):
        path = self.project.write("Source/Game/Bad.cpp", 'UE_LOGFMT(LogTemp, Log, "x");\n')
        out = self.project.hook("post_edit.py", self.edit_event(path))
        self.assertEqual(out["decision"], "block")
        self.assertIn("LogTemp", out["reason"])

    def test_post_edit_is_silent_on_a_clean_file(self):
        path = self.project.write("Source/Game/Good.cpp", 'UE_LOGFMT(LogGameThing, Log, "[{Obj}] ok", GetNameSafe(this));\n')
        self.assertIsNone(self.project.hook("post_edit.py", self.edit_event(path)))

    def test_post_edit_passes_warnings_as_context(self):
        path = self.project.write("Source/Game/Counter.cpp", "static int32 hits = 0;\n")
        out = self.project.hook("post_edit.py", self.edit_event(path))
        self.assertIn("mutable static", out["hookSpecificOutput"]["additionalContext"])

    def test_post_edit_ignores_files_that_are_not_source(self):
        path = self.project.write("Docs/notes.md", "LogTemp\n")
        self.assertIsNone(self.project.hook("post_edit.py", self.edit_event(path)))

    def test_guard_denies_an_edit_to_the_pinned_standard(self):
        event = self.edit_event(self.project.root / "standards/rules/03-cpp.md")
        event["hook_event_name"] = "PreToolUse"
        out = self.project.hook("guard_standards.py", event)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_guard_allows_an_edit_to_project_code(self):
        event = self.edit_event(self.project.root / "Source/Game/Thing.cpp")
        event["hook_event_name"] = "PreToolUse"
        self.assertIsNone(self.project.hook("guard_standards.py", event))

    def test_stop_gate_blocks_once_then_lets_the_turn_end(self):
        path = self.project.write("Source/Game/Bad.cpp", "TAtomic<int32> hits;\n")
        self.project.hook("post_edit.py", self.edit_event(path, "s2"))
        stop = {"session_id": "s2", "hook_event_name": "Stop", "cwd": str(self.project.root), "stop_hook_active": False}
        self.assertEqual(self.project.hook("stop_gate.py", stop)["decision"], "block")
        stop["stop_hook_active"] = True
        out = self.project.hook("stop_gate.py", stop)
        self.assertNotIn("decision", out)
        self.assertIn("still reports", out["systemMessage"])

    def test_stop_gate_is_silent_when_the_session_edited_nothing_wrong(self):
        path = self.project.write("Source/Game/Good.cpp", "int32 Add(int32 a, int32 b);\n")
        self.project.hook("post_edit.py", self.edit_event(path, "s3"))
        stop = {"session_id": "s3", "hook_event_name": "Stop", "cwd": str(self.project.root), "stop_hook_active": False}
        self.assertIsNone(self.project.hook("stop_gate.py", stop))
        self.assertIsNone(self.project.hook("stop_gate.py", {**stop, "session_id": "never-edited"}))


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.common = load("ue_common", KIT / "scripts/ue_common.py")
        cls.build = load("ue_build", KIT / "scripts/ue_build.py")
        cls.log = load("ue_log", KIT / "scripts/ue_log.py")
        cls.validate = load("ue_validate", KIT / "scripts/ue_validate.py")
        cls.engine = load("ue_engine", KIT / "scripts/ue_engine.py")
        cls.status = load("statusline", KIT / "statusline.py")

    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.project = Path(self._dir.name).resolve()

    def tearDown(self) -> None:
        self._dir.cleanup()

    def test_build_summary_keeps_errors_and_project_warnings_only(self):
        own = str(self.project / "Source/Game/Thing.cpp")
        lines = [
            f"{own}(12): error C2065: 'hits': undeclared identifier",
            f"{self.project}/Source/Game/Other.cpp:7:3: error: no member named 'Foo'",
            f"{own}(30): warning C4996: 'Old' was declared deprecated",
            "C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/X.h(5): warning C4100: unreferenced",
            "Module.Game.cpp.obj : error LNK2019: unresolved external symbol",
            "Unable to build while Live Coding is active. Exit the editor and game, or press Ctrl+Alt+F11",
            "Result: Failed (OtherCompilationError)",
        ]
        errors, warnings, result, live = self.build.summarise(lines, self.project)
        self.assertEqual(result, "Failed")
        self.assertTrue(live)
        self.assertIn("Source/Game/Thing.cpp:12  C2065: 'hits': undeclared identifier", errors)
        self.assertIn("Source/Game/Other.cpp:7  no member named 'Foo'", errors)
        self.assertTrue(any("LNK2019" in e for e in errors))
        self.assertEqual(warnings, ["Source/Game/Thing.cpp:30  C4996: 'Old' was declared deprecated"])

    def test_an_engine_path_is_never_a_project_file_from_inside_the_project(self):
        # On Linux or macOS a drive-letter path is relative, so resolving it from the project root
        # used to graft it onto the project and report the engine's warning as the project's own
        engine = "C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/X.h(5): warning C4100: unreferenced"
        previous = os.getcwd()
        os.chdir(self.project)
        try:
            _, warnings, _, _ = self.build.summarise([engine], self.project)
        finally:
            os.chdir(previous)
        self.assertEqual(warnings, [])

    def test_log_filter_by_level_and_category_and_crash_block(self):
        lines = [
            "[2026.10.12-10.00.00:000][  0]LogGameQuest: Warning: step missing",
            "[2026.10.12-10.00.00:001][  0]LogGameQuest: Warning: step missing",
            "[2026.10.12-10.00.00:002][  0]LogGameQuest: started",
            "[2026.10.12-10.00.00:003][  0]LogOther: Error: broken",
            "[2026.10.12-10.00.00:004][  0]LogWindows: Error: === Critical error: ===",
            "[2026.10.12-10.00.00:005][  0]LogWindows: Error: Assertion failed: IsValid(x)",
        ]
        quest = self.log.filter_lines(lines, "warning", "LogGameQuest", None)
        self.assertEqual(self.common.compact(quest, 10)[0], ["LogGameQuest: Warning: step missing  (x2)"])
        self.assertEqual(len(self.log.filter_lines(lines, "error", None, None)), 3)
        self.assertIn("Assertion failed", " ".join(self.log.crash_block(lines)))

    def test_validation_findings_drop_the_summary_prefix(self):
        lines = ["[2026.10.12-10.00.00:000][  0]LogContentValidation: Error: 'BP_Main' must start with 'BP_GM_' (standard 7.2).",
                 "LogInit: Display: LogContentValidation: Error: 'BP_Main' must start with 'BP_GM_' (standard 7.2).",
                 "LogContentValidation: Warning: 'M_Old' is a redirector left by a rename (standard 14.3)."]
        errors, warnings = self.validate.findings(lines)
        self.assertEqual(len(set(errors)), 1)
        self.assertEqual(len(warnings), 1)

    def test_engine_hit_is_shortened_relative_to_the_engine(self):
        engine = self.project / "UE_5.8"
        hit = f"{engine}/Engine/Source/X.cpp:125:    bool Foo();"
        self.assertEqual(self.engine.shorten(hit, engine), "Engine/Source/X.cpp:125: bool Foo();")

    def test_engine_resolves_from_ue_root_and_target_from_target_files(self):
        engine = self.project / "MyEngine"
        (engine / "Engine/Build").mkdir(parents=True)
        (engine / "Engine/Build/Build.version").write_text('{"MajorVersion": 5, "MinorVersion": 8, "PatchVersion": 3}')
        os.environ["UE_ROOT"] = str(engine)
        try:
            self.assertEqual(self.common.resolve_engine("5.8"), engine)
            self.assertEqual(self.common.engine_version(engine), "5.8.3")
        finally:
            del os.environ["UE_ROOT"]
        (self.project / "Source").mkdir()
        (self.project / "Source/Game.Target.cs").write_text("Type = TargetType.Game;")
        (self.project / "Source/GameEditor.Target.cs").write_text("Type = TargetType.Editor;")
        self.assertEqual(self.common.target_name(self.project), "GameEditor")

    def test_statusline_never_fails(self):
        line = self.status.render({"model": {"display_name": "Opus"}, "context_window": {"used_percentage": 23.4},
                                   "prompt_cache": {"hit_ratio": 0.91, "warm": True}})
        self.assertTrue(line.startswith("Opus | ctx 23% | cache 91% warm | std "))
        self.assertTrue(self.status.render({}).startswith("Claude | std "))


if __name__ == "__main__":
    unittest.main()
