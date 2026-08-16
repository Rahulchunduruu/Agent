#!/usr/bin/env bash
# ============================================
# AI Agent Bot - One-command setup (Linux / Mac)
# Usage: bash setup.sh
# ============================================
set -e

echo "=== [1/4] Creating virtual environment ==="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Created .venv"
else
    echo ".venv already exists, skipping"
fi

source .venv/bin/activate

echo "=== [2/4] Installing pinned Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [3/4] Installing Playwright Chromium browser binaries ==="
playwright install chromium

echo "=== [4/4] Installing Playwright system dependencies ==="
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Requires sudo on Linux for system libraries (libnss3, libatk, etc.)
    sudo playwright install-deps chromium || playwright install-deps chromium
else
    echo "macOS detected - system deps not required, skipping install-deps"
fi

echo ""
echo "=== Setup complete! ==="
echo "Next steps:"
echo "  1. Create your .env file (see README.md)"
echo "  2. Add Gmail credentials.json + token.json"
echo "  3. Run: streamlit run app.py"
