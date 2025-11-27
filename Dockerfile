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

# Mudar para a pasta backend
WORKDIR /app/backend

# Expor a porta da aplicação
EXPOSE 5000

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Comando para rodar a aplicação
CMD ["python", "app.py"]