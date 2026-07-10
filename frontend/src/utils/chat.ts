import type { ChatMessage, ConversationMessageItem } from '@/types/chat.types'
import type { ChatResponseData } from '@/types/chat.types'
import type { InteractionDraft } from '@/types/interaction.types'

export function createMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function mapHistoryToMessages(
  history: ConversationMessageItem[],
): ChatMessage[] {
  return history.map((item) => ({
    id: `hist-${item.sequence_number}`,
    role: item.role === 'assistant' || item.role === 'user' ? item.role : 'assistant',
    content: item.content,
    toolCalled: item.tool_called,
    timestamp: item.timestamp ?? new Date().toISOString(),
  }))
}

export function mergeInteractionDraft(
  current: InteractionDraft,
  incoming: Partial<InteractionDraft>,
): InteractionDraft {
  const merged: InteractionDraft = { ...current }

  for (const key of Object.keys(incoming) as (keyof InteractionDraft)[]) {
    const value = incoming[key]
    if (value === undefined) continue
    merged[key] = value as never
  }

  return merged
}

export function parseChatResponseData(
  payload: Record<string, unknown>,
): ChatResponseData {
  return payload as unknown as ChatResponseData
}

export function canSaveInteraction(draft: InteractionDraft): boolean {
  return Boolean(draft.hcp_name?.trim() && draft.interaction_date?.trim())
}
