# 20. Accessibility and localisation

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

Both are about players who are not you. Both are cheap when designed in and ruinous when retrofitted,
and both appear in platform certification.

---

### 20.1 This is a requirement, not a polish task

- **Console certification checks several of these.** A title can fail submission on subtitles, on key
  remapping or on a flashing-image violation. Treat a cert item like a crash, not like a nice-to-have.
- **Every item below is decided before the first UI screen is built** (12.6), because each one
  constrains layout.
- **Accessibility options are settings** (9.6), saved with the rest (9.14), and never reset by a
  patch.

### 20.2 Subtitles

- **Every spoken line has a subtitle** (19.7), including barks and incidental lines.
- **Default them on.** A player who needs them should not have to know they exist.
- **Attribute the speaker** when more than one character can talk in a scene.
- **Size and background are player options** - at minimum a size scale and an opaque backing plate.
- **A subtitle is `FText` from a string table** (12.5), never assembled by concatenation.
- **Never let a subtitle depend on audio playback to advance.** If the line is cut short, the
  subtitle still completes or clears; the owner is the dialogue system, not the `UAudioComponent`
  (9.4).

### 20.3 Colour and contrast

- **Colour is never the only channel.** Anything communicated by colour - team, threat, rarity,
  status - also carries a shape, an icon, a label or a pattern.
- **The test:** screenshot the screen in greyscale. If you cannot play from it, it fails.
- **Do not ship a "colourblind mode" that only rotates a palette** where the underlying design
  depends on hue. Fix the channel, then offer the palette.
- **Hold UI text to a contrast ratio** the project writes down; check it against the busiest
  background the text can sit on, not a flat swatch.

### 20.4 Input

- **Every gameplay action is remappable**, on every device the project ships on. Enhanced Input
  supports this natively - mark actions with player-mappable key settings rather than building a
  parallel system.
- **Never hard-code a key name or glyph in text** (12.5). Show the current binding.
- **Nothing requires a rapid repeated press or a simultaneous multi-button press without an
  alternative.** Offer hold-to-confirm in place of mash, and toggle in place of hold.
- **Input timing windows are tunable data** (9.13), not constants - so an accessibility preset can
  widen them.

### 20.5 Text and layout

- **Text scale is a player setting**, and the UI survives it. Fixed-height boxes with text inside
  are the usual casualty (section 16).
- **Nothing player-readable is baked into a texture.** A texture cannot be localised, scaled or
  read by a screen reader.
- **Respect the platform's title-safe area** on console.
- **No text-only critical information where an icon would also serve**, and no icon-only where the
  meaning is not conventional.

### 20.6 Motion, flashing and camera

- **Camera shake, head bob and motion blur each have an intensity setting including zero.**
- **Nothing flashes faster than three times per second** at significant screen coverage. This is the
  photosensitivity rule cert checks; it is also the one that can genuinely hurt someone.
- **Field of view is adjustable** where the project's camera makes that meaningful.

### 20.7 Difficulty and assists

- **An assist option never gates story or content.** Anything that changes only how hard the game is
  - aim assist, damage scaling, slow mode, skippable challenges - leaves the rest of the game intact.
- **Assist settings are changeable mid-session**, not locked at new-game.

### 20.8 Localisation

- **All player-facing text is `FText` from a string table** (12.5). `LOCTEXT` in C++ is acceptable for
  text that genuinely belongs to code; anything a writer edits belongs in a string table.
- **Build sentences with `FText::Format` and named arguments** (12.5). Never concatenate, and never
  assume word order survives translation.
- **Plurals and gendered forms go through the format string**, not an `if`. `FText::Format` supports
  ICU plural and gender selection; a hand-rolled `if (count == 1)` is wrong in most languages.
- **Budget text expansion.** Assume a translated string is 30-40 per cent longer than English, and
  more for short strings. A button that fits its English label exactly is a bug.
- **Never build a key from runtime data.** Keys are authored constants; a key assembled at runtime
  cannot be gathered.
- **Culture-varying assets** - voice, textures with text, culture-specific icons - go through the
  localisation-aware asset path, not an `if (culture)` branch.
- **Dates, times, numbers, percentages and money use the `FText::As*` family** (12.5).

### 20.9 Testing

- **Run a pseudo-localisation pass regularly** - it lengthens strings and marks unlocalised text, and
  it finds concatenation and baked text faster than any review.
- **Lay out against the longest supported language**, not English.
- **Keep an accessibility pass in the pre-ship checklist** (14.5): greyscale screenshot, text scale
  at maximum, every action remapped, subtitles on, motion at zero.
- **Cert requirements differ per platform.** Each target's list lives in the project README with a
  named owner (13.2).
