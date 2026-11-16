---
name: wff-custom-assets
description: >-
  Use this skill when importing user photos, generating custom holiday/pet
  centerpiece portraits, regenerating Watch Face Format (WFF v4) WebP drawables,
  watch hands, weather overlays, or burn-in-safe Always-On Display (AOD) outlines.
---

# Custom Centerpiece & Watch Face Asset Pipeline Skill

Create, swap, and optimize crisp, memory-safe PNG/WebP layers for both the interactive HTML simulator (`html/assets/`) and the Android Watch Face Format package (`watchface/app/src/main/res/drawable-nodpi/`).

## Quick Workflow: Importing Any Custom Image

1. **One-Command Custom Portrait Swap (`tools/set_custom_art.py`):**
   - Place any PNG/JPG/WebP photo in `assets/custom-art/` (or pass any file path) and run:
     ```bash
     uv run --with pillow python3 tools/set_custom_art.py --input assets/custom-art/my_pet.jpg --build
     ```
   - This automatically:
     - Center-crops & masks the image into `html/assets/centerpiece_primary.png` (or `--slot alt` for `centerpiece_alt.png`).
     - Synthesizes a burn-in-safe warm-gold outline on pure `#000000` black (`html/assets/centerpiece_aod.png`, `< 4%` OPR) unless `--aod-input` is provided.
     - Runs [generate_wff_drawables.py](./scripts/generate_wff_drawables.py) to regenerate all `drawable-nodpi` WebP assets, Customize swatches (`opt_centerpiece_*.webp`), `preview.png`, and `docs/images/preview_*.png`.
     - With `--build`, runs `tools/optimize_watchface.py` to validate XSD, OPR, geometry, and RAM budget (`< 10 MB` AOD / `< 100 MB` Active).

2. **Generating AI Artwork (`image-generator`):**
   - **Active Centerpiece (`centerpiece_primary.png` / `centerpiece_alt.png`):** Square `360×360` composition framed cleanly inside a circular medallion (`180×180` WebP in APK for optimal RAM).
   - **AOD Silhouette (`centerpiece_aod.png`):** Thin gold/ivory line-art outline on `#000000` black so Ambient mode stays well below `15%` On-Pixel Ratio and `< 10 MB` RAM.

3. **Standalone Asset Preparation (`prepare_wff_asset.py`):**
   - Use [prepare_wff_asset.py](./scripts/prepare_wff_asset.py) to resize, feather-crop, dark-key, and inspect exact RGBA RAM (`width × height × 4` bytes) + OPR contribution of any individual asset.
