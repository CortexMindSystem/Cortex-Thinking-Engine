FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY cortex_core ./cortex_core

EXPOSE 8420

CMD ["sh", "-c", "uvicorn cortex_core.api.server:app --host 0.0.0.0 --port ${PORT:-8420}"]
