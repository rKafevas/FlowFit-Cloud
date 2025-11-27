FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar backend
COPY backend/ .

# Copiar frontend - método alternativo
COPY frontend ./frontend/

# Debug: verificar se os arquivos foram copiados
RUN echo "=== VERIFICANDO FRONTEND ===" && \
    ls -la frontend/ && \
    echo "=== ARQUIVOS HTML ===" && \
    ls -la frontend/*.html

RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]