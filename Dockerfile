# Stage 1: Base com Python e dependências do sistema
FROM python:3.10-slim AS base

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: API
FROM base AS api

# Copiar e instalar dependências da API
COPY requirements/api.txt ./requirements/
RUN pip install --no-cache-dir -r requirements/api.txt

# Copiar código completo
COPY . .

COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# Criar diretórios necessários
RUN mkdir -p temp/archives temp/chats temp/users

# Definir variáveis de ambiente
ENV PORT=8000
ENV PYTHONPATH=/app

EXPOSE $PORT

# Usar a variável PORT do Cloud Run
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port $PORT"]
