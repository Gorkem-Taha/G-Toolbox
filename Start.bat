@echo off
title G-Toolbox
echo Launching G-Toolbox Application (PC & Mobile LAN)...
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
echo Access locally: http://localhost:8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause