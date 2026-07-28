FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY . .

# Меняем main.py на запуск сервера Django через manage.py
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
