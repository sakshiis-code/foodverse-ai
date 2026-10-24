@echo off
cd /d "%~dp0backend"
if not exist venv\Scripts\python.exe (
  echo Creating virtual environment...
  if exist venv rmdir /s /q venv
  python -m venv venv
)
echo Installing libraries (first time takes a few minutes)...
venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist .env (
  copy .env.example .env >nul
  echo.
  // here you can add your Groq key to the .env file
  echo Notepad will open. Paste your Groq key after GROQ_API_KEY= , save, close it, then run this file again.
  notepad .env
  pause
  exit /b
)
venv\Scripts\python.exe -m uvicorn main:app --reload
pause
