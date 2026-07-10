import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import {
  EMPTY_INTERACTION_DRAFT,
  type InteractionDraft,
  type InteractionFieldKey,
  type InteractionStatus,
} from '@/types/interaction.types'

interface InteractionState {
  draft: InteractionDraft
  status: InteractionStatus
  currentHcp: Record<string, unknown> | null
  validationErrors: string[]
  isSaving: boolean
  saveError: string | null
  lastSavedInteractionId: string | null
}

const initialState: InteractionState = {
  draft: EMPTY_INTERACTION_DRAFT,
  status: 'draft',
  currentHcp: null,
  validationErrors: [],
  isSaving: false,
  saveError: null,
  lastSavedInteractionId: null,
}

export function detectChangedFields(
  previous: InteractionDraft,
  next: InteractionDraft,
): InteractionFieldKey[] {
  const changed: InteractionFieldKey[] = []
  const keys = Object.keys(next) as InteractionFieldKey[]

  for (const key of keys) {
    const prevValue = previous[key]
    const nextValue = next[key]

    if (Array.isArray(prevValue) && Array.isArray(nextValue)) {
      if (JSON.stringify(prevValue) !== JSON.stringify(nextValue)) {
        changed.push(key)
      }
      continue
    }

    if (prevValue !== nextValue) {
      changed.push(key)
    }
  }

  return changed
}

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    applyInteractionDraft(
      state,
      action: PayloadAction<{
        draft: Partial<InteractionDraft>
        status?: InteractionStatus
        currentHcp?: Record<string, unknown> | null
        validationErrors?: string[]
      }>,
    ) {
      state.draft = { ...state.draft, ...action.payload.draft }
      if (action.payload.status !== undefined) {
        state.status = action.payload.status
      }
      if (action.payload.currentHcp !== undefined) {
        state.currentHcp = action.payload.currentHcp
      }
      if (action.payload.validationErrors !== undefined) {
        state.validationErrors = action.payload.validationErrors
      }
    },
    setInteractionStatus(state, action: PayloadAction<InteractionStatus>) {
      state.status = action.payload
    },
    setSaving(state, action: PayloadAction<boolean>) {
      state.isSaving = action.payload
    },
    setSaveError(state, action: PayloadAction<string | null>) {
      state.saveError = action.payload
    },
    setLastSavedInteractionId(state, action: PayloadAction<string | null>) {
      state.lastSavedInteractionId = action.payload
    },
    resetInteraction() {
      return initialState
    },
  },
})

export const {
  applyInteractionDraft,
  setInteractionStatus,
  setSaving,
  setSaveError,
  setLastSavedInteractionId,
  resetInteraction,
} = interactionSlice.actions

export const interactionReducer = interactionSlice.reducer
