import { useEffect, useRef } from 'react'

import { DEMO_USER_ID } from '@/services/apiClient'
import { chatService } from '@/services/chatService'
import { useAppDispatch } from '@/store/hooks'
import {
  setConversationId,
  syncConversationHistory,
} from '@/store/slices/chatSlice'
import { setSelectedHcp } from '@/store/slices/hcpSlice'
import { applyInteractionDraft } from '@/store/slices/interactionSlice'
import { mapHistoryToMessages, mergeInteractionDraft } from '@/utils/chat'
import {
  hasMeaningfulDraft,
  loadWorkspaceSession,
  type PersistedWorkspaceSession,
} from '@/utils/sessionPersistence'

function applyPersistedSession(
  dispatch: ReturnType<typeof useAppDispatch>,
  session: PersistedWorkspaceSession,
) {
  if (session.conversationId) {
    dispatch(setConversationId(session.conversationId))
  }

  dispatch(
    applyInteractionDraft({
      draft: session.draft,
      status: session.status,
      currentHcp: session.currentHcp,
      validationErrors: [],
    }),
  )

  if (session.selectedHcpId || session.selectedHcpName) {
    dispatch(
      setSelectedHcp({
        hcpId: session.selectedHcpId,
        name: session.selectedHcpName,
      }),
    )
  }

  if (session.messages.length > 0) {
    dispatch(syncConversationHistory(session.messages))
  }
}

/**
 * Rehydrate chat + interaction state after a browser refresh.
 */
export function useSessionRestore() {
  const dispatch = useAppDispatch()
  const restoredRef = useRef(false)

  useEffect(() => {
    if (restoredRef.current) {
      return
    }
    restoredRef.current = true

    const restore = async () => {
      const localSession = loadWorkspaceSession()
      if (!localSession) {
        return
      }

      if (
        !localSession.conversationId &&
        !hasMeaningfulDraft(localSession.draft) &&
        localSession.messages.length <= 1
      ) {
        return
      }

      if (localSession.conversationId) {
        try {
          const serverSession = await chatService.getSession(
            localSession.conversationId,
            DEMO_USER_ID,
          )

          dispatch(setConversationId(serverSession.conversation_id))
          dispatch(
            applyInteractionDraft({
              draft: mergeInteractionDraft(
                localSession.draft,
                serverSession.interaction_draft ?? {},
              ),
              status: serverSession.interaction_status ?? localSession.status,
              currentHcp: serverSession.current_hcp ?? localSession.currentHcp,
              validationErrors: serverSession.validation_errors ?? [],
            }),
          )

          const hcpId = serverSession.current_hcp?.hcp_id as string | undefined
          const hcpName = serverSession.current_hcp?.name as string | undefined
          if (hcpId || hcpName) {
            dispatch(
              setSelectedHcp({
                hcpId: hcpId ?? localSession.selectedHcpId,
                name: hcpName ?? localSession.selectedHcpName,
              }),
            )
          } else if (localSession.selectedHcpId || localSession.selectedHcpName) {
            dispatch(
              setSelectedHcp({
                hcpId: localSession.selectedHcpId,
                name: localSession.selectedHcpName,
              }),
            )
          }

          if (serverSession.conversation_history?.length) {
            dispatch(
              syncConversationHistory(
                mapHistoryToMessages(serverSession.conversation_history),
              ),
            )
          } else if (localSession.messages.length > 0) {
            dispatch(syncConversationHistory(localSession.messages))
          }

          return
        } catch {
          // Fall back to browser session storage when the API is unavailable.
        }
      }

      applyPersistedSession(dispatch, localSession)
    }

    void restore()
  }, [dispatch])
}
