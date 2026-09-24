"""Creates the validator test assets inside a headless editor. Run by run-validator-test.ps1.

Every asset is built to pass or to fail one specific rule; the runner checks that exactly those
findings come back. Textures are written as PNGs here, with only the standard library, so the
harness needs nothing but the engine.
"""
import struct
import zlib

import unreal

ROOT = "/Game/_Test"
OUTSIDE = "/Game/_Other"

tools = unreal.AssetToolsHelpers.get_asset_tools()
library = unreal.EditorAssetLibrary

# An automated import syncs the Content Browser whenever this variable exists, whatever the task
# says, and the sync asserts in a commandlet because there is no Slate application (standard 16.9)
unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.SyncToBrowser 0")


def write_png(path, width, height):
    rows = b"".join(b"\x00" + bytes([40, 90, 160]) * width for _ in range(height))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    with open(path, "wb") as png:
        png.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                  + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def blueprint(name, path, parent, factory=None):
    factory = factory or unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    tools.create_asset(name, path, unreal.Blueprint, factory)


def texture(name, width, height):
    source = f"{unreal.Paths.project_saved_dir()}{name}.png"
    write_png(source, width, height)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", source)
    task.set_editor_property("destination_path", ROOT)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    tools.import_asset_tasks([task])


# Naming (7.1-7.3)
blueprint("BP_Main", ROOT, unreal.GameModeBase)           # FAIL: a GameMode needs BP_GM_ (7.2)
blueprint("BP_GM_Main", ROOT, unreal.GameModeBase)        # pass
blueprint("BP_TEMP_ragdoll", ROOT, unreal.Actor)          # FAIL: lower case after BP_TEMP_ (7.3)
blueprint("BP_Door", ROOT, unreal.Actor)                  # pass
blueprint("BP_whatever", OUTSIDE, unreal.Actor)           # SILENT: outside the content root
blueprint("MacroHelpers", ROOT, unreal.Actor, unreal.BlueprintMacroFactory())  # pass: 7.1 gives no prefix
tools.create_asset("Unmapped", ROOT, unreal.SubsurfaceProfile, unreal.SubsurfaceProfileFactory())  # WARNING

# Content (23.1, 23.2) - budgets are lowered in Config/DefaultEditor.ini so small assets trip them
texture("T_Ok", 256, 256)                                 # pass
texture("T_NotPow2", 300, 200)                            # FAIL: can never stream
texture("T_Big", 1024, 1024)                              # FAIL: over the 512 budget
library.duplicate_asset("/Engine/BasicShapes/Sphere", f"{ROOT}/SM_Sphere")   # FAIL: 960 triangles, one LOD
library.duplicate_asset("/Engine/BasicShapes/Cube", f"{ROOT}/SM_Cube")       # pass: 12 triangles

library.save_directory(ROOT)
library.save_directory(OUTSIDE)
