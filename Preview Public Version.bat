@echo off
title College Sponsorship Dashboard (public version) - keep this window open
cd /d "%~dp0"
echo Starting the public version: what Anvara will see. It will open in your web browser.
echo If it doesn't, open your browser and go to:  http://localhost:8502
echo.
echo Keep this window open while you use it. Close it to stop.
echo.
set PUBLIC=1
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8502
pause
