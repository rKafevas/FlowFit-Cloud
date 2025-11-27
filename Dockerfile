FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar APENAS o backend por enquanto
COPY backend/ .

# Criar estrutura vazia do frontend para evitar erros
RUN mkdir -p frontend/css frontend/js frontend/midia
RUN echo "<html><body><h1>Frontend não carregado - Configure separadamente</h1></body></html>" > frontend/login.html

EXPOSE 5000
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["python", "app.py"]