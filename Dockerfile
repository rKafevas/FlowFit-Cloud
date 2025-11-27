FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt da RAIZ
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO o conteúdo da pasta backend para /app
COPY backend/ .

# === DEBUG: VERIFICAR ESTRUTURA DE ARQUIVOS ===
RUN echo "=== ESTRUTURA DE ARQUIVOS ==="
RUN pwd
RUN ls -la
RUN echo "=== CONTEÚDO DA PASTA BACKEND ==="
RUN ls -la backend/
RUN echo "=== VERIFICANDO app.py ==="
RUN find . -name "app.py" -type f

# Expor a porta da aplicação
EXPOSE 5000

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Comando para rodar a aplicação
CMD ["python", "app.py"]