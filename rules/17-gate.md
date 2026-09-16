# 17. Pre-commit checklist - the gate

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**This is the file to keep loaded.** Twelve items, run on every commit. The full review list is
[17-review.md](17-review.md) and is read at review time, not at commit time.

---

## 17. Pre-commit checklist

### 17.1 The gate - twelve things

**Run this on every commit.** These twelve are here because no tool catches them and because getting
one wrong is expensive to undo later. Everything else has either a tool (17.2) or a reviewer (17.3).

- [ ] **You did an editor-closed build** if you touched a header, a delegate declaration, a
      constructor default or a new class - and regenerated project files for a `.Build.cs` change
      (15, item 1)
- [ ] **You played it in PIE.** Compiling is not testing
- [ ] **If an assistant wrote any of it, you read every line** and you can explain it (14.2)
- [ ] **Any conflict with a pillar or a rule was raised in a `CONFLICT` block before the code**, and
      answered (14.1)
- [ ] **The new state has exactly one owner** - you did not add a second path that completes it (9.4)
- [ ] **Adding the *second* one of this thing is a content change, not a code change** (9.2)
- [ ] **Every `UObject*` member is a `UPROPERTY` or a `TWeakObjectPtr`**, and every lambda that
      outlives the frame captures weak - never raw, never by reference (3.8, 10.2)
- [ ] **Teardown mirrors setup exactly** - every timer stored and cleared, every delegate unbound,
      every handle cancelled (9.3, 10.5)
- [ ] **Nothing touches a `UObject` off the game thread**, weak-pointer resolution included (10.1)
- [ ] **Every replicated state change is authority-gated and every `Server` RPC validates** - if the
      project replicates (11.2, 11.4)
- [ ] **Every new hard reference is deliberate**, and you looked at the Reference Viewer and Size Map
      before committing content (3.5, 8.3, 13.3)
- [ ] **Player-facing text is `FText`**, and anything new a player reads or hears has its subtitle and
      accessibility consequence handled (12.5, 20.2)
