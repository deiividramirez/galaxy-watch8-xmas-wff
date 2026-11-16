#!/usr/bin/env python3
"""Resize, circular-mask/clean, and audit WFF memory footprint for watch face assets.

Usage:
  uv run --with pillow .agents/skills/wff-custom-assets/scripts/prepare_wff_asset.py \
      --input raw.png --output html/assets/centerpiece_primary.png --size 360 --circle-feather 8
"""

import argparse
import math
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter


def apply_circular_feather(img: Image.Image, feather_px: int) -> Image.Image:
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    inset = max(2, feather_px)
    draw.ellipse((inset, inset, w - inset, h - inset), fill=255)
    if feather_px > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather_px / 2.0))
    r, g, b, a = img.split()
    combined_alpha = ImageChops.multiply(a, mask)
    img.putalpha(combined_alpha)
    return img


def key_near_black_to_alpha(img: Image.Image, threshold: int) -> Image.Image:
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            lum = max(r, g, b)
            if lum <= threshold:
                pixels[x, y] = (0, 0, 0, 0)
            elif lum < threshold * 2:
                scale = (lum - threshold) / float(threshold)
                pixels[x, y] = (r, g, b, int(a * scale))
    return img


def compute_opr_percent(img: Image.Image) -> float:
    w, h = img.size
    total_lum = 0.0
    pixels = img.get_flattened_data() if hasattr(img, "get_flattened_data") else img.getdata()
    for r, g, b, a in pixels:
        alpha = a / 255.0
        lum = ((0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0) * alpha
        total_lum += lum
    return (total_lum / (w * h)) * 100.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare WFF-compliant PNG/WebP asset")
    parser.add_argument("--input", required=True, help="Source image path")
    parser.add_argument("--output", required=True, help="Destination PNG/WebP path")
    parser.add_argument("--size", type=int, default=280, help="Square target dimension in px")
    parser.add_argument("--crop-ratio", type=float, default=1.0, help="Center square crop ratio (0.1 to 1.0)")
    parser.add_argument("--circle-feather", type=int, default=0, help="Circular vignette feather px")
    parser.add_argument("--black-key", type=int, default=0, help="Convert near-black <= threshold to transparent")
    args = parser.parse_args()

    src = Image.open(args.input).convert("RGBA")
    # Center-crop to square and optional inner ratio
    w, h = src.size
    side = int(min(w, h) * max(0.1, min(1.0, args.crop_ratio)))
    left = (w - side) // 2
    top = (h - side) // 2
    src = src.crop((left, top, left + side, top + side))

    resized = src.resize((args.size, args.size), Image.Resampling.LANCZOS)

    if args.black_key > 0:
        resized = key_near_black_to_alpha(resized, args.black_key)
    if args.circle_feather > 0:
        resized = apply_circular_feather(resized, args.circle_feather)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = "WEBP" if out_path.suffix.lower() == ".webp" else "PNG"
    resized.save(out_path, format=fmt, optimize=True)

    rgba_bytes = args.size * args.size * 4
    rgba_mb = rgba_bytes / (1024 * 1024)
    opr = compute_opr_percent(resized)
    print(
        f"Saved {out_path} ({args.size}x{args.size} {fmt}) | "
        f"Uncompressed WFF RAM: {rgba_mb:.3f} MB | Avg OPR contribution: {opr:.2f}%"
    )


if __name__ == "__main__":
    main()
