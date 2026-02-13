FROM python:3.11-slim

# Установка Chrome
RUN apt-get update && apt-get install -y --no-install-recommends wget gnupg ca-certificates \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Создаем папки заранее
RUN mkdir -p /app/output /app/data

# Сначала зависимости (для кэша)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё остальное
COPY . .

# Перемещаем файлы в нужную папку внутри образа (вместо COPY, чтобы не дублировать)
RUN mv checked_urls.json /app/data/ 2>/dev/null || true
RUN mv contracts_data.xlsx /app/data/ 2>/dev/null || true

CMD ["python", "main.py"]
