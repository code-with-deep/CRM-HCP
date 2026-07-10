import { InteractionCard } from '@/components/interaction/InteractionCard'
import { AIChatPanel } from '@/components/chat/AIChatPanel'
import { SplitScreenLayout } from '@/components/layout/SplitScreenLayout'
import { useChatActions } from '@/hooks/useChatActions'
import { useSessionRestore } from '@/hooks/useSessionRestore'

export function LogInteractionPage() {
  useSessionRestore()

  const { sendMessage, saveInteraction, retryLastMessage, beginNewInteraction, lastFailedMessage } =
    useChatActions()
  return (
    <SplitScreenLayout
      leftPanel={
        <InteractionCard
          onSave={saveInteraction}
          onStartNew={beginNewInteraction}
          onAskAssistant={sendMessage}
        />
      }
      rightPanel={
        <AIChatPanel
          onSendMessage={sendMessage}
          onRetry={retryLastMessage}
          canRetry={Boolean(lastFailedMessage)}
        />      }
    />
  )
}
