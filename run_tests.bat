@echo off
cd /d "%~dp0"
call backend\venv\Scripts\activate.bat
pip install requests pillow
python tests\edge_case_tests.py
pause
