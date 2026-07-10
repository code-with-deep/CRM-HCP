import { describe, expect, it, vi } from 'vitest'

import { interactionReducer } from '@/store/slices/interactionSlice'
import { uiReducer } from '@/store/slices/uiSlice'
import { chatReducer } from '@/store/slices/chatSlice'
import { hcpReducer } from '@/store/slices/hcpSlice'
import { configureStore } from '@reduxjs/toolkit'

vi.mock('@/services/interactionService', () => ({
  interactionService: {
    saveInteraction: vi.fn(async () => ({
      id: 'saved-1',
      hcp_id: 'hcp-1',
      user_id: 'user-1',
      interaction_type_id: 'type-1',
      interaction_date: '2026-07-09',
      status: 'completed',
    })),
  },
}))

import { saveInteractionDraft } from '@/store/thunks/integrationThunks'

function createTestStore() {
  return configureStore({
    reducer: {
      chat: chatReducer,
      interaction: interactionReducer,
      ui: uiReducer,
      hcp: hcpReducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({ serializableCheck: false }),
  })
}

describe('saveInteractionDraft', () => {
  it('marks interaction completed after successful save', async () => {
    const store = createTestStore()
    store.dispatch({
      type: 'interaction/applyInteractionDraft',
      payload: {
        draft: {
          hcp_name: 'Dr Sharma',
          interaction_date: '2026-07-09',
        },
      },
    })

    await store.dispatch(saveInteractionDraft())

    const state = store.getState()
    expect(state.interaction.status).toBe('completed')
    expect(state.interaction.lastSavedInteractionId).toBe('saved-1')
    expect(state.ui.toasts[0]?.type).toBe('success')
  })
})
