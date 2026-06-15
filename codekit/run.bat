@echo off
title CodeKit — Package Manager
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден. Установите Python 3.11+ и запустите снова.
    echo [ERROR] https://www.python.org/downloads/
    pause
    exit /b 1
)

python -c "import textual, rich" 2>nul
if %errorlevel% neq 0 (
    echo [..] Устанавливаю зависимости...
    pip install textual rich
    if %errorlevel% neq 0 (
        echo [ERROR] Не удалось установить зависимости.
        pause
        exit /b 1
    )
    echo [OK] Зависимости установлены.
)

python main.py
pause
