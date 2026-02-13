@echo off
chcp 65001 >nul
echo ============================================
echo  Запуск парсера данных госзакупок (Docker)
echo ============================================
echo.

REM 1. Проверка, запущен ли Docker Desktop
echo [1/3] Проверка состояния Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ОШИБКА: Docker Desktop не запущен или не отвечает.
    echo.
    echo 1. Убедитесь, что Docker Desktop запущен (иконка в трее должна быть белой).
    echo 2. Попробуйте запустить его из меню "Пуск".
    echo.
    pause
    exit /b 1
)
echo Успех: Docker Desktop запущен и работает.

REM 2. Пересборка и запуск контейнеров (в фоновом режиме)
echo.
echo [2/3] Сборка и запуск проекта (это может занять пару минут)...
echo Пожалуйста, подождите...
docker-compose up --build -d
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось запустить контейнеры.
    pause
    exit /b 1
)

REM 3. Проверка, что контейнеры успешно запустились
echo.
echo [3/3] Проверка состояния контейнеров...
timeout /t 3 /nobreak >nul
docker-compose ps
if %errorlevel% neq 0 (
    echo ВНИМАНИЕ: Не удалось получить статус контейнеров.
)

echo.
echo ============================================
echo  Готово! Парсер запущен в фоновом режиме.
echo ============================================
echo.
echo  Ключевые команды:
echo   1. Просмотр логов:   docker-compose logs -f
echo   2. Остановка:        docker-compose down
echo   3. Перезапуск:       docker-compose restart
echo.
echo  Результаты работы появятся в папке data/
echo.
pause