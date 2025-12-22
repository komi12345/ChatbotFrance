// Types pour l'authentification

export type UserRole = "super_admin" | "admin";

export interface User {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse extends Token {
  user: User;
}

export interface UserCreate {
  email: string;
  password: string;
  role: UserRole;
}

export interface UserUpdate {
  email?: string;
  password?: string;
  is_active?: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
