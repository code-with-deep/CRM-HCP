import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'

import type { ApiErrorResponse } from '@/types/api.types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
const MAX_RETRIES = 3
const RETRY_DELAY_MS = 1000
const TOKEN_STORAGE_KEY = 'crm_access_token'

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  __retryCount?: number
}

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function isRetryableError(error: AxiosError): boolean {
  if (!error.response) {
    return true
  }

  const status = error.response.status
  return status === 408 || status === 429 || status >= 500
}

export function classifyApiError(error: unknown): {
  message: string
  code: 'network' | 'timeout' | 'validation' | 'server' | 'tool' | 'unknown'
  retryable: boolean
} {
  if (!navigator.onLine) {
    return {
      message: 'No internet connection. Check your network and try again.',
      code: 'network',
      retryable: true,
    }
  }

  if (error instanceof Error) {
    const text = error.message.toLowerCase()

    if (text.includes('timeout') || text.includes('timed out')) {
      return {
        message: 'The AI request timed out. Please try again.',
        code: 'timeout',
        retryable: true,
      }
    }

    if (text.includes('network') || text.includes('failed to fetch')) {
      return {
        message: 'Unable to reach the server. Ensure the backend is running.',
        code: 'network',
        retryable: true,
      }
    }

    if (text.includes('validation')) {
      return {
        message: error.message,
        code: 'validation',
        retryable: false,
      }
    }

    if (text.includes('tool') || text.includes('langgraph')) {
      return {
        message: error.message,
        code: 'tool',
        retryable: true,
      }
    }

    if (text.includes('database')) {
      return {
        message: 'A database error occurred while saving. Please try again.',
        code: 'server',
        retryable: true,
      }
    }

    return {
      message: error.message,
      code: 'unknown',
      retryable: true,
    }
  }

  return {
    message: 'An unexpected error occurred.',
    code: 'unknown',
    retryable: true,
  }
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000,
})

apiClient.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const config = error.config as RetryableRequestConfig | undefined

    if (error.response?.status === 401) {
      clearToken()
      window.location.href = '/login'
      return Promise.reject(new Error('Session expired. Please log in again.'))
    }

    if (config && isRetryableError(error)) {
      config.__retryCount = config.__retryCount ?? 0

      if (config.__retryCount < MAX_RETRIES) {
        config.__retryCount += 1
        await delay(RETRY_DELAY_MS * config.__retryCount)
        return apiClient(config)
      }
    }

    const message =
      error.response?.data?.message ??
      error.response?.data?.errors?.[0] ??
      error.message ??
      'An unexpected network error occurred.'

    const classified = classifyApiError(new Error(message))
    return Promise.reject(new Error(classified.message))
  },
)

export function getApiBaseUrl(): string {
  return API_BASE_URL
}

/**
 * Decode the stored JWT payload and return the user's ID (the `sub` claim).
 * Falls back to the VITE_DEMO_USER_ID env variable for unauthenticated sessions.
 */
export function getCurrentUserId(): string {
  const token = getToken()
  if (token) {
    try {
      const payloadBase64 = token.split('.')[1]
      const payload = JSON.parse(atob(payloadBase64))
      if (payload.sub) return payload.sub
    } catch {
      // Malformed token — fall through to env fallback
    }
  }
  return import.meta.env.VITE_DEMO_USER_ID ?? ''
}

