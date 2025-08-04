/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

// Detecta se estamos em desenvolvimento local
const isDevelopment = typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// Configuração baseada no ambiente
const getApiBaseUrl = (): string => {
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
