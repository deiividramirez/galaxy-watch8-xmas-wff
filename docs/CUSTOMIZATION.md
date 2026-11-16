# Customization & Developer Guide

This project lets you customize the watch face in **three ways**—ranging from **zero code on your phone** to **one-command CLI image replacement** to **full Watch Face Format v4 XML editing** (or asking an AI coding agent to do it for you).

---

## 1. Change the Centerpiece Photo Without Rebuilding (Phone App)

Because the APK uses native **Watch Face Format v4 `<PhotosConfiguration>`**, anyone who installs `watch8-holiday-xmas.apk` can swap the central medallion image directly from their phone:

1. Open the **Galaxy Wearable** app on your phone (or long-press the watch face → **Customize**).
2. Under **Centerpiece Art** (`Imagen central`), select **Custom Photo (Phone)**.
3. Pick any photo of your pet, family, or holiday art in the companion photo picker.
4. The watch automatically crops and masks your photo inside the `148×148` gold-ringed medallion in Active mode while switching to the burn-in-safe `< 4%` OPR outline in Always-On Display (AOD) mode.

---

## 2. Bake Your Own Artwork Into the Simulator & APK (`set_custom_art.py`)

If you want your own pet/illustration baked in as the default preset (including a matching custom **Always-On Display neon outline** and Watch picker thumbnail):

1. Place your image (`PNG`, `JPG`, or `WebP`) in `assets/custom-art/` (git-ignored so private photos aren't committed by accident).
2. Run:
   ```bash
   uv run --with pillow python3 tools/set_custom_art.py \
       --input assets/custom-art/my_pet.jpg \
       --crop-ratio 0.9 \
       --build
   ```
3. What this script updates automatically:
   - `html/assets/centerpiece_primary.png` (or `centerpiece_alt.png` with `--slot alt`)
   - `html/assets/centerpiece_aod.png` (auto-synthesized champagne-gold line art on `#000000` black, `< 4%` OPR)
   - All `watchface/app/src/main/res/drawable-nodpi/` WebP medallions, Customize swatch icons (`opt_centerpiece_*.webp`), and `preview.png`
   - `docs/images/preview_active.png` & `docs/images/preview_aod.png`
   - Re-validates and compiles `watch8-holiday-xmas.apk` (`--build`)

---

## 3. Customizing Colors, Name, Package ID & Languages

### Change Color Palettes
Edit `<ColorConfiguration id="color_theme">` in [`watchface/app/src/main/res/raw/watchface.xml`](../watchface/app/src/main/res/raw/watchface.xml):
- Each `<ColorOption colors="#AARRGGBB #AARRGGBB #AARRGGBB" />` defines three slots:
  - `[CONFIGURATION.color_theme.0]` — Primary accent ring & countdown pill border
  - `[CONFIGURATION.color_theme.1]` — Secondary highlight (date, medallion ring, ranged gauges)
  - `[CONFIGURATION.color_theme.2]` — Capsule card surface fill

### Change Watch Face Name or Add a Language
- English labels: [`watchface/app/src/main/res/values/strings.xml`](../watchface/app/src/main/res/values/strings.xml)
- Spanish labels: [`watchface/app/src/main/res/values-es/strings.xml`](../watchface/app/src/main/res/values-es/strings.xml)
- Add any new locale by creating `values-<lang>/strings.xml` (avoid raw `%` characters inside `<string>` values so Android resource formatting stays clean).

### Change Package ID (`applicationId`)
If you want to install multiple independent copies side-by-side on the same watch, change `namespace` and `applicationId` in [`watchface/app/build.gradle.kts`](../watchface/app/build.gradle.kts), then run `./optimize_watchface.sh`.

---

## 4. Watch Face Format v4 Engineering Rules (Important!)

When editing `watchface.xml` manually or with an AI agent, keep these verified Wear OS 6 / One UI 8 Watch rules intact:

1. **Zero Nested Configurations in `<Scene>`:** Keep `<ListConfiguration>` and `<BooleanConfiguration>` flat inside `<Scene>` (nesting one `*Configuration` inside another triggers a `ConcurrentModificationException` in Samsung's on-watch `EditorActivity`).
2. **Always Provide `icon` + `highlight` Drawables:** Every entry under `<UserConfigurations>` includes `icon="icon_*"` and `highlight="hl_*"` so Watch Customize highlights the edited region without `ResourceManager` warnings.
3. **Zero `TAP` Triggers on Full-Screen Sprites:** Keep `<AnimationController play="ON_VISIBLE" ... />` without `TAP` so touching complications or the background never lags the watch.
4. **Hardware Budgets Verified by `./optimize_watchface.sh`:**
   - Ambient (AOD) RAM `< 10 MB` · Active RAM `< 100 MB`
   - Ambient (AOD) On-Pixel Ratio (OPR) `< 15%`
   - `android:hasCode="false"` (`0` `.dex` files in the signed APK)
