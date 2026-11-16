#!/usr/bin/env bash
# ==============================================================================
# Configure Tracked Git Hooks (.githooks/) for Galaxy Watch 8 Holiday WFF v4
# ==============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

chmod +x \
  .githooks/pre-commit \
  tools/bump_version.py \
  tools/set_custom_art.py \
  tools/optimize_watchface.py \
  optimize_watchface.sh \
  watchface/install_to_watch8.sh

git config core.hooksPath .githooks

echo "✅ Git hooks installed (core.hooksPath -> .githooks)"
echo "   • Default commit (auto patch bump + tests): git commit -m \"...\""
echo "   • Minor / Major bump on commit            : BUMP=minor git commit -m \"...\""
echo "   • Skip version bump for docs-only commit  : SKIP_VERSION_BUMP=1 git commit -m \"...\""
