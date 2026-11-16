---
name: wff-apk-builder
description: >-
  Use this skill when translating the `html/` watch face design into a native
  Wear OS 6 Watch Face Format (WFF v4) Gradle project (`watchface/`), validating
  XML and memory limits, compiling the `.apk`, or sideloading to a Samsung Galaxy
  Watch 8 over Wireless ADB.
---

# Watch Face Format v4 APK Builder & Watch 8 Sideloader Skill

Convert the `450 × 450` design from `html/` into a standalone, code-free (`android:hasCode="false"`) Wear OS 6 Watch Face Format v4 package in `watchface/`.

## Project Layout (`watchface/`)

```text
watchface/
├── settings.gradle.kts
├── build.gradle.kts
├── install_to_watch8.sh                  # Wireless ADB auto-detect & installer
└── app/
    ├── build.gradle.kts                  # namespace io.github.watch8.xmasface, compileSdk 36, minSdk 34
    └── src/main/
        ├── AndroidManifest.xml           # android:hasCode="false", WFF version "4"
        └── res/
            ├── drawable-nodpi/           # Optimized WebP/PNG assets + preview.png
            ├── values/strings.xml        # English display title & UserConfiguration labels
            ├── values-es/strings.xml     # Spanish localized labels
            ├── xml/watch_face_info.xml   # <Preview value="@drawable/preview"/>, <Editable value="true"/>
            └── raw/watchface.xml         # Full 450x450 WFF v4 scene matching html/ 1-to-1
```

## Key WFF v4 Architecture Rules

1. **Flat Configurations Only (`EditorActivity` Crash Safety):**
   - Never nest `<ListConfiguration>` or `<BooleanConfiguration>` inside another `*Configuration` block inside `<Scene>`. Keep every configuration ID mounted at flat scene level and provide `icon="icon_*"` + `highlight="hl_*"` on every `<UserConfigurations>` entry.

2. **Native Companion Custom Photo (`<PhotosConfiguration>`):**
   - `<PhotosConfiguration id="custom_photo" configType="SINGLE" />` pairs with `<Photos source="[CONFIGURATION.custom_photo]" defaultImageResource="centerpiece_primary" width="180" height="180" />` inside a circular `<PartDraw renderMode="MASK">` group so users can pick any photo on their phone without recompiling.

3. **5 Universal Samsung Complication Slots (`slotId="1..5"`):**
   - Support `SHORT_TEXT`, `RANGED_VALUE`, `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE` (plus `GOAL_PROGRESS` & `LONG_TEXT` on Slot 5) with masked capsule interiors and auto-sized 2-line text/title fallback.

4. **One-Command Validate, Optimize & Build:**
   ```bash
   ./optimize_watchface.sh
   ```
   Runs WebP alpha-zeroing, complication bezel clearance math, AOD OPR (`< 15%`), `wff-validator.jar`, Gradle `assembleDebug` (`0` `.dex`), `apksigner verify`, and `memory-footprint.jar` (`< 10 MB` Ambient / `< 100 MB` Active), outputting `watch8-holiday-xmas.apk`.
