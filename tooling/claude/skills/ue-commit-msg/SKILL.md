---
name: ue-commit-msg
description: Drafts a commit message in the team format (14.3) for the current change - a system prefix, an imperative summary, a bullet body. Use when the user asks for a commit message or to commit.
---

Draft the commit message for the current change. Read the change first from the project's source
control - `git diff --staged`, or the equivalent for its system (26.3).

```
System: Imperative summary under 72 characters

* What changed, one short line
* Why, when it is not obvious
* What was tested
```

- **Title:** the system the change touches, a colon, then an imperative summary - `Quest: Reset
  transition phase on map arrival`. Under 72 characters.
- **Body:** a `*` bullet list after a blank line - one short line per bullet. No prose paragraphs. A
  one-line change needs no body.
- **One logical change per commit.** If the change holds two, say so and suggest the split.
- **No emoji** (5.5). Add co-author or attribution lines only if the user asks for them.
- **"What was tested" is evidence you have** - the build, the gate, a PIE check the user reported -
  never a test you did not run.

Show the message. Commit only if the user asked you to commit.
