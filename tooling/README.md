# Enforcement tooling

Starter files for section 18 of the team standard, so the mechanical rules are checked by a tool
instead of by memory. Copy them into a project. If a project needs a change, change it here too.

| File | Goes to | Enforces |
|---|---|---|
| `.clang-format` | Project root | Braces, indentation, line length (3.10). Includes are never reordered, so `.generated.h` stays last (3.4). |
| `.editorconfig` | Project root | Encoding, tabs and trailing whitespace, for editors that do not read `.clang-format`. |
| `Validators/AssetNamingValidator.h` / `.cpp` | The project's editor module | Asset prefixes (7.1), and PascalCase names with no spaces (7.3) - on save, from Validate Data, and in CI. |

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
