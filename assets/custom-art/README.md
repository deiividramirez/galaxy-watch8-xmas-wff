# Custom Artwork Drop-In Folder (`assets/custom-art/`)

Drop any PNG, JPG, or WebP photo of your pet, family, or holiday illustration in this folder (files placed here are git-ignored by default so your private photos stay local).

## Bake Your Image Into the Simulator & APK in One Command

```bash
# Replace the primary centerpiece, auto-generate a burn-in-safe AOD outline, and rebuild the APK:
uv run --with pillow python3 tools/set_custom_art.py --input assets/custom-art/your_photo.jpg --build
```

- Use `--slot alt` to replace the secondary preset instead of the primary preset.
- Use `--crop-ratio 0.8` (values `0.25`–`1.0`) to zoom in tighter on the center of your photo.
- Use `--aod-input assets/custom-art/your_outline.png` if you prefer supplying your own custom Always-On Display line art.
