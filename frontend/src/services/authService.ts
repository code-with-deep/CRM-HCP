/**
 * Authentication service — handles register/login calls and token management.
 */

import { apiClient, clearToken, saveToken } from './apiClient'

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
  role: string
  full_name: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  first_name: string
  last_name: string
  email: string
  password: string
  role?: 'medical_representative' | 'manager' | 'admin'
}

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/login', credentials)
  saveToken(response.data.access_token)
  return response.data
}

export async function register(details: RegisterRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/register', details)
  saveToken(response.data.access_token)
  return response.data
}

export function logout(): void {
  clearToken()
  window.location.href = '/login'
}
