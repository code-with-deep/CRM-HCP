export type SentimentValue = 'positive' | 'neutral' | 'negative' | null

export type InteractionStatus = 'draft' | 'completed' | 'archived' | string

export interface InteractionDraft {
  hcp_name: string | null
  interaction_type: string | null
  interaction_date: string | null
  interaction_time: string | null
  attendees: string[]
  topics_discussed: string[]
  materials_shared: string[]
  samples_distributed: string[]
  sentiment: SentimentValue
  outcomes: string | null
  follow_up_actions: string | null
  additional_notes: string | null
}

export const EMPTY_INTERACTION_DRAFT: InteractionDraft = {
  hcp_name: null,
  interaction_type: null,
  interaction_date: null,
  interaction_time: null,
  attendees: [],
  topics_discussed: [],
  materials_shared: [],
  samples_distributed: [],
  sentiment: null,
  outcomes: null,
  follow_up_actions: null,
  additional_notes: null,
}

export type InteractionFieldKey = keyof InteractionDraft
