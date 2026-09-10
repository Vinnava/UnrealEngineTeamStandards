# 5-6. Comments and logging

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

---

## 5. Comment standard

### 5.1 What must be commented

- **Every `UPROPERTY` declaration** - Doxygen `/** */`
- **Every `UFUNCTION` declaration** - Doxygen `/** */`
- **Every variable and every function in a header** - including private and non-reflected ones.
  The comment adds what the name does not: a unit, a lifetime, what null means, a caller contract.
  **A trivial accessor whose name says everything** (`GetCurrentHealth`, `IsTransitioning`) **is
  exempt.**
- **Every enumerator** in a `UENUM`
- **Every class** - a `/** */` block above `UCLASS()` stating its role and its lifetime

### 5.2 The two-line rule

> **Two lines maximum. No exceptions.** Applies to every comment you *write*.

- No paragraph comments. No multi-line rationale blocks.
- **Reasoning that needs more than two lines belongs in a design doc**, not above the code.
- Plainly worded. State the point, not the full argument.
- Applies to `//` inline, `/** Doxygen */` and file-scope comments alike.
- **Per-parameter comments may sit on their own line, one line each** - never wrap a single parameter
  across two lines.

```cpp
/** Currently active runner - null when no quest is running */
UPROPERTY()
TObjectPtr<UQuestRunner> activeRunner;

/** Loaded registry asset - held strong so soft-resolved quests don't unload mid-execution */
UPROPERTY()
TObjectPtr<UQuestRegistry> loadedRegistry;
```

The **class-level block** is the one place a slightly longer form is acceptable:

```cpp
/**
 * Persistent orchestrator. Lives for the GameInstance's lifetime, but its memory
 * footprint is one runner pointer plus one registry pointer when idle.
 */
UCLASS()
class GAME_API UQuestDirectorSubsystem : public UGameInstanceSubsystem
```

### 5.3 Inline comments

`//` comments are for **non-obvious rationale only** - the *why*, never the *what*.

```cpp
// WRONG - restates the code, adds nothing
// Set health to 100
currentHealth = 100;

// CORRECT - explains a decision the code cannot show
// Built BEFORE the step starts, so a step that hides the HUD finds one to hide.
EnsureGameplayHUD();
```

**If deleting the comment loses nothing but words, delete it.**

### 5.4 Comment maintenance (new and modified code)

- **Code you add or change meets this standard in full.** A declaration you touch with no comment
  gets one; a comment of three lines or more is rewritten down to two, preserving its meaning.
- **Do not repair the rest of the file as a drive-by.** Untouched code is brought up to standard in a
  planned cleanup pass, in its own commit - the same rule as logging (6.5).

### 5.5 Forbidden content

- **No emojis anywhere** - comments, logs, documentation, commit messages, code.
- **Never write the Unicode replacement character `U+FFFD`.** When you find one while editing, remove
  it and restore the intended character where the meaning is recoverable.
- **No commented-out code in a commit.** Delete it; git remembers.
- **No anonymous `TODO`.** A `TODO` has a name and a reason - or fix it, ticket it, or delete it.

---

## 6. Logging standard

### 6.1 Mandatory format

```cpp
UE_LOGFMT(LogGameQuestDirector, Log, "[{Obj}] [FunctionName] Description: {Detail}",
    GetNameSafe(this), detailValue);
```

**Every log line includes four things:**

1. **What happened** - the description
2. **The class** - `GetNameSafe(this)`, in the leading `[{Obj}]`
3. **The function name** - in its own `[Brackets]`
4. **The relevant context value** - the id, tag, index or count that makes the line actionable

How those values are produced:

- **`GetNameSafe(obj)`, never `obj->GetName()`.** `GetNameSafe` returns `"None"` for null.
- **Enums through `UEnum::GetValueAsString(value)`**, never a `(uint8)` cast.
- **Conditional lines use `UE_CLOGFMT(condition, ...)`** instead of wrapping `UE_LOGFMT` in an `if`.

### 6.2 Category naming and declaration

**Every log category is `Log` + the project short name + the domain.** Declare it with
`DEFINE_LOG_CATEGORY_STATIC` at the top of the `.cpp` that owns it:

```cpp
// QuestRunner.cpp
#include "QuestRunner.h"

DEFINE_LOG_CATEGORY_STATIC(LogGameQuestRunner, Log, All);
```

- **`DEFINE_LOG_CATEGORY_STATIC` is the default.**
- **The `DECLARE_LOG_CATEGORY_EXTERN` (header) + `DEFINE_LOG_CATEGORY` (cpp) pair only when several
  translation units log to the same category** - a subsystem plus its helper classes.
- **One category per meaningful subsystem** - not one per class, not one for the whole project.
- A module-wide fallback category (`LogGame`) for genuinely cross-cutting code, used sparingly.
- **Never `LogTemp` in committed code.**

### 6.3 Severity

| Level | Use for | Example |
|---|---|---|
| `Error` | Critical failure - the feature cannot proceed | A null definition, an unresolved catalogue row |
| `Warning` | Recoverable issue, **or a tripwire for a state that should not occur** | "Could not resolve PlayerController - steps requiring PC will fail" |
| `Log` | Normal flow worth tracing | "Quest 'X' starting at section index 2" |
| `Verbose` | Detailed per-frame or per-item debug | Per-message parse detail |

**When an invariant is re-established rather than enforced** - a flag unexpectedly true, a cache
unexpectedly empty - **log a Warning and proceed.** Never recover silently.

### 6.4 Examples

```cpp
UE_LOGFMT(LogGameQuestRunner, Error, "[{Obj}] [LaunchQuest] Quest definition is null",
    GetNameSafe(this));

UE_LOGFMT(LogGameQuestRunner, Warning,
    "[{Obj}] [LaunchQuest] Section '{Section}' not found in quest '{Quest}' - starting from beginning",
    GetNameSafe(this), resumeFromSectionId, quest->GetQuestId());

UE_LOGFMT(LogGameQuestRunner, Log,
    "[{Obj}] [LaunchQuest] Quest '{Quest}' starting at section index {Index}",
    GetNameSafe(this), quest->GetQuestId(), currentSectionIndex);
```

### 6.5 UE_LOGFMT vs UE_LOG

| | `UE_LOGFMT` | `UE_LOG` |
|---|---|---|
| Placeholders | `{Tokens}` | `%s`, `%d` |
| FString | Pass directly | Needs `*` dereference |
| Literals | Plain string | Needs `TEXT()` |
| Type safety | High - a type mismatch cannot corrupt the output | Low - a wrong specifier compiles and prints garbage |

- **`{Tokens}` are readable labels, not a binding.** Bare values are the positional form - matched by
  order; `{0}` and `{Obj}` behave identically. Only the pair form, `("Obj", a), ("Id", b)`, matches by
  name (`StructuredLog.h`). **Keep argument order matching token order.**
- **`UE_LOGFMT` is the standard for all new and modified code.**
- **Do not convert an existing file's logging as a side effect of an unrelated change.** Lines you
  write or change use `UE_LOGFMT`; the rest is converted in a planned cleanup pass, in its own commit
  (5.4).

### 6.6 What to log

- **Every early return from a guard clause that signals a problem**, at the right level:
  - **Unexpected but recoverable** - `Warning` or `Error` (6.3).
  - **Expected** - no target in range, an optional component absent, a hot-path early-out -
    `Verbose`, or no log at all.
  - **A programmer error that should never happen** - `ensure` (3.9).
- **Every state transition** in a subsystem or runner - entered, completed, aborted.
- **Every DataAsset validation failure**, naming the asset and the row that failed.
- **Never log at `Log` level inside Tick or a per-frame loop.** Use `Verbose`. On a hot path, pass raw
  values as tokens - never build an `FString` (`FString::Printf`, concatenation) only to log it.
- **No emojis in log strings.**

### 6.7 Validation passes

- **Any system driven by authored data has a `Validate*` function that runs once on load** and logs an
  `Error` for every unresolvable reference, duplicate id or miscategorised row.
- **Catch it in the editor too.** Override `IsDataValid(FDataValidationContext&) const` (inside
  `#if WITH_EDITOR`) on DataAsset and actor classes, so bad data fails on save and in the Data
  Validation pass. Keep the runtime `Validate*` pass as well.
