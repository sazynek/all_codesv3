#!/bin/bash
# ===========================================
# Установка Telegram Account Manager Bot
# ===========================================

set -e

BOT_DIR="/opt/tg-account-bot"
BOT_USER="bot"

echo "=== Установка Telegram Account Manager Bot ==="

# 1. Создание пользователя
if ! id "$BOT_USER" &>/dev/null; then
    echo "-> Создаю пользователя $BOT_USER..."
    sudo useradd -r -s /bin/false $BOT_USER
fi

# 2. Создание директории
echo "-> Создаю директорию $BOT_DIR..."
sudo mkdir -p $BOT_DIR
sudo chown $BOT_USER:$BOT_USER $BOT_DIR

# 3. Копирование файлов (предполагается, что скрипт запущен из папки с проектом)
echo "-> Копирую файлы..."
sudo cp -r ./* $BOT_DIR/
sudo chown -R $BOT_USER:$BOT_USER $BOT_DIR

# 4. Создание виртуального окружения
echo "-> Создаю виртуальное окружение..."
sudo -u $BOT_USER python3 -m venv $BOT_DIR/.venv
sudo -u $BOT_USER $BOT_DIR/.venv/bin/pip install --upgrade pip
sudo -u $BOT_USER $BOT_DIR/.venv/bin/pip install -r $BOT_DIR/requirements.txt

# 5. Создание .env.example если нет
if [ ! -f "$BOT_DIR/.env.example" ]; then
    echo "-> Копирую .env.example.example в .env.example..."
    sudo cp $BOT_DIR/.env.example.example $BOT_DIR/.env.example
    sudo chown $BOT_USER:$BOT_USER $BOT_DIR/.env.example
    echo "!!! ВАЖНО: Отредактируйте $BOT_DIR/.env.example перед запуском !!!"
fi

# 6. Создание директорий для данных
echo "-> Создаю директории для данных..."
sudo -u $BOT_USER mkdir -p $BOT_DIR/sessions $BOT_DIR/storage

# 7. Установка systemd сервиса
echo "-> Устанавливаю systemd сервис..."
sudo cp $BOT_DIR/deploy/tg-account-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "=== Установка завершена! ==="
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте конфиг: sudo nano $BOT_DIR/.env.example"
echo "2. Запустите бота: sudo systemctl start tg-account-bot"
echo "3. Включите автозапуск: sudo systemctl enable tg-account-bot"
echo "4. Проверьте статус: sudo systemctl status tg-account-bot"
echo "5. Смотрите логи: sudo journalctl -u tg-account-bot -f"
