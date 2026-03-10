@echo off
title VIP Swiss Army Knife - Uninstaller and Cleaner
color 4f
echo WARNING: This process will delete the project, all downloaded libraries, and AI models from your computer!
pause

echo.
echo 1. Deleting Virtual Environment (Libraries)...
rmdir /s /q venv

echo.
echo 2. Cleaning up AI Models (Caches)...
:: Hidden folder where rembg models are downloaded
if exist "%USERPROFILE%\.u2net" rmdir /s /q "%USERPROFILE%\.u2net"

:: Hidden folder where Hugging Face and PyTorch models are downloaded
if exist "%USERPROFILE%\.cache\huggingface" rmdir /s /q "%USERPROFILE%\.cache\huggingface"
if exist "%USERPROFILE%\.cache\torch" rmdir /s /q "%USERPROFILE%\.cache\torch"

echo.
echo Cleanup complete! Gigabytes of disk space have been freed.
echo You can now manually delete this project folder as well.
pause