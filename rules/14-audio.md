# 19. Audio

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

Audio naming lives in 7.1. This section is the architecture.

---

### 19.1 Nothing plays a sound by reaching for an asset

**Gameplay code states intent; the audio layer decides what that sounds like.** A component asks for
`Footstep.Stone`; it does not hold a `USoundBase*` and call `PlaySoundAtLocation`.

- **One audio component or subsystem owns playback for a domain** - footsteps, UI, weapons, ambience.
  Gameplay calls it with a tag and a context, never with an asset.
- **A `USoundBase` hard reference in a gameplay class is a defect** (3.5). The asset lives in a
  DataAsset the audio layer owns, keyed by tag (9.2).
- **No `switch` on surface, material or state to pick a sound.** A tag-keyed map in data (9.2).
- **The test:** an audio designer changes every footstep in the game without a compile.

### 19.2 MetaSounds and Sound Cues

- **New work is a MetaSound.** Sound Cues are supported and fine where they already exist - do not
  migrate on principle (the same rule as Behavior Trees, 9.15).
- **Randomisation, pitch variation and layering live in the MetaSound**, not in C++ and not in
  Blueprint. Code triggers; the asset decides how it varies.
- **A MetaSound parameter is an input, not a second code path.** Drive intensity, material and
  distance as parameters rather than picking between assets in gameplay.

### 19.3 Concurrency is mandatory

> **Every gameplay sound belongs to a concurrency group with a voice cap.**

An uncapped one-shot is the most common audio bug in Unreal: twenty impacts in one frame become
twenty voices, the mix collapses, and the platform's voice limit starts stealing whatever it likes.

- **Set the cap and the resolution rule** (`StopOldest`, `StopFarthestThenOldest`,
  `PreventNew`) per group, deliberately.
- **Cap per-sound, per-owner and globally** where the sound can come from many actors at once.
- **The cap is a design number, not a guess** - it is written in the audio budget (19.9).

### 19.4 Attenuation, submixes and mixing

- **Every world sound has an attenuation asset**; none carries hand-tuned per-instance radii.
- **Share attenuation assets by role** - `ATT_Footsteps`, `ATT_Weapon_Medium` - never one per sound.
- **Volume balance lives in Sound Classes and submixes, never in per-call volume multipliers.** A
  multiplier at a call site is how a mix becomes unbalanceable.
- **Ducking is a Sound Mix**, pushed and popped by the system that owns the moment - dialogue,
  cinematics, pause. One owner per mix push (9.4), and every push has its matching pop.
- **Occlusion and reverb cost real time.** Enable them per attenuation asset where they matter, not
  globally.

### 19.5 Loading

- **Audio is soft-referenced and streamed** (3.5, 10.3). A character Blueprint that hard-references
  every line of its dialogue pulls all of it into memory on spawn.
- **Mark long assets for streaming**; keep short, frequent one-shots resident.
- **Load a scene's audio with the scene**, through the same preload moment as its other assets
  (10.3).

### 19.6 Sound that follows gameplay state

- **An animation notify is a cosmetic trigger, never a state owner** (9.4, section 16). A footstep
  notify may be skipped by a blend-out; a sound that must happen is driven by the code that owns the
  event.
- **A looping sound has exactly one owner** that starts it and stops it, and stops it in the same
  teardown that unbinds delegates (10.5). A loop surviving its owner is an audible leak.
- **Stop by handle, not by asset.** Store the `UAudioComponent` you started.
- **Sound follows the actor, not the socket, unless it must** - attached components cost more than
  fire-and-forget one-shots at a location.

### 19.7 Dialogue

- **Every spoken line has a subtitle** (20.2). No exceptions, including barks.
- **Dialogue is data** - a DataAsset or DataTable row carrying the line, its audio, its subtitle text
  and its speaker - never a hard-coded pairing in a Blueprint.
- **Dialogue audio is localised alongside its text** (20.8). A line that ships in one language only
  is a content bug, not an audio bug.

### 19.8 Debug and instrumentation

- **A subsystem that owns audio is instrumented like any other** (13.6).
- **Know these:** `stat audio`, `au.Debug.Sounds 1` for the active voice list, `au.3dVisualize.Enabled 1`
  for spatialisation, and the Audio Insights panel in 5.x.
- **Read the voice count before the CPU time** (13.2, "read the count before the time").

### 19.9 Budget

- **The project README carries an audio budget**: concurrent voices, memory, and CPU on the audio
  thread, per target platform, with a named owner (13.2).
- **Mobile is the binding platform** (13.1) - voice counts there are a fraction of desktop.
- **Audio is in the regression gate** (13.9) when the project has a voice budget worth defending.
