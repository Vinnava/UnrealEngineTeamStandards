# 27. AI assistants: Claude Code

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**How a project works with Claude Code, and the kit that sets it up.** 14.2 is the working style for
any assistant; this section is the Claude Code setup behind it. Read it when a project adopts the
kit, and when Claude Code or the kit changes. The one constraint behind every rule here: **the context
window is the scarce resource** - it fills fast, and quality drops as it fills.

The kit is [`tooling/claude/`](../tooling/claude/): rule groups, agents, skills, hooks, scripts and a
status line, installed by `tooling/claude/install.py` (27.7). Connecting Claude to the running editor
is optional (27.8).

---

### 27.1 What loads, and when

| Loads | What | Why |
|---|---|---|
| **Every session** | The project's `CLAUDE.md`, importing `00-core`, `14-15-practice` and `17-gate` | Needed for every decision: the pillars, the working style, the gate |
| **The first time Claude touches a matching file** | The rule groups in `tooling/claude/rule-groups.json` - C++, networking, UI, audio, online, save data, GAS, platforms | A rule loads where it applies, and only there |
| **When the task matches, or by name** | Skills - async (10), performance (13), engine traps (16), content (7, 8, 23), source control (26) | Topics that do not follow a file path |

- **Never `@`-import an on-demand rule file into `CLAUDE.md`.** Imports load at launch, so an import
  is an always-loaded rule (README, "Giving this to an AI assistant", holds the budget).
- **`CLAUDE.md` stays under 200 lines.** A long one gets half-followed. Project facts, overrides and
  canonical examples belong there; procedures belong in skills.
- **Async (10) is a skill, not a C++ rule group** - most C++ edits are not async, and the gate already
  carries the three async safety items in every session.
- **Every rule group has a token budget** in `rule-groups.json`, which `check-standard.py` enforces, as
  it does the always-loaded budget.

### 27.2 Choosing a workflow

**Size the task first.**

| Task | Workflow |
|---|---|
| **The change fits in one sentence** | Do it directly. Planning it costs more than it saves |
| **Medium** - several files, one session's work | Plan in plan mode, then build in the same session |
| **Large** - a feature, many files, or independent parts | Plan in plan mode with `/ue-plan`, then **`/clear`** and run `/ue-implement` on the plan in a fresh session |

- **The project default model is `opusplan`** - Opus in plan mode, Sonnet once you leave it. The
  thinking that decides quality - architecture, ownership, `CONFLICT` analysis - runs on Opus; the
  writing runs on Sonnet at half the price.
- **Effort is set per model in the project settings** - Opus `high` for planning, Sonnet `medium` for
  building. Raise Sonnet's when its output needs correcting more than once.
- **Leave plan mode once per task.** Each entry and exit switches model, and each switch re-reads the
  whole conversation uncached. Returning to plan mode mid-build costs a full rebuild.
- **A large task builds in a fresh session** because the plan is the hand-off: the builder starts
  small and focused instead of re-reading everything the planning explored. So the plan must stand
  alone - files, interfaces, state owners, rule sections, work packages and an end-to-end check. Plans
  live in `.claude/plans/`; one that records a lasting design decision is copied into the project's docs.
- **The advisor is optional.** `/advisor opus` lets Sonnet consult Opus at decision points - a
  recurring error, before declaring done. It is experimental, each consultation reads the whole
  conversation at Opus rates, and it is off unless a person turns it on.

### 27.3 Agents

> **An agent earns its place only for a big read with a small answer, with no need for the
> conversation's history - ideally on a cheaper model or in parallel.**

Each agent starts cold and spends its own tokens; what it saves is the main context. A job that needs
back-and-forth stays in the main session. The kit has four, all task agents:

| Agent | Job | Model |
|---|---|---|
| **ue-implementer** | Builds one work package of an approved plan | Sonnet |
| **ue-reviewer** | Reviews a change against the standard and its plan, read-only, in a fresh context | Sonnet |
| **ue-engine-source** | Checks an engine claim in the installed source, with quotes; remembers what it verified, per engine version | Sonnet |
| **ue-runner** | Digs a long log - a crash, a failed cook - down to its root cause | Haiku |

- **Roles are reviewer checklists, not agents.** A technical-art or networking review is ue-reviewer
  given the content or networking checklist (17.2) - the same expertise without a second main session.
- **At most two implementers at once, on packages that share no file,** and only one build of a target
  at a time. Worktree isolation is git-only (26.3), so on other systems implementers share one tree.
- **A reviewer reports only what affects correctness, the standard or the plan.** One asked to find
  gaps always finds some; chasing every suggestion produces over-engineering.
- **A build or a validation run is a script, not an agent** (27.4). ue-runner is for output that takes
  judgment to read.

### 27.4 Claude checks its own work

> **Give Claude a check it can run at every step, and require evidence, never "done".**

| Speed | Check | How |
|---|---|---|
| Instant | Text-scan rules on the file just edited | The edit hook runs `check-project.py --files` |
| Seconds | Compile errors, without a build | The `clangd-lsp` code-intelligence plugin |
| Minutes | The build | `tooling/claude/scripts/ue_build.py` |
| Minutes | Assets | `tooling/claude/scripts/ue_validate.py` |
| Minutes | Behaviour | Automation tests (14.4) |
| The person | PIE | Claude lists what to try (17.1) |

- **Three hooks, all command hooks.** They run outside the model and cost no tokens unless they report
  something:
  - **after every edit** - `check-project.py` on that file; an error comes back to Claude at once;
  - **before an edit to the pinned standard** - refused (26.4);
  - **when a turn ends** - if a file edited this session still has errors, Claude keeps working once;
    if they remain, the turn ends and you are told, rather than looping.
- **Scripts print only what matters.** `ue_build`, `ue_validate`, `ue_log` and `ue_engine` turn
  thousands of log lines into the errors, the project's own warnings and a result line, and keep the
  full log in `Saved/Claude/`.
- **clangd needs a compile database and `tooling/.clangd`:** generate `compile_commands.json` with
  UnrealBuildTool's `GenerateClangDatabase` mode - the command in tooling/README.md, "Running
  clang-tidy" - after adding files or modules, and build once first so the generated headers exist.
  Copy `.clangd` to the project root: without it a clean file shows about twenty false errors, and
  Claude takes them for real ones. The kit enables the `clangd-lsp` plugin for the project; each
  machine installs the `clangd` binary on its `PATH`. A machine without it turns the plugin off in its
  own `.claude/settings.local.json`. The compile database and clangd's index, `.cache/`, are per
  machine and go in the ignore file (26.1); `.clangd` is shared and committed.
- **Evidence means the command and its output** - the build line, the validator count, the test
  result. A claim of success without it is not a result.

### 27.5 Sessions

- **`/clear` between unrelated tasks.** Stale context costs tokens on every later turn and degrades
  quality.
- **After two failed corrections, `/clear`** and start again with a better prompt that carries what you
  learned. A clean session beats a long one full of failed attempts.
- **`/rewind` abandons a dead end** without the cost of compaction; **`/btw`** asks a side question
  whose answer never enters the conversation.
- **Compact at a natural break**, not mid-task. The project's `CLAUDE.md` says what a summary must
  keep (the project template has the block).
- **Point at sources** - name the files, the class to follow, the symptom and what "fixed" looks like.
  A vague request is paid for in exploration.

### 27.6 Measuring

- **The kit's status line shows the model, how full the context is, the prompt-cache hit rate and the
  standard's version** - at no token cost.
- **`/context`** shows what the window holds; **`/usage`** shows what each agent, skill and plugin cost;
  **`/doctor`** proposes cuts to `CLAUDE.md`.
- **Claude Code's own usage is a pilot measure** (PILOT.md), compared on similar tasks before and after
  a change to the kit.

### 27.7 The kit

- **Install and refresh it with `tooling/claude/install.py`** from the project root. `--replicates`
  loads section 11 with the C++ rules; `--editor-mcp` enables the editor connection (27.8). Both are
  remembered by later refreshes and turned off with `--no-replicates` and `--no-editor-mcp`. It
  generates the rule groups, agents and skills into `.claude/`, merges its keys into
  `.claude/settings.json` - including the plugins it enables - without touching the rest, and removes
  files an older kit made.
- **Hooks, scripts and the status line run from the pinned copy** in `standards/`, so
  `verify-standard.py` proves them unedited (26.4).
- **Never edit a generated file.** `install.py --check` fails CI on one; change the standard, or record
  an override in `CLAUDE.md`.
- **After an upgrade of the standard, re-run the installer** (`/ue-upgrade-standard`).
- **Claude Code 2.1.251 or later** - per-model effort and the status line's cache figures need it.
- **The Claude Code behaviour this section relies on is re-proven when Claude Code changes,** the way
  22.2 re-proves engine claims: that path-scoped rules load only for matching files; that hook
  arguments expand `${CLAUDE_PROJECT_DIR}`; that `plansDirectory` resolves against the project; that
  `opusplan` switches model on leaving plan mode; that `enabledPlugins` in project settings turns a
  plugin on for everyone; and the model names under `modelSettings`, which change with each model
  generation. Last proven on Claude Code 2.1.296 (CHANGELOG, 4.1.0); per-model effort is the one
  behaviour shown only indirectly.

### 27.8 The editor connection - optional

> **Optional, per project: decided once and written in `CLAUDE.md`, like replication (11.1).**

- **What it is.** UE 5.8 ships **Unreal MCP**, experimental: a server inside the running editor that
  exposes the editor's toolsets - actors, Blueprints, materials, widgets, GAS, StateTree, automation
  tests and more. Epic's Claude Code plugin, `unreal-engine-skills-for-claude-code` in Anthropic's
  official marketplace, teaches Claude to use it. It is how Claude sees and changes assets, which it
  cannot open as files.
- **Turning it on:**
  1. In the project, enable the **Unreal MCP** and **All Toolsets** plugins - or only the toolsets the
     project needs.
  2. Install the kit with `--editor-mcp`, which enables Epic's plugin for everyone (27.7). A plugin
     added to a claude.ai account is synced to Claude Code and loads whatever the project's settings
     say, so a project with the connection off also needs it off in the account.
  3. On each machine, run `ModelContextProtocol.GenerateClientConfig ClaudeCode` in the editor console
     - it writes `.mcp.json` at the project root - and start the server each session with
     `ModelContextProtocol.StartServer`, or turn on Auto Start Server in Editor Preferences.
- **Check the data terms first.** The plugin logs that what it sends to an LLM service is Licensed
  Technology under the Unreal Engine EULA, and that you are responsible for the provider not training
  on it. Confirm the account's data-use settings before turning it on.
- **It listens on the local machine only, with no authentication.** Never expose or forward its port.
- **An editor change is not a code change:**
  - An asset Claude changes is a binary file: lock it first (14.3), name it by section 7, and run
    `ue_validate` afterwards - the edit hook sees only source files.
  - Claude Code's checkpoints and `/rewind` cover only files Claude edits directly; they do not undo
    an editor change. Source control and the editor's own undo do.
  - Tool calls run one at a time on the editor's game thread, so only one agent drives the editor at
    a time - never two implementers at once (27.3).
  - The connection needs the editor running; a header change needs it closed (15, item 1). Order the
    work so each phase has what it needs.
- **The context cost is low.** With tool search on - the default - Claude sees three tools, to list,
  describe and call the rest, until it uses one.
- **It is experimental.** Re-prove it on every engine upgrade (22.3): its tools change between
  versions.
