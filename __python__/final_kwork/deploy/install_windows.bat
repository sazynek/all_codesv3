@echo off
REM ===========================================
REM Установка бота как Windows-сервиса через NSSM
REM ===========================================

setlocal

set BOT_DIR=%~dp0..
set SERVICE_NAME=TgAccountBot

echo === Установка Telegram Account Manager Bot ===
echo.

REM Проверяем NSSM
where nssm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ОШИБКА: NSSM не найден!
    echo Скачайте NSSM с https://nssm.cc/download
    echo и добавьте в PATH
    pause
    exit /b 1
)

REM Останавливаем если запущен
echo -^> Останавливаю сервис если запущен...
nssm stop %SERVICE_NAME% >nul 2>&1
nssm remove %SERVICE_NAME% confirm >nul 2>&1

REM Создаём виртуальное окружение
echo -^> Проверяю виртуальное окружение...
if not exist "%BOT_DIR%\.venv" (
    echo -^> Создаю виртуальное окружение...
    python -m venv "%BOT_DIR%\.venv"
    "%BOT_DIR%\.venv\Scripts\pip" install --upgrade pip
    "%BOT_DIR%\.venv\Scripts\pip" install -r "%BOT_DIR%\requirements.txt"
)

REM Проверяем .env.example
if not exist "%BOT_DIR%\.env.example" (
    echo -^> Копирую .env.example.example в .env.example...
    copy "%BOT_DIR%\.env.example.example" "%BOT_DIR%\.env.example"
    echo.
    echo !!! ВАЖНО: Отредактируйте %BOT_DIR%\.env.example перед запуском !!!
    echo.
)

REM Создаём директории
echo -^> Создаю директории...
if not exist "%BOT_DIR%\sessions" mkdir "%BOT_DIR%\sessions"
if not exist "%BOT_DIR%\storage" mkdir "%BOT_DIR%\storage"

REM Устанавливаем сервис через NSSM
echo -^> Устанавливаю Windows-сервис...
nssm install %SERVICE_NAME% "%BOT_DIR%\.venv\Scripts\python.exe" "%BOT_DIR%\main.py"
nssm set %SERVICE_NAME% AppDirectory "%BOT_DIR%"
nssm set %SERVICE_NAME% Description "Telegram Account Manager Bot"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START
nssm set %SERVICE_NAME% AppStdout "%BOT_DIR%\logs\stdout.log"
nssm set %SERVICE_NAME% AppStderr "%BOT_DIR%\logs\stderr.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateBytes 10485760

REM Создаём папку для логов
if not exist "%BOT_DIR%\logs" mkdir "%BOT_DIR%\logs"

echo.
echo === Установка завершена! ===
echo.
echo Следующие шаги:
echo 1. Отредактируйте конфиг: notepad "%BOT_DIR%\.env.example"
echo 2. Запустите сервис: nssm start %SERVICE_NAME%
echo 3. Проверьте статус: nssm status %SERVICE_NAME%
echo 4. Смотрите логи: type "%BOT_DIR%\logs\stdout.log"
echo.
echo Альтернативно - запуск без сервиса:
echo    cd "%BOT_DIR%" ^&^& .venv\Scripts\python main.py
echo.

pause
