#!/usr/bin/env python3
"""
One-Command Custom Centerpiece Artwork Importer (HTML Simulator + WFF v4 APK)
=============================================================================
Allows any user or AI agent to replace the watch face's centerpiece image
with their own pet, family portrait, or holiday illustration—automatically
generating a burn-in-safe Always-On Display (AOD) outline (< 15% OPR),
syncing all WebP drawables + preview thumbnails, and optionally compiling
a validated Wear OS 6 APK.

Examples:
  # Replace the primary centerpiece and auto-generate burn-in-safe AOD line art:
  uv run --with pillow python3 tools/set_custom_art.py --input assets/custom-art/my_pet.jpg

  # Replace the primary centerpiece AND immediately rebuild + validate the APK:
  uv run --with pillow python3 tools/set_custom_art.py --input assets/custom-art/my_pet.jpg --build

  # Replace the secondary ("alt") preset slot without overwriting the primary slot:
  uv run --with pillow python3 tools/set_custom_art.py --input assets/custom-art/second_pet.png --slot alt
"""

import argparse
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
HTML_ASSETS = ROOT / "html" / "assets"
GEN_DRAWABLES = ROOT / ".agents" / "skills" / "wff-custom-assets" / "scripts" / "generate_wff_drawables.py"
OPTIMIZER = ROOT / "tools" / "optimize_watchface.py"


def center_crop_square(img: Image.Image, crop_ratio: float = 1.0) -> Image.Image:
    w, h = img.size
    ratio = max(0.25, min(1.0, crop_ratio))
    side = int(min(w, h) * ratio)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def apply_circular_medallion(img: Image.Image, size: int = 360) -> Image.Image:
    resized = img.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((4, 4, size - 5, size - 5), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=2.0))
    r, g, b, orig_a = resized.split()
    final_a = Image.composite(orig_a, Image.new("L", (size, size), 0), mask)
    out = Image.merge("RGBA", (r, g, b, final_a))
    return out


def synthesize_burn_in_safe_aod(active_rgba: Image.Image, size: int = 360) -> Image.Image:
    """Create a warm-gold & soft-ivory outline on pure #000000 black (< 4% OPR)."""
    gray = active_rgba.convert("L")
    gray = ImageOps.autocontrast(gray, cutoff=2)
    edges = gray.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(radius=0.8))
    edges = ImageEnhance.Contrast(edges).enhance(2.4)

    # Fade outer rim cleanly so circular boundary doesn't create a bright ring
    rim_mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(rim_mask).ellipse((14, 14, size - 15, size - 15), fill=255)
    rim_mask = rim_mask.filter(ImageFilter.GaussianBlur(radius=6.0))

    _, _, _, orig_a = active_rgba.split()
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    epx = edges.load()
    mpx = rim_mask.load()
    apx = orig_a.load()
    opx = out.load()

    for y in range(size):
        for x in range(size):
            strength = (epx[x, y] * mpx[x, y] * apx[x, y]) / (255.0 * 255.0)
            if strength < 26:
                continue
            alpha = min(205, int((strength - 26) * 1.45))
            # Warm holiday champagne-gold linework (#F5C542 -> ivory highlights)
            t = min(1.0, strength / 220.0)
            r = int(225 + 30 * t)
            g = int(182 + 55 * t)
            b = int(72 + 120 * t)
            opx[x, y] = (r, g, b, alpha)

    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import any custom pet/portrait image into the HTML simulator & WFF v4 watch face."
    )
    parser.add_argument("--input", required=True, help="Path to source image (PNG, JPG, or WebP)")
    parser.add_argument(
        "--aod-input",
        default=None,
        help="Optional custom AOD outline image (auto-generated from --input if omitted)",
    )
    parser.add_argument(
        "--slot",
        choices=["primary", "alt"],
        default="primary",
        help="Which built-in centerpiece preset slot to replace (default: primary)",
    )
    parser.add_argument(
        "--crop-ratio",
        type=float,
        default=1.0,
        help="Center-square zoom crop ratio from 0.25 (tight zoom) to 1.0 (full square, default)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Also run the 4-stage WFF v4 optimizer & rebuild watch8-holiday-xmas.apk",
    )
    args = parser.parse_args()

    src_path = Path(args.input).expanduser().resolve()
    if not src_path.exists():
        print(f"ERROR: Source image not found: {src_path}", file=sys.stderr)
        return 1

    print(f"[1/3] Preparing circular medallion from {src_path.name} (slot={args.slot})...")
    raw_img = Image.open(src_path).convert("RGBA")
    cropped = center_crop_square(raw_img, crop_ratio=args.crop_ratio)
    medallion = apply_circular_medallion(cropped, size=360)

    target_active = HTML_ASSETS / (
        "centerpiece_primary.png" if args.slot == "primary" else "centerpiece_alt.png"
    )
    target_aod = HTML_ASSETS / (
        "centerpiece_aod.png" if args.slot == "primary" else "centerpiece_alt_aod.png"
    )
    medallion.save(target_active, format="PNG", optimize=True)
    print(f"  -> Saved {target_active.relative_to(ROOT)}")

    if args.aod_input:
        aod_src = Image.open(Path(args.aod_input).expanduser().resolve()).convert("RGBA")
        aod_img = apply_circular_medallion(center_crop_square(aod_src, args.crop_ratio), size=360)
    else:
        aod_img = synthesize_burn_in_safe_aod(medallion, size=360)
    aod_img.save(target_aod, format="PNG", optimize=True)
    print(f"  -> Saved burn-in-safe AOD outline {target_aod.relative_to(ROOT)}")

    print("[2/3] Regenerating Watch Face Format v4 WebP drawables, Customize icons & previews...")
    subprocess.run([sys.executable, str(GEN_DRAWABLES)], check=True)

    if args.build:
        print("[3/3] Running full WFF v4 validator, optimizer & APK build...")
        subprocess.run([sys.executable, str(OPTIMIZER)], check=True)
    else:
        print("[3/3] Done! Open html/index.html to preview or pass --build to compile the APK.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
