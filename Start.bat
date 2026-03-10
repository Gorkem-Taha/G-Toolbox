@echo off
title VIP Swiss Army Knife
echo Launching VIP Application...
call venv\Scripts\activate.bat
echo Please navigate to http://localhost:8000 in your browser.
uvicorn main:app --reload --port 8000
pause