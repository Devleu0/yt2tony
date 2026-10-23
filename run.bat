@echo off
chcp 65001 > nul
title Youtube Vocal Splitter Pipeline
cd /d "%~dp0"

echo [System] Initialize...
echo.

py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python 3.11 is required. Install it from https://www.python.org/downloads/
    pause
    exit /b
)

if not exist ".venv\Scripts\python.exe" (
    echo [Step 1] Creating Python virtual environment...
    py -3.11 -m venv .venv
    if errorlevel 1 (
        echo [Error] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

echo [Step 2] Installing CUDA-enabled PyTorch and TorchAudio...
".venv\Scripts\python.exe" -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 (
    echo [Error] Failed to install PyTorch.
    pause
    exit /b 1
)

echo [Step 3] Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [Error] Failed to install dependencies.
    pause
    exit /b 1
)

echo [Step 4] Executing main.py...
echo.
".venv\Scripts\python.exe" main.py

echo.
echo [System] Process terminated. Press any key to close.
pause