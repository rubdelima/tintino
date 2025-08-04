// Exemplo de uso da configuração de API

import { API_CONFIG, buildApiUrl, getApiEndpoint } from '@/lib/api-config';

// Métodos disponíveis:

// 1. Usar endpoints pré-definidos
const usersEndpoint = getApiEndpoint('USERS');     // '/api/users'
const chatsEndpoint = getApiEndpoint('CHATS');     // '/api/chats'

// 2. Construir URLs customizadas
const customUrl = buildApiUrl('/api/custom/endpoint');

// 3. Acessar configuração diretamente
const baseUrl = API_CONFIG.BASE_URL;

// Exemplos de uso em fetch:

// Criar usuário
fetch(getApiEndpoint('USERS') + '/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ name: 'John Doe' })
});

// Buscar chats
fetch(getApiEndpoint('CHATS'), {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Endpoint customizado
fetch(buildApiUrl('/api/custom/endpoint'), {
  method: 'GET'
});
