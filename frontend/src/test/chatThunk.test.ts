import { configureStore } from '@reduxjs/toolkit'
import { describe, expect, it, vi } from 'vitest'

import { chatReducer, failAssistantResponse } from '@/store/slices/chatSlice'
import { interactionReducer } from '@/store/slices/interactionSlice'
import { uiReducer } from '@/store/slices/uiSlice'
import { hcpReducer } from '@/store/slices/hcpSlice'

vi.mock('@/services/chatService', () => ({
  chatService: {
    sendMessage: vi.fn(),
    streamMessage: async function* () {
      yield {
        event: 'complete',
        data: {
          response: {
            conversation_id: 'conv-1',
            assistant_message: 'Updated Dr Sharma interaction.',
            interaction_draft: {
              hcp_name: 'Dr Sharma',
              interaction_type: 'Meeting',
              interaction_date: '2026-07-09',
              interaction_time: null,
              attendees: [],
              topics_discussed: ['CardioMax'],
              materials_shared: [],
              samples_distributed: [],
              sentiment: 'positive',
              outcomes: null,
              follow_up_actions: null,
              additional_notes: null,
            },
            current_hcp: { hcp_id: 'hcp-1', name: 'Dr Sharma' },
            interaction_status: 'draft',
            conversation_history: [],
            selected_tool: 'log_interaction',
            tool_result: null,
            validation_errors: [],
            suggested_prompts: [],
            memory: {},
            error_message: null,
          },
        },
      }
    },
  },
}))

import { sendChatMessage } from '@/store/thunks/integrationThunks'

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

describe('sendChatMessage integration', () => {
  it('updates interaction draft and highlights changed fields', async () => {
    const store = createTestStore()
    await store.dispatch(sendChatMessage('I met Dr Sharma today.'))

    const state = store.getState()
    expect(state.interaction.draft.hcp_name).toBe('Dr Sharma')
    expect(state.interaction.draft.topics_discussed).toEqual(['CardioMax'])
    expect(state.chat.conversationId).toBe('conv-1')
    expect(state.chat.selectedTool).toBe('log_interaction')
    expect(state.hcp.selectedHcpId).toBe('hcp-1')
  })
})

describe('chat error handling', () => {
  it('removes failed streaming placeholder messages', () => {
    let state = chatReducer(undefined, { type: 'init' })
    state = chatReducer(
      state,
      failAssistantResponse('Backend unavailable'),
    )

    expect(state.error).toBe('Backend unavailable')
    expect(state.streamingMessageId).toBeNull()
  })
})
