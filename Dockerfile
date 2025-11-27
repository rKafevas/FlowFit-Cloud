FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO o projeto
COPY . .

# DEBUG COMPLETO
RUN echo "=== ESTRUTURA COMPLETA COM tree ===" && tree -a || ls -la
RUN echo "=== TODOS OS ARQUIVOS .py ===" && find . -name "*.py" -type f
RUN echo "=== TODOS OS ARQUIVOS E PASTAS ===" && find . -type f | head -20
RUN echo "=== VERIFICANDO BACKEND ===" && ls -la backend/ 2>/dev/null || echo "Pasta backend não existe"

EXPOSE 5000

# Apenas mostrar estrutura, não executar
CMD ["sh", "-c", "echo '=== ESTRUTURA FINAL ===' && find . -name '*.py' -type f && echo '=== LISTA COMPLETA ===' && find . -type f | sort"]