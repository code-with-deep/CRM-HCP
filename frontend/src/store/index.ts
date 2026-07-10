import { configureStore } from '@reduxjs/toolkit'

import { appReducer } from '@/store/slices/appSlice'
import { chatReducer } from '@/store/slices/chatSlice'
import { hcpReducer } from '@/store/slices/hcpSlice'
import { interactionReducer } from '@/store/slices/interactionSlice'
import { uiReducer } from '@/store/slices/uiSlice'

export const store = configureStore({
  reducer: {
    app: appReducer,
    chat: chatReducer,
    interaction: interactionReducer,
    ui: uiReducer,
    hcp: hcpReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
