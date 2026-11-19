FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_NAME="Page & Pour Book Cafe" \
    APP_VERSION="v1.0.0" \
    APP_ENV="production" \
    PORT=8000

WORKDIR /app

# Install curl for container HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT}/health || exit 1

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 app.main:app"]
