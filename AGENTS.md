# Galaxy Watch 8 Holiday Watch Face (WFF v4) — AI Agent Rules (`AGENTS.md`)

This repository builds a standalone, zero-Kotlin **Samsung Galaxy Watch 8** holiday & custom-photo watch face targeting **Wear OS 6 (API 36) / Watch Face Format (WFF) v4**.

## Built-In AI Skills & Agent Workflows (`.agents/`)

AI coding assistants (Antigravity, Claude Code, Cursor, Codex, GitHub Copilot) should consult the specialized skills in `.agents/skills/` before editing assets, simulator code, or WFF XML:

- [`.agents/skills/wff-custom-assets/SKILL.md`](.agents/skills/wff-custom-assets/SKILL.md) — Replacing centerpiece pet/family portraits (`tools/set_custom_art.py`), regenerating crisp `4x`-supersampled WebP drawables, and synthesizing burn-in-safe AOD outlines.
- [`.agents/skills/wff-watch8-simulator/SKILL.md`](.agents/skills/wff-watch8-simulator/SKILL.md) — Maintaining 1:1 browser preview parity in `html/index.html`, `html/styles.css`, and `html/simulator.js` (`file://` compatible, zero server required).
- [`.agents/skills/wff-apk-builder/SKILL.md`](.agents/skills/wff-apk-builder/SKILL.md) — Editing `watchface/app/src/main/res/raw/watchface.xml`, running the 4-stage optimizer (`./optimize_watchface.sh`), validating against Google/Samsung WFF v4 XSDs, and sideloading via Wireless ADB.
- [`.agents/agents/watchface-customizer.md`](.agents/agents/watchface-customizer.md) — Ready-to-invoke subagent persona for end-to-end watch face customization tasks.

## Core Architecture: Dual-Stage 1:1 Parity

1. **Stage 1 — Interactive Galaxy Watch 8 HTML Simulator (`html/`):**
   - Strictly uses the **WFF `450 × 450` virtual coordinate system** (`clipShape="CIRCLE"`), scaled dynamically to physical Galaxy Watch 8 screen presets:
     - **Watch 8 44mm:** `480 × 480 px` (1.47" Super AMOLED)
     - **Watch 8 40mm:** `438 × 438 px` (1.34" Super AMOLED)
     - **Watch 8 Classic 46mm:** `438 × 438 px` (1.34" Super AMOLED + rotating bezel ring)
   - Every element, complication slot, pivot, expression, and animation in `html/` must remain 100% expressible in **Watch Face Format v4 XML**.

2. **Stage 2 — Native Watch Face Format APK (`watchface/`):**
   - Pure declarative XML (`android:hasCode="false"`, `com.google.wear.watchface.format.version = 4`, `0` `.dex` files).
   - Core layout in `watchface/app/src/main/res/raw/watchface.xml` and picker metadata in `watchface/app/src/main/res/xml/watch_face_info.xml`.

## Strict Galaxy Watch 8 / WFF Hardware Constraints

- **Memory Footprint:** `< 10 MB` uncompressed bitmap/font footprint in **Ambient (AOD)** mode; `< 100 MB` in **Interactive (Active)** mode (verified automatically by `watchface/tools/memory-footprint.jar`).
- **AOD Burn-In Safety (OPR):** Always-On Display (`<Variant mode="AMBIENT">`) must keep **On-Pixel Ratio (OPR) < 15%**, hiding heavy backgrounds and animations in favor of pure `#000000` black + dimmed line-art outline + clean time/essential info.
- **Frame Rate & Tap Responsiveness:** `<AnimatedImages>` loops must stay `<= 15 FPS` with compact WebP frames and `play="ON_VISIBLE"` (avoid `TAP` triggers on full-screen `450×450` overlays).
- **Flat `<Scene>` Configuration Rule:** Never nest `*Configuration` tags inside other `*Configuration` tags in `watchface.xml` (prevents `ConcurrentModificationException` in Samsung's `EditorActivity`). Always provide `icon` and `highlight` drawables on `<UserConfigurations>`.

## User Configurations & 5 Universal Complication Slots

### User Configurations (`<UserConfigurations>`)
- **`color_theme` (`ColorConfiguration`):** *Cranberry & Gold*, *Frosty Midnight Ice*, *Pine & Peppermint*.
- **`centerpiece_style` (`ListConfiguration`) + `custom_photo` (`PhotosConfiguration`):** *Holiday Cat (Classic)*, *Holiday Cat (Fluffy)*, or *Custom Photo (Phone)* (lets users pick any photo directly in the Galaxy Wearable phone app).
- **`lock_info_visible` (`BooleanConfiguration`):** Keep live Watch Battery `%` & fallback capsules visible while locked (`TRUE` default) or switch to icons-only privacy mode (`FALSE`).
- **`snow_enabled` (`BooleanConfiguration`):** Toggle falling snow + wrist-tilt parallax (`[ACCELEROMETER_ANGLE_X]` / `[ACCELEROMETER_ANGLE_Y]`).
- **`power_mode` (`ListConfiguration`):** `auto_eco` (4s wake burst + auto-stop `<= 25%` battery), `max_battery` (`0 FPS`), or `vivid_always`.
- **`clock_mode` (`ListConfiguration`):** `digital` (default), `analog`, or `hybrid`.

### 5 Universal Complication Slots (`<ComplicationSlot>`)
1. **`slotId="1"` — Weather / Upper-Left:** Native `[WEATHER.*]` fallback + `SHORT_TEXT`, `RANGED_VALUE`, `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE`.
2. **`slotId="2"` — Sun Heat / UV Index / Upper-Right:** Native `[WEATHER.UV_INDEX]` gauge fallback + `RANGED_VALUE`, `SHORT_TEXT`, `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE`.
3. **`slotId="3"` — Heart Rate / Lower-Left:** Native `[HEART_RATE]` fallback + `SHORT_TEXT`, `RANGED_VALUE`, `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE`.
4. **`slotId="4"` — Watch Battery / Lower-Right:** Live `[BATTERY_PERCENT]` fallback + `RANGED_VALUE`, `SHORT_TEXT`, `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE`.
5. **`slotId="5"` — Energy Score / Steps / Bottom Arc:** Native `[STEP_COUNT]` fallback + `RANGED_VALUE`, `GOAL_PROGRESS`, `SHORT_TEXT`, `LONG_TEXT`, `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE` with curved bottom progress arc.
