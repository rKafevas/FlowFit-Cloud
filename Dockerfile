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

# Copiar TUDO do contexto de build
COPY . .

# Debug: verificar estrutura copiada
RUN echo "=== ESTRUTURA COPIADA ===" && ls -la
RUN echo "=== BACKEND ===" && ls -la backend/ 2>/dev/null || echo "Backend não encontrado"
RUN echo "=== FRONTEND ===" && ls -la frontend/ 2>/dev/null || echo "Frontend não encontrado"

# Mover arquivos do backend para o WORKDIR
RUN if [ -d "backend" ]; then \
        mv backend/* ./ && \
        rm -rf backend && \
        echo "Backend movido com sucesso"; \
    else \
        echo "Backend já está no lugar certo"; \
    fi

RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]