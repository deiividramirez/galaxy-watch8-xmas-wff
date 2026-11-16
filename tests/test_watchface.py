#!/usr/bin/env python3
"""
Automated Parity, Regression & Custom-Art Tests for Galaxy Watch 8 Holiday WFF v4
=================================================================================
Run locally or in CI:
  uv run --with pillow python3 -m unittest discover -s tests -v
  # or: python3 -m unittest discover -s tests -v
"""

import importlib.util
import re
import shutil
import subprocess
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "html"
INDEX_HTML = HTML_DIR / "index.html"
SIMULATOR_JS = HTML_DIR / "simulator.js"
WATCHFACE_XML = ROOT / "watchface" / "app" / "src" / "main" / "res" / "raw" / "watchface.xml"
DRAWABLE_DIR = ROOT / "watchface" / "app" / "src" / "main" / "res" / "drawable-nodpi"
STRINGS_EN = ROOT / "watchface" / "app" / "src" / "main" / "res" / "values" / "strings.xml"
STRINGS_ES = ROOT / "watchface" / "app" / "src" / "main" / "res" / "values-es" / "strings.xml"
SET_CUSTOM_ART = ROOT / "tools" / "set_custom_art.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class WatchFaceProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wff_tree = ET.parse(WATCHFACE_XML)
        cls.wff_root = cls.wff_tree.getroot()
        cls.html_text = INDEX_HTML.read_text(encoding="utf-8")
        cls.js_text = SIMULATOR_JS.read_text(encoding="utf-8")

    def test_simulator_js_syntax(self) -> None:
        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node not installed in current environment")
        res = subprocess.run([node_bin, "--check", str(SIMULATOR_JS)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, msg=f"simulator.js syntax error:\n{res.stderr}")

    def test_html_and_js_asset_references_exist(self) -> None:
        refs = set(re.findall(r'["\'](assets/[a-zA-Z0-9_./-]+\.(?:png|webp|svg|jpg))["\']', self.html_text))
        refs.update(re.findall(r'["\'](assets/[a-zA-Z0-9_./-]+\.(?:png|webp|svg|jpg))["\']', self.js_text))
        self.assertGreaterEqual(len(refs), 10, "Expected simulator asset references to be discovered")
        for rel in sorted(refs):
            target = HTML_DIR / rel
            self.assertTrue(target.is_file(), f"Missing simulator asset referenced in HTML/JS: {rel}")
            self.assertGreater(target.stat().st_size, 0, f"Empty simulator asset file: {rel}")

    def test_html_and_wff_complication_bounds_parity(self) -> None:
        html_slots = {}
        for sid, bounds_str in re.findall(
            r'data-slot-id="(\d+)"\s+data-wff-bounds="([^"]+)"', self.html_text
        ):
            kv = dict(re.findall(r"([xywh])=(\d+)", bounds_str))
            html_slots[sid] = (int(kv["x"]), int(kv["y"]), int(kv["w"]), int(kv["h"]))

        xml_slots = {}
        for slot in self.wff_root.iter("ComplicationSlot"):
            sid = slot.attrib["slotId"]
            xml_slots[sid] = (
                int(slot.attrib["x"]),
                int(slot.attrib["y"]),
                int(slot.attrib["width"]),
                int(slot.attrib["height"]),
            )

        self.assertEqual(set(xml_slots.keys()), {"1", "2", "3", "4", "5"})
        self.assertEqual(html_slots, xml_slots, "HTML simulator slot bounds drifted from watchface.xml!")

    def test_no_nested_configurations_in_scene_and_icons_present(self) -> None:
        """Guards against Samsung EditorActivity ConcurrentModificationException & ResourceManager errors."""
        cfg_tags = {"ListConfiguration", "BooleanConfiguration", "ColorConfiguration"}
        drawable_stems = {p.stem for p in DRAWABLE_DIR.iterdir() if p.is_file()}

        user_cfgs = self.wff_root.find("UserConfigurations")
        self.assertIsNotNone(user_cfgs)
        for cfg in user_cfgs:
            if cfg.tag in cfg_tags:
                icon = cfg.attrib.get("icon", "")
                highlight = cfg.attrib.get("highlight", "")
                self.assertTrue(icon, f"{cfg.tag} id={cfg.attrib.get('id')} missing icon attribute")
                self.assertTrue(highlight, f"{cfg.tag} id={cfg.attrib.get('id')} missing highlight attribute")
                self.assertIn(icon, drawable_stems, f"Missing drawable for icon={icon}")
                self.assertIn(highlight, drawable_stems, f"Missing drawable for highlight={highlight}")
                for opt in cfg:
                    opt_icon = opt.attrib.get("icon", "")
                    if opt_icon:
                        self.assertIn(opt_icon, drawable_stems, f"Missing option swatch icon={opt_icon}")

        scene = self.wff_root.find("Scene")
        self.assertIsNotNone(scene)

        def walk(node: ET.Element, inside_cfg: str | None) -> None:
            current_cfg = inside_cfg
            if node.tag in cfg_tags:
                self.assertIsNone(
                    inside_cfg,
                    f"Nested {node.tag} (id={node.attrib.get('id')}) inside {inside_cfg} will crash Samsung EditorActivity!",
                )
                current_cfg = f"{node.tag}:{node.attrib.get('id')}"
            for child in node:
                walk(child, current_cfg)

        walk(scene, None)

    def test_no_tap_animation_triggers_and_fps_cap(self) -> None:
        for ctrl in self.wff_root.iter("AnimationController"):
            play_attr = ctrl.attrib.get("play", "")
            self.assertNotIn(
                "TAP",
                play_attr.split(),
                "TAP on AnimationController causes touch lag on full-screen sprite layers!",
            )
        for anim in self.wff_root.iter("AnimatedImages"):
            fps = float(anim.attrib.get("fps", "15"))
            self.assertLessEqual(fps, 15.0, f"AnimatedImages fps={fps} exceeds 15 FPS battery rule!")

    def test_localization_strings_parity_and_format_safety(self) -> None:
        def parse_strings(path: Path) -> dict[str, str]:
            root = ET.parse(path).getroot()
            return {el.attrib["name"]: (el.text or "") for el in root.findall("string")}

        en = parse_strings(STRINGS_EN)
        es = parse_strings(STRINGS_ES)
        self.assertEqual(set(en.keys()), set(es.keys()), "English and Spanish strings.xml keys do not match!")

        for locale_name, table in [("en", en), ("es", es)]:
            for key, val in table.items():
                self.assertNotIn(
                    "%",
                    val,
                    f"Raw '%' found in {locale_name} string '{key}' ('{val}') — causes Android UnknownFormatConversionException!",
                )

        # Every displayName / screenReaderText in UserConfigurations & ComplicationSlot must exist in strings.xml
        for el in self.wff_root.iter():
            for attr in ("displayName", "screenReaderText"):
                if attr in el.attrib:
                    ref_key = el.attrib[attr]
                    self.assertIn(ref_key, en, f"{el.tag} {attr}='{ref_key}' missing from strings.xml!")

    def test_custom_art_importer_synthesizes_burn_in_safe_aod(self) -> None:
        art_mod = _load_module(SET_CUSTOM_ART, "set_custom_art")
        # Create a bright synthetic test portrait (500x380 non-square)
        synth = Image.new("RGBA", (500, 380), (220, 45, 55, 255))
        d = ImageDraw.Draw(synth)
        d.ellipse((140, 60, 360, 300), fill=(245, 220, 180, 255), outline=(255, 255, 255, 255), width=6)
        d.ellipse((195, 130, 225, 160), fill=(25, 35, 45, 255))
        d.ellipse((275, 130, 305, 160), fill=(25, 35, 45, 255))

        sq = art_mod.center_crop_square(synth, crop_ratio=0.95)
        self.assertEqual(sq.size[0], sq.size[1])

        medallion = art_mod.apply_circular_medallion(sq, size=360)
        self.assertEqual(medallion.size, (360, 360))
        # Corners outside circular medallion must be completely transparent
        self.assertEqual(medallion.getpixel((0, 0))[3], 0)

        aod = art_mod.synthesize_burn_in_safe_aod(medallion, size=360)
        self.assertEqual(aod.size, (360, 360))
        # Verify synthesized AOD outline has very low On-Pixel Ratio (< 10%)
        lum_sum = 0.0
        pixels = aod.get_flattened_data() if hasattr(aod, "get_flattened_data") else aod.getdata()
        for r, g, b, a in pixels:
            lum_sum += ((r + g + b) / (3.0 * 255.0)) * (a / 255.0)
        opr_pct = (lum_sum / (360 * 360)) * 100.0
        self.assertLess(opr_pct, 10.0, f"Synthesized AOD OPR {opr_pct:.2f}% is too bright for OLED burn-in safety!")

    def test_no_hardcoded_local_home_paths(self) -> None:
        check_paths = [
            ROOT / "README.md",
            ROOT / "AGENTS.md",
            ROOT / "optimize_watchface.sh",
            ROOT / "watchface" / "install_to_watch8.sh",
            ROOT / "tools" / "optimize_watchface.py",
            ROOT / "tools" / "set_custom_art.py",
            INDEX_HTML,
            SIMULATOR_JS,
            WATCHFACE_XML,
        ]
        # Build pattern dynamically so this test file itself doesn't hardcode a user directory
        forbidden_prefix = "/" + "home" + "/"
        for p in check_paths:
            txt = p.read_text(encoding="utf-8")
            self.assertNotIn(
                forbidden_prefix,
                txt,
                f"Hardcoded Linux home path leaked in {p.relative_to(ROOT)}!",
            )


if __name__ == "__main__":
    unittest.main()
