#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/jdk/bin:$HOME/.local/bin:/usr/bin:/bin:$PATH"
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
    exec uv run --with pillow python3 tools/optimize_watchface.py "$@"
else
    exec python3 tools/optimize_watchface.py "$@"
fi
