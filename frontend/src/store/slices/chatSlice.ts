import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { ChatMessage, ChatStatus } from '@/types/chat.types'

interface ChatState {
  messages: ChatMessage[]
  conversationId: string | null
  status: ChatStatus
  isTyping: boolean
  streamingMessageId: string | null
  selectedTool: string | null
  error: string | null
  lastFailedMessage: string | null
}

const initialState: ChatState = {
  messages: [
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Describe your HCP interaction in your own words. I will update the form using the available tools.',
      timestamp: new Date().toISOString(),
    },
  ],
  conversationId: null,
  status: 'idle',  isTyping: false,
  streamingMessageId: null,
  selectedTool: null,
  error: null,
  lastFailedMessage: null,
}

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addUserMessage(state, action: PayloadAction<ChatMessage>) {
      state.messages.push(action.payload)
      state.error = null
      state.lastFailedMessage = null
    },
    startAssistantResponse(
      state,
      action: PayloadAction<{ messageId: string; isStreaming?: boolean }>,
    ) {
      state.isTyping = true
      state.status = action.payload.isStreaming ? 'streaming' : 'connecting'
      state.streamingMessageId = action.payload.messageId
      state.error = null
      state.messages.push({
        id: action.payload.messageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: action.payload.isStreaming ?? false,
      })
    },
    appendAssistantToken(state, action: PayloadAction<string>) {
      const message = state.messages.find(
        (item) => item.id === state.streamingMessageId,
      )
      if (message) {
        message.content += action.payload
        message.isStreaming = true
        state.isTyping = false
      }
    },
    completeAssistantResponse(
      state,
      action: PayloadAction<{
        content: string
        selectedTool?: string | null
        toolCalled?: string | null
      }>,    ) {
      const message = state.messages.find(
        (item) => item.id === state.streamingMessageId,
      )
      if (message) {
        message.content = action.payload.content
        message.isStreaming = false
        message.toolCalled = action.payload.toolCalled ?? action.payload.selectedTool
      }
      state.isTyping = false
      state.status = 'idle'
      state.streamingMessageId = null
      state.selectedTool = action.payload.selectedTool ?? null
      state.error = null
      state.lastFailedMessage = null
    },    failAssistantResponse(state, action: PayloadAction<string>) {
      if (state.streamingMessageId) {
        state.messages = state.messages.filter(
          (message) => message.id !== state.streamingMessageId,
        )
      }
      state.isTyping = false
      state.status = 'error'
      state.streamingMessageId = null
      state.error = action.payload
    },
    setConversationId(state, action: PayloadAction<string | null>) {
      state.conversationId = action.payload
    },
    setChatStatus(state, action: PayloadAction<ChatStatus>) {      state.status = action.payload
    },
    setChatError(state, action: PayloadAction<string | null>) {
      state.error = action.payload
      if (action.payload) {
        state.isTyping = false
        state.status = 'error'
      }
    },
    setLastFailedMessage(state, action: PayloadAction<string | null>) {
      state.lastFailedMessage = action.payload
    },
    syncConversationHistory(state, action: PayloadAction<ChatMessage[]>) {
      if (action.payload.length > 0) {
        state.messages = action.payload
      }
    },
    resetChat() {
      return initialState
    },
  },
})

export const {
  addUserMessage,
  startAssistantResponse,
  appendAssistantToken,
  completeAssistantResponse,
  failAssistantResponse,
  setConversationId,
  setChatStatus,  setChatError,
  setLastFailedMessage,
  syncConversationHistory,
  resetChat,
} = chatSlice.actions

export const chatReducer = chatSlice.reducer
