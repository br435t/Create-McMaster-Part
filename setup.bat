@echo off
REM ============================================================
REM  Create-McMaster-Part - one-click setup
REM  Double-click this file. It creates the Python virtual
REM  environment the scraper needs, installs dependencies
REM  (works behind the corporate SSL proxy), and logs in to
REM  McMaster. Pass "nologin" to skip the McMaster login step.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   Create-McMaster-Part  -  one-click setup
echo ============================================================
echo.

REM --- 1. Find a Python interpreter -------------------------------------
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo [ERROR] Python was not found on this machine.
  echo.
  echo   Install Python 3.10+ from https://www.python.org/downloads/
  echo   ^(tick "Add python.exe to PATH" during install^), then run this again.
  echo.
  pause
  exit /b 1
)
echo [1/4] Python found:
%PY% --version
echo.

REM --- 2. Create the virtual environment -------------------------------
if exist ".venv\Scripts\python.exe" (
  echo [2/4] Virtual environment .venv already exists - reusing it.
) else (
  echo [2/4] Creating virtual environment .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment.
    pause
    exit /b 1
  )
)
set "VENV_PY=%CD%\.venv\Scripts\python.exe"
echo.

REM --- 3. Install dependencies (corporate-SSL safe) --------------------
REM  pip-system-certs makes pip trust the Windows cert store (the corporate
REM  root CA lives there), so later installs verify normally. It is
REM  bootstrapped with --trusted-host because that first install is what
REM  the SSL interception blocks.
echo [3/4] Installing dependencies ...
"%VENV_PY%" -m pip install --disable-pip-version-check --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org pip-system-certs
if errorlevel 1 (
  echo [ERROR] Could not install pip-system-certs. See messages above.
  pause
  exit /b 1
)
"%VENV_PY%" -m pip install --disable-pip-version-check -r scraper\requirements.txt
if errorlevel 1 (
  echo [ERROR] Could not install scraper requirements. See messages above.
  pause
  exit /b 1
)
echo.

REM --- 4. Log in to McMaster (opens Edge) ------------------------------
if /i "%~1"=="nologin" (
  echo [4/4] Skipping McMaster login ^(nologin^). You can run it later with:
  echo        .venv\Scripts\python.exe scraper\mcmaster_scraper.py login
) else (
  echo [4/4] Opening McMaster login - sign in when the browser appears.
  echo        ^(This is optional; the tool also prompts to log in on demand.^)
  "%VENV_PY%" scraper\mcmaster_scraper.py login
)
echo.

echo ============================================================
echo   Setup complete.
echo.
echo   To create a part:
echo     1. Open NX 2506 with an active Teamcenter session.
echo     2. File ^> Execute ^> NX Open...
echo     3. Select:  %CD%\create_VENDOR_part.py
echo ============================================================
echo.
pause
