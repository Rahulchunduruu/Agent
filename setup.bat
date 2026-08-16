@echo off
REM ============================================
REM AI Agent Bot - One-command setup (Windows)
REM Usage: setup.bat
REM ============================================

echo === [1/3] Creating virtual environment ===
if not exist ".venv" (
    python -m venv .venv
    echo Created .venv
) else (
    echo .venv already exists, skipping
)

call .venv\Scripts\activate.bat

echo === [2/3] Installing pinned Python dependencies ===
pip install --upgrade pip
pip install -r requirements.txt

echo === [3/3] Installing Playwright Chromium browser binaries ===
REM NOTE: 'playwright install-deps' is Linux-only and not needed on Windows
playwright install chromium

echo.
echo === Setup complete! ===
echo Next steps:
echo   1. Create your .env file (see README.md)
echo   2. Add Gmail credentials.json + token.json
echo   3. Run: streamlit run app.py
