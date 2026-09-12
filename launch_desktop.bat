@echo off
title G-Toolbox Desktop
cd /d "%~dp0"
echo Launching G-Toolbox Native Desktop Window...
python desktop_app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred while running G-Toolbox.
    pause
)
