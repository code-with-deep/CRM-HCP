import { useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import type { AppDispatch, RootState } from '@/store'
import {
  saveInteractionDraft,
  sendChatMessage,
  startNewInteraction,
} from '@/store/thunks/integrationThunks'
import { setChatError } from '@/store/slices/chatSlice'
import { setSaveError } from '@/store/slices/interactionSlice'

export function useChatActions() {
  const dispatch = useDispatch<AppDispatch>()
  const lastFailedMessage = useSelector(
    (state: RootState) => state.chat.lastFailedMessage,
  )
  const isBusy = useSelector(
    (state: RootState) =>
      state.chat.status === 'streaming' ||
      state.chat.status === 'connecting' ||
      state.chat.isTyping,
  )
  const isSaving = useSelector((state: RootState) => state.interaction.isSaving)

  const sendMessage = useCallback(
    (message: string) => {
      dispatch(setChatError(null))
      void dispatch(sendChatMessage(message))
    },
    [dispatch],
  )

  const retryLastMessage = useCallback(() => {
    if (lastFailedMessage) {
      sendMessage(lastFailedMessage)
    }
  }, [lastFailedMessage, sendMessage])

  const saveInteraction = useCallback(() => {
    dispatch(setSaveError(null))
    void dispatch(saveInteractionDraft())
  }, [dispatch])

  const beginNewInteraction = useCallback(() => {
    void dispatch(startNewInteraction())
  }, [dispatch])

  return {
    sendMessage,
    saveInteraction,
    retryLastMessage,
    beginNewInteraction,
    lastFailedMessage,
    isBusy,
    isSaving,
  }
}
