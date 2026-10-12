---
name: ue-traps
description: Known Unreal engine traps that fail silently (section 16) - level transitions and the PlayerController, movement and montages, reflection and data, soft pointers, SaveGame flags, widget geometry, async callbacks, replication, collision and input, formatting, textures, editor automation. Use before touching any of those systems, and whenever something behaves impossibly or works in the editor but not in a build.
---

Work down the debugging playbook first (section 15, always loaded) - item 1 solves more mysteries than
the rest. These are the traps it points to:

{{INCLUDE rules/16-engine-traps.md}}
