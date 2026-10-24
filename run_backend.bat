@echo off
cd /d "%~dp0backend"
if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing libraries (first time takes a few minutes)...
pip install -r requirements.txt
if not exist .env (
  copy .env.example .env >nul
  echo.
  echo Notepad will open. Paste your Groq key after GROQ_API_KEY= , save, close it, then run this file again.
  notepad .env
  pause
  exit /b
)
uvicorn main:app --reload
pause
