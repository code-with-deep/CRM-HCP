import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'

import type { ApiErrorResponse } from '@/types/api.types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
const MAX_RETRIES = 3
const RETRY_DELAY_MS = 1000

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  __retryCount?: number
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
    'X-User-Id': import.meta.env.VITE_DEMO_USER_ID ?? '',
  },
  timeout: 90000,
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const config = error.config as RetryableRequestConfig | undefined

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

export const DEMO_USER_ID =
  import.meta.env.VITE_DEMO_USER_ID ?? '00000000-0000-0000-0000-000000000001'
