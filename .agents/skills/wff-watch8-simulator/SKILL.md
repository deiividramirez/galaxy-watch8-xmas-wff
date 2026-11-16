---
name: wff-watch8-simulator
description: >-
  Use this skill when creating, updating, or testing the interactive HTML/CSS/JS
  Samsung Galaxy Watch 8 simulator in `html/` to preview Watch Face Format (WFF v4)
  layouts, custom photos, complications, animations, Christmas countdowns, and
  Always-On Display (AOD) behavior before compiling the Wear OS APK.
---

# Galaxy Watch 8 WFF v4 HTML Simulator Skill

Maintain a zero-build-step browser simulation (`html/index.html`, `html/styles.css`, `html/simulator.js`) of the **Samsung Galaxy Watch 8** running the **Watch Face Format (WFF v4)** holiday & custom-photo watch face.

## Design & Technical Requirements

1. **Zero-Server `file://` Compatibility:**
   - `html/index.html` works immediately when opened directly via `file://` in any desktop browser (no bundler or local server required).
   - Keep CSS in `html/styles.css`, JS in `html/simulator.js`, and art layers in `html/assets/`.

2. **Samsung Galaxy Watch 8 Hardware Realism:**
   - Renders Samsung's squircle cushion case + circular Super AMOLED viewport + Home/Back physical buttons across `44mm` (`480×480`), `40mm` (`438×438`), and `46mm Classic` (`438×438` + rotating bezel).
   - Mounts an exact `450 × 450` WFF virtual canvas scaled via CSS transform (`scale(displayPx / 450)`).

3. **Interactive WFF Controls:**
   - **Active vs. Always-On (AOD)** power state & **Smart Battery Saver** (`auto_eco`, `max_battery`, `vivid_always`, plus `<= 25%` battery auto-freeze).
   - **Clock Mode (`clock_mode`):** `Digital`, `Analog`, `Hybrid`.
   - **Centerpiece Art (`centerpiece_style` + `PhotosConfiguration`):** Switch between built-in holiday cat presets (`primary`, `alt`) or upload **any local pet/family photo** live in the browser via `FileReader`.
   - **Lock-Screen Info Toggle (`lock_info_visible`):** Preview locked-watch privacy vs. live battery/capsule visibility.
   - **5 Complication Sliders & Live Weather Sky:** Test Sunny, Partly Cloudy, Windy, Rainy, Storm, Snowy, Starry Night, Fog, UV Index (`0–11`), Heart Rate, Battery, and Energy Score.

## Validation Checklist
- Run `node --check html/simulator.js` to verify clean JavaScript syntax.
- Confirm all coordinates in `html/` stay 1:1 synchronized with `watchface/app/src/main/res/raw/watchface.xml`.
