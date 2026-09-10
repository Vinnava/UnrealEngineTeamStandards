# Why - the reasoning behind the rules

The [rule files](rules/) say what to do. This file says why, section by section, and tells the real
incidents behind them. It is written for people: read it when a rule looks arbitrary, and before you
propose changing one.

Section numbers match the rule files. A section with no entry here needs no explanation beyond the
rule itself.

---

## The pillars and the precedence order

The pillars are **ranked** so that a conflict between two good rules has an answer that does not
depend on who is in the room. The precedence order at the top of the README exists for the same
reason at the document level: when a project rule file and this standard disagree, the question
"which one wins?" should never be settled by habit. An unwritten deviation is a defect because nobody
reviewing the code can tell a decision from an accident.

---

## 1. Project and module structure

**1.1 Modules.** The split is not ceremony. It keeps `HTTP` / `Json` dependencies out of the gameplay
module and makes the wire contract reviewable in isolation. It also limits rebuild scope: a change
confined to the online module's `.cpp` files does not recompile the game module. A change to its
public headers still does - which is why that public surface stays small.

**1.2 Build.cs discipline.** A dependency list nobody can prune is a dependency list that only grows.
The one-line comment is what makes pruning possible later.

**1.3 Source folder layout.** A reader should be able to guess where a class lives from what it
*is*. When nobody can decide where a class goes, the class is usually doing two jobs.

**1.4 Compile-time gating.** An editor module is stripped by the cook as a whole, so editor code in it
can never leak into a shipped build. `#if WITH_EDITOR` blocks scattered through a game module rely on
every author getting every guard right.

**1.5 Plugins and engine changes.** An engine patch is paid for again at every engine upgrade, usually
by someone who did not write it. Undocumented patches are why teams get stranded on old engine
versions.

## 2. Content folder structure

**2.1 One root.** The leading underscore sorts the project root to the top of the Content Browser,
above every marketplace and engine folder.

**2.2 Third-party content.** Reorganising or editing vendor content in place breaks the vendor's
update path and produces enormous redirector churn.

**2.3 No content outside the root.** An asset saved to `Content/` directly, or into a marketplace
folder, gets lost track of. Moving one creates a redirector, which is why the move is a deliberate
change of its own rather than part of unrelated work.

---

## 3. C++ coding standards

**3.1 Header section order.** Diffability and scan speed: being able to read any header in the
codebase the same way is worth more than local cohesion.

**3.2 Never initialise in the header.** An inline default in a header and a constructor assignment
can disagree, and the header value is the one that is easy to miss in review. One place for defaults
means one place to look. The constructor also runs for the class default object at editor startup,
when there is no world - which is why world or asset access there breaks, and why
`ConstructorHelpers::FObjectFinder` slows editor startup for every class that uses it.

**3.3 UPROPERTY categories.** The distinction is authored versus observed: anything you *set* is
`Initialize`, including debug switches; anything you only *watch* is `Runtime`. Clamps and units mean
a designer cannot enter an invalid value, and the Details panel shows what a number means.

**3.4 Pointers and includes.** Relying on a transitive include is a build break waiting for someone
else's refactor. `IsValid` matters because an actor that has been destroyed is still non-null until
the garbage collector runs.

**3.5 Soft vs hard references.** An accidental hard reference in a widely-included header pulls a
large slice of content into memory at load, and the cost does not show up anywhere obvious. The
`IsValid()` trap in section 16 is the single most common soft-pointer bug.

**3.7 General quality bar.** A component ticking for the life of the game to check a bool is a real
cost at scale. Requiring approval for Tick turns a vague preference into a review step. A five-level
actor hierarchy is a refactor you will not be able to afford later.

**3.8 Object lifetime.** The garbage collector only knows about references it can see. A raw member
pointer is invisible to it: the object can be collected underneath, and the pointer still reads
non-null. A rooted object is never collected, and nothing records who rooted it or why. A `UObject` in
a `TSharedPtr` has two owners - the GC and a reference count - that do not know about each other.
Renaming a class or property orphans every asset that saved the old name, and a default subobject's
name is its saved identity.

**3.9 Assertions.** A crash in Shipping is worse than a missing feature, which is why `ensure` is the
default. Logic inside `check` disappears in Shipping along with the check.

**3.10 Formatting.** Braces on their own line are Epic's style and the style of every example here.
Everything else is left to a tool, because formatting enforced by memory is not enforced.

**3.11 Lifecycle.** `OnConstruction` re-runs every time the actor is edited in the editor, so it must
be safe to run repeatedly. An unregistered runtime component simply does nothing. `Destroy()` only
marks an actor; until GC runs, the pointer still looks valid to a null check.

**3.12 Tick.** A tick costs something before your code runs - the dispatch itself, per actor and per
component, and one NPC is often ten tick functions. That is why most tick fixes are deletion rather
than optimisation. Without staggering, a thousand actors on the same interval all fire on the same
frame and produce a spike.

---

## 4. C++ naming conventions

**4.1 The core table.** camelCase members are a deliberate deviation from Epic, held consistently
across every project on this team - consistency within our code is worth more than matching the
engine's.

**4.2 Booleans.** A double negative in an `if` is a bug waiting to happen.

**4.3 Verb vocabulary.** A reader should be able to guess what a function does from its first word.
Mixing `On` and `Handle` makes a delegate graph unreadable.

**4.4 Class names.** Inconsistent use of a project infix is worse than none, because it stops meaning
anything.

**4.5 Enums.** The explicit `uint8` matters for serialisation size and for Blueprint exposure. The
enumerator-0 rules were learned the hard way: a wire enum needs 0 free so "field absent" stays
representable; a behaviour enum's 0 must be inert so a half-authored data row can never latch active
state; an outcome enum's default should never blame the player for something they did not do.

**4.6 Structs.** Reflected fields are zeroed only when the engine allocates the struct - inside a
`UObject`, a `TArray` property, a DataTable row. A struct you declare as a local holds garbage. The
types-only-header exception exists because the point of 3.2 is one place to look for defaults, and a
constructor body satisfies that wherever it lives.

**4.7 Delegates.** Dynamic delegate parameter names become Blueprint pin labels - a designer reads
them. A context struct means a new field never breaks an existing listener. Choosing the wrong
delegate kind is the most common new-developer bug in Unreal.

**4.8 Short names.** Readable beats short.

**4.9 File naming.** Shared type-only headers let two systems share a shape without depending on each
other's classes.

**4.10 GameplayTags.** A flat sprawl of unrelated roots is as bad as no tags. A tag with an empty
`DevComment` is one nobody else can safely reuse, and you end up with three tags meaning the same
thing. A tag is a content-side addition; an enum is a code change. `RequestGameplayTag` with a literal
turns a typo into a silent no-match.

**4.11 Console commands.** They cost an hour to write and save days of clicking through content to
reach the state you need to test. A leaked `IConsoleCommand` outlives its subsystem and fires into a
dead object.

---

## 5. Comment standard

Comments are enforced as strictly as code because a codebase carries non-obvious decisions that
nothing else records.

**5.1** A comment that repeats a trivial accessor's name is exactly the self-evident comment 5.3 bans.

**5.2** Reasoning that needs more than two lines belongs in a design doc, where it can be read in
full. The class-level block is allowed to be longer because it documents a contract rather than a
line of code.

**5.4** Documentation decays unless it is repaired, so repair is planned. It is not done as a
drive-by because a real edit should not hide inside cleanup noise.

**5.5** `U+FFFD` is a mojibake artifact, not content. Encoding corruption spreads silently through a
codebase once it is committed once. Commented-out code is noise; git remembers.

---

## 6. Logging standard

Logging is the only debugging instrument you have on device, in a packaged build and over remote
streaming - anywhere a debugger cannot attach. Treat log lines as a deliverable, not as scaffolding.

**6.1** A line that says "failed" without saying what, where and with what input is not a log line;
you will read it at 2am and learn nothing. A log line is most often written exactly when something is
null, which is why `GetNameSafe`. A number in a log goes stale the moment its enum is edited; a name
does not.

**6.2** The point of a category is filtering the Output Log down to one system. A static category is
one line, file-local, and needs no header - right for the overwhelming majority, because one system
is usually one `.cpp`.

**6.3** A silent recovery is a bug you will meet again later with no evidence.

**6.5** Token names in `UE_LOGFMT`'s positional form do nothing, so reordering the arguments compiles
and lies - exactly as with `UE_LOG`. Converting a file's logging as part of an unrelated change is
diff noise hiding a real edit.

**6.6** A silent `return` on a failure costs an hour to find. A guard that fires every frame by design
is not news. Authored-data errors otherwise surface at runtime as "a thing that never appears", which
reads as a missing feature rather than bad data.

**6.7** This is the highest-value logging you will write. Bad authored data fails silently by
default; a validation pass converts a mystery into a line in the log. The editor check catches it
before anyone presses Play; the runtime pass catches data that only goes wrong in combination.

---

## 7. Blueprint and content naming

**7.1** A prefix that is sometimes one thing and sometimes another cannot be searched for. Where the
community uses two, we pick the one that matches our C++ convention.

**7.3** Spaces break command-line tooling and cook paths. A `BS_Idle_Walk_Run_1` next to
`BS_Idle_Walk_Run` is a decision nobody made. Git holds history; the asset name holds identity.

**7.4** A `BindWidget` member has to match the widget's object name, which is why it is the one member
name with an underscore.

**7.6 Why this is strict.** Asset names are effectively permanent. A rename creates a redirector,
rewrites a binary file and risks breaking every reference - so in practice, misspellings and vendor
names survive to ship. Real damage from projects this team has worked on:

- One character with four spellings across 69 assets, because the first import had a typo and every
  later asset copied it.
- "Circle" misspelled two different ways in the same UI folder.
- A folder name misspelled in the core content path, permanently.
- Vendor names in the shipping tree - tool exports, stock-site downloads, scratch geometry names.
- Maps inconsistently prefixed, so half the level list sorts away from the other half.

---

## 8. Blueprint discipline

**8.1** Rules must be correct, testable and diffable, which Blueprint graphs are not. The gameplay
half of the split is a default because it suits a designer-heavy team; choosing per feature would give
a project two architectures. A `BlueprintPure` node is re-evaluated for every pin that reads it. A
`.uasset` cannot merge, so Blueprint logic is effectively single-writer.

**8.2** Iterating in Blueprint is faster than iterating a header, and finding out a design is wrong is
cheaper there. But a prototype indistinguishable from shipping content becomes shipping content by
accident; "left in because it works" is how a codebase acquires a second, undocumented architecture;
one layer of scaffolding is a prototype, two is a system nobody designed; and temp assets outlive
their intent more often than not, with an unprefixed one the hardest to find later. Debug actors may
stay because their job is permanent.

**8.3** A graph with no comment boxes is unreviewable; if you cannot read it, neither can the next
person. `Cast To BP_X` loads `BP_X` and everything it references. A surprising dependency chain is
easier to see in the Reference Viewer than to debug later.

---

## 9. Architecture rules

**9.1** A Desktop/Mobile split differs in layout, input model and hit targets, and retrofitting it is
far more expensive than starting with it. GameMode is destroyed on map load, so anything caching it
dies with it - but match rules are per-map and server-only by nature, which is why GameMode still owns
them.

**9.2** These rules exist because content always grows faster than code. A `switch` on identity makes
every new case a code change in a file unrelated to the new content. An enum-keyed map was never
content-only - adding a case is already a code change - and it carries the serialisation hazard in
section 16 for nothing. The second one of anything always arrives; if adding it touches C++, the first
was built wrong.

**9.3** Mixing delegate kinds does not compile, which is the one merciful part. A dangling bind on a
destroyed object is a crash you will reproduce once a week. A delegate cannot see a raw `[this]`
capture, so it fires into a dead object.

**9.4** Two paths that can both advance the same state produce restart loops that are extremely hard
to reproduce.

**9.6** `Saved/Config` winning over every other layer is the usual cause of "works on my machine".

**9.7** `Cast<IInterface>` returns null for a Blueprint implementation because there is no C++ vtable
to cast to, and a direct call on a cast pointer skips the Blueprint implementation.

**9.8** Each layer can be tested on its own, and new modifiers slot in without changing signatures.

**9.9** If a behaviour exists only in a `Do*` handler, the AI cannot use it and the player's version
cannot be tested without input.

**9.10** Unreal already has native forms of most patterns; inventing a second form of one splits the
codebase. Pooling anything that is not numerous and short-lived is complexity with no payback.

**9.11** Who owns it and how long it lives are the two questions every framework class answers. When
the answers disagree, you are looking at two pieces of state.

**9.12** A World subsystem without a world-type filter spawns into editor previews and thumbnail
worlds. Initialisation order left to luck changes between machines and builds.

**9.13** Movement bound to `Started` moves for exactly one frame - the classic Enhanced Input bug.
`SetMovementMode` from input is invisible to the server on a networked project.

**9.14** Players skip versions, so migrations must chain. A saved pointer means nothing on the next
load. A migration never run against a real old save is a hypothesis.

**9.15** GAS has a steep ramp and a large commitment; the middle path keeps the option open.

---

## 10. Async and threading

**10.1** The garbage collector, the `UObject` registry and every `UPROPERTY` pointer are not
thread-safe. A data race is nondeterministic everywhere - it never fails on demand, in any
configuration. Tighter optimisation and different thread timing make a latent race surface later, not
never, so passing a test pass is not evidence. `check(IsInGameThread())` costs nothing in Shipping and
turns a rare, unexplainable crash into an immediate, obvious one.

**10.2** The object can be collected between the lambda being created and the lambda running. A raw
pointer then passes a null check and reads freed memory - a use-after-free that typically does not
crash at the point of the bug, and often not at all until the allocation is reused. An address
sanitiser catches it; ordinary testing frequently does not. `[&]` is the same bug with none of the
warning signs. Between two `.Get()` calls on a weak pointer, the answer can change.

**10.3** `LoadSynchronous()` on the Game Thread stalls the frame for the whole I/O, and on a cold
cache that is not a small number. Dropping the streamable handle releases your reference, so the
asset can be collected the same frame. A hitch is almost always a load that started when the asset
was needed.

**10.4** `.Then()` runs on an unspecified thread, so a continuation chain ends up hand-writing the same
marshalling step with an extra layer of indirection. If a worker needs a lock, the snapshot was too
narrow. A pipe beats a mutex because nobody waits and it cannot deadlock. A thread firing into a
destroyed subsystem is an intermittent crash with a stack trace that points nowhere near the cause.

**10.5** Every deferred callback is the same class of bug as an async lambda: something fires later,
into an object that may be gone.

**10.6** The thread-safe update is safe precisely because it only reads the copies the game-thread
update made. Animation is usually the largest line on the game thread.

---

## 11. Networking and replication

**11.1** Retrofitting replication is a rewrite, not a feature: authority checks, RPC boundaries and
replicated state change who owns every piece of state. Guarding a state change with `HasAuthority()`
costs one line and is a no-op in standalone. Code that is authority-aware in some places and not
others is worse than code that is consistently neither.

**11.2** A client writing replicated state directly works silently in single-player PIE and fails
silently on a dedicated server - the worst failure mode there is, because the code that is wrong is
the code that tested fine. A subsystem has no network role, which is why authoritative state goes
through an actor.

**11.3** With auto-registration on, a property you meant to be owner-only quietly replicates to every
client; with it off and no ensure, the client holds its constructor default forever. Turning the
ensure on makes a missing registration loud. The engine matches `OnRep_` by declared name, and a
reader needs to see which property fired it. A door opened by a multicast is closed for everyone who
joins later. Anything replicated is in the client's memory and readable there.

**11.4** The reliable buffer can overflow and disconnect the client. Without `WithValidation` there is
no validation step at all - the RPC executes with whatever arrives over the wire. A reliable stream
stalls behind one lost packet.

**11.5** The 100 Hz default is the most common replication performance leak in multiplayer projects,
and nothing warns about it. `NetUpdateFrequency` moved behind accessors during UE 5, which is why an
older sample that assigns the member may not build. `bAlwaysRelevant` opts an actor out of culling for
the whole session. A dormant actor changed without a flush leaves server and clients disagreeing
forever, silently.

**11.6** Nothing else at the call site tells you where an RPC runs. A codebase with both
`ServerFoo` and `Server_Foo` is one where nobody can grep for either.

**11.7** Single-process PIE shares statics and hides a whole category of bug. A listen server is both
authority and client, so it masks missing `OnRep_` calls and missing authority checks. Prediction bugs
are invisible at 0 ms. `stat net` shows a 100 Hz actor long before a player reports it.

**11.8** Push model means the server compares only properties you marked, instead of every property on
every update. Iris changes how replication is configured and prioritised, not its rules.

**11.9** Capturing a move without restoring it is an intermittent desync that LAN testing never shows.
Server-side rewind moves the unfairness to the victim: with it, "I was shot around a corner"; without
it, high-ping players cannot hit anything.

---

## 12. UMG and Slate

**12.2** Each wrapper is an extra layout pass and another place for alignment to go wrong. A property
you set that does nothing is worse than one you did not set.

**12.3** The other developer needs to know about layout bugs you found.

**12.4** Engine widget internals are private layout and change between versions (see the real case in
section 16).

**12.5** Only `FText` is gathered for localisation. Word order changes between languages, so
concatenated sentences cannot be translated. Culture-aware formatting is the only way numbers, dates
and currency read correctly everywhere.

**12.6** The moment a widget holds authoritative data, the UI becomes the hardest part of the codebase
to change. UMG property bindings are evaluated every frame, usually to find nothing changed. `Hidden`
still pays for layout. An `InvalidationBox` around animated content is strictly slower. Every
world-space widget is its own render target. Without `CommonGameViewportClient`, Common UI's input
routing silently does nothing; without a desired focus target, gamepad users get a screen with nothing
selected.

---

## 13. Performance and platform

**13.1** "It runs fine on my 4090" is not a result. An unused Mobile widget tree is maintenance cost
with no user.

**13.2** Frame rate is a reciprocal and misstates severity - "we lost 15 fps" is 1.2 ms at 120 fps and
11 ms at 45. A Development editor build is a different program, and PIE can rank the stages in the
wrong order, not merely inflate them. 340 calls of 6 microseconds is an algorithm problem no
micro-optimisation fixes. A budget line with no owner is a wish. Problems that only appear in a cook
are the expensive kind, and they compound the longer you wait.

**13.3** An asset reached only through a soft path or a string is not cooked: it exists in the editor
and is absent in the build. Chunking cannot be retrofitted. Cook-only bugs exist nowhere else.

**13.4** A project comfortably under its byte budget can still hitch every few seconds because it has
too many objects. One `memreport` is usage; two are the answer; an editor report includes the editor.
Untagged memory has no budget line and no owner. A `UObject` held alive by a forgotten reference is
correctly tracked memory, so allocation tools cannot see the leak. The classic pool bug is the one
field nobody remembered to reset. On PC, VRAM overcommit degrades into erratic GPU time rather than
crashing.

**13.5** A hitch is one frame that did a second's work, and players remember the freeze long after
they forget the average frame rate. The cause is often in the frame *before* the spike. 300 spawns in
one frame is a freeze; 30 a frame for ten frames is invisible. Fixing pop-in by blocking trades a
visual bug for a freeze, which then gets reported as a different bug.

**13.6** An uninstrumented codebase profiles as one enormous anonymous block called `TickActors`.
Instrumentation is a permanent, near-free vocabulary that makes every future capture legible.

**13.7** Material cost is instructions x pixels x layers, so the expensive material is rarely the
complicated one - it is the cheap one covering the screen twice. Ten static switches produce 1,024
variants of one material. Wrong bounds defeat every culling stage at once. A handheld benchmark
improves for ninety seconds, then stops telling you anything true.

**13.8** Server cost scales with the product of actors and connections, which is why a game is fine at
four players and unplayable at sixty-four. A replicated property costs a comparison per connection
per tick whether or not it changed. Nothing is off-screen to a server.

**13.9** Manual profiling finds problems that already shipped into the branch; an automated gate names
the commit that caused them while its author still remembers it. A warning is ignored by week three,
and a gate that noise can trip is a gate nobody trusts. A trend catches the 0.3 ms a week that no gate
does. An optimisation with no recorded justification can never be removed, because nobody can prove
it does anything.

---

## 14. Working style

**14.1** A fix applied to a symptom you have not explained will come back. A fixed `CONFLICT` format
makes a conflict reviewable and hard to skip. A pattern nobody else understands is a liability
regardless of whether it is correct. Existing code is evidence someone wrote it, not evidence the team
understands it.

**14.2** The right amount of work to hand an assistant is set by how well you understand the plan, not
by the size of the task. The point of going one file at a time is the stopping: a wrong direction
caught at file one costs a conversation; caught at file twenty it costs the whole change. Stopping
every file when you already understand the plan is pure overhead, and twenty small diffs are harder to
review than one coherent change. "The AI wrote it" explains nothing in a review or a post-mortem, and a
large diff you did not understand is debugging deferred to a worse moment.

**14.3** Moving assets into LFS later rewrites history. Binary assets cannot be merged, so without a
lock the second person's work is lost. Binary assets diverge on long branches and cannot be merged
back.

**14.4** Functional tests are slow and brittle; logic tests are cheap and precise.

**14.5** A gate that does not fail the build is theatre. A crash without symbols is a list of hex
addresses. Telemetry only works retroactively, so it has to exist before you need it. The editor is
not your game.

---

## 15. Debugging playbook

**Item 1.** The failure is silent - stale reflection data, so the thing you just wrote behaves as if it
does not exist. Deleting `Intermediate/` and `Binaries/` is slow and almost never the fix.

---

## 16. Known engine traps

Every entry is an engine-level behaviour, not a project quirk, and every one fails silently - that is
the bar for the list. Entries marked *(real case)* are incidents this team shipped and then had to
find; the rest were documented before they cost us anything. None are invented.

**Cosmetic fade callbacks.** A transition phase reset only inside a loading widget's
`OnFadeOutComplete` never fires: that callback rides the widget's `NativeTick`, and a hard map load
drops the widget from the viewport so it stops ticking. The phase sticks non-Idle forever,
`IsTransitioning()` returns a permanent false positive, and the *next* transition wedges.

**Persistent overlays.** After a hard `OpenLevel` the GameInstance-owned widget object survives and
`SetRenderOpacity` still applies, but nothing is drawn - `IsInViewport()` is false in the new world. The
subsystem timer works because the subsystem persists across the load and the new world's timers tick
reliably.

**Stale widget references.** A cached pointer to a widget from the outgoing world passes a null check
and then does nothing.

**World timers.** Anything armed on a world timer that conceptually survives the load latches its state
for the rest of the session unless resolved on arrival.

**Faking `GetVelocity()`.** Movement, network prediction and everything else that reads the movement
component still see zero, so the override only hides the bug from the AnimBP.

**Montage end delegates.** Without auto blend-out, any listener waiting on the end delegate parks
forever.

**`EditInstanceOnly` on spawned actors.** A spawned actor has no level instance, so a per-instance
property has nowhere to receive a value.

**Enum-keyed maps** *(real case)*. A background-texture map was authored against a six-value enum.
Removing one enumerator left one row null and two rows pointing at the wrong asset. The UI rendered
solid white in PIE while the editor showed all five entries assigned - the details panel re-labels
whatever bytes it finds, so the map still read as a complete, sensible list. Properties serialise by
name and survive any enum edit, which is why named fields are the fix.

**`TSoftObjectPtr::IsValid()`** *(real case)*. A contact-photo field: contacts the player had opened
elsewhere showed a photo; contacts they had not showed the authored blank brush. It surfaced first in
a search view - the one place that lists people you have never visited - and read as missing content
rather than a missing load. `IsValid()` returns false for every assigned-but-unloaded reference, so the
guarded load only ever succeeded when something else had loaded the asset first.

**Wire enums with a real zero.** `TryGetField` and friends leave the output untouched on a miss, so
the enum's default *is* the "field not present" value.

**Inactive switcher slots** *(real case)*. A scroll box measured zero from `NativeConstruct`; a
10-attempt resolve gave up roughly 1.1 seconds before the player ever opened the panel, so the
row-width clamp it computed was never applied in any session. The only symptom was a give-up warning
nobody connected to the visual. The switcher arranges only its active child, so an inactive child is
constructed but never laid out - no retry can outlast that.

**Fading.** `SetColorAndOpacity` pushes a tint down into child brushes, and a material that ignores the
incoming Slate colour (a video surface) will not fade. `SetRenderOpacity` is a composited alpha
multiply on the widget's draw output.

**Walking engine widget children** *(real case)*. A custom text box walked `GetChildren()` expecting
`SBorder -> SScrollBox -> FSlot`, and silently early-returned for the entire life of the feature.
`SMultiLineEditableTextBox` **is** an `SBorder` (it calls `SBorder::Construct` on itself), so child 0
was already the content and the walk skipped a level; and its subtree contained no `SScrollBox` at
all. The padding it existed to apply never took effect once.

**`OnKeyDownHandler` ordering.** The inner editable text holds keyboard focus and runs the handler
first, only falling through to its own layout when the handler returns Unhandled.

**`SizeBox` and line height.** `SBox` computes its desired size as `Min(child, max)`, then arranges a
`VAlign_Fill` child at the *allotted* height - so the text wraps and grows, but every line past the
first exists only inside the box's own scroll offset. Padding derived as `(barHeight - fontSize) / 2`
is wrong because a line is taller than its font (a 15pt face measures around 20px); one line then
wants more height than the clamp allows, and an internal scrollbar appears permanently. Deriving both
numbers from one measured line height means they cannot drift.

**Weak pointers off the Game Thread.** Resolution reads the engine's object-validity table, which the
garbage collector mutates. The window is small - which is the problem: it survives every test pass and
fails in a long session.

**Callbacks after PIE stops.** A load in flight when the user hits stop delivers its callback into a
world that no longer exists; the object can outlive its world.

**Streaming sub-levels.** Code expecting a sub-level's actors immediately after
`LoadLevelInstanceBySoftObjectPtr` finds an empty world.

**`ReplicatedUsing` on the host.** On a listen server this reads as "the effect works for everyone
except the host".

**`bReplicates` timing.** Miss the window with `SetReplicates()` and the actor simply never
replicates, with no warning. The constructor is the one place the ordering cannot be wrong.

**`BeginPlay` starting values.** A value assigned in `BeginPlay` can land after the first replication
packet, showing as a one-frame flicker or a client that holds the pre-assignment value for the rest of
the session.

**The CDO trap, networked.** It is harder to spot than the non-networked version because the actor
otherwise appears to work.

**Overlaps.** The collision responses can look perfectly correct while one component's
`bGenerateOverlapEvents` is off.

**Enhanced Input hold actions.** Bound only to `Started`, a hold begins and never ends; bound to
`Triggered`, it fires every frame while held.

**`FDateTime` formatting** *(real case)*. `"%d %b %Y"` passed through `ToString` rendered **"27 b
2026"** on screen. It looked like a data bug, not a format bug. Both functions end their token
`switch` with `default: AppendChar(*Format)`, so an unrecognised token is emitted as its own literal
character, with no warning - which is why every format string is verified in PIE.

---

## 17-18. Checklists

**18.** Retrofitting replication later is a rewrite, and a half-answer produces code that is
authority-aware in some places and not others. A canonical-examples list points at working code, which
beats describing it, and stands in for the invented class names used throughout the rule files.
