import { apiClient, classifyApiError, getApiBaseUrl, getToken } from '@/services/apiClient'
import type { ApiResponse } from '@/types/api.types'
import type { ChatRequest, ChatResponseData } from '@/types/chat.types'

export class ChatService {
  async sendMessage(request: ChatRequest): Promise<ChatResponseData> {
    const response = await apiClient.post<ApiResponse<ChatResponseData>>(
      '/chat',
      request,
    )
    return response.data.data
  }

  async getSession(conversationId: string): Promise<ChatResponseData> {
    const response = await apiClient.get<ApiResponse<ChatResponseData>>(
      `/chat/session/${conversationId}`,
    )
    return response.data.data
  }

  async *streamMessage(
    request: ChatRequest,
    signal?: AbortSignal,
  ): AsyncGenerator<{ event: string; data: Record<string, unknown> }> {
    const baseUrl = getApiBaseUrl()
    const token = getToken()

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    let response: Response
    try {
      response = await fetch(`${baseUrl}/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
        signal,
      })
    } catch (error) {
      throw new Error(classifyApiError(error).message)
    }

    if (!response.ok) {
      let errorMessage = `Stream request failed with status ${response.status}`
      try {
        const payload = (await response.json()) as ApiResponse<null>
        errorMessage = payload.message ?? errorMessage
      } catch {
        // Keep default message when error body is not JSON.
      }
      throw new Error(errorMessage)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Streaming is not supported in this environment.')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''

      for (const part of parts) {
        if (!part.trim()) continue

        const lines = part.split('\n')
        let event = 'message'
        let dataLine = ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            event = line.replace('event:', '').trim()
          } else if (line.startsWith('data:')) {
            dataLine = line.replace('data:', '').trim()
          }
        }

        if (dataLine) {
          yield { event, data: JSON.parse(dataLine) as Record<string, unknown> }
        }
      }
    }
  }
}

export const chatService = new ChatService()
