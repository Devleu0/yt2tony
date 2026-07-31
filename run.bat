@echo off
chcp 65001 > nul
title Youtube Vocal Splitter Pipeline

echo [System] Initialize...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python is not installed or not in system PATH.
    pause
    exit /b
)

echo [Step 1] Installing PyTorch with CUDA 12.1...
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)

echo [Step 2] Installing dependencies...
pip install -q -r requirements.txt

echo [Step 3] Executing main.py...
echo.
python main.py

echo.
echo [System] Process terminated. Press any key to close.
pause