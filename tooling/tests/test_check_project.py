"""Tests for tooling/check-project.py. Run from the repository root:

    python -m unittest discover -s tooling/tests -v

Every check has a case that must fire and a case that must not. The second kind matters as much as
the first: a check that fires on a comment, a constant or the engine's own idioms gets disabled.
Emoji and U+FFFD are built with chr() so this file stays ASCII (5.5).
"""

import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path

TOOLING = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_project", TOOLING / "check-project.py")
check_project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_project)


class ProjectFixture:
    """A throwaway project tree; each test writes only the files it needs."""

    def __init__(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        (self.root / "Source").mkdir()

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")

    def run(self, warn_only: bool = False):
        return check_project.run(self.root, warn_only)

    def close(self) -> None:
        self._dir.cleanup()


class CheckProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = ProjectFixture()

    def tearDown(self) -> None:
        self.project.close()

    def assertFinding(self, findings, *fragments):
        matches = [f for f in findings if all(fragment in f for fragment in fragments)]
        self.assertTrue(matches, f"no finding containing {fragments} in {findings}")

    def assertNoFinding(self, findings, fragment):
        self.assertFalse([f for f in findings if fragment in f], f"unexpected '{fragment}' in {findings}")

    # --- a clean file produces nothing, including the idioms that look like violations ---

    def test_clean_file_has_no_findings(self):
        self.project.write("Source/Game/Clean.cpp", """
            // Never use LogTemp or TAtomic<int32> here - a comment is not a use
            static constexpr int32 MaxSlots = 4;
            static const FName DefaultTag = TEXT("Default");
            static void RegisterCommands();
            static TAutoConsoleVariable<int32> CVarDebug(TEXT("game.debug"), 0, TEXT("LogTemp in a string"));
            void UThing::Run()
            {
                UE_LOGFMT(LogGameThing, Log, "[{Obj}] [Run] started", GetNameSafe(this));
            }
            """)
        report = self.project.run()
        self.assertEqual(report.errors, [])
        self.assertEqual(report.warnings, [])

    # --- errors ---

    def test_tatomic_is_an_error(self):
        self.project.write("Source/Game/Counter.h", "TAtomic<int32> hits;\n")
        self.assertFinding(self.project.run().errors, "Counter.h:1", "(10.8)")

    def test_log_temp_is_an_error(self):
        self.project.write("Source/Game/Thing.cpp", 'UE_LOGFMT(LogTemp, Log, "x");\n')
        self.assertFinding(self.project.run().errors, "Thing.cpp:1", "(6.2)")

    def test_sync_load_in_gameplay_is_an_error(self):
        self.project.write("Source/Game/Loader.cpp", "UTexture2D* icon = iconAsset.LoadSynchronous();\n")
        self.assertFinding(self.project.run().errors, "Loader.cpp:1", "(10.3)")

    def test_every_sync_load_spelling_is_caught(self):
        self.project.write("Source/Game/Loader.cpp", """
            a = LoadObject<UTexture2D>(nullptr, path);
            b = StaticLoadObject(UTexture2D::StaticClass(), nullptr, path);
            """)
        errors = self.project.run().errors
        self.assertFinding(errors, "Loader.cpp:1", "(10.3)")
        self.assertFinding(errors, "Loader.cpp:2", "(10.3)")

    def test_sync_load_marked_ok_is_allowed_on_the_line_or_above(self):
        self.project.write("Source/Game/Loading.cpp", """
            // sync-load-ok: runs behind the loading screen
            a = splash.LoadSynchronous();
            b = logo.LoadSynchronous(); // sync-load-ok: loading screen
            """)
        self.assertNoFinding(self.project.run().errors, "(10.3)")

    def test_sync_load_in_an_editor_module_is_allowed(self):
        self.project.write("Source/GameEditor/Tool.cpp", "a = LoadObject<UDataTable>(nullptr, path);\n")
        self.assertNoFinding(self.project.run().errors, "(10.3)")

    def test_emoji_and_replacement_char_are_errors(self):
        self.project.write("Source/Game/Notes.cpp", f"// done {chr(0x2705)}\n// broken {chr(0xFFFD)}\n")
        errors = self.project.run().errors
        self.assertFinding(errors, "Notes.cpp:1", "emoji", "(5.5)")
        self.assertFinding(errors, "Notes.cpp:2", "U+FFFD", "(5.5)")

    # --- warnings ---

    def test_mutable_static_is_a_warning_not_an_error(self):
        self.project.write("Source/Game/Cache.cpp", "static int32 callCount = 0;\nstatic TMap<FName, int32> cache;\n")
        report = self.project.run()
        self.assertFinding(report.warnings, "Cache.cpp:1", "(3.7)")
        self.assertFinding(report.warnings, "Cache.cpp:2", "(3.7)")
        self.assertNoFinding(report.errors, "(3.7)")

    def test_ue_log_beside_ue_logfmt_is_a_warning(self):
        self.project.write("Source/Game/Mixed.cpp", """
            UE_LOGFMT(LogGameThing, Log, "new");
            UE_LOG(LogGameThing, Log, TEXT("old"));
            """)
        self.assertFinding(self.project.run().warnings, "Mixed.cpp:2", "(6.5)")

    def test_ue_log_alone_is_not_flagged(self):
        self.project.write("Source/Game/Old.cpp", 'UE_LOG(LogGameThing, Log, TEXT("old"));\n')
        self.assertNoFinding(self.project.run().warnings, "(6.5)")

    # --- prototype module: safety checks only (1.6) ---

    def test_prototype_module_skips_everything_but_safety(self):
        self.project.write("Source/GamePrototype/Proto.cpp", """
            static int32 hits = 0;
            a = thing.LoadSynchronous();
            UE_LOGFMT(LogTemp, Log, "quick");
            TAtomic<int32> stillWrong;
            """)
        report = self.project.run()
        for rule in ("(6.2)", "(10.3)", "(3.7)"):
            self.assertNoFinding(report.errors + report.warnings, rule)
        self.assertFinding(report.errors, "Proto.cpp:4", "(10.8)")

    # --- threading candidate registry (10.10) ---

    def _candidate(self, relative: str, name: str) -> None:
        self.project.write(relative, f"""
            /** Recalculates affinity in bulk. THREADING-CANDIDATE */
            UCLASS()
            class GAME_API {name} : public UGameInstanceSubsystem
            {{
            }};
            """)

    def _registry(self, *names: str) -> None:
        rows = "\n".join(f"| {name} | Ana | 1, 3 | 2026-09-01 | 2026-09-20 |" for name in names)
        self.project.write("CLAUDE.md", f"""
            # Game

            ## Threading candidates

            | System | Owner | Criteria met (10.10) | Registered | Last reviewed |
            |---|---|---|---|---|
            {rows}

            ## How to work here
            """)

    def test_registry_matching_the_markers_passes(self):
        self._candidate("Source/Game/Affinity.h", "UAffinitySubsystem")
        self._registry("UAffinitySubsystem")
        self.assertNoFinding(self.project.run().errors, "(10.10)")

    def test_marked_but_not_registered_is_an_error(self):
        self._candidate("Source/Game/Affinity.h", "UAffinitySubsystem")
        self._registry()
        self.assertFinding(self.project.run().errors, "UAffinitySubsystem is marked", "(10.10)")

    def test_registered_but_not_marked_is_an_error(self):
        self._candidate("Source/Game/Affinity.h", "UAffinitySubsystem")
        self._registry("UAffinitySubsystem", "ULookupSubsystem")
        self.assertFinding(self.project.run().errors, "ULookupSubsystem is in the registry", "(10.10)")

    def test_marker_without_a_registry_section_is_an_error(self):
        self._candidate("Source/Game/Affinity.h", "UAffinitySubsystem")
        self.assertFinding(self.project.run().errors, "no '## Threading candidates' table", "(10.10)")

    # --- retrofit mode (18.4) ---

    def test_warn_only_turns_errors_into_warnings(self):
        self.project.write("Source/Game/Counter.h", "TAtomic<int32> hits;\n")
        report = self.project.run(warn_only=True)
        self.assertEqual(report.errors, [])
        self.assertFinding(report.warnings, "(10.8)")

    # --- scope ---

    def test_intermediate_and_third_party_are_not_scanned(self):
        self.project.write("Source/Game/Intermediate/Gen.cpp", "TAtomic<int32> generated;\n")
        self.project.write("Source/ThirdParty/Lib/lib.h", "TAtomic<int32> vendored;\n")
        self.assertEqual(self.project.run().errors, [])

    def test_project_plugins_are_scanned(self):
        self.project.write("Plugins/GameTools/Source/GameTools/Thing.cpp", "TAtomic<int32> hits;\n")
        self.assertFinding(self.project.run().errors, "Plugins/GameTools", "(10.8)")


if __name__ == "__main__":
    unittest.main()
