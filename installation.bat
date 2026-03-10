@echo off
title VIP Swiss Army Knife - Setup
echo Welcome to the VIP Swiss Army Knife Setup!
echo.
echo Step 1: Creating virtual environment (Sandbox)...
python -m venv venv

echo.
echo Step 2: Downloading libraries and AI requirements...
echo Please wait (This may take 5-10 minutes depending on your internet speed)...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo Setup completed successfully! You can now run the project using 'baslat.bat'.
pause