import { apiClient } from '@/services/apiClient'
import type { ApiResponse } from '@/types/api.types'
import type { InteractionDraft } from '@/types/interaction.types'

export interface SaveInteractionRequest {
  user_id: string
  conversation_id?: string | null
  hcp_id?: string | null
  interaction_draft: InteractionDraft
  status?: 'draft' | 'completed' | 'archived'
  ai_generated_summary?: string | null
}

export interface SavedInteraction {
  id: string
  hcp_id: string
  user_id: string
  interaction_type_id: string
  conversation_id?: string | null
  interaction_date: string
  interaction_time?: string | null
  summary?: string | null
  sentiment?: string | null
  outcome?: string | null
  follow_up?: string | null
  additional_notes?: string | null
  status: string
}

/**
 * Interaction API service for /interaction/save and /interaction/{id}.
 */
export class InteractionService {
  async saveInteraction(
    request: SaveInteractionRequest,
  ): Promise<SavedInteraction> {
    const response = await apiClient.post<ApiResponse<SavedInteraction>>(
      '/interaction/save',
      request,
    )
    return response.data.data
  }

  async getInteraction(interactionId: string): Promise<SavedInteraction> {
    const response = await apiClient.get<ApiResponse<SavedInteraction>>(
      `/interaction/${interactionId}`,
    )
    return response.data.data
  }
}

export const interactionService = new InteractionService()
