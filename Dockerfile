FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO o projeto
COPY . .

# DEBUG: Verificar estrutura completa
RUN echo "=== ESTRUTURA COMPLETA ===" && ls -la
RUN echo "=== PROCURANDO app.py ===" && find . -name "app.py" 2>/dev/null | head -5
RUN echo "=== ARQUIVOS PYTHON ===" && find . -name "*.py" | head -10

# Expor porta
EXPOSE 5000

# Tentar encontrar e executar app.py automaticamente
CMD ["sh", "-c", "APP_FILE=$(find . -name app.py -type f | head -1); if [ -f \"$APP_FILE\" ]; then echo \"Executando: $APP_FILE\"; python \"$APP_FILE\"; else echo \"ERRO: app.py não encontrado!\"; find . -name \"*.py\" | head -10; exit 1; fi"]