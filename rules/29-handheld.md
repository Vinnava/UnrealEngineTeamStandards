# 29. Handheld readiness

Part of the [Unreal Engine Team Standards](../README.md). Section numbers are global; the reasoning
is in [why.md](../why.md).

**Handhelds are not a current target.** Steam Deck, ROG Ally, Legion Go and Switch-class devices are a
planned future one. This section builds nothing for them: it keeps the decisions that are free now and
a rewrite later, so that adding a handheld is a config-and-test task. It applies to every project,
single-platform included - section 28 covers a project that already ships on more than one.

---

### 29.1 Scope

- **Do not build handheld-specific features, profiles or optimisations yet.** No handheld device
  profile, no handheld budget, no handheld code path.
- **13.7's handheld bullet** - thermal steady state, dynamic resolution - applies from the day
  handhelds become a target, not before.
- **When they do, add 29.6** - and nothing in 29.2 to 29.5 should need to change.

### 29.2 Input and text entry

- **No keyboard, mouse or touch requirement anywhere in the game flow** - menus, text entry, login,
  the EULA and every first-run screen included. **A gamepad reaches everything**, on a PC-only
  project too (28.3). Test it with the keyboard and mouse unplugged.
- **Text entry goes through one platform-layer function.** Every text field asks the platform service
  layer (29.3) for text rather than reading a keyboard itself, so an on-screen keyboard plugs in
  behind that function later without touching a screen.
- **Button glyphs always resolve from input data, per device** (12.5, 28.3) - never baked into a
  texture or a widget.

### 29.3 Device knowledge has one home

- **Device detection and device-specific behaviour live only in the platform service layer** - a
  project-owned subsystem (28.2) and per-platform config (9.6, 28.6). **Gameplay never checks the
  hardware**, as it never checks for a gamepad (9.13).

### 29.4 UI layout and scale

- **Layouts are aspect-ratio and resolution independent** - 16:10, 16:9 and wider - built with
  anchors and safe zones (20.5, 28.3). **Never assume 1920x1080.**
- **Keep a UI and text scale setting in the settings system** (20.5), even if it offers one value at
  first. The setting, its storage and every widget that reads it exist from the start; only the range
  grows.

### 29.5 Frame rate, scalability, lifecycle and the build

- **Frame rate is never hard-coded.** The frame cap and vsync are user settings, driven by config and
  scalability.
- **Scalability and device profiles stay data-driven** (9.2, 28.6), so a handheld tier is a config
  addition later, not code.
- **PSO caching is in the build pipeline from the start** (13.5). It helps PC and mobile now and is
  essential on a handheld.
- **Suspend and resume are safe at any moment** - mid-load, mid-save, mid-request - through the
  lifecycle handlers in 28.7, on every platform.
- **Saves follow section 24 unchanged,** 24.8 included. There is no handheld-specific save logic.
- **No middleware, anti-cheat or launcher known to break under Proton or on Windows handhelds.** Check
  before adopting one, and record the check where the dependency is chosen.

### 29.6 When handhelds become a target

Add, as config and test work:

- Handheld device profiles and their budgets, as tiers in `CLAUDE.md` (28.4, 28.6).
- Steam Deck Verified testing.
- Device-specific glyph detection, inside the platform service layer (29.3).
- Frame-cap presets over the user settings in 29.5.
