/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

// Configuração baseada no ambiente
const getApiBaseUrl = (): string => {
  // SEMPRE usa variável de ambiente - obrigatória
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  
  // Se não há variável de ambiente, lança erro
  throw new Error('NEXT_PUBLIC_API_BASE_URL deve estar definida no .env.local');
};

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  ENDPOINTS: {
    USERS: '/api/users',
    CHATS: '/api/chats',
  },
} as const;

/**
 * Helper function to build API URLs
 */
export const buildApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

/**
 * Helper function to get full endpoint URL
 */
export const getApiEndpoint = (key: keyof typeof API_CONFIG.ENDPOINTS): string => {
  return buildApiUrl(API_CONFIG.ENDPOINTS[key]);
};

/**
 * Helper function to build WebSocket URLs
 */
export const getWebSocketUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
  const httpUrl = baseUrl.replace(/^https?:\/\//, '');
  return `${wsProtocol}://${httpUrl}${endpoint}`;
};

    