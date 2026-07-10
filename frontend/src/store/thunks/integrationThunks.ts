import { createAsyncThunk } from '@reduxjs/toolkit'

import { classifyApiError, DEMO_USER_ID } from '@/services/apiClient'
import { chatService } from '@/services/chatService'
import { hcpService } from '@/services/hcpService'
import {
  interactionService,
  type SaveInteractionRequest,
} from '@/services/interactionService'
import type { RootState } from '@/store'
import {
  addUserMessage,
  appendAssistantToken,
  completeAssistantResponse,
  failAssistantResponse,
  resetChat,
  setChatStatus,
  setConversationId,
  setLastFailedMessage,
  startAssistantResponse,
  syncConversationHistory,
} from '@/store/slices/chatSlice'
import {
  resetHcpState,
  setHistoryError,
  setHistoryLoading,
  setHcpHistory,
  setSearchError,
  setSearchLoading,
  setSearchResults,
  setSelectedHcp,
} from '@/store/slices/hcpSlice'
import {
  applyInteractionDraft,
  detectChangedFields,
  setInteractionStatus,
  setLastSavedInteractionId,
  resetInteraction,
  setSaving,
  setSaveError,
} from '@/store/slices/interactionSlice'
import {
  addToast,
  clearHighlightedFields,
  setHighlightedFields,
} from '@/store/slices/uiSlice'
import type { ChatRequest, ChatResponseData } from '@/types/chat.types'
import {
  canSaveInteraction,
  createMessageId,
  mapHistoryToMessages,
  mergeInteractionDraft,
  parseChatResponseData,
} from '@/utils/chat'
import {
  clearWorkspaceSession,
  persistWorkspaceSession,
} from '@/utils/sessionPersistence'

function highlightChangedFields(
  dispatch: (action: unknown) => void,
  previous: RootState['interaction']['draft'],
  next: RootState['interaction']['draft'],
) {
  const changedFields = detectChangedFields(previous, next)
  if (changedFields.length > 0) {
    dispatch(setHighlightedFields(changedFields))
    window.setTimeout(() => dispatch(clearHighlightedFields()), 2500)
  }
}

function applyChatResponse(
  dispatch: (action: unknown) => void,
  getState: () => RootState,
  response: ChatResponseData,
  assistantContent: string,
) {
  const state = getState()
  const previousDraft = state.interaction.draft
  const nextDraft = mergeInteractionDraft(
    previousDraft,
    response.interaction_draft ?? {},
  )

  dispatch(
    completeAssistantResponse({
      content: assistantContent,
      selectedTool: response.selected_tool,
      toolCalled: response.selected_tool,
    }),  )

  dispatch(setConversationId(response.conversation_id))

  dispatch(
    applyInteractionDraft({
      draft: nextDraft,
      status: response.interaction_status ?? 'draft',
      currentHcp: response.current_hcp,
      validationErrors: response.validation_errors ?? [],
    }),
  )

  if (response.current_hcp) {
    const hcpId = response.current_hcp.hcp_id as string | undefined
    const hcpName = response.current_hcp.name as string | undefined
    if (hcpId || hcpName) {
      dispatch(
        setSelectedHcp({
          hcpId: hcpId ?? state.hcp.selectedHcpId,
          name: hcpName ?? state.hcp.selectedHcpName,
        }),
      )
    }
  }

  if (response.conversation_history?.length) {
    dispatch(syncConversationHistory(mapHistoryToMessages(response.conversation_history)))
  }

  highlightChangedFields(dispatch, previousDraft, nextDraft)
  persistWorkspaceSession(getState())
}

export const sendChatMessage = createAsyncThunk(
  'chat/sendMessage',
  async (message: string, { dispatch, getState, signal, rejectWithValue }) => {
    const state = getState() as RootState

    dispatch(
      addUserMessage({
        id: createMessageId(),
        role: 'user',
        content: message,
        timestamp: new Date().toISOString(),
      }),
    )

    const assistantMessageId = createMessageId()
    dispatch(
      startAssistantResponse({
        messageId: assistantMessageId,
        isStreaming: true,
      }),
    )
    dispatch(setLastFailedMessage(message))

    const request: ChatRequest = {
      message,
      conversation_id: state.chat.conversationId,
      user_id: DEMO_USER_ID,
      current_interaction: state.interaction.draft as unknown as Record<string, unknown>,
      current_hcp: state.interaction.currentHcp,
    }

    try {
      let finalContent = ''
      let responseData: ChatResponseData | null = null

      for await (const event of chatService.streamMessage(request, signal)) {
        if (event.event === 'token') {
          const token = String(event.data.content ?? '')
          finalContent += token
          dispatch(appendAssistantToken(token))
        }

        if (event.event === 'complete') {
          const response = event.data.response as Record<string, unknown> | undefined
          if (response) {
            responseData = parseChatResponseData(response)
            finalContent = responseData.assistant_message ?? finalContent
          }
        }

        if (event.event === 'error') {
          throw new Error(String(event.data.message ?? 'Stream failed'))
        }
      }

      if (!responseData) {
        responseData = await chatService.sendMessage(request)
        finalContent = responseData.assistant_message ?? ''
      }

      applyChatResponse(dispatch, () => getState() as RootState, responseData, finalContent)
      return responseData
    } catch (error) {
      const classified = classifyApiError(error)
      dispatch(failAssistantResponse(classified.message))
      dispatch(
        addToast({
          type: 'error',
          message: classified.message,
        }),
      )
      return rejectWithValue(classified.message)
    } finally {
      dispatch(setChatStatus('idle'))
    }
  },
)

export const saveInteractionDraft = createAsyncThunk(
  'interaction/save',
  async (_, { dispatch, getState, rejectWithValue }) => {
    const state = getState() as RootState

    if (!canSaveInteraction(state.interaction.draft)) {
      const message =
        'Cannot save yet. Ask the AI to capture the HCP name and interaction date first.'
      dispatch(setSaveError(message))
      dispatch(addToast({ type: 'error', message }))
      return rejectWithValue(message)
    }

    if (state.interaction.validationErrors.length > 0) {
      const message =
        'Resolve AI validation notes before saving, or ask the assistant to correct the draft.'
      dispatch(setSaveError(message))
      dispatch(addToast({ type: 'error', message }))
      return rejectWithValue(message)
    }

    dispatch(setSaving(true))
    dispatch(setSaveError(null))

    const request: SaveInteractionRequest = {
      user_id: DEMO_USER_ID,
      conversation_id: state.chat.conversationId,
      hcp_id: state.hcp.selectedHcpId,
      interaction_draft: state.interaction.draft,
      status: 'completed',
    }

    try {
      const saved = await interactionService.saveInteraction(request)
      dispatch(setLastSavedInteractionId(saved.id))
      dispatch(setInteractionStatus('completed'))
      clearWorkspaceSession()
      dispatch(
        addToast({
          type: 'success',
          message: 'Interaction saved successfully.',
        }),
      )
      return saved
    } catch (error) {
      const classified = classifyApiError(error)
      dispatch(setSaveError(classified.message))
      dispatch(addToast({ type: 'error', message: classified.message }))
      return rejectWithValue(classified.message)
    } finally {
      dispatch(setSaving(false))
    }
  },
)

export const startNewInteraction = createAsyncThunk(
  'interaction/startNew',
  async (_, { dispatch }) => {
    clearWorkspaceSession()
    dispatch(resetChat())
    dispatch(resetInteraction())
    dispatch(resetHcpState())
    dispatch(clearHighlightedFields())
    dispatch(
      addToast({
        type: 'info',
        message: 'Started a new interaction draft.',
      }),
    )
  },
)

export const searchHcps = createAsyncThunk(
  'hcp/search',
  async (
    params: {
      doctor_name?: string
      hospital?: string
      city?: string
      specialization?: string
    },
    { dispatch },
  ) => {
    dispatch(setSearchLoading(true))
    try {
      const results = await hcpService.searchHcps(params)
      dispatch(setSearchResults(results.items))
      return results
    } catch (error) {
      const classified = classifyApiError(error)
      dispatch(setSearchError(classified.message))
      throw error
    } finally {
      dispatch(setSearchLoading(false))
    }
  },
)

export const fetchHcpHistory = createAsyncThunk(
  'hcp/history',
  async (hcpId: string, { dispatch }) => {
    dispatch(setHistoryLoading(true))
    try {
      const history = await hcpService.getHcpHistory(hcpId)
      dispatch(setHcpHistory(history.interactions))
      dispatch(
        setSelectedHcp({
          hcpId: history.hcp_id,
          name: history.hcp_name,
        }),
      )
      return history
    } catch (error) {
      const classified = classifyApiError(error)
      dispatch(setHistoryError(classified.message))
      throw error
    } finally {
      dispatch(setHistoryLoading(false))
    }
  },
)
