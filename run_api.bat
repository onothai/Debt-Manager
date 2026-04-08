@echo off
cd /d "%~dp0"
if not exist "env\Scripts\activate.bat" (
  echo ยังไม่มี venv — รันก่อน: python -m venv env
  pause
  exit /b 1
)
call env\Scripts\activate.bat
echo venv OK — DB จากไฟล์ .env ถ้ามี
uvicorn api:app --host 192.168.137.50 --port 8000 --reload
pause
