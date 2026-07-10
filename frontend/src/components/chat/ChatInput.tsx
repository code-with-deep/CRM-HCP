import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'

import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

const chatSchema = z.object({
  message: z.string().trim().min(1, 'Message is required'),
})

type ChatFormValues = z.infer<typeof chatSchema>

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Describe Interaction...',
  className,
}: ChatInputProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChatFormValues>({
    resolver: zodResolver(chatSchema),
    defaultValues: { message: '' },
  })

  const onSubmit = handleSubmit(({ message }) => {
    onSend(message)
    reset()
  })

  return (
    <form
      onSubmit={onSubmit}
      className={cn('flex items-end gap-3', className)}
      aria-label="Chat message form"
    >
      <div className="flex-1">
        <label htmlFor="chat-input" className="sr-only">
          Message
        </label>
        <Textarea
          id="chat-input"
          {...register('message')}
          placeholder={placeholder}
          disabled={disabled}
          rows={3}
          className="min-h-[84px] resize-none rounded-md border-slate-300 bg-white"
          aria-label="Describe interaction for the AI assistant"
          aria-invalid={Boolean(errors.message)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void onSubmit()
            }
          }}
        />
        {errors.message ? (
          <p className="mt-1 text-xs text-red-600" role="alert">
            {errors.message.message}
          </p>
        ) : null}
      </div>
      <button
        type="submit"
        disabled={disabled}
        aria-label="Log interaction with AI"
        className={cn(
          'flex h-14 w-14 shrink-0 flex-col items-center justify-center rounded-full bg-blue-600 text-white shadow-md transition hover:bg-blue-700',
          'disabled:cursor-not-allowed disabled:opacity-60',
        )}
      >
        <span className="text-base font-bold leading-none">A</span>
        <span className="mt-0.5 text-[10px] font-semibold uppercase tracking-wide">
          Log
        </span>
      </button>
    </form>
  )
}
