@echo off
REM ===========================================
REM Запуск бота локально (без установки сервиса)
REM ===========================================

setlocal

cd /d "%~dp0.."

REM Проверяем .env.example
if not exist ".env.example" (
    echo ОШИБКА: Файл .env.example не найден!
    echo Скопируйте .env.example.example в .env.example и заполните данные
    pause
    exit /b 1
)

REM Проверяем виртуальное окружение
if not exist ".venv\Scripts\python.exe" (
    echo Виртуальное окружение не найдено, создаю...
    python -m venv .venv
    .venv\Scripts\pip install --upgrade pip
    .venv\Scripts\pip install -r requirements.txt
)

echo === Запуск Telegram Account Manager Bot ===
echo Для остановки нажмите Ctrl+C
echo.

.venv\Scripts\python main.py

pause
