@echo off
title College Sponsorship Dashboard - keep this window open
cd /d "%~dp0"
echo Starting the dashboard... it will open in your web browser.
echo If it doesn't, open your browser and go to:  http://localhost:8501
echo.
echo Keep this window open while you use the dashboard. Close it to stop.
echo.
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501
pause
