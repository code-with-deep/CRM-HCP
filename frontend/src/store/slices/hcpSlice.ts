import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { HcpHistoryItem, HcpRecord } from '@/types/hcp.types'

interface HcpState {
  searchResults: HcpRecord[]
  searchLoading: boolean
  searchError: string | null
  selectedHcpId: string | null
  selectedHcpName: string | null
  history: HcpHistoryItem[]
  historyLoading: boolean
  historyError: string | null
}

const initialState: HcpState = {
  searchResults: [],
  searchLoading: false,
  searchError: null,
  selectedHcpId: null,
  selectedHcpName: null,
  history: [],
  historyLoading: false,
  historyError: null,
}

const hcpSlice = createSlice({
  name: 'hcp',
  initialState,
  reducers: {
    setSearchLoading(state, action: PayloadAction<boolean>) {
      state.searchLoading = action.payload
    },
    setSearchResults(state, action: PayloadAction<HcpRecord[]>) {
      state.searchResults = action.payload
      state.searchError = null
    },
    setSearchError(state, action: PayloadAction<string | null>) {
      state.searchError = action.payload
      state.searchLoading = false
    },
    setSelectedHcp(
      state,
      action: PayloadAction<{ hcpId: string | null; name?: string | null }>,
    ) {
      state.selectedHcpId = action.payload.hcpId
      state.selectedHcpName = action.payload.name ?? state.selectedHcpName
    },
    setHistoryLoading(state, action: PayloadAction<boolean>) {
      state.historyLoading = action.payload
    },
    setHcpHistory(state, action: PayloadAction<HcpHistoryItem[]>) {
      state.history = action.payload
      state.historyError = null
    },
    setHistoryError(state, action: PayloadAction<string | null>) {
      state.historyError = action.payload
      state.historyLoading = false
    },
    resetHcpState() {
      return initialState
    },
  },
})

export const {
  setSearchLoading,
  setSearchResults,
  setSearchError,
  setSelectedHcp,
  setHistoryLoading,
  setHcpHistory,
  setHistoryError,
  resetHcpState,
} = hcpSlice.actions

export const hcpReducer = hcpSlice.reducer
