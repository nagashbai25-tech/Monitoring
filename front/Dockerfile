FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Один процесс с несколькими потоками: так метрики prometheus_client остаются в одном
# процессе и /metrics отдаёт полную картину без multiprocess-режима.
CMD ["gunicorn", "--workers", "1", "--threads", "4", "--bind", "0.0.0.0:5000", "app:app"]
