# 26. Source control

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**Read this when a project chooses or sets up source control, and when it pins or upgrades this
standard.** 14.3 is the always-loaded summary. The standard names no system: it states what any system
must provide, and 26.3 records how each one provides it.

---

### 26.1 What any system must provide

Set up before the first asset is committed - moving binaries into the right store later rewrites
history on some systems and is expensive on all of them.

| Requirement | Why |
|---|---|
| **Binary assets in a store built for them** - `.uasset`, `.umap`, source art (23.4) and audio | A binary diff is a full copy; a plain text store bloats until clones and syncs fail |
| **An exclusive lock on every `.uasset` and `.umap`**, and on source art that cannot merge, taken before editing (14.3) | Binary files cannot be merged. Without a lock, the second person to save loses their work |
| **Generated folders never committed** - `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/`, `.vs/`, and the per-machine files of 27: `compile_commands.json`, clangd's `.cache/`, `.claude/settings.local.json` - listed in the system's ignore file | They are rebuilt from source, differ per machine, and are large |
| **Text stays text, with fixed line endings** | A line-ending change shows every line as modified and buries the real diff |
| **The commit message format in 14.3**, whatever the system calls a commit - changelist, changeset, snapshot | `System: Summary` makes history searchable by system on every system |
| **This standard pinned to a release** (26.4) | A project upgrades when it decides to, not when the standard moves |

**The editor's source-control integration is turned on** where the system has one, so the editor
shows locks, checks files out on edit and warns before a locked file is changed.

### 26.2 Choosing a system

Decide once, before the first asset, and write the choice in the project's `CLAUDE.md`. Choose by the
work, not by habit:

- **Who edits binary assets, and how often.** Artists and designers saving `.uasset` files daily need
  locking that the server enforces and the editor shows, not a convention.
- **Where it is hosted.** Self-hosted, cloud, or either - and who maintains it.
- **Whether the editor integrates with it.** A system the editor cannot see makes 14.3's locks a
  manual step that gets skipped.
- **Repository size over the project's life.** Binary history only grows.

**Keep branches short-lived** on any system: binary assets diverge on a branch and cannot be merged
back. **One mainline serves every platform** - never a per-platform branch; platform differences
live behind interfaces and in config (28.1, 28.6). **One File Per Actor** (23.3) turns a level into
thousands of small files - budget for that on a system that slows with file count.

### 26.3 How each system provides it

Each row was correct when written. **A row marked Unverified has not yet been run by a project**: the
first project to use that system checks every column, and the fix lands here as a patch release. An
unverified row is a starting point, not a promise.

| System | Binary store | Exclusive lock | Ignore file | Status |
|---|---|---|---|---|
| **Git + LFS** | Git LFS, set up from [`tooling/project-template/.gitattributes`](../tooling/project-template/.gitattributes) | `lockable` in `.gitattributes`, then `git lfs lock`; lockable files check out read-only | `.gitignore` | Template shipped here |
| **Gitea** | Git LFS - the server must have LFS enabled | Git LFS locking - the server must support the LFS locks API | `.gitignore` | Unverified |
| **Perforce (Helix Core)** | Native | The `+l` (exclusive open) file type, set for `.uasset` and `.umap` in the server typemap | `.p4ignore`, named by `P4IGNORE` | Unverified |
| **Plastic SCM (Unity Version Control)** | Native | Lock rules for `.uasset` and `.umap`, set on the server or organisation | `ignore.conf` | Unverified |
| **Diversion** | Native | Per Diversion's documentation - record it here on first use | `.dvignore` at the workspace root, paths relative to it | Ignore file verified in use; locking unverified |

A system not in the table is added the same way: a row, marked Unverified, by the first project that
uses it.

### 26.4 Pinning this standard

> **A project uses one release of this standard, never a moving branch, and proves it in CI.**

| Method | Works with | How |
|---|---|---|
| **Vendored copy** - the default | Every system | Copy the release into `standards/` at the project root |
| **Git submodule** | Git, Gitea | Add the repository as a submodule at `standards/`, checked out at the release tag |

- **Get a release's files** from the release archive on the host, or `git archive v4.1.0` in a clone.
  Every release is a tag (README, "Versioning").
- **A vendored copy may leave out** `.github/`, `tooling/tests/`, `.gitattributes` and `.gitignore` -
  CI and test scaffolding for this repository. Copy everything else whole. Keep
  `tooling/tests/save-version-harness/` if the project saves data: 24.3 points to it for code.
- **Never edit the pinned copy.** A deviation is an override in the project's `CLAUDE.md` (00-core); a
  rule that is wrong is raised against the standard (14.1).
- **Prove it in the every-commit tier** (14.5): `python standards/tooling/verify-standard.py` checks
  every file against `MANIFEST.sha256`, which ships in each release, and prints the version. An edited
  or missing file fails; a file the project added - a note recording where the copy came from - only
  warns.
- **Record the version** in the project's `CLAUDE.md` (`Standard version:`), so a reader can tell
  whether a rule has moved on.
- **Upgrading is replacing the whole folder** with the new release - never merging file by file - then
  reading the changelog's `Rule change:` bullets, running the verifier, and updating the version line.
