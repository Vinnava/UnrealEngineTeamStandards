---
name: ue-async
description: Team rules for async and threaded Unreal code (section 10) - the game-thread rule, lambda captures, async asset loading, UE::Tasks and ParallelFor, timers, AnimBP thread-safe update, stale results, locks, and when to thread at all. Use before writing or changing anything that runs later, elsewhere or on another thread - a timer, a delegate binding, a lambda that outlives the frame, an async load, an HTTP callback or a task.
---

The always-loaded gate (17.1) already holds the three async safety items. This is the full section:

{{INCLUDE rules/10-async.md}}
