import { motion } from 'framer-motion'

import { Label } from '@/components/ui/label'
import { notifyManualFormEditBlocked } from '@/utils/manualEditGuard'
import { cn } from '@/lib/utils'
import type { SentimentValue } from '@/types/interaction.types'

interface SentimentSelectorProps {
  value: SentimentValue
  highlighted?: boolean
}

const SENTIMENTS = [
  { value: 'positive' as const, label: 'Positive', emoji: '😊' },
  { value: 'neutral' as const, label: 'Neutral', emoji: '😐' },
  { value: 'negative' as const, label: 'Negative', emoji: '😟' },
]

export function SentimentSelector({
  value,
  highlighted,
}: SentimentSelectorProps) {
  return (
    <motion.div
      layout
      className="space-y-2 border-t border-slate-200 pt-5"
      animate={
        highlighted
          ? {
              boxShadow: '0 0 0 2px rgb(124 58 237 / 0.2)',
              backgroundColor: 'rgb(245 243 255 / 0.7)',
            }
          : { boxShadow: '0 0 0 0px transparent', backgroundColor: 'transparent' }
      }
      transition={{ duration: 0.35, ease: 'easeOut' }}
      style={{ borderRadius: '0.5rem', padding: highlighted ? '0.4rem' : '0' }}
      onMouseDown={(event) => {
        event.preventDefault()
        notifyManualFormEditBlocked('Sentiment')
      }}
    >
      <Label className="text-sm font-bold text-slate-800">
        Observed/Inferred HCP Sentiment
      </Label>
      <div
        className="flex flex-wrap items-center gap-6"
        role="radiogroup"
        aria-label="HCP Sentiment"
        aria-readonly="true"
      >
        {SENTIMENTS.map(({ value: sentiment, label, emoji }) => {
          const isActive = value === sentiment
          return (
            <button
              key={sentiment}
              type="button"
              aria-checked={isActive}
              role="radio"
              className="flex cursor-pointer items-center gap-2 text-sm text-slate-700"
              onClick={(event) => {
                event.preventDefault()
                notifyManualFormEditBlocked('Sentiment')
              }}
            >
              <span
                className={cn(
                  'flex h-4 w-4 items-center justify-center rounded-full border-2',
                  isActive
                    ? 'border-violet-600 bg-violet-600'
                    : 'border-slate-300 bg-white',
                )}
                aria-hidden="true"
              >
                {isActive ? (
                  <span className="h-1.5 w-1.5 rounded-full bg-white" />
                ) : null}
              </span>
              <span aria-hidden="true">{emoji}</span>
              <span className={cn(isActive && 'font-semibold text-slate-900')}>
                {label}
              </span>
            </button>
          )
        })}
      </div>
    </motion.div>
  )
}
