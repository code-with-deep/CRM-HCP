import { memo } from 'react'

import { cn } from '@/lib/utils'
import type { ChatMessage } from '@/types/chat.types'

interface MessageBubbleProps {
  message: ChatMessage
}

export const MessageBubble = memo(function MessageBubble({
  message,
}: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}
      role="article"
      aria-label={`${message.role} message`}
    >
      <div
        className={cn(
          'max-w-[92%] rounded-2xl px-4 py-3 text-sm leading-6',
          isUser
            ? 'rounded-br-md bg-blue-600 text-white shadow-sm'
            : 'rounded-bl-md bg-sky-100 text-slate-800',
        )}
      >
        <p className="whitespace-pre-wrap break-words">
          {message.content}
          {message.isStreaming ? (
            <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-current" />
          ) : null}
        </p>
        {message.toolCalled ? (
          <p
            className={cn(
              'mt-2 text-xs',
              isUser ? 'text-blue-100' : 'text-sky-700',
            )}
          >
            Tool: {message.toolCalled}
          </p>
        ) : null}
      </div>
    </div>
  )
})
