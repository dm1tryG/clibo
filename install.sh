#!/usr/bin/env bash
# clibo installer — installs the `clibo` command from GitHub.
set -euo pipefail

REPO="https://github.com/dm1tryG/clibo.git"

echo "📦 Installing clibo..."

if command -v uv >/dev/null 2>&1; then
    uv tool install --from "git+${REPO}" clibo
elif command -v pipx >/dev/null 2>&1; then
    pipx install "git+${REPO}"
else
    echo "✗ Need 'uv' or 'pipx' installed first." >&2
    echo "  uv:   https://docs.astral.sh/uv/" >&2
    echo "  pipx: https://pipx.pypa.io/" >&2
    exit 1
fi

echo "✓ clibo installed. Try:  clibo --help"
