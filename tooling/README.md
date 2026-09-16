# Enforcement tooling

Starter files for section 18 of the team standard, so the mechanical rules are checked by a tool
instead of by memory. Copy them into a project. If a project needs a change, change it here too.

| File | Goes to | Enforces |
|---|---|---|
| `.clang-format` | Project root | Braces, indentation, line length (3.10). Includes are never reordered, so `.generated.h` stays last (3.4). |
| `.clang-tidy` | Project root | The case rules in 4.1 - camelCase members, locals and parameters; PascalCase functions, constants and enumerators. |
| `.editorconfig` | Project root | Encoding, tabs and trailing whitespace, for editors that do not read `.clang-format`. |
| `check-standard.py` | Stays here | Consistency of **this repository**, not of a project: section references, links, encoding, checklist citations, the file index and the version. |
| `Validators/AssetNamingValidator.h` / `.cpp` | The project's editor module | Asset prefixes (7.1), core-framework role prefixes (7.2), and PascalCase names with no spaces (7.3) - on save, from Validate Data, and in CI. |

## Checking the standard itself

`check-standard.py` is the only file here that is not copied into a project - it maintains this
repository. Run it from the repository root before committing a change to any rule:

```bash
python tooling/check-standard.py
```

It fails on a reference to a section that does not exist, a broken relative link, a non-ASCII
character or `U+FFFD` (5.5), a rule file missing from the README index, and a version in the README
that disagrees with the newest changelog entry. It warns when a review-list item in 17.2 cites no
section - that citation is what makes a rule change greppable across the five places a rule tends to
be mentioned.

It needs Python 3.9 or newer and nothing else. Run it in the every-commit CI tier (14.5).

## Running clang-format

```
clang-format --style=file:tooling/.clang-format -i <changed files>
```

Verified with clang-format 19. The two options that matter most are not obvious:
`UseTab: ForContinuationAndIndentation` and `AlignAfterOpenBracket: DontAlign`, without which
clang-format indents wrapped lines and braced-list rows with **spaces** and the file ends up mixing
both against 3.10. `Cpp11BracedListStyle: false` keeps Epic's `{ A, B }` spacing, and
`AlignTrailingComments: Leave` keeps the aligned `private:   // Variables` block from 3.1.

`Validators/AssetNamingValidator.h` and `.cpp` are formatted with this file and produce no diff, so
they double as its test case: format them, and a non-empty diff means the config drifted.

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

## Installing the validator

1. Copy both files into `Source/<Project>Editor/Private/Validators/`. Nothing else includes the header,
   so it stays private and needs no `_API` export.
2. Add `"DataValidation"` to the editor module's `PrivateDependencyModuleNames`, with a comment
   saying why (1.2).
3. Set the project's content root in `Config/DefaultEditor.ini`:

   ```ini
   [/Script/<Project>Editor.AssetNamingValidator]
   contentRoot=/Game/_<Project>
   ```

4. Run it across the project from **Tools > Validate Data**, and in CI:

   ```
   UnrealEditor-Cmd.exe <Project>.uproject -run=DataValidation -unattended -nopause -nosplash
   ```

The validator reads only assets under the content root, so third-party folders are never touched
(2.2). Assets that already break the rules will fail: rename them in a planned batch (7.6), not on
sight.

**What it checks, and what it lets through.** A type with no entry in its table returns
`NotValidated` rather than failing - a Blueprint Macro Library, and any asset type 7.1 has no row
for. Textures accept `T_` or `HDRI_` (7.1). Core-framework Blueprints are matched by parent class
and must carry their 7.2 role prefix, so a GameMode Blueprint named `BP_Main` fails and
`BP_GM_Main` passes - with `BP_TEMP_` / `WBP_TEMP_` accepted whatever the parent, so prototypes
are not pushed out of the naming rules (8.2). Validation loads each asset, so a content root full of maps makes the
every-commit CI tier slow (14.5) - split maps into their own nightly pass if it bites.

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
