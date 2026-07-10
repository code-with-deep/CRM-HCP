import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type { ApplicationInfo, HealthCheck } from '@/types/api.types'

interface AppState {
  applicationInfo: ApplicationInfo | null
  healthCheck: HealthCheck | null
  isLoading: boolean
  error: string | null
}

const initialState: AppState = {
  applicationInfo: null,
  healthCheck: null,
  isLoading: false,
  error: null,
}

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setLoading(state, action: PayloadAction<boolean>) {
      state.isLoading = action.payload
    },
    setApplicationInfo(state, action: PayloadAction<ApplicationInfo>) {
      state.applicationInfo = action.payload
      state.error = null
    },
    setHealthCheck(state, action: PayloadAction<HealthCheck>) {
      state.healthCheck = action.payload
      state.error = null
    },
    setError(state, action: PayloadAction<string>) {
      state.error = action.payload
      state.isLoading = false
    },
    resetAppState() {
      return initialState
    },
  },
})

export const {
  setLoading,
  setApplicationInfo,
  setHealthCheck,
  setError,
  resetAppState,
} = appSlice.actions

export const appReducer = appSlice.reducer
