---
name: ue-content
description: Team rules for Unreal content and Blueprints (sections 7, 8 and 23) - asset prefixes and names, Blueprint class names and role infixes, naming inside a Blueprint, the C++/Blueprint boundary, graph hygiene, textures and map-type suffixes, meshes and collision, levels, source art, materials, animation, design data and content budgets. Use before naming, creating, importing or scripting an asset or a Blueprint, and when reviewing content.
---

Claude cannot open a .uasset or .umap - they are binary. Content is reached through what a script or
the editor exposes, and named by these rules. On a project with more than one platform, how an asset
varies per platform is 28.5 - read `{{STANDARDS}}/rules/28-cross-platform.md` first.

{{INCLUDE rules/07-08-content-blueprint.md}}

{{INCLUDE rules/23-content-pipeline.md}}
