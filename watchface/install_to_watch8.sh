#!/usr/bin/env bash
# ==============================================================================
# Galaxy Watch 8 Holiday Watch Face (WFF v4) — Wireless ADB Installer
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Locate adb automatically (ANDROID_HOME, standard SDK paths, or system PATH)
if [[ -n "${ANDROID_HOME:-}" && -x "${ANDROID_HOME}/platform-tools/adb" ]]; then
    ADB="${ANDROID_HOME}/platform-tools/adb"
elif [[ -x "${HOME}/Android/Sdk/platform-tools/adb" ]]; then
    ADB="${HOME}/Android/Sdk/platform-tools/adb"
elif [[ -x "${HOME}/Library/Android/sdk/platform-tools/adb" ]]; then
    ADB="${HOME}/Library/Android/sdk/platform-tools/adb"
elif command -v adb >/dev/null 2>&1; then
    ADB="$(command -v adb)"
else
    echo "ERROR: 'adb' not found. Install Android SDK Platform-Tools or set ANDROID_HOME." >&2
    exit 1
fi

# Prefer top-level prebuilt APK, falling back to release or debug build output
APK_PATH="${ROOT_DIR}/watch8-holiday-xmas.apk"
if [[ ! -f "${APK_PATH}" ]]; then
    if [[ -f "${SCRIPT_DIR}/app/build/outputs/apk/release/app-release.apk" ]]; then
        APK_PATH="${SCRIPT_DIR}/app/build/outputs/apk/release/app-release.apk"
    elif [[ -f "${SCRIPT_DIR}/app/build/outputs/apk/debug/app-debug.apk" ]]; then
        APK_PATH="${SCRIPT_DIR}/app/build/outputs/apk/debug/app-debug.apk"
    else
        echo "ERROR: Compiled APK not found. Run './optimize_watchface.sh' first." >&2
        exit 1
    fi
fi

echo "========================================================"
echo "  Galaxy Watch 8 Holiday Watch Face (WFF v4) Installer"
echo "  APK: ${APK_PATH}"
echo "========================================================"
echo ""
echo "On your Galaxy Watch 8:"
echo "  1. Connect your Watch 8 to the same Wi-Fi network as your computer."
echo "  2. Go to Settings -> About watch -> Software information"
echo "     and tap 'Software version' 7 times to unlock Developer options."
echo "  3. Go to Settings -> Developer options -> enable 'ADB debugging'"
echo "     -> open 'Wireless debugging' -> enable it."
echo "  4. Tap 'Pair new device' (first time only) to view IP, Pair Port & 6-digit code."
echo ""

WATCH_IP="${1:-}"
CONNECT_PORT="${2:-}"

# Auto-detect an already connected Watch 8 or active Wireless ADB mDNS endpoint when no IP is passed
if [[ -z "${WATCH_IP}" ]]; then
    EXISTING_SERIAL="$("${ADB}" devices | awk 'NR>1 && $2=="device" {print $1; exit}')"
    if [[ -z "${EXISTING_SERIAL}" ]]; then
        MDNS_EP="$("${ADB}" mdns services 2>/dev/null | awk '/_adb-tls-connect\._tcp/ {print $3; exit}')"
        if [[ -n "${MDNS_EP}" ]]; then
            echo "-> Discovered Watch 8 over mDNS (${MDNS_EP}), connecting..."
            "${ADB}" connect "${MDNS_EP}" >/dev/null || true
            EXISTING_SERIAL="$("${ADB}" devices | awk 'NR>1 && $2=="device" {print $1; exit}')"
        fi
    fi
    if [[ -n "${EXISTING_SERIAL}" ]]; then
        echo "-> Found active Watch 8 ADB connection: ${EXISTING_SERIAL}"
        echo "-> Installing Watch Face APK..."
        "${ADB}" -s "${EXISTING_SERIAL}" install -r "${APK_PATH}"
        echo ""
        echo "SUCCESS! Holiday Pet Xmas is installed on your Galaxy Watch 8 (${EXISTING_SERIAL})."
        exit 0
    fi
    read -r -p "Enter Watch IP address (e.g. 192.168.1.88): " WATCH_IP
fi

read -r -p "Do you need to pair this computer with your Watch 8 first? [y/N]: " NEED_PAIR
if [[ "${NEED_PAIR}" =~ ^[Yy]$ ]]; then
    read -r -p "Enter Pairing Port shown under 'Pair new device' (e.g. 39123): " PAIR_PORT
    read -r -p "Enter 6-digit Wi-Fi Pairing Code: " PAIR_CODE
    "${ADB}" pair "${WATCH_IP}:${PAIR_PORT}" "${PAIR_CODE}"
fi

if [[ -z "${CONNECT_PORT}" ]]; then
    read -r -p "Enter Wireless Debugging Connect Port (main Wireless debugging screen): " CONNECT_PORT
fi

echo ""
echo "-> Connecting to ${WATCH_IP}:${CONNECT_PORT}..."
"${ADB}" connect "${WATCH_IP}:${CONNECT_PORT}"

echo "-> Installing Watch Face APK..."
"${ADB}" -s "${WATCH_IP}:${CONNECT_PORT}" install -r "${APK_PATH}"

echo ""
echo "SUCCESS! Holiday Pet Xmas is installed on your Galaxy Watch 8."
echo "Long-press your watch face -> swipe right to '+ Add watch face' ->"
echo "scroll to 'Downloaded' -> tap 'Holiday Pet Xmas' -> tap 'Customize'!"
