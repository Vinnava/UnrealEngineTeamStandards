# Enforcement tooling

Starter files for section 18 of the team standard, so the mechanical rules are checked by a tool
instead of by memory. Copy them into a project. If a project needs a change, change it here too.

| File | Goes to | Enforces |
|---|---|---|
| `.clang-format` | Project root | Braces, indentation, line length (3.10). Includes are never reordered, so `.generated.h` stays last (3.4). |
| `.clang-tidy` | Project root | The case rules in 4.1 - camelCase members, locals and parameters; PascalCase functions, constants and enumerators. |
| `.editorconfig` | Project root | Encoding, tabs and trailing whitespace, for editors that do not read `.clang-format`. |
| `check-standard.py` | Stays here | Consistency of **this repository**, not of a project: section references, links, encoding, checklist citations, file numbering, the index, the version policy and the always-loaded token budget. |
| `check-project.py` | The project's CI | The rules in a **project's** source that a text scan can decide: `TAtomic`, `LogTemp`, unmarked synchronous loads, emoji and `U+FFFD`, the threading-candidate registry; mutable statics and mixed logging as warnings. |
| `Validators/ProjectValidatorBase.h` / `.cpp` | The project's editor module | The shared base: owns the one content-root setting both validators read. |
| `Validators/AssetNamingValidator.h` / `.cpp` | The project's editor module | Asset prefixes (7.1), core-framework role prefixes (7.2), and PascalCase names with no spaces (7.3) - on save, from Validate Data, and in CI. |
| `Validators/AssetContentValidator.h` / `.cpp` | The project's editor module | Textures that cannot stream or break the size budget, and heavy non-Nanite meshes with no LODs (23.1, 23.2). |
| `tests/` | Stays here | Unit and mutation tests for both checkers, and the in-engine validator harness. |
| `project-template/CLAUDE.md` | Project root | The rule-file imports, the project's pinned decisions, and **the override table** (00-core). The file an assistant actually reads. |
| `project-template/.gitattributes` | Project root, before the first asset | Git LFS with `lockable`, without which `git lfs lock` in 14.3 does not work. |
| `project-template/PULL_REQUEST_TEMPLATE.md` | The project's `.github/` | The rules no tool can check (18.2), sized like 17.1 rather than 17.2. |

## Starting a project

Copy `project-template/` into the new project and fill in every `<Project>`:

| From | To |
|---|---|
| `project-template/CLAUDE.md` | `CLAUDE.md` at the project root |
| `project-template/.gitattributes` | `.gitattributes` at the project root, **before the first asset commit** |
| `project-template/PULL_REQUEST_TEMPLATE.md` | `.github/PULL_REQUEST_TEMPLATE.md` |

`CLAUDE.md` is the one that matters most. It holds the rule-file imports **and the override table**:
the precedence order in `00-core` makes a written override beat the standard, and the assistant only
ever sees the overrides that live in the file it is given. An override recorded solely in the project
README is invisible to it, which makes it an unwritten deviation - a defect, not an override.

## Checking the standard itself

`check-standard.py` is the only file here that is not copied into a project - it maintains this
repository. Run it from the repository root before committing a change to any rule:

```bash
python tooling/check-standard.py
```

It fails on a reference to a section that does not exist, a broken relative link, a non-ASCII
character or `U+FFFD` (5.5), a rule file whose name disagrees with the sections it holds, a rule file
missing from the README index, a README, changelog or project template that disagree on the version,
a release that changes a rule's meaning without a major version, and an always-loaded import set over
its token budget. It warns when a review-list item in 17.2 cites no section - that citation is what
makes a rule change greppable across the five places a rule tends to be mentioned.

It needs Python 3.10 or newer and nothing else. CI runs it on every push.

## Checking a project

`check-project.py` is copied into nothing - a project's CI runs it from the pinned submodule:

```bash
python standards/tooling/check-project.py . --warn-only
```

It scans `Source/` and every `Plugins/*/Source/`, and skips `Intermediate`, `Binaries` and
`ThirdParty`. It reads code with comments and string literals blanked out, so `// never use LogTemp`
is not a use of `LogTemp`. It knows the engine's idioms - a file-scope `TAutoConsoleVariable` is not
reported as a mutable static - and an editor module (a folder ending in `Editor`) may load
synchronously. Code in a prototype module (1.6) is checked only for `TAtomic` and encoding.

- **Errors fail the build; warnings print and never do.** The warnings are the checks with known false
  positives.
- **`--warn-only` reports everything as a warning and exits 0** - the retrofit mode 18.4 asks for, so a
  backlog is visible before the gate is switched on. Drop the flag once the backlog is clear.
- **An allowed synchronous load carries `// sync-load-ok: <reason>`** on its line or the line above
  (10.3); that marker is how the checker tells an exception from a hitch.

## Tests

```bash
python -m unittest discover -s tooling/tests -v
```

- **`test_check_project.py`** gives every check a case that must fire and a case that must not. The
  second kind matters as much: a check that fires on a comment, a constant or an engine idiom gets
  disabled.
- **`test_check_standard.py`** copies the repository, breaks it one way at a time, and asserts
  `check-standard.py` notices. A consistency checker that passes a clean repository proves nothing on
  its own - in 1.8 a check whose regex contained a backspace character passed everything, because it
  matched nothing. These tests are what caught it.

CI runs both on every push.

## Running clang-format

```
clang-format --style=file:tooling/.clang-format -i <changed files>
```

Verified with clang-format 19. The two options that matter most are not obvious:
`UseTab: ForContinuationAndIndentation` and `AlignAfterOpenBracket: DontAlign`, without which
clang-format indents wrapped lines and braced-list rows with **spaces** and the file ends up mixing
both against 3.10. `Cpp11BracedListStyle: false` keeps Epic's `{ A, B }` spacing, and
`AlignTrailingComments: Leave` keeps the aligned `private:   // Variables` block from 3.1.

Every file in `Validators/` is formatted with this config and produces no diff, so they double as its
test case: format them, and a non-empty diff means the config drifted. CI checks exactly that.

## Running clang-tidy

clang-tidy needs a compile database, which UBT generates:

```
Build.bat -Mode=GenerateClangDatabase -Project=<Project>.uproject <Project>Editor Win64 Development
```

That writes `compile_commands.json` to the project root. Then run it over the files a commit
touched, not the whole tree - a full pass on an Unreal project takes hours:

```
clang-tidy -p . Source/<Project>/Character/PlayerCharacter.cpp
```

**Never pass `--fix`.** A rename of a `UPROPERTY` or a `BindWidget` member breaks reflection and the
widget bind (3.8, 7.4); the tool reports, a person renames with the Core Redirect.

**In CI, pass `--warnings-as-errors`.** clang-tidy exits 0 even when it reports violations, so without
this the every-commit tier (14.5) prints them and passes anyway:

```
clang-tidy -p . --warnings-as-errors=readability-identifier-naming <changed files>
```

Scope it to the check named, not `*`, so a future check added to the file cannot fail the build the
day it is added.

What it cannot check is listed at the top of the file - type prefixes, the `b` prefix on booleans,
the verb vocabulary. Those stay in the pull request template (18).

## Installing the validators

1. Copy every file in `Validators/` into `Source/<Project>Editor/Private/Validators/`. Nothing else
   includes the headers, so they stay private and need no `_API` export.
2. Add `"DataValidation"` to the editor module's `PrivateDependencyModuleNames`, with a comment
   saying why (1.2).
3. Configure them in `Config/DefaultEditor.ini`. **The content root is set once, on the base class** -
   it is `GlobalConfig`, so both validators read that one value:

   ```ini
   [/Script/<Project>Editor.ProjectValidatorBase]
   contentRoot=/Game/_<Project>

   [/Script/<Project>Editor.AssetContentValidator]
   maxTextureSize=4096
   lodTriangleThreshold=1000
   ```

4. Run them across the project from **Tools > Validate Data**, and in CI:

   ```
   UnrealEditor-Cmd.exe <Project>.uproject -run=DataValidation -unattended -nopause -nosplash
   ```

   The commandlet exits non-zero when an asset fails, and zero when there are only warnings - both
   verified by the harness below.

The validators read only assets under the content root, so third-party folders are never touched
(2.2). Assets that already break the rules will fail: rename them in a planned batch (7.6), not on
sight. Validation loads each asset, so a content root full of maps makes the every-commit tier slow
(14.5) - split maps into their own nightly pass if it bites.

**What the naming validator lets through.** A Blueprint macro library passes - 7.1 gives it no
prefix. A type with no row in the table **passes with a warning** naming the type, so a new engine
type never blocks a commit but the table grows instead of quietly ageing. Textures accept `T_` or
`HDRI_` (7.1). Core-framework Blueprints are matched by parent class and must carry their 7.2 role
prefix, so a GameMode Blueprint named `BP_Main` fails and `BP_GM_Main` passes - with `BP_TEMP_` /
`WBP_TEMP_` accepted whatever the parent (8.2). A Blueprint's generated class (`BP_Door_C`) is
skipped; the Blueprint carries the name.

**Writing another validator:** once `CanValidateAsset` accepts an asset, every path through
`ValidateLoadedAsset` must end in `AssetPasses` or `AssetFails`. Returning `NotValidated` fires an
engine `ensure` on every run, and `AssetWarning` alone is not a verdict (16.9). Decide what to skip in
`CanValidateAsset`.

## Proving the validators work

```
powershell -ExecutionPolicy Bypass -File tooling\tests\validator-harness\run-validator-test.ps1
```

Run it after changing a validator and on every engine upgrade (22.2). It needs only an installed
engine (`-EngineRoot`, default `C:\Program Files\Epic Games\UE_5.7`). It:

1. **compiles the validators** in a scratch project with no PCH and no unity build - so a missing
   include cannot hide behind a shared PCH - and fails on any warning in them;
2. **creates eleven assets** in a headless editor, each built to pass, fail or warn on one rule;
3. **runs the `DataValidation` commandlet** - the command CI runs - and checks each of the five
   expected errors and the one warning, that nothing outside the content root is checked, that no
   generated class is reported twice, and that no engine `ensure` fires;
4. **removes the failing assets and validates again**, checking that a warning alone exits 0.

It exits 0 only if every check passes. It was built by doing all of this by hand first, and that
first run found three real bugs that compiling never could: a `NotValidated` path that had fired an
engine `ensure` since 1.0, every Blueprint being reported twice, and the unmapped-type path returning
no verdict.

Written against the UE 5.7 `UEditorValidatorBase` API. The class-name table uses asset class names
rather than types, so it links nothing beyond `Engine` and `DataValidation`. GAS classes are matched
by name for the same reason.

## Blueprint lint

Unreal has no Blueprint linter. Lint rules are written as further `UEditorValidatorBase` subclasses,
added as a project needs them:

- `Event Tick` used without an approval comment in the graph (3.12)
- A node-count budget per graph
- `Cast To` a Blueprint class - a hard reference (8.3)
- Hard-reference size past the asset's reference budget (13.3)
