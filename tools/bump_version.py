#!/usr/bin/env python3
"""
Synchronized Version Bumper & Checker for Galaxy Watch 8 Holiday WFF v4
=======================================================================
Keeps Android APK metadata, optimizer reports, and the web simulator badge
in 1:1 lockstep across commits:
  1. watchface/app/build.gradle.kts      (versionCode & versionName)
  2. tools/optimize_watchface.py         ("version": "X.Y.Z")
  3. html/index.html                     (<code id="appVersionBadge">vX.Y.Z</code>)
  4. watchface/optimization_report.json  ("version": "X.Y.Z", when present)

Usage:
  ./tools/bump_version.py                 # Bump patch (2.3.0 -> 2.3.1) & versionCode +1
  ./tools/bump_version.py --part minor    # Bump minor (2.3.0 -> 2.4.0) & versionCode +1
  ./tools/bump_version.py --part major    # Bump major (2.3.0 -> 3.0.0) & versionCode +1
  ./tools/bump_version.py --set 2.5.0     # Explicit versionName & versionCode +1
  ./tools/bump_version.py --check         # Verify all tracked files share the exact version
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRADLE_KTS = ROOT / "watchface" / "app" / "build.gradle.kts"
OPTIMIZER_PY = ROOT / "tools" / "optimize_watchface.py"
INDEX_HTML = ROOT / "html" / "index.html"
REPORT_JSON = ROOT / "watchface" / "optimization_report.json"

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
GRADLE_CODE_RE = re.compile(r"(versionCode\s*=\s*)(\d+)")
GRADLE_NAME_RE = re.compile(r'(versionName\s*=\s*")([^"]+)(")')
OPT_VER_RE = re.compile(r'("version"\s*:\s*")([^"]+)(")')
HTML_BADGE_RE = re.compile(r'(<code\s+id="appVersionBadge">v?)([^<]+)(</code>)')


def read_versions() -> dict:
    gradle_txt = GRADLE_KTS.read_text(encoding="utf-8")
    code_m = GRADLE_CODE_RE.search(gradle_txt)
    name_m = GRADLE_NAME_RE.search(gradle_txt)
    if not code_m or not name_m:
        raise RuntimeError(f"Could not parse versionCode/versionName from {GRADLE_KTS}")

    opt_txt = OPTIMIZER_PY.read_text(encoding="utf-8")
    opt_m = OPT_VER_RE.search(opt_txt)
    if not opt_m:
        raise RuntimeError(f"Could not parse report version from {OPTIMIZER_PY}")

    html_txt = INDEX_HTML.read_text(encoding="utf-8")
    html_m = HTML_BADGE_RE.search(html_txt)
    if not html_m:
        raise RuntimeError(f"Could not find #appVersionBadge in {INDEX_HTML}")

    data = {
        "version_code": int(code_m.group(2)),
        "gradle_version": name_m.group(2).strip(),
        "optimizer_version": opt_m.group(2).strip(),
        "html_version": html_m.group(2).strip().lstrip("v"),
    }

    if REPORT_JSON.is_file():
        rep = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        if "version" in rep:
            data["report_version"] = str(rep["version"]).strip()

    return data


def compute_next_semver(current: str, part: str) -> str:
    m = SEMVER_RE.match(current)
    if not m:
        raise ValueError(f"Invalid semantic version '{current}' (expected MAJOR.MINOR.PATCH)")
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def write_version(new_version: str, new_code: int) -> None:
    if not SEMVER_RE.match(new_version):
        raise ValueError(f"Target version '{new_version}' must match MAJOR.MINOR.PATCH")

    gradle_txt = GRADLE_KTS.read_text(encoding="utf-8")
    gradle_txt = GRADLE_CODE_RE.sub(rf"\g<1>{new_code}", gradle_txt, count=1)
    gradle_txt = GRADLE_NAME_RE.sub(rf"\g<1>{new_version}\g<3>", gradle_txt, count=1)
    GRADLE_KTS.write_text(gradle_txt, encoding="utf-8")

    opt_txt = OPTIMIZER_PY.read_text(encoding="utf-8")
    opt_txt = OPT_VER_RE.sub(rf"\g<1>{new_version}\g<3>", opt_txt, count=1)
    OPTIMIZER_PY.write_text(opt_txt, encoding="utf-8")

    html_txt = INDEX_HTML.read_text(encoding="utf-8")
    html_txt = HTML_BADGE_RE.sub(f'<code id="appVersionBadge">v{new_version}</code>', html_txt, count=1)
    INDEX_HTML.write_text(html_txt, encoding="utf-8")

    if REPORT_JSON.is_file():
        rep = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        rep["version"] = new_version
        REPORT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")


def check_sync() -> tuple[bool, dict]:
    info = read_versions()
    expected = info["gradle_version"]
    ok = (
        info["optimizer_version"] == expected
        and info["html_version"] == expected
        and info.get("report_version", expected) == expected
    )
    return ok, info


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump or verify Watch 8 project version in lockstep.")
    parser.add_argument(
        "--part",
        choices=("patch", "minor", "major"),
        default="patch",
        help="Semantic version segment to increment (default: patch).",
    )
    parser.add_argument("--set", dest="set_version", help="Set an explicit MAJOR.MINOR.PATCH version.")
    parser.add_argument("--version-code", type=int, help="Explicit integer versionCode override.")
    parser.add_argument("--check", action="store_true", help="Verify all files share the same version without editing.")
    args = parser.parse_args()

    if args.check:
        ok, info = check_sync()
        if not ok:
            print(f"[version] ERROR: Version mismatch detected: {info}", file=sys.stderr)
            return 1
        print(f"[version] OK: v{info['gradle_version']} (versionCode={info['version_code']}) synchronized across all files.")
        return 0

    info = read_versions()
    old_ver = info["gradle_version"]
    old_code = info["version_code"]
    new_ver = args.set_version.lstrip("v") if args.set_version else compute_next_semver(old_ver, args.part)
    new_code = args.version_code if args.version_code is not None else (old_code + 1)

    write_version(new_ver, new_code)
    print(f"[version] Bumped v{old_ver} (code {old_code}) -> v{new_ver} (code {new_code})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
