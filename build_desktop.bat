@echo off
title G-Toolbox - Windows Desktop Build
cd /d "%~dp0"

echo =======================================================
echo     G-Toolbox Windows Desktop Executable Builder (.exe)
echo =======================================================
echo.

python -c "import PyInstaller" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [!] PyInstaller is not installed. Installing...
    pip install pyinstaller pywebview
    if %ERRORLEVEL% neq 0 (
        echo [-] Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo [*] Starting PyInstaller Standalone Folder Compilation...
echo [*] Packaging templates, static assets, and Edge WebView2 runtime...
echo.

pyinstaller --noconfirm --onedir --windowed ^
    --name "G-Toolbox" ^
    --icon "static/favicon.ico" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan" ^
    --hidden-import "uvicorn.lifespan.on" ^
    --hidden-import "webview.platforms.winforms" ^
    desktop_app.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo =======================================================
    echo   [+] BUILD SUCCESSFUL!
    echo   Standalone executable created at:
    echo   dist\G-Toolbox\G-Toolbox.exe
    echo =======================================================
) else (
    echo.
    echo [-] Build failed. Check the error log above.
)

pause
