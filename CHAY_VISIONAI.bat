@echo off
setlocal
cd /d "%~dp0"
title VisionAI Pro - Gemini
chcp 65001 >nul
echo ============================================
echo       VisionAI Pro - Gemini Assistant
echo ============================================
where py >nul 2>nul
if errorlevel 1 (
  echo Khong tim thay Python launcher.
  echo Hay cai Python 3.11 hoac 3.12 va chon Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Tao moi truong Python...
  py -3 -m venv .venv
  if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -c "import sys; print('Python:', sys.version.split()[0])"
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Da tao file .env mau. Hay dien GEMINI_API_KEY vao file nay.
)
echo [2/3] Kiem tra/cai dat thu vien (khong nang cap pip rieng)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto error
echo [3/3] Dang mo VisionAI Pro...
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto error
exit /b 0
:error
echo.
echo Co loi cai dat hoac khoi dong. Hay chup phan loi cuoi cung va gui lai.
pause
exit /b 1
