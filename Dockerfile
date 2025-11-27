FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema + curl para health check
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para melhor cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar backend E frontend
COPY backend/ .
COPY frontend/ ./frontend/

# Criar usuário não-root para segurança (opcional)
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

# Expor a porta da aplicação
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Comando para rodar a aplicação
CMD ["python", "app.py"]