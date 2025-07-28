@echo off
echo Starting Adcellerant Social Caption Generator...
echo.
cd /d "%~dp0"
.venv\Scripts\python.exe -m streamlit run social_post_generator.py --server.headless false --server.port 8501
pause
