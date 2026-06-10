@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist ".env" (
  echo [ERROR] .env not found.
  echo Copy .env.example to .env and set your ANTHROPIC_API_KEY, then run again.
  echo   copy .env.example .env
  pause
  exit /b 1
)

findstr /C:"sk-ant-your-key-here" .env >nul
if %errorlevel%==0 (
  echo [ERROR] ANTHROPIC_API_KEY in .env is still the placeholder.
  echo Edit .env and set a real key, then run again.
  pause
  exit /b 1
)

where python >nul 2>nul
if %errorlevel% neq 0 (
  echo [ERROR] Python not found on PATH. Install Python 3.11+ and retry.
  pause
  exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
  echo [ERROR] Node.js not found on PATH. Install Node 18+ and retry.
  pause
  exit /b 1
)

if not exist "venv" (
  echo Creating virtual environment...
  python -m venv venv
)

echo Installing backend dependencies...
venv\Scripts\python.exe -m pip install --quiet --upgrade pip
venv\Scripts\python.exe -m pip install --quiet -r backend\requirements.txt
if %errorlevel% neq 0 (
  echo [ERROR] Backend dependency install failed.
  pause
  exit /b 1
)

echo Seeding database...
venv\Scripts\python.exe data\init_db.py

echo Installing frontend dependencies...
pushd frontend
call npm install
if %errorlevel% neq 0 (
  echo [ERROR] Frontend dependency install failed.
  popd
  pause
  exit /b 1
)
popd

echo.
echo Launching servers in separate windows...
start "NovaMart Backend" cmd /k "cd /d "%~dp0backend" && "%~dp0venv\Scripts\python.exe" -m uvicorn main:app --port 8000"
start "NovaMart Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ============================================
echo   NovaMart AI Refund Agent is starting.
echo   Frontend : http://localhost:5173
echo   Backend  : http://localhost:8000/docs
echo ============================================
echo Close the two opened windows to stop the servers.
echo.
pause
