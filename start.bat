@echo off
echo Starting AI-Powered Website Link Analysis API...
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe run.py
) else (
    python run.py
)
pause
