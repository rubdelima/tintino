/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

// Configuração baseada no ambiente
const getApiBaseUrl = (): string => {
  // Verifica se há variável de ambiente definida
  if (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  
  // Detecta se estamos em desenvolvimento local
  const isDevelopment = typeof window !== 'undefined' && 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  
  // Para desenvolvimento local
  if (isDevelopment) {
    return 'http://localhost:8000';
  }
  
  // Para produção
  return 'https://tintino.onrender.com';
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

    