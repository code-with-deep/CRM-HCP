import type { RootState } from '@/store'
import type { ChatMessage } from '@/types/chat.types'
import type { InteractionDraft, InteractionStatus } from '@/types/interaction.types'
import { EMPTY_INTERACTION_DRAFT } from '@/types/interaction.types'
import { getCurrentUserId } from '@/services/apiClient'

const STORAGE_KEY_PREFIX = 'crm-hcp-workspace-session'

/**
 * Return a user-scoped sessionStorage key so that different users logging in
 * on the same browser tab never share each other's conversation state.
 */
function getStorageKey(): string {
  const userId = getCurrentUserId()
  return userId ? `${STORAGE_KEY_PREFIX}-${userId}` : STORAGE_KEY_PREFIX
}

export interface PersistedWorkspaceSession {
  conversationId: string | null
  draft: InteractionDraft
  status: InteractionStatus
  currentHcp: Record<string, unknown> | null
  messages: ChatMessage[]
  selectedHcpId: string | null
  selectedHcpName: string | null
}

export function hasMeaningfulDraft(draft: InteractionDraft): boolean {
  return Object.entries(draft).some(([key, value]) => {
    if (key === 'sentiment') {
      return value !== null
    }
    if (Array.isArray(value)) {
      return value.length > 0
    }
    return typeof value === 'string' && value.trim().length > 0
  })
}

export function hasPersistableSession(state: RootState): boolean {
  if (state.chat.conversationId) {
    return true
  }
  if (hasMeaningfulDraft(state.interaction.draft)) {
    return true
  }
  return state.chat.messages.some((message) => message.id !== 'welcome')
}

export function persistWorkspaceSession(state: RootState): void {
  const key = getStorageKey()
  if (!hasPersistableSession(state)) {
    sessionStorage.removeItem(key)
    return
  }

  const payload: PersistedWorkspaceSession = {
    conversationId: state.chat.conversationId,
    draft: state.interaction.draft,
    status: state.interaction.status,
    currentHcp: state.interaction.currentHcp,
    messages: state.chat.messages,
    selectedHcpId: state.hcp.selectedHcpId,
    selectedHcpName: state.hcp.selectedHcpName,
  }

  sessionStorage.setItem(key, JSON.stringify(payload))
}

export function loadWorkspaceSession(): PersistedWorkspaceSession | null {
  const key = getStorageKey()
  const raw = sessionStorage.getItem(key)
  if (!raw) {
    return null
  }

  try {
    const parsed = JSON.parse(raw) as Partial<PersistedWorkspaceSession>
    return {
      conversationId: parsed.conversationId ?? null,
      draft: { ...EMPTY_INTERACTION_DRAFT, ...parsed.draft },
      status: parsed.status ?? 'draft',
      currentHcp: parsed.currentHcp ?? null,
      messages: Array.isArray(parsed.messages) ? parsed.messages : [],
      selectedHcpId: parsed.selectedHcpId ?? null,
      selectedHcpName: parsed.selectedHcpName ?? null,
    }
  } catch {
    sessionStorage.removeItem(key)
    return null
  }
}

export function clearWorkspaceSession(): void {
  sessionStorage.removeItem(getStorageKey())
}
