#!/bin/sh

# Encerra o script imediatamente se um comando falhar
set -e

# Imprime uma mensagem para os logs, útil para depuração
echo "Iniciando o script de entrada..."

# Cria o arquivo firebase.json a partir da variável de ambiente
# Esta variável será configurada no Cloud Run a partir do Secret Manager
echo "Criando o arquivo firebase.json a partir do secret..."
echo "$FIREBASE_CREDENTIALS_JSON" > /app/firebase.json

exec "$@"
