#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BLENDER_BIN="${BLENDER_BIN:-/home/antigravity/tools/blender-4.2.23-linux-x64/blender}"
if [ ! -x "$BLENDER_BIN" ]; then
    BLENDER_BIN="$(command -v blender)"
fi

echo "[1/2] Generating procedural high-res textures..."
python3 "$REPO_ROOT/src/model_s_plaid/textures.py"

echo "[2/2] Building master 2024 Tesla Model S Plaid (Ultra Red) .blend..."
"$BLENDER_BIN" -b --python-exit-code 1 --python "$REPO_ROOT/src/model_s_plaid/build_all.py"
