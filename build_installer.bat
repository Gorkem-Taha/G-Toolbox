@echo off
title G-Toolbox - Windows Setup Builder
cd /d "%~dp0"

echo =======================================================
echo     G-Toolbox Setup (.exe) Installer Builder
echo =======================================================
echo.

if not exist "dist\G-Toolbox\G-Toolbox.exe" (
    echo [*] Executable not found in dist. Compiling desktop app first...
    call build_desktop.bat
)

echo [*] Checking for Inno Setup Compiler (ISCC.exe)...

set "ISCC_PATH="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if "%ISCC_PATH%"=="" (
    where iscc >nul 2>&1
    if %ERRORLEVEL% equ 0 set "ISCC_PATH=iscc"
)

if "%ISCC_PATH%"=="" (
    echo.
    echo [-] Inno Setup 6 was not found in Program Files or PATH.
    echo [!] To compile G-Toolbox-Setup.exe:
    echo     1. Download Inno Setup 6 free: https://jrsoftware.org/isdl.php
    echo     2. Right click 'installer.iss' and select 'Compile'.
    echo.
    pause
    exit /b 1
)

echo [*] Compiling installer using: "%ISCC_PATH%"
"%ISCC_PATH%" installer.iss

if %ERRORLEVEL% equ 0 (
    echo.
    echo =======================================================
    echo   [+] INSTALLER CREATED SUCCESSFULLY!
    echo   Setup executable located at:
    echo   installer_dist\G-Toolbox-Setup-v4.1.0.exe
    echo =======================================================
) else (
    echo.
    echo [-] Installer compilation failed.
)

pause
