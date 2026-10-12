---
name: ue-conflict
description: Writes a CONFLICT block (14.1) when a request conflicts with a pillar, a rule or the existing architecture, then stops for an answer. Use before writing any code that would break a rule.
---

A request conflicts with the standard or the architecture. Do not write the code. Write the block
14.1 defines and wait for a written answer:

```
CONFLICT
Rule:      <pillar or section, e.g. Pillar 2 / 9.4>
Existing:  <what the code or design does now>
Requested: <what the change needs>
Options:   A) <approach> - <trade-off>
           B) <approach> - <trade-off>
Recommend: <A or B, and why>
```

- **Name the section, and read it first.** A conflict against a rule you have not read is a guess.
- **The pillars are ranked** (00-core): when two rules pull apart, the higher pillar decides - say
  which pillar the recommendation serves.
- **Give real options.** One of them may be a written project override in `CLAUDE.md`; another may be
  changing the standard itself, if the rule is wrong (README, "Changing this standard").
- **Stop after the block.** The answer decides the code.
