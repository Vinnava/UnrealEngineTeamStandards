# 25. Gameplay Ability System naming

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**This section applies only if the project uses GAS.** 9.15 decides whether to use it and how; this
section names everything it creates - assets, tags, C++ classes and attributes - so that one ability
reads as one name in all of them.

---

### 25.1 Assets

| Prefix | Asset | Parent class | Example |
|---|---|---|---|
| `GA_` | Gameplay Ability Blueprint | `UGameplayAbility` | `GA_Dash`, `GA_Weapon_Fire` |
| `GE_` | Gameplay Effect Blueprint | `UGameplayEffect` | `GE_Damage_Fire`, `GE_Cooldown_Dash` |
| `GC_` | Gameplay Cue Notify - static, burst, actor or looping | `UGameplayCueNotify_Static`, `AGameplayCueNotify_Actor` | `GC_Damage_Fire` |
| `BP_AC_` | Ability system component Blueprint (7.2) | `UAbilitySystemComponent` | `BP_AC_AbilitySystem` |
| `DA_` | Ability set, or any GAS data asset | `UPrimaryDataAsset` | `DA_AbilitySet_Guard` |
| `DT_` | Attribute initialisation table | row type `FAttributeMetaData` | `DT_Attributes_Guard` |
| `CT_` | Scalable-float curve table | - | `CT_DamageByLevel` |

`AssetNamingValidator` enforces `GA_`, `GE_`, `GC_` and `BP_AC_` by parent class, matched by name so
the validator links nothing from GAS.

- **An ability is named for the action the designer says.** `GA_Dash`, `GA_Interact`. A family
  shares its first segment: `GA_Weapon_Fire`, `GA_Weapon_Reload`.
- **An effect's first segment is its purpose, the second its subject:**

  | Purpose | Form | Example |
  |---|---|---|
  | Damage | `GE_Damage_<Type>` | `GE_Damage_Fire` |
  | Healing | `GE_Heal_<Source>` | `GE_Heal_Potion` |
  | Cooldown | `GE_Cooldown_<Ability>` | `GE_Cooldown_Dash` |
  | Cost | `GE_Cost_<Ability>` | `GE_Cost_Dash` |
  | Buff / debuff | `GE_Buff_<Name>`, `GE_Debuff_<Name>` | `GE_Debuff_Stunned` |
  | Regeneration | `GE_Regen_<Attribute>` | `GE_Regen_Stamina` |
  | Startup values | `GE_Init_<Owner>` | `GE_Init_Guard` |

  `GE_Cooldown_Dash` sorts with the other cooldowns and names the ability it gates.
- **A cue is named for its tag**, without the `GameplayCue` root, segments joined by underscores:
  `GameplayCue.Damage.Fire` is `GC_Damage_Fire`. This is the form the editor reads back: a notify
  whose cue tag is empty derives one from its asset name, stripping `GC_` and turning underscores
  into dots. The derivation runs only in an interactive editor, so **set the cue tag explicitly
  anyway** - the name is for people, the property is what ships.

### 25.2 Gameplay tags

GAS tags follow 4.10 - hierarchical, PascalCase segments - under these roots:

| Root | Holds | Example |
|---|---|---|
| `Ability.` | An ability's own identity tag - what it is activated by (9.15) | `Ability.Dash`, `Ability.Weapon.Fire` |
| `Cooldown.` | The tag a cooldown effect grants while it runs | `Cooldown.Dash` |
| `State.` | A status the owner is in - granted, blocking or required tags | `State.Stunned`, `State.Dead` |
| `Event.` | A gameplay event sent to an ability | `Event.Montage.Hit` |
| `Data.` | A SetByCaller magnitude key | `Data.Damage` |
| `Damage.` | A damage type, read by the damage execution | `Damage.Type.Fire` |
| `GameplayCue.` | Every cue tag - the engine's cue pickers offer only this root | `GameplayCue.Damage.Fire` |

- **One name, every place.** The tag segments are the asset name segments: `GA_Weapon_Fire` is
  `Ability.Weapon.Fire`; `GE_Cooldown_Dash` grants `Cooldown.Dash`; `GC_Damage_Fire` plays
  `GameplayCue.Damage.Fire`. Someone holding any one of them can find the rest by search.
- **Add a root only as 4.10 allows** - the list stays short, and every tag has its `DevComment`.
- **A native tag (4.10) is named `TAG_` plus its segments joined by underscores:** `Cooldown.Dash`
  is `TAG_Cooldown_Dash`, declared with `UE_DECLARE_GAMEPLAY_TAG_EXTERN(TAG_Cooldown_Dash)`.

### 25.3 C++ classes

Section 4 applies; GAS adds these shapes:

| Kind | Name | Example |
|---|---|---|
| The project's base ability | `U<Project>GameplayAbility` | `UGameGameplayAbility` |
| An ability | `U<Thing>Ability` | `UDashAbility` - its Blueprint child is `GA_Dash` |
| Ability system component | `U<Project>AbilitySystemComponent` | `UGameAbilitySystemComponent` |
| Attribute set | `U<Domain>AttributeSet` | `UHealthAttributeSet`, `UCombatAttributeSet` |
| Execution calculation | `U<Thing>Execution` | `UDamageExecution` |
| Magnitude calculation | `U<Thing>MagnitudeCalculation` | `UCooldownMagnitudeCalculation` |
| Ability task | `UAbilityTask_<Verb><Thing>` | `UAbilityTask_WaitInteract` |

- **Ability tasks keep the engine's `UAbilityTask_` form**, the one class name here with an
  underscore. Every engine task is named that way (`UAbilityTask_WaitGameplayEvent`), and a project
  task beside them should not be the odd one out in the class picker.
- **Gameplay effects are not subclassed in C++.** An effect is configured as a `GE_` Blueprint;
  logic it needs belongs in an execution or magnitude calculation.

### 25.4 Attributes

> **An attribute is PascalCase - the one member variable besides a delegate that is (4.1).**

```cpp
// NOLINTBEGIN(readability-identifier-naming) - attribute accessors paste the member name (25.4)
UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_Health, Category = "Attributes|Health")
FGameplayAttributeData Health;
ATTRIBUTE_ACCESSORS_BASIC(UHealthAttributeSet, Health)

UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_MaxHealth, Category = "Attributes|Health")
FGameplayAttributeData MaxHealth;
ATTRIBUTE_ACCESSORS_BASIC(UHealthAttributeSet, MaxHealth)

/** Meta attribute: damage waiting to be applied in PostGameplayEffectExecute (9.15). Never replicated */
UPROPERTY(BlueprintReadOnly, Category = "Attributes|Meta")
FGameplayAttributeData IncomingDamage;
ATTRIBUTE_ACCESSORS_BASIC(UHealthAttributeSet, IncomingDamage)
// NOLINTEND(readability-identifier-naming)
```

- **Why PascalCase:** the accessor macros paste the member name into `GetHealth`, `SetHealth`,
  `InitHealth` and `GetHealthAttribute`. A camelCase `health` produces `Gethealth()` - a function
  name that breaks 4.1 on every call site instead of one member that breaks it once.
- **Wrap the attribute block in `NOLINTBEGIN` / `NOLINTEND(readability-identifier-naming)`.**
  `.clang-tidy` cannot tell an attribute from any other member, so the exception is marked where it
  is taken, and nowhere else.
- **A maximum is its own attribute, named `Max` first:** `MaxHealth`, not `HealthMax` - as
  `MaxInventorySlots` in 4.1.
- **A meta attribute is named for what is incoming:** `IncomingDamage`, `IncomingHealing`. It is
  never replicated.
- **Rep notifies are `OnRep_<Attribute>`** (11.6).
- **Attribute table rows are `<SetClass>.<Attribute>`**, the class without its `U`:
  `HealthAttributeSet.MaxHealth`. That is the row name `InitFromMetaDataTable` looks up; any other
  name is silently skipped and the attribute starts at zero.
