import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

// Configuration de base de l'API
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// Clés localStorage
const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const TOKEN_EXPIRY_KEY = "token_expiry";

// Flag pour éviter les refresh multiples simultanés
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: Error) => void;
}> = [];

// ==========================================================================
// ROBUSTESSE - Configuration des retries et timeouts
// ==========================================================================
const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;
const REQUEST_TIMEOUT_MS = 30000; // 30 secondes

// Codes d'erreur réseau qui méritent un retry
const RETRYABLE_ERRORS = [
  "ECONNABORTED",
  "ETIMEDOUT",
  "ENOTFOUND",
  "ENETUNREACH",
  "ECONNREFUSED",
  "ECONNRESET",
  "ERR_NETWORK",
];

// Codes HTTP qui méritent un retry
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

/**
 * Vérifie si une erreur est récupérable (mérite un retry)
 */
function isRetryableError(error: AxiosError): boolean {
  // Erreur réseau sans réponse
  if (!error.response) {
    const code = error.code || "";
    return RETRYABLE_ERRORS.some(e => code.includes(e));
  }
  
  // Erreur HTTP récupérable
  return RETRYABLE_STATUS_CODES.includes(error.response.status);
}

/**
 * Attend un délai avec backoff exponentiel
 */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Création de l'instance Axios avec configuration robuste
export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: REQUEST_TIMEOUT_MS,
});

/**
 * Vérifie si le token est proche de l'expiration (moins de 5 minutes)
 */
function isTokenExpiringSoon(): boolean {
  if (typeof window === "undefined") return false;
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
  if (!expiry) return false;
  const expiryTime = parseInt(expiry, 10);
  const now = Date.now();
  // Refresh si moins de 5 minutes restantes
  return expiryTime - now < 5 * 60 * 1000;
}

/**
 * Rafraîchit le token d'accès
 */
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) return null;

  try {
    const response = await axios.post(`${API_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    const { access_token, expires_in } = response.data;
    
    // Stocker le nouveau token et son expiration
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(TOKEN_EXPIRY_KEY, String(Date.now() + expires_in * 1000));
    
    return access_token;
  } catch {
    // Refresh token invalide, nettoyer (mais ne pas rediriger ici)
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    localStorage.removeItem("user");
    return null;
  }
}

// Intercepteur pour ajouter le token JWT aux requêtes
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    if (typeof window === "undefined") return config;

    // Vérifier si le token expire bientôt et le rafraîchir proactivement
    if (isTokenExpiringSoon() && !config.url?.includes("/auth/")) {
      if (!isRefreshing) {
        isRefreshing = true;
        const newToken = await refreshAccessToken();
        isRefreshing = false;
        processQueue(null, newToken);
        
        if (newToken && config.headers) {
          config.headers.Authorization = `Bearer ${newToken}`;
          return config;
        }
      } else {
        // Attendre que le refresh en cours se termine
        return new Promise((resolve, reject) => {
          failedQueue.push({
            resolve: (token: string) => {
              if (config.headers) {
                config.headers.Authorization = `Bearer ${token}`;
              }
              resolve(config);
            },
            reject: (err: Error) => {
              reject(err);
            },
          });
        });
      }
    }

    // Ajouter le token actuel
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Intercepteur pour gérer les erreurs de réponse avec retry automatique
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { 
      _retry?: boolean;
      _retryCount?: number;
    };

    // Gestion des retries pour les erreurs réseau/serveur
    if (isRetryableError(error) && originalRequest) {
      const retryCount = originalRequest._retryCount || 0;
      
      if (retryCount < MAX_RETRIES) {
        originalRequest._retryCount = retryCount + 1;
        
        // Backoff exponentiel: 1s, 2s, 4s
        const waitTime = RETRY_DELAY_MS * Math.pow(2, retryCount);
        
        console.warn(
          `[API] Retry ${retryCount + 1}/${MAX_RETRIES} après erreur ${error.code || error.response?.status}. ` +
          `Attente ${waitTime}ms...`
        );
        
        await delay(waitTime);
        return api(originalRequest);
      }
      
      console.error(`[API] Échec après ${MAX_RETRIES} tentatives:`, error.message);
    }

    // Si erreur 401 et pas déjà en retry
    if (error.response?.status === 401 && !originalRequest._retry && typeof window !== "undefined") {
      // Ne pas gérer les erreurs 401 pour les endpoints d'auth - laisser le composant gérer
      if (originalRequest.url?.includes("/auth/")) {
        return Promise.reject(error);
      }

      // Vérifier si on est déjà sur la page login pour éviter la boucle
      const currentPath = window.location.pathname;
      if (currentPath === "/login" || currentPath === "/") {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      // Essayer de refresh le token
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (refreshToken && !isRefreshing) {
        isRefreshing = true;
        const newToken = await refreshAccessToken();
        isRefreshing = false;

        if (newToken) {
          processQueue(null, newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        }
      }

      // Pas de refresh token ou refresh échoué - nettoyer et rediriger
      processQueue(new Error("Auth failed"), null);
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(TOKEN_EXPIRY_KEY);
      localStorage.removeItem("user");
      
      // Rediriger seulement si pas déjà sur login ou page d'accueil
      if (currentPath !== "/login" && currentPath !== "/") {
        window.location.href = "/login";
      }
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

// Types pour les réponses API
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// ==========================================================================
// ROBUSTESSE - Fonctions utilitaires pour la gestion des erreurs
// ==========================================================================

/**
 * Extrait un message d'erreur lisible depuis une erreur Axios
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    // Erreur réseau sans réponse
    if (!error.response) {
      if (error.code === "ECONNABORTED" || error.code === "ETIMEDOUT") {
        return "La requête a expiré. Vérifiez votre connexion internet.";
      }
      if (error.code === "ERR_NETWORK") {
        return "Erreur réseau. Vérifiez votre connexion internet.";
      }
      return "Impossible de contacter le serveur. Réessayez plus tard.";
    }
    
    // Erreur HTTP avec réponse
    const status = error.response.status;
    const detail = error.response.data?.detail;
    
    // Message personnalisé selon le code HTTP
    switch (status) {
      case 400:
        return typeof detail === "string" ? detail : "Données invalides";
      case 401:
        return "Session expirée. Veuillez vous reconnecter.";
      case 403:
        return "Accès non autorisé";
      case 404:
        return "Ressource non trouvée";
      case 409:
        return typeof detail === "string" ? detail : "Conflit de données";
      case 429:
        return "Trop de requêtes. Veuillez patienter.";
      case 500:
        return "Erreur serveur. Réessayez plus tard.";
      case 502:
      case 503:
      case 504:
        return "Service temporairement indisponible. Réessayez plus tard.";
      default:
        return typeof detail === "string" ? detail : `Erreur ${status}`;
    }
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return "Une erreur inattendue s'est produite";
}

/**
 * Vérifie si une erreur est une erreur réseau (pas de réponse du serveur)
 */
export function isNetworkError(error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    return !error.response;
  }
  return false;
}

/**
 * Vérifie si une erreur est une erreur d'authentification
 */
export function isAuthError(error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    return error.response?.status === 401;
  }
  return false;
}

/**
 * Vérifie si une erreur est une erreur de rate limiting
 */
export function isRateLimitError(error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    return error.response?.status === 429;
  }
  return false;
}

export default api;
