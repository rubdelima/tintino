/**
 * API Configuration
 * Centralized configuration for API endpoints
 */

// Configuração baseada no ambiente
const isBrowser = typeof window !== 'undefined';

/**
 * Base da API
 * - No browser: base relativa (""), para passar pelo Nginx em /api
 * - No servidor (SSR/API Routes): usa INTERNAL_API_URL (ex.: http://api:8000)
 *   com fallback para NEXT_PUBLIC_API_BASE_URL (apenas para DEV) ou http://localhost:8000
 */
const getApiBaseUrl = (): string => {
  if (isBrowser) {
    const envBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
    if (envBase && /^https?:\/\//.test(envBase)) {
      return envBase;
    }
    // Sem base absoluta definida para o cliente: usar caminho relativo (via Nginx)
    return '';
  }

  // Server-side
  if (process.env.INTERNAL_API_URL) {
    return process.env.INTERNAL_API_URL;
  }

  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }

  // Fallback de desenvolvimento (SSR local)
  return 'http://localhost:8000';
};

export const API_CONFIG = {
  // No browser ficará "" (base relativa); no server, absoluto
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
  if (isBrowser) {
    const envBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
    if (envBase && /^https?:\/\//.test(envBase)) {
      const wsProtocol = envBase.startsWith('https') ? 'wss' : 'ws';
      const httpUrl = envBase.replace(/^https?:\/\//, '');
      return `${wsProtocol}://${httpUrl}${endpoint}`;
    }
    const { protocol, host } = window.location;
    const wsProtocol = protocol === 'https:' ? 'wss' : 'ws';
    return `${wsProtocol}://${host}${endpoint}`;
  }

  const baseUrl = getApiBaseUrl(); // absoluto no server
  const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
  const httpUrl = baseUrl.replace(/^https?:\/\//, '');
  return `${wsProtocol}://${httpUrl}${endpoint}`;
};

    