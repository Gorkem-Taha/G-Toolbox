@echo off
CD /D %~dp0
setlocal
title G-Toolbox - Setup

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python and check 'Add to PATH' option.
    pause
    exit
)

echo ==================================================
echo    Welcome to G-Toolbox Setup
echo ==================================================
echo.

if exist venv (
    echo [INFO] Virtual environment already exists.
) else (
    echo [STEP 1] Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo.
echo [STEP 2] Choose engine:
echo 1) CPU Mode
echo 2) GPU Mode
echo 3) Skip
echo.
set /p choice="Enter (1/2/3): "

if "%choice%"=="1" pip install "rembg[cpu]"
if "%choice%"=="2" pip install "rembg[gpu]"

echo [STEP 3] Installing requirements...
pip install -r requirements.txt

echo Setup finished!
pause