---
name: ue-new-class
description: Creates a new Unreal C++ class pair that already meets the standard - folder, file name, header section order, constructor defaults, comments, log category. Use whenever a new UCLASS, USTRUCT or interface is added.
argument-hint: "[class name] [parent class]"
---

Create the class `$ARGUMENTS` to the standard. Decide each of these before writing, and say what you
chose:

1. **Folder** by role, not feature (1.3) - a subsystem goes in `Subsystem/<Scope>/`. If you cannot
   tell which folder it belongs in, the class is doing two jobs: split it.
2. **Name** (4.1, 4.4): the `A`/`U`/`F`/`I`/`E` prefix, the composition pattern for its kind, and the
   project infix only if it is project-core. **File name** is the class name without its prefix (4.9).
3. **Owner and lifetime** (9.4, 9.11): what owns the state this class holds, and how long it lives.

Then write the pair in this shape:

```cpp
// QuestRunner.h
#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "QuestRunner.generated.h"

class UQuestStep;

/**
 * <Role in one line.>
 * <Lifetime: who owns it and when it dies.>
 */
UCLASS()
class GAME_API UQuestRunner : public UObject
{
	GENERATED_BODY()

private:   // Variables
	/** <What it is - unit, lifetime, what null means> */
	UPROPERTY()
	TObjectPtr<UQuestStep> currentStep;

protected: // Variables

public:    // Variables

private:   // Functions

protected: // Functions

public:    // Functions
	/** Sets defaults; touches no world, actor or asset (3.2) */
	UQuestRunner();
};
```

```cpp
// QuestRunner.cpp
#include "QuestRunner.h"

DEFINE_LOG_CATEGORY_STATIC(LogGameQuestRunner, Log, All);

UQuestRunner::UQuestRunner()
{
	currentStep = nullptr;
}
```

- **Every default in the constructor**, none in the header (3.2); actors keep `bCanEverTick = false`
  unless Tick was approved (3.7, 3.12).
- **Forward declare in the header**, include in the `.cpp`; `.generated.h` last (3.4).
- **Doxygen on every member and the class**, two lines unless it earns more (5.1, 5.2).
- **Log category** `Log<Project><Domain>` with `DEFINE_LOG_CATEGORY_STATIC` (6.2); log with `UE_LOGFMT` (6.1).
- **Export with `<Project>_API` only** if another module calls it (3.4).
- Delete the empty access sections you do not use.

A new class needs an editor-closed build (15, item 1).
