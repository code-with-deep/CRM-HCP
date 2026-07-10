import { useEffect, useRef } from 'react'
import { Bot } from 'lucide-react'
import { useSelector } from 'react-redux'

import { ChatInput } from '@/components/chat/ChatInput'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { TypingIndicator } from '@/components/chat/TypingIndicator'
import { StatusBadge } from '@/components/common/StatusBadge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { RootState } from '@/store'
import { cn } from '@/lib/utils'

interface AIChatPanelProps {
  onSendMessage: (message: string) => void
  onRetry?: () => void
  canRetry?: boolean
  className?: string
}

export function AIChatPanel({
  onSendMessage,
  onRetry,
  canRetry = false,
  className,
}: AIChatPanelProps) {
  const messages = useSelector((state: RootState) => state.chat.messages)
  const isTyping = useSelector((state: RootState) => state.chat.isTyping)
  const status = useSelector((state: RootState) => state.chat.status)
  const streamingMessageId = useSelector(
    (state: RootState) => state.chat.streamingMessageId,
  )
  const selectedTool = useSelector((state: RootState) => state.chat.selectedTool)
  const error = useSelector((state: RootState) => state.chat.error)

  const bottomRef = useRef<HTMLDivElement>(null)
  const isBusy = status === 'streaming' || status === 'connecting'
  const showTypingIndicator =
    (isTyping || status === 'connecting') &&
    !messages.some(
      (message) => message.id === streamingMessageId && message.content.length > 0,
    )

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  return (
    <div className={cn('flex h-full flex-col border-l border-slate-200 bg-white', className)}>
      <header className="border-b border-slate-200 px-5 py-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-blue-600">
              <Bot className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-blue-600">AI Assistant</h2>
              <p className="text-xs text-slate-500">
                Log Interaction details here via chat
              </p>
            </div>
          </div>
          <StatusBadge
            label={isBusy ? 'processing' : 'ready'}
            variant={isBusy ? 'warning' : 'success'}
          />
        </div>
        {selectedTool ? (
          <p className="mt-2 text-xs text-slate-500">
            Last tool:{' '}
            <span className="font-medium text-slate-700">{selectedTool}</span>
          </p>
        ) : null}
      </header>

      <ScrollArea className="flex-1 px-5 py-4">
        <div className="space-y-4" role="log" aria-live="polite" aria-relevant="additions">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {showTypingIndicator ? <TypingIndicator /> : null}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {error ? (
        <div
          className="mx-5 mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700"
          role="alert"
        >
          <p>{error}</p>
          {canRetry && onRetry ? (
            <button
              type="button"
              onClick={onRetry}
              className="mt-2 font-medium text-red-800 underline underline-offset-2 hover:text-red-900"
            >
              Retry last message
            </button>
          ) : null}
        </div>
      ) : null}

      <div className="border-t border-slate-200 bg-white px-5 py-4">
        <ChatInput onSend={onSendMessage} disabled={isBusy} />
      </div>    </div>
  )
}
