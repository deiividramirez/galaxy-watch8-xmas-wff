#!/usr/bin/env python3
"""
Generate all crisp 4x-supersampled PNG/WebP drawables for Galaxy Watch 8 Holiday Watch Face (WFF v4):
- Tightly framed centerpiece portraits (Primary, Alt, Burn-In-Safe AOD)
- High-visibility 450x450 dial backdrop & perimeter fairy lights (pushed to outer rim r=204..219)
- 10 vivid 72x72 Weather Condition icons (Sunny, Clear Night, Partly Day/Night, Cloudy, Fog, Windy, Rain, Storm, Snow)
- 4 vivid 64x64 Complication icons (Sun-Heat UV, ECG Heart, Battery Bolt, Energy Sparkle)
- 5 Live Weather 450x450 Sky Overlays (Sunny sunbeams, Partly Cloudy, Starry Night, Cloudy Mist, Rain/Storm canopy)
- Seamless animated loops: Snow, Wind gusts, Rain streaks
- Customize icons, highlight overlays, picker preview.png & docs/images/ previews
"""

import math
import random
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[4]
HTML_ASSETS = ROOT / "html" / "assets"
HTML_ICONS = HTML_ASSETS / "icons"
RES_DRAWABLE = ROOT / "watchface" / "app" / "src" / "main" / "res" / "drawable-nodpi"
DOCS_IMAGES = ROOT / "docs" / "images"
RES_DRAWABLE.mkdir(parents=True, exist_ok=True)
HTML_ICONS.mkdir(parents=True, exist_ok=True)
DOCS_IMAGES.mkdir(parents=True, exist_ok=True)


def save_drawable(img: Image.Image, name: str, also_html: bool = False) -> None:
    out = RES_DRAWABLE / name
    if name.endswith(".webp"):
        img.save(out, format="WEBP", lossless=True, quality=95)
    else:
        img.save(out, format="PNG", optimize=True)
    if also_html:
        shutil.copy2(out, HTML_ICONS / name)


def circular_crop_tight(src: Image.Image, out_size: int = 240, crop_inset_pct: float = 0.06) -> Image.Image:
    w, h = src.size
    inset_x = int(w * crop_inset_pct)
    inset_y = int(h * crop_inset_pct)
    cropped = src.crop((inset_x, inset_y, w - inset_x, h - inset_y)).resize(
        (out_size, out_size), Image.Resampling.LANCZOS
    )
    mask = Image.new("L", (out_size, out_size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((2, 2, out_size - 3, out_size - 3), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1.0))
    out = Image.new("RGBA", (out_size, out_size), (0, 0, 0, 0))
    out.paste(cropped, (0, 0), mask)
    # Multiply existing alpha so already-transparent corners remain transparent
    r, g, b, orig_a = cropped.split()
    final_a = Image.composite(orig_a, Image.new("L", (out_size, out_size), 0), mask)
    return Image.merge("RGBA", (r, g, b, final_a))


def make_portraits() -> None:
    for src_name, dst_name, inset in [
        ("centerpiece_primary.png", "centerpiece_primary.webp", 0.065),
        ("centerpiece_alt.png", "centerpiece_alt.webp", 0.055),
        ("centerpiece_aod.png", "centerpiece_aod.webp", 0.055),
    ]:
        src = Image.open(HTML_ASSETS / src_name).convert("RGBA")
        # 180x180 exceeds Watch 8 44mm physical 158x158 medallion pixels while saving 44% RGBA RAM!
        tight = circular_crop_tight(src, out_size=180, crop_inset_pct=inset)
        save_drawable(tight, dst_name)


def make_dial_backdrop_and_ticks() -> None:
    size = 450
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    px = bg.load()
    cx, cy = 225.0, 228.0
    for y in range(size):
        for x in range(size):
            dist = math.hypot(x - 225.0, y - 225.0)
            if dist > 225.0:
                px[x, y] = (0, 0, 0, 0)
                continue
            d_glow = min(1.0, math.hypot(x - cx, y - cy) / 220.0)
            t = (1.0 - d_glow) ** 1.65
            r = int(5 + 15 * t)
            g = int(13 + 34 * t)
            b = int(9 + 22 * t)
            px[x, y] = (r, g, b, 255)

    # Outer rim ticks pushed cleanly to r=211..220 (ss=900 -> r=422..440) so inner r<=203 is wide open!
    ss = 900
    ticks = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(ticks)
    d.ellipse((10, 10, ss - 10, ss - 10), outline=(255, 255, 255, 28), width=3)

    bulb_colors = [
        (255, 82, 82, 245),
        (255, 215, 64, 245),
        (105, 240, 174, 245),
        (64, 196, 255, 245),
    ]
    lights_a = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    lights_b = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    da = ImageDraw.Draw(lights_a)
    db = ImageDraw.Draw(lights_b)

    for i in range(60):
        rad = math.radians(i * 6 - 90)
        is_hr = i % 5 == 0
        r_out = 440
        r_in = 420 if is_hr else 430
        x1 = 450 + r_out * math.cos(rad)
        y1 = 450 + r_out * math.sin(rad)
        x2 = 450 + r_in * math.cos(rad)
        y2 = 450 + r_in * math.sin(rad)
        col = (245, 197, 66, 195) if is_hr else (255, 255, 255, 58)
        d.line((x1, y1, x2, y2), fill=col, width=6 if is_hr else 2)

        if is_hr:
            idx = i // 5
            bx = 450 + 409 * math.cos(rad)
            by = 450 + 409 * math.sin(rad)
            c = bulb_colors[idx % len(bulb_colors)]
            dim = (c[0], c[1], c[2], 95)
            if idx % 2 == 0:
                da.ellipse((bx - 8, by - 8, bx + 8, by + 8), fill=c)
                db.ellipse((bx - 5, by - 5, bx + 5, by + 5), fill=dim)
            else:
                da.ellipse((bx - 5, by - 5, bx + 5, by + 5), fill=dim)
                db.ellipse((bx - 8, by - 8, bx + 8, by + 8), fill=c)

    lights_a = lights_a.filter(ImageFilter.GaussianBlur(radius=1.4)).resize((450, 450), Image.Resampling.LANCZOS)
    lights_b = lights_b.filter(ImageFilter.GaussianBlur(radius=1.4)).resize((450, 450), Image.Resampling.LANCZOS)
    ticks_450 = ticks.resize((450, 450), Image.Resampling.LANCZOS)

    bg = Image.alpha_composite(bg, ticks_450)
    save_drawable(bg, "dial_backdrop.webp")
    save_drawable(lights_a, "fairy_lights_0.webp")
    save_drawable(lights_b, "fairy_lights_1.webp")


def _draw_cloud(d: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, fill_col, outline_col=None) -> None:
    # Supersampled plush cloud centered around (cx, cy) on 288x288 canvas
    r1 = int(38 * scale)
    r2 = int(50 * scale)
    r3 = int(34 * scale)
    d.ellipse((cx - int(72 * scale), cy - r1 + int(10 * scale), cx - int(72 * scale) + 2 * r1, cy + r1 + int(10 * scale)), fill=fill_col)
    d.ellipse((cx - int(32 * scale), cy - r2 - int(10 * scale), cx - int(32 * scale) + 2 * r2, cy + r2 - int(10 * scale)), fill=fill_col)
    d.ellipse((cx + int(22 * scale), cy - r3 + int(12 * scale), cx + int(22 * scale) + 2 * r3, cy + r3 + int(12 * scale)), fill=fill_col)
    d.rounded_rectangle(
        (cx - int(68 * scale), cy + int(4 * scale), cx + int(82 * scale), cy + int(46 * scale)),
        radius=int(20 * scale),
        fill=fill_col,
    )
    if outline_col:
        d.line(
            (cx - int(54 * scale), cy + int(44 * scale), cx + int(68 * scale), cy + int(44 * scale)),
            fill=outline_col,
            width=max(3, int(6 * scale)),
        )


def _draw_sun(d: ImageDraw.ImageDraw, cx: int, cy: int, r_core: int, r_ray_in: int, r_ray_out: int) -> None:
    for i in range(8):
        ang = math.radians(i * 45)
        x1 = cx + r_ray_in * math.cos(ang)
        y1 = cy + r_ray_in * math.sin(ang)
        x2 = cx + r_ray_out * math.cos(ang)
        y2 = cy + r_ray_out * math.sin(ang)
        d.line((x1, y1, x2, y2), fill=(255, 213, 79, 255), width=16)
    d.ellipse((cx - r_core - 6, cy - r_core - 6, cx + r_core + 6, cy + r_core + 6), fill=(255, 160, 0, 110))
    d.ellipse((cx - r_core, cy - r_core, cx + r_core, cy + r_core), fill=(255, 215, 64, 255), outline=(255, 248, 225, 255), width=6)


def _draw_moon(cw: Image.Image, cx: int, cy: int, radius: int) -> None:
    moon = Image.new("RGBA", cw.size, (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    md.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(255, 224, 130, 255))
    # Subtract offset circle for crisp crescent
    cut = Image.new("L", cw.size, 0)
    cd = ImageDraw.Draw(cut)
    cd.ellipse((cx - int(radius * 0.52), cy - int(radius * 1.12), cx + int(radius * 1.28), cy + int(radius * 0.68)), fill=255)
    r, g, b, a = moon.split()
    a = Image.composite(Image.new("L", cw.size, 0), a, cut)
    moon = Image.merge("RGBA", (r, g, b, a))
    cw.alpha_composite(moon)


def _draw_star4(d: ImageDraw.ImageDraw, cx: int, cy: int, r_out: int, col=(255, 245, 157, 255)) -> None:
    r_in = max(3, int(r_out * 0.28))
    pts = []
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rr = r_out if i % 2 == 0 else r_in
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=col)


def make_weather_and_complication_icons() -> None:
    S = 288  # 4x supersample for 72x72 icons

    # 1. SUNNY (wx_sunny.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _draw_sun(d, 144, 144, 58, 76, 118)
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_sunny.webp", also_html=True)

    # 2. CLEAR NIGHT (wx_clear_night.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    _draw_moon(im, 148, 152, 86)
    d = ImageDraw.Draw(im)
    _draw_star4(d, 214, 76, 26, (255, 245, 157, 255))
    _draw_star4(d, 74, 82, 18, (179, 229, 252, 255))
    _draw_star4(d, 228, 152, 15, (255, 255, 255, 240))
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_clear_night.webp", also_html=True)

    # 3. PARTLY CLOUDY DAY (wx_partly_day.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _draw_sun(d, 108, 106, 44, 58, 88)
    _draw_cloud(d, 154, 170, 1.08, (245, 250, 255, 255), (176, 190, 197, 255))
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_partly_day.webp", also_html=True)

    # 4. PARTLY CLOUDY NIGHT (wx_partly_night.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    _draw_moon(im, 114, 104, 62)
    d = ImageDraw.Draw(im)
    _draw_star4(d, 216, 76, 20, (255, 245, 157, 255))
    _draw_cloud(d, 150, 174, 1.08, (227, 242, 253, 255), (144, 164, 174, 255))
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_partly_night.webp", also_html=True)

    # 5. CLOUDY (wx_cloudy.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _draw_cloud(d, 118, 122, 0.92, (176, 190, 197, 235))
    _draw_cloud(d, 154, 164, 1.12, (245, 250, 255, 255), (144, 164, 174, 255))
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_cloudy.webp", also_html=True)

    # 6. FOG / MIST (wx_fog.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _draw_cloud(d, 144, 118, 0.98, (224, 242, 241, 245))
    for idx, yy in enumerate([192, 222, 252]):
        pad = 42 if idx != 1 else 28
        d.rounded_rectangle((pad, yy - 8, S - pad, yy + 8), radius=8, fill=(178, 235, 242, 245))
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_fog.webp", also_html=True)

    # 7. WINDY (wx_windy.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for x_start, x_end, y_line, r_curl, up, col in [
        (32, 194, 108, 32, True, (128, 216, 255, 255)),
        (20, 224, 154, 34, False, (255, 255, 255, 255)),
        (48, 168, 200, 28, False, (179, 229, 252, 255)),
    ]:
        pts = [(x_start, y_line), (x_end, y_line)]
        cy_c = y_line - r_curl if up else y_line + r_curl
        for step in range(1, 19):
            deg = (90 - step * 13) if up else (-90 + step * 13)
            rad = math.radians(deg)
            pts.append((x_end + r_curl * math.cos(rad), cy_c + r_curl * math.sin(rad)))
        d.line(pts, fill=col, width=20, joint="curve")
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_windy.webp", also_html=True)

    # 8. RAIN (wx_rain.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _draw_cloud(d, 144, 116, 1.06, (207, 216, 220, 255), (120, 144, 156, 255))
    for rx in [92, 148, 204]:
        d.line((rx + 12, 182, rx - 10, 248), fill=(64, 196, 255, 255), width=18)
        d.ellipse((rx - 19, 236, rx - 1, 256), fill=(64, 196, 255, 255))
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_rain.webp", also_html=True)

    # 9. STORM / THUNDERSTORM (wx_storm.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _draw_cloud(d, 144, 110, 1.06, (144, 164, 174, 255), (84, 110, 122, 255))
    bolt = [(158, 156), (116, 212), (150, 212), (128, 270), (192, 198), (156, 198)]
    d.polygon(bolt, fill=(255, 215, 64, 255))
    d.line((86, 184, 68, 238), fill=(64, 196, 255, 255), width=16)
    d.line((222, 184, 204, 238), fill=(64, 196, 255, 255), width=16)
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_storm.webp", also_html=True)

    # 10. SNOW (wx_snow.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 144, 144
    for i in range(6):
        ang = math.radians(i * 60)
        x2 = cx + 108 * math.cos(ang)
        y2 = cy + 108 * math.sin(ang)
        d.line((cx, cy, x2, y2), fill=(225, 245, 254, 255), width=16)
        # Crystal branches
        bx = cx + 68 * math.cos(ang)
        by = cy + 68 * math.sin(ang)
        for side in (-45, 45):
            sang = ang + math.radians(side)
            d.line((bx, by, bx + 34 * math.cos(sang), by + 34 * math.sin(sang)), fill=(128, 216, 255, 255), width=12)
    d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(255, 255, 255, 255))
    save_drawable(im.resize((72, 72), Image.Resampling.LANCZOS), "wx_snow.webp", also_html=True)

    # --- 4 COMPLICATION ICONS (64x64, Unified 36..252 Optical Bounding Grid on 288x288) ---
    # A. UV Sun Heat Icon (ic_uv_sun.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(12):
        ang = math.radians(i * 30)
        d.line(
            (144 + 72 * math.cos(ang), 144 + 72 * math.sin(ang), 144 + 110 * math.cos(ang), 144 + 110 * math.sin(ang)),
            fill=(255, 179, 64, 255),
            width=16,
        )
    d.ellipse((80, 80, 208, 208), fill=(255, 196, 0, 255), outline=(255, 238, 88, 255), width=10)
    d.ellipse((102, 102, 186, 186), fill=(255, 109, 0, 220))
    save_drawable(im.resize((64, 64), Image.Resampling.LANCZOS), "ic_uv_sun.webp", also_html=True)

    # B. Heart Rate ECG Icon (ic_heart.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((38, 50, 152, 164), fill=(255, 82, 82, 255))
    d.ellipse((136, 50, 250, 164), fill=(255, 82, 82, 255))
    d.polygon([(44, 128), (244, 128), (144, 246)], fill=(255, 82, 82, 255))
    ecg = [(62, 144), (108, 144), (126, 104), (152, 182), (174, 130), (192, 144), (226, 144)]
    d.line(ecg, fill=(255, 255, 255, 255), width=14, joint="curve")
    save_drawable(im.resize((64, 64), Image.Resampling.LANCZOS), "ic_heart.webp", also_html=True)

    # C. Crisp Rounded Battery + Charge Bolt Icon (ic_battery.webp — zero clipped tips!)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Top positive battery terminal cap
    d.rounded_rectangle((112, 34, 176, 58), radius=10, fill=(185, 246, 202, 255))
    # Rounded battery body outline + dark inner chamber
    d.rounded_rectangle(
        (68, 54, 220, 250),
        radius=30,
        fill=(14, 42, 30, 235),
        outline=(105, 240, 174, 255),
        width=16,
    )
    # Glowing green charge level block inside lower half
    d.rounded_rectangle((88, 146, 200, 230), radius=14, fill=(0, 230, 118, 220))
    # Crisp bright white/mint lightning bolt centered inside the battery cell
    bolt = [(158, 76), (106, 154), (144, 154), (128, 224), (184, 142), (146, 142)]
    d.polygon(bolt, fill=(255, 255, 255, 255))
    save_drawable(im.resize((64, 64), Image.Resampling.LANCZOS), "ic_battery.webp", also_html=True)

    # D. Energy Score Galaxy Sparkle Icon (ic_energy.webp)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _draw_star4(d, 136, 150, 102, (255, 215, 64, 255))
    _draw_star4(d, 136, 150, 58, (255, 255, 255, 255))
    _draw_star4(d, 218, 72, 36, (105, 240, 174, 255))
    save_drawable(im.resize((64, 64), Image.Resampling.LANCZOS), "ic_energy.webp", also_html=True)


def _apply_dial_circle_mask(img: Image.Image) -> Image.Image:
    size = img.size[0]
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((2, 2, size - 3, size - 3), fill=255)
    r, g, b, a = img.split()
    a = Image.composite(a, Image.new("L", (size, size), 0), mask)
    return Image.merge("RGBA", (r, g, b, a))


def make_live_weather_sky_layers() -> None:
    size = 450

    # 1. SUNNY SKY (sky_sunny.webp): Warm golden sunbeams from top-left (95, 72)
    sunny = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sunny)
    sx, sy = 88, 76
    for i in range(10):
        ang = math.radians(-15 + i * 16)
        ang2 = ang + math.radians(6.5)
        r_len = 330
        pts = [
            (sx, sy),
            (sx + r_len * math.cos(ang), sy + r_len * math.sin(ang)),
            (sx + r_len * math.cos(ang2), sy + r_len * math.sin(ang2)),
        ]
        sd.polygon(pts, fill=(255, 202, 40, 26))
    sd.ellipse((sx - 68, sy - 68, sx + 68, sy + 68), fill=(255, 213, 79, 58))
    sd.ellipse((sx - 34, sy - 34, sx + 34, sy + 34), fill=(255, 241, 118, 82))
    sunny = _apply_dial_circle_mask(sunny.filter(ImageFilter.GaussianBlur(radius=9.0))).resize((225, 225), Image.Resampling.LANCZOS)
    save_drawable(sunny, "sky_sunny.webp", also_html=True)

    # 2. PARTLY CLOUDY DAY SKY (sky_partly_cloudy.webp)
    pcloud = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pcloud)
    pd.ellipse((42, 24, 166, 148), fill=(255, 213, 79, 52))
    pd.ellipse((34, 58, 178, 126), fill=(227, 242, 253, 42))
    pd.ellipse((268, 48, 412, 118), fill=(227, 242, 253, 38))
    pcloud = _apply_dial_circle_mask(pcloud.filter(ImageFilter.GaussianBlur(radius=10.0))).resize((225, 225), Image.Resampling.LANCZOS)
    save_drawable(pcloud, "sky_partly_cloudy.webp", also_html=True)

    # 3. STARRY NIGHT SKY (sky_starry_night.webp)
    night = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    nd = ImageDraw.Draw(night)
    nd.ellipse((20, 12, 430, 210), fill=(26, 54, 118, 68))
    night = night.filter(ImageFilter.GaussianBlur(radius=16.0))
    nd = ImageDraw.Draw(night)
    rng = random.Random(20261224)
    for _ in range(34):
        ang = rng.uniform(0, math.tau)
        rad = rng.uniform(86, 202)
        x = 225 + rad * math.cos(ang)
        y = 225 + rad * math.sin(ang)
        if 120 < x < 330 and 55 < y < 140:
            continue
        sr = rng.choice([1.4, 1.8, 2.4])
        al = rng.randint(125, 240)
        nd.ellipse((x - sr, y - sr, x + sr, y + sr), fill=(255, 248, 225, al))
    night = _apply_dial_circle_mask(night).resize((225, 225), Image.Resampling.LANCZOS)
    save_drawable(night, "sky_starry_night.webp", also_html=True)

    # 4. CLOUDY / MIST SKY (sky_cloudy_mist.webp)
    mist = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    md.ellipse((30, 18, 240, 125), fill=(176, 190, 197, 46))
    md.ellipse((210, 22, 420, 130), fill=(176, 190, 197, 44))
    mist = _apply_dial_circle_mask(mist.filter(ImageFilter.GaussianBlur(radius=13.0))).resize((225, 225), Image.Resampling.LANCZOS)
    save_drawable(mist, "sky_cloudy_mist.webp", also_html=True)

    # 5. RAIN / STORM SKY (sky_rain_storm.webp)
    storm = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    std = ImageDraw.Draw(storm)
    std.ellipse((20, 10, 430, 165), fill=(38, 70, 115, 76))
    storm = _apply_dial_circle_mask(storm.filter(ImageFilter.GaussianBlur(radius=14.0))).resize((225, 225), Image.Resampling.LANCZOS)
    save_drawable(storm, "sky_rain_storm.webp", also_html=True)


def make_seamless_weather_particle_loops() -> None:
    dim = 200
    half = dim / 2.0

    # 1. SNOW (8 seamless frames at 8 FPS — saves 56% particle RGBA RAM vs 10x240!)
    rng = random.Random(20261225)
    n_snow = 8
    flakes = [
        {
            "x0": rng.uniform(0, dim),
            "y0": rng.uniform(0, dim),
            "r": rng.uniform(0.95, 1.85),
            "speed": rng.choice([1, 2]),
            "sway_amp": rng.uniform(2.0, 5.5),
            "sway_phase": rng.uniform(0, math.tau),
            "alpha": rng.randint(105, 205),
        }
        for _ in range(34)
    ]
    for f_idx in range(n_snow):
        t = f_idx / float(n_snow)
        frame = Image.new("RGBA", (dim, dim), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        for fl in flakes:
            x = (fl["x0"] + math.sin(math.tau * t + fl["sway_phase"]) * fl["sway_amp"]) % dim
            y = (fl["y0"] + t * dim * fl["speed"]) % dim
            if math.hypot(x - half, y - half) > (half - 5):
                continue
            dist_face = math.hypot(x - half, y - half)
            alpha = int(fl["alpha"] * 0.25) if dist_face < 36 else fl["alpha"]
            r = fl["r"]
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, alpha))
        save_drawable(frame, f"snow_{f_idx:02d}.webp")

    # 2. WIND STREAKS (6 seamless frames, sweeping left-to-right gusts)
    rng_w = random.Random(20261115)
    n_wind = 6
    gusts = [
        {
            "x0": rng_w.uniform(0, dim),
            "y0": rng_w.uniform(18, dim - 18),
            "length": rng_w.uniform(22, 44),
            "wave": rng_w.uniform(2.0, 4.5),
            "phase": rng_w.uniform(0, math.tau),
            "alpha": rng_w.randint(95, 185),
        }
        for _ in range(15)
    ]
    for f_idx in range(n_wind):
        t = f_idx / float(n_wind)
        frame = Image.new("RGBA", (dim, dim), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        for g in gusts:
            x = (g["x0"] + t * dim) % dim
            y = g["y0"] + math.sin(math.tau * t + g["phase"]) * g["wave"]
            if math.hypot(x - half, y - half) > (half - 8):
                continue
            if 65 < x < 135 and 26 < y < 135:
                al = int(g["alpha"] * 0.25)
            else:
                al = g["alpha"]
            pts = []
            for s in range(6):
                px = x + (s / 5.0) * g["length"]
                py = y + math.sin((s / 5.0) * math.pi + g["phase"]) * 2.0
                if math.hypot(px - half, py - half) <= (half - 6):
                    pts.append((px, py))
            if len(pts) >= 2:
                d.line(pts, fill=(179, 229, 252, al), width=2)
        save_drawable(frame, f"wind_{f_idx:02d}.webp")

    # 3. RAIN STREAKS (6 seamless frames, angled falling rain)
    rng_r = random.Random(20261201)
    n_rain = 6
    drops = [
        {
            "x0": rng_r.uniform(0, dim),
            "y0": rng_r.uniform(0, dim),
            "len": rng_r.uniform(8, 14),
            "alpha": rng_r.randint(105, 195),
        }
        for _ in range(28)
    ]
    for f_idx in range(n_rain):
        t = f_idx / float(n_rain)
        frame = Image.new("RGBA", (dim, dim), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        for dr in drops:
            x = (dr["x0"] - t * (dim * 0.25)) % dim
            y = (dr["y0"] + t * dim) % dim
            if math.hypot(x - half, y - half) > (half - 8):
                continue
            al = int(dr["alpha"] * 0.25) if math.hypot(x - half, y - half) < 38 else dr["alpha"]
            d.line((x, y, x - dr["len"] * 0.28, y + dr["len"]), fill=(100, 196, 255, al), width=2)
        save_drawable(frame, f"rain_{f_idx:02d}.webp")


def make_analog_hands() -> Image.Image:
    ss = 900
    # 1. Candy-cane & Gold Hour Hand -> tight strip (x=211, y=130, w=28, h=115, pivot=(0.5, 0.826087))
    hr = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(hr)
    d.rounded_rectangle((440, 272, 464, 474), radius=12, fill=(0, 0, 0, 140))
    d.rounded_rectangle((442, 270, 458, 472), radius=8, fill=(255, 248, 231, 255))
    for sy in range(282, 460, 28):
        d.rounded_rectangle((442, sy, 458, min(466, sy + 14)), radius=3, fill=(212, 36, 38, 255))
    d.rounded_rectangle((443, 266, 457, 280), radius=6, fill=(245, 197, 66, 255))
    d.ellipse((436, 436, 464, 464), fill=(26, 30, 36, 255), outline=(245, 197, 66, 255), width=4)
    hr_450 = hr.resize((450, 450), Image.Resampling.LANCZOS)
    save_drawable(hr_450.crop((211, 130, 239, 245)), "hand_hour.webp", also_html=True)

    # 2. Warm Gold Minute Hand -> tight strip (x=211, y=75, w=28, h=170, pivot=(0.5, 0.882353))
    mn = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(mn)
    d.rounded_rectangle((442, 160, 462, 480), radius=10, fill=(0, 0, 0, 140))
    d.rounded_rectangle((444, 158, 456, 478), radius=6, fill=(245, 197, 66, 255))
    d.rounded_rectangle((448, 176, 452, 304), radius=2, fill=(255, 255, 255, 235))
    d.ellipse((435, 435, 465, 465), fill=(26, 30, 36, 255), outline=(245, 197, 66, 255), width=5)
    mn_450 = mn.resize((450, 450), Image.Resampling.LANCZOS)
    save_drawable(mn_450.crop((211, 75, 239, 245)), "hand_minute.webp", also_html=True)

    # 3. Full Second Hand (Analog mode) -> tight strip (x=213, y=40, w=24, h=215, pivot=(0.5, 0.860465))
    sc = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(sc)
    d.line((450, 504, 450, 86), fill=(212, 36, 38, 255), width=4)
    d.ellipse((440, 104, 460, 124), fill=(245, 197, 66, 255), outline=(212, 36, 38, 255), width=4)
    d.ellipse((444, 444, 456, 456), fill=(212, 36, 38, 255))
    sc_450 = sc.resize((450, 450), Image.Resampling.LANCZOS)
    save_drawable(sc_450.crop((213, 40, 237, 255)), "hand_second_full.webp", also_html=True)

    # 4. Bezel-Orbiting Ornament Second Indicator -> tight strip (x=211, y=8, w=28, h=220, pivot=(0.5, 0.986364))
    bz = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(bz)
    d.ellipse((432, 24, 468, 60), fill=(245, 197, 66, 95))
    bz = bz.filter(ImageFilter.GaussianBlur(radius=3.0))
    d = ImageDraw.Draw(bz)
    d.ellipse((438, 30, 462, 54), fill=(245, 197, 66, 255), outline=(212, 36, 38, 255), width=3)
    d.ellipse((445, 36, 455, 46), fill=(255, 255, 255, 255))
    bz_450 = bz.resize((450, 450), Image.Resampling.LANCZOS)
    save_drawable(bz_450.crop((211, 8, 239, 228)), "hand_second_bezel.webp", also_html=True)
    return bz_450


def make_config_icons_and_preview(bz_450: Image.Image) -> None:
    try:
        f_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        f_badge_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except Exception:
        f_badge = f_badge_sm = ImageFont.load_default()

    # 1. All 6 <UserConfigurations> Category Icons (72x72 WebP)
    for name, accent, symbol in [
        ("icon_color_theme.webp", (212, 36, 38, 255), "palette"),
        ("icon_clock_mode.webp", (245, 197, 66, 255), "clock"),
        ("icon_portrait_style.webp", (144, 202, 249, 255), "cat"),
        ("icon_lock_info.webp", (255, 213, 79, 255), "lock"),
        ("icon_snow_toggle.webp", (225, 245, 254, 255), "snow"),
        ("icon_power_mode.webp", (105, 240, 174, 255), "eco"),
    ]:
        ic = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
        d = ImageDraw.Draw(ic)
        d.ellipse((4, 4, 68, 68), fill=(20, 32, 28, 255), outline=accent, width=3)
        if symbol == "palette":
            d.pieslice((14, 14, 58, 58), start=180, end=300, fill=(212, 36, 38, 255))
            d.pieslice((14, 14, 58, 58), start=300, end=60, fill=(245, 197, 66, 255))
            d.pieslice((14, 14, 58, 58), start=60, end=180, fill=(46, 125, 50, 255))
            d.ellipse((14, 14, 58, 58), outline=(255, 255, 255, 220), width=2)
        elif symbol == "clock":
            d.line((36, 36, 36, 18), fill=(255, 255, 255, 255), width=4)
            d.line((36, 36, 52, 36), fill=accent, width=3)
            d.ellipse((33, 33, 39, 39), fill=accent)
        elif symbol == "cat":
            center_thumb = Image.open(RES_DRAWABLE / "centerpiece_primary.webp").convert("RGBA").resize((58, 58), Image.Resampling.LANCZOS)
            ic.alpha_composite(center_thumb, (7, 7))
        elif symbol == "lock":
            d.arc((24, 15, 48, 39), start=180, end=360, fill=accent, width=4)
            d.rounded_rectangle((20, 31, 52, 55), radius=6, fill=accent)
            d.ellipse((33, 39, 39, 45), fill=(20, 32, 28, 255))
        elif symbol == "eco":
            batt_ic = Image.open(RES_DRAWABLE / "ic_battery.webp").convert("RGBA").resize((42, 42), Image.Resampling.LANCZOS)
            ic.alpha_composite(batt_ic, (15, 15))
        else:
            for deg in range(0, 180, 60):
                rad = math.radians(deg)
                dx, dy = 18 * math.cos(rad), 18 * math.sin(rad)
                d.line((36 - dx, 36 - dy, 36 + dx, 36 + dy), fill=accent, width=3)
        save_drawable(ic, name)

    # 2. Option Swatch Icons for Galaxy Wearable Phone App & Watch Customize (72x72 WebP)
    for opt_name, c1, c2, c3 in [
        ("opt_theme_cranberry.webp", (212, 36, 38, 255), (245, 197, 66, 255), (22, 48, 32, 255)),
        ("opt_theme_frost.webp", (100, 181, 246, 255), (227, 242, 253, 255), (13, 27, 42, 255)),
        ("opt_theme_evergreen.webp", (46, 125, 50, 255), (255, 205, 210, 255), (15, 36, 23, 255)),
    ]:
        sw = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
        d = ImageDraw.Draw(sw)
        d.ellipse((4, 4, 68, 68), fill=c3, outline=c2, width=3)
        d.pieslice((12, 12, 60, 60), start=135, end=315, fill=c1)
        d.pieslice((12, 12, 60, 60), start=315, end=135, fill=c2)
        save_drawable(sw, opt_name)

    for opt_name, src_file in [
        ("opt_centerpiece_primary.webp", "centerpiece_primary.webp"),
        ("opt_centerpiece_alt.webp", "centerpiece_alt.webp"),
    ]:
        im = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((4, 4, 68, 68), fill=(22, 48, 32, 255), outline=(245, 197, 66, 255), width=3)
        thumb = Image.open(RES_DRAWABLE / src_file).convert("RGBA").resize((60, 60), Image.Resampling.LANCZOS)
        im.alpha_composite(thumb, (6, 6))
        save_drawable(im, opt_name)

    # Custom Phone Photo swatch icon (72x72 camera + frame badge)
    cam = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cam)
    cd.ellipse((4, 4, 68, 68), fill=(20, 32, 28, 255), outline=(144, 202, 249, 255), width=3)
    cd.rounded_rectangle((17, 25, 55, 51), radius=6, fill=(144, 202, 249, 255))
    cd.polygon([(26, 25), (30, 19), (42, 19), (46, 25)], fill=(144, 202, 249, 255))
    cd.ellipse((28, 30, 44, 46), fill=(20, 32, 28, 255), outline=(255, 255, 255, 255), width=2)
    save_drawable(cam, "opt_centerpiece_custom.webp")

    for opt_name, label, accent in [
        ("opt_clock_digital.webp", "08:52", (255, 255, 255, 255)),
        ("opt_clock_analog.webp", "ANLG", (245, 197, 66, 255)),
        ("opt_clock_hybrid.webp", "HYB", (255, 138, 128, 255)),
        ("opt_power_eco.webp", "ECO", (105, 240, 174, 255)),
        ("opt_power_max.webp", "MAX", (255, 213, 79, 255)),
        ("opt_power_vivid.webp", "VIVID", (128, 216, 255, 255)),
    ]:
        im = Image.new("RGBA", (72, 72), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse((4, 4, 68, 68), fill=(20, 32, 28, 255), outline=accent, width=3)
        if opt_name == "opt_clock_analog.webp":
            d.line((36, 38, 36, 17), fill=(212, 36, 38, 255), width=4)
            d.line((36, 38, 53, 28), fill=(245, 197, 66, 255), width=3)
            d.ellipse((33, 35, 39, 41), fill=(255, 255, 255, 255))
        elif opt_name == "opt_clock_hybrid.webp":
            d.text((36, 25), "08", font=f_badge_sm, fill=(255, 255, 255, 255), anchor="mm")
            d.line((36, 48, 24, 36), fill=(212, 36, 38, 255), width=3)
            d.line((36, 48, 51, 37), fill=(245, 197, 66, 255), width=3)
        else:
            use_f = f_badge_sm if len(label) >= 5 else f_badge
            d.text((36, 36), label, font=use_f, fill=accent, anchor="mm")
        save_drawable(im, opt_name)

    # 3. Transparent 450x450 Customize Highlight Overlays (Eliminates ResourceManager null-path errors!)
    hl_hi = (255, 255, 255, 235)
    hl_glow = (245, 197, 66, 150)

    # hl_color_theme: Outer theme ring + countdown pill
    hl = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    d.ellipse((6, 6, 444, 444), outline=hl_hi, width=4)
    d.rounded_rectangle((137, 29, 313, 61), radius=15, outline=hl_glow, width=3)
    save_drawable(hl, "hl_color_theme.webp")

    # hl_portrait_style: Center medallion ring
    hl = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    d.ellipse((147, 147, 303, 303), outline=hl_hi, width=4)
    save_drawable(hl, "hl_portrait_style.webp")

    # hl_lock_info: Outlines around all 5 info capsules
    hl = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    for box in [(26, 144, 144, 220), (306, 144, 424, 220), (26, 230, 144, 306), (306, 230, 424, 306), (117, 314, 333, 370)]:
        d.rounded_rectangle(box, radius=27, outline=hl_hi, width=3)
    save_drawable(hl, "hl_lock_info.webp")

    # hl_snow_toggle: Upper sky & snow perimeter arc
    hl = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    d.ellipse((18, 18, 432, 432), outline=hl_hi, width=3)
    save_drawable(hl, "hl_snow_toggle.webp")

    # hl_power_mode: Fairy bulb perimeter ring
    hl = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    d.ellipse((14, 14, 436, 436), outline=hl_hi, width=3)
    save_drawable(hl, "hl_power_mode.webp")

    # hl_clock_mode: Crisp frame around top Digital/Analog Clock zone so Clock tab is unmistakable!
    hl = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    d = ImageDraw.Draw(hl)
    d.rounded_rectangle((88, 54, 362, 143), radius=22, outline=hl_hi, width=4)
    save_drawable(hl, "hl_clock_mode.webp")

    # Rich 450x450 Watch Face Picker Preview (v2.1 Eco-Optimized + Zero-Clip Aligned Edition)
    prev = Image.open(RES_DRAWABLE / "dial_backdrop.webp").convert("RGBA")
    prev.alpha_composite(Image.open(RES_DRAWABLE / "sky_sunny.webp").convert("RGBA").resize((450, 450), Image.Resampling.BILINEAR))
    prev.alpha_composite(Image.open(RES_DRAWABLE / "fairy_lights_0.webp").convert("RGBA"))

    # Centerpiece medallion (x=151, y=151, 148x148)
    d = ImageDraw.Draw(prev)
    d.ellipse((151, 151, 299, 299), fill=(22, 48, 32, 225))
    center_img = Image.open(RES_DRAWABLE / "centerpiece_primary.webp").convert("RGBA").resize((148, 148), Image.Resampling.LANCZOS)
    prev.alpha_composite(center_img, (151, 151))
    d = ImageDraw.Draw(prev)
    d.ellipse((152, 152, 298, 298), outline=(245, 197, 66, 235), width=3)

    try:
        f_time = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
        f_date = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
        f_xmas = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        f_val = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        f_energy = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except Exception:
        f_time = f_date = f_xmas = f_val = f_energy = ImageFont.load_default()

    # Countdown pill (139, 31, 172, 28)
    d.rounded_rectangle((139, 31, 311, 59), radius=14, fill=(22, 48, 32, 230), outline=(212, 36, 38, 235), width=2)
    d.text((225, 45), "40D TO XMAS", font=f_xmas, fill=(245, 197, 66, 255), anchor="mm")

    # Huge Digital Time + Bold Date
    d.text((225, 88), "08:52", font=f_time, fill=(255, 255, 255, 255), anchor="mm")
    d.text((225, 128), "SUN · NOV 15", font=f_date, fill=(245, 197, 66, 255), anchor="mm")

    # Slot 1: Weather (x=28, y=146, w=114, h=72, r=26) — Icon & Temp centered on y=182 midline
    d.rounded_rectangle((28, 146, 142, 218), radius=26, fill=(22, 48, 32, 230), outline=(245, 197, 66, 185), width=2)
    wx_ic = Image.open(RES_DRAWABLE / "wx_partly_day.webp").convert("RGBA").resize((40, 40), Image.Resampling.LANCZOS)
    prev.alpha_composite(wx_ic, (36, 162))
    d = ImageDraw.Draw(prev)
    d.text((108, 182), "19°", font=f_val, fill=(255, 255, 255, 255), anchor="mm")

    # Slot 2: Sun Heat / UV (x=308, y=146, w=114, h=72, r=26) — Unified top row y=172 + bar y=197
    d.rounded_rectangle((308, 146, 422, 218), radius=26, fill=(22, 48, 32, 230), outline=(245, 197, 66, 185), width=2)
    uv_ic = Image.open(RES_DRAWABLE / "ic_uv_sun.webp").convert("RGBA").resize((30, 30), Image.Resampling.LANCZOS)
    prev.alpha_composite(uv_ic, (320, 157))
    d = ImageDraw.Draw(prev)
    d.text((382, 172), "UV 4", font=f_val, fill=(255, 213, 79, 255), anchor="mm")
    d.rounded_rectangle((322, 197, 408, 204), radius=3, fill=(255, 255, 255, 55))
    d.rounded_rectangle((322, 197, 362, 204), radius=3, fill=(255, 179, 0, 255))

    # Slot 3: Heart Rate (x=28, y=232, w=114, h=72, r=26) — Unified top row y=258 + bar y=283
    d.rounded_rectangle((28, 232, 142, 304), radius=26, fill=(22, 48, 32, 230), outline=(245, 197, 66, 185), width=2)
    hr_ic = Image.open(RES_DRAWABLE / "ic_heart.webp").convert("RGBA").resize((30, 30), Image.Resampling.LANCZOS)
    prev.alpha_composite(hr_ic, (40, 243))
    d = ImageDraw.Draw(prev)
    d.text((102, 258), "83", font=f_val, fill=(255, 138, 128, 255), anchor="mm")
    d.rounded_rectangle((42, 283, 128, 290), radius=3, fill=(255, 255, 255, 55))
    d.rounded_rectangle((42, 283, 76, 290), radius=3, fill=(255, 82, 82, 255))

    # Slot 4: Watch Battery (x=308, y=232, w=114, h=72, r=26) — Unified top row y=258 + bar y=283 (Zero Clip!)
    d.rounded_rectangle((308, 232, 422, 304), radius=26, fill=(22, 48, 32, 230), outline=(245, 197, 66, 185), width=2)
    bt_ic = Image.open(RES_DRAWABLE / "ic_battery.webp").convert("RGBA").resize((30, 30), Image.Resampling.LANCZOS)
    prev.alpha_composite(bt_ic, (320, 243))
    d = ImageDraw.Draw(prev)
    d.text((381, 258), "83%", font=f_val, fill=(105, 240, 174, 255), anchor="mm")
    d.rounded_rectangle((322, 283, 408, 290), radius=3, fill=(255, 255, 255, 55))
    d.rounded_rectangle((322, 283, 394, 290), radius=3, fill=(105, 240, 174, 255))

    # Slot 5: Energy Score / Steps (x=119, y=316, w=212, h=52, r=26) + UNCLIPPED curved bottom arc (r=186 -> 39..411)
    d.rounded_rectangle((119, 316, 331, 368), radius=26, fill=(22, 48, 32, 230), outline=(245, 197, 66, 190), width=2)
    en_ic = Image.open(RES_DRAWABLE / "ic_energy.webp").convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)
    prev.alpha_composite(en_ic, (148, 326))
    d = ImageDraw.Draw(prev)
    d.text((238, 342), "12,606", font=f_energy, fill=(255, 255, 255, 255), anchor="mm")
    d.arc((39, 39, 411, 411), start=65, end=115, fill=(255, 255, 255, 65), width=7)
    d.arc((39, 39, 411, 411), start=68, end=115, fill=(245, 197, 66, 255), width=7)

    # Subtle snow + bezel ornament
    prev.alpha_composite(Image.open(RES_DRAWABLE / "snow_00.webp").convert("RGBA").resize((450, 450), Image.Resampling.BILINEAR))
    prev.alpha_composite(bz_450)
    save_drawable(prev, "preview.png")

    # Export clean circular README documentation previews (Active + AOD)
    circ_mask = Image.new("L", (450, 450), 0)
    ImageDraw.Draw(circ_mask).ellipse((0, 0, 449, 449), fill=255)
    doc_active = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    doc_active.paste(prev, (0, 0), circ_mask)
    doc_active.save(DOCS_IMAGES / "preview_active.png", format="PNG", optimize=True)

    doc_aod = Image.new("RGBA", (450, 450), (0, 0, 0, 255))
    aod_art = Image.open(RES_DRAWABLE / "centerpiece_aod.webp").convert("RGBA").resize((148, 148), Image.Resampling.LANCZOS)
    r_ch, g_ch, b_ch, a_ch = aod_art.split()
    a_ch = a_ch.point(lambda p: int(p * (215 / 255.0)))
    doc_aod.alpha_composite(Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch)), (151, 151))
    da = ImageDraw.Draw(doc_aod)
    da.text((225, 45), "40D TO XMAS", font=f_xmas, fill=(245, 197, 66, 175), anchor="mm")
    da.text((225, 88), "08:52", font=f_time, fill=(255, 255, 255, 215), anchor="mm")
    da.text((225, 128), "SUN · NOV 15", font=f_date, fill=(245, 197, 66, 175), anchor="mm")
    da.text((85, 182), "19°", font=f_val, fill=(255, 255, 255, 185), anchor="mm")
    da.text((365, 268), "83%", font=f_val, fill=(105, 240, 174, 185), anchor="mm")
    da.text((225, 342), "12,606", font=f_val, fill=(255, 255, 255, 185), anchor="mm")
    doc_aod_out = Image.new("RGBA", (450, 450), (0, 0, 0, 0))
    doc_aod_out.paste(doc_aod, (0, 0), circ_mask)
    doc_aod_out.save(DOCS_IMAGES / "preview_aod.png", format="PNG", optimize=True)


if __name__ == "__main__":
    # Clean stale drawables first so unused legacy files don't linger in APK!
    for old in RES_DRAWABLE.iterdir():
        if old.is_file():
            old.unlink()
    make_portraits()
    make_dial_backdrop_and_ticks()
    make_weather_and_complication_icons()
    make_live_weather_sky_layers()
    make_seamless_weather_particle_loops()
    bz_450 = make_analog_hands()
    make_config_icons_and_preview(bz_450)
    files = sorted(RES_DRAWABLE.iterdir())
    total_kb = sum(f.stat().st_size for f in files) / 1024.0
    print(f"Generated {len(files)} WFF v2.1 Eco-Optimized drawable resources in {RES_DRAWABLE} ({total_kb:.1f} KB on disk)")
