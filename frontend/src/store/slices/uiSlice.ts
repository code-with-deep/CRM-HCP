import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { InteractionFieldKey } from '@/types/interaction.types'

export type ToastType = 'success' | 'error' | 'info'

export interface ToastMessage {
  id: string
  type: ToastType
  message: string
}

interface UiState {
  highlightedFields: InteractionFieldKey[]
  isMobileChatOpen: boolean
  activePanel: 'form' | 'chat'
  toasts: ToastMessage[]
}

const initialState: UiState = {
  highlightedFields: [],
  isMobileChatOpen: false,
  activePanel: 'form',
  toasts: [],
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setHighlightedFields(state, action: PayloadAction<InteractionFieldKey[]>) {
      state.highlightedFields = action.payload
    },
    clearHighlightedFields(state) {
      state.highlightedFields = []
    },
    setMobileChatOpen(state, action: PayloadAction<boolean>) {
      state.isMobileChatOpen = action.payload
    },
    setActivePanel(state, action: PayloadAction<'form' | 'chat'>) {
      state.activePanel = action.payload
    },
    addToast(state, action: PayloadAction<{ type: ToastType; message: string }>) {
      state.toasts.push({
        id: `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        type: action.payload.type,
        message: action.payload.message,
      })
    },
    removeToast(state, action: PayloadAction<string>) {
      state.toasts = state.toasts.filter((toast) => toast.id !== action.payload)
    },
    clearToasts(state) {
      state.toasts = []
    },
  },
})

export const {
  setHighlightedFields,
  clearHighlightedFields,
  setMobileChatOpen,
  setActivePanel,
  addToast,
  removeToast,
  clearToasts,
} = uiSlice.actions

export const uiReducer = uiSlice.reducer
