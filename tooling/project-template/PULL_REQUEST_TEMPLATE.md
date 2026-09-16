<!--
Project pull request template - standard 18.2. Copy to .github/PULL_REQUEST_TEMPLATE.md.

This list is deliberately short and deliberately not 17.2. It carries only what no tool can check:
if clang-format, clang-tidy or a validator can catch it, it does not belong here (17.4).
-->

## What and why

<!-- What changed, and the reason. Link the issue or the decision. -->

## Conflicts raised

<!-- Any CONFLICT block from 14.1, and the answer it got. "None" is a valid answer. -->

## Checks a tool cannot do

- [ ] **Editor-closed build** if a header, delegate, constructor default or new class was touched;
      project files regenerated for a `.Build.cs` change (15, item 1)
- [ ] **Played in PIE** - compiling is not testing
- [ ] **Header section order** is right: variables before functions, within each access level (3.1)
- [ ] **Comments explain why, not what**, and earn any line past the second (5.2, 5.3)
- [ ] **The new state has exactly one owner** - no second path completes it (9.4)
- [ ] **Adding the second one of this thing is a content change, not a code change** (9.2)
- [ ] **Teardown mirrors setup** - timers cleared, delegates unbound, handles cancelled (9.3, 10.5)
- [ ] **Every new hard reference is deliberate**; Reference Viewer and Size Map checked (3.5, 13.3)
- [ ] **If an assistant wrote any of it, I read every line and can explain it** (14.2)
- [ ] **Any deviation from the standard is written in `CLAUDE.md` as an override**, with its section
      number and reason - not left unwritten (00-core)

## Which pillar does this serve

<!-- 1 separation of concerns, 2 loose coupling, 3 data-driven, 4 event-driven. If it fights one,
     say which and why the higher-ranked pillar still wins. -->
