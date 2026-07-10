import type { InteractionDraft } from '@/types/interaction.types'

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  toolCalled?: string | null
  timestamp: string
  isStreaming?: boolean
}

export interface ConversationMessageItem {
  role: string
  content: string
  tool_called?: string | null
  sequence_number: number
  timestamp?: string | null
}

export interface ChatResponseData {
  conversation_id: string
  assistant_message: string | null
  interaction_draft: InteractionDraft
  current_hcp: Record<string, unknown> | null
  interaction_status: string
  conversation_history: ConversationMessageItem[]
  selected_tool: string | null
  tool_result: Record<string, unknown> | null
  validation_errors: string[]
  suggested_prompts: string[]
  memory: Record<string, unknown>
  error_message: string | null
}

export interface ChatRequest {
  message: string
  conversation_id?: string | null
  user_id: string
  current_interaction?: Record<string, unknown>
  current_hcp?: Record<string, unknown> | null
}

export interface StreamEvent {
  event: 'status' | 'token' | 'complete' | 'error'
  data: Record<string, unknown>
}

export type ChatStatus = 'idle' | 'connecting' | 'streaming' | 'saving' | 'error'
