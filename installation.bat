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
echo [STEP 2] Choose AI acceleration engine:
echo 1) CPU Mode (Standard computers)
echo 2) GPU Mode (NVIDIA CUDA acceleration)
echo 3) Skip
echo.
set /p choice="Enter (1/2/3): "

if "%choice%"=="1" (
    echo [INFO] Installing CPU-optimized PyTorch and rembg...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    pip install "rembg[cpu]"
)
if "%choice%"=="2" (
    echo [INFO] Installing NVIDIA CUDA-accelerated PyTorch and rembg...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    pip install "rembg[gpu]"
)

echo.
echo [STEP 3] Installing remaining requirements...
echo [INFO] Pre-installing basicsr without build isolation to avoid C++ build errors...
pip install basicsr --no-deps
pip install -r requirements.txt

echo.
echo Setup finished successfully!
pause