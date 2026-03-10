@echo off
title G-Toolbox
echo Launching G-Toolbox Application...
call venv\Scripts\activate.bat
echo Please navigate to http://localhost:8000 in your browser.
uvicorn main:app --reload --port 8000
pause