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

# Criar pasta frontend e copiar manualmente os arquivos
RUN mkdir -p frontend

# Copiar arquivos HTML
COPY frontend/*.html frontend/

# Copiar CSS
COPY frontend/css/ frontend/css/

# Copiar JS  
COPY frontend/js/ frontend/js/

# Copiar imagens
COPY frontend/midia/ frontend/midia/

# Verificar se copiou
RUN echo "=== ARQUIVOS COPIADOS ===" && ls -la frontend/

RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["python", "app.py"]