import { memo, useCallback } from 'react'
import { Mic } from 'lucide-react'
import { useSelector } from 'react-redux'
import { toast } from 'sonner'

import {
  DateField,
  HcpNameField,
  InteractionField,
  InteractionTypeField,
  MaterialsSamplesSection,
  TagListField,
  TimeField,
} from '@/components/interaction/InteractionField'
import { SaveButton } from '@/components/interaction/SaveButton'
import { SentimentSelector } from '@/components/interaction/SentimentSelector'
import { HcpContextBanner } from '@/components/interaction/HcpContextBanner'
import { StatusBadge } from '@/components/common/StatusBadge'
import { Button } from '@/components/ui/button'
import type { RootState } from '@/store'
import { notifyManualFormEditBlocked } from '@/utils/manualEditGuard'
import { canSaveInteraction } from '@/utils/chat'
import { cn } from '@/lib/utils'

interface InteractionCardProps {
  onSave: () => void
  onStartNew?: () => void
  onAskAssistant?: (message: string) => void
  className?: string
}

function guideToChat(example: string) {
  toast.error('Use the AI Assistant', {
    description: `This form is AI-controlled. Type in the chat on the right — for example: “${example}”.`,
    duration: 5500,
  })
}

export const InteractionCard = memo(function InteractionCard({
  onSave,
  onStartNew,
  className,
}: InteractionCardProps) {
  const draft = useSelector((state: RootState) => state.interaction.draft)
  const status = useSelector((state: RootState) => state.interaction.status)
  const validationErrors = useSelector(
    (state: RootState) => state.interaction.validationErrors,
  )
  const isSaving = useSelector((state: RootState) => state.interaction.isSaving)
  const saveError = useSelector((state: RootState) => state.interaction.saveError)
  const lastSavedInteractionId = useSelector(
    (state: RootState) => state.interaction.lastSavedInteractionId,
  )
  const highlightedFields = useSelector(
    (state: RootState) => state.ui.highlightedFields,
  )

  const isHighlighted = (field: string) => highlightedFields.includes(field as never)
  const canSave =
    canSaveInteraction(draft) &&
    status !== 'completed' &&
    validationErrors.length === 0

  const handleVoiceNoteClick = useCallback(() => {
    guideToChat(
      'Summarize from voice note with consent: met Dr Sharma, discussed CardioMax, positive sentiment',
    )
  }, [])

  return (
    <div className={cn('flex h-full flex-col bg-white', className)}>
      <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4 lg:px-6">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">
            Log HCP Interaction
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Fields are filled by the AI Assistant — edit through chat, not the form.
          </p>
        </div>
        <StatusBadge
          label={status}
          variant={status === 'completed' ? 'success' : 'default'}
        />
      </header>

      <div className="flex-1 overflow-y-auto px-5 py-5 lg:px-6">
        <div className="mx-auto max-w-3xl space-y-5">
          <HcpContextBanner />

          <HcpNameField
            value={draft.hcp_name ?? ''}
            highlighted={isHighlighted('hcp_name')}
          />

          <div className="grid gap-4 sm:grid-cols-3">
            <InteractionTypeField
              value={draft.interaction_type ?? ''}
              highlighted={isHighlighted('interaction_type')}
            />
            <DateField
              value={draft.interaction_date ?? ''}
              highlighted={isHighlighted('interaction_date')}
            />
            <TimeField
              value={draft.interaction_time ?? ''}
              highlighted={isHighlighted('interaction_time')}
            />
          </div>

          <TagListField
            id="attendees"
            label="Attendees"
            items={draft.attendees}
            highlighted={isHighlighted('attendees')}
            placeholder="Enter names or search..."
          />

          <div className="space-y-2">
            <InteractionField
              id="topics-discussed"
              label="Topics Discussed"
              value={draft.topics_discussed.join(', ')}
              placeholder="Enter key discussion points..."
              multiline
              rows={4}
              highlighted={isHighlighted('topics_discussed')}
            />
            <button
              type="button"
              onClick={handleVoiceNoteClick}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 transition hover:text-blue-700"
            >
              <Mic className="h-3.5 w-3.5" aria-hidden="true" />
              Summarize from Voice Note (Requires Consent)
            </button>
          </div>

          <MaterialsSamplesSection
            materials={draft.materials_shared}
            samples={draft.samples_distributed}
            materialsHighlighted={isHighlighted('materials_shared')}
            samplesHighlighted={isHighlighted('samples_distributed')}
            onSearchAddMaterials={() =>
              guideToChat('Shared CardioMax brochure and dosing leaflet')
            }
            onAddSample={() =>
              guideToChat('Distributed 2 CardioMax sample packs')
            }
          />

          <SentimentSelector
            value={draft.sentiment}
            highlighted={isHighlighted('sentiment')}
          />

          <div
            onMouseDown={(event) => {
              event.preventDefault()
              notifyManualFormEditBlocked('Outcomes')
            }}
          >
            <InteractionField
              id="outcomes"
              label="Outcomes"
              value={draft.outcomes ?? ''}
              placeholder="Key outcomes or agreements..."
              multiline
              rows={4}
              highlighted={isHighlighted('outcomes')}
            />
          </div>

          <InteractionField
            id="follow-up-actions"
            label="Follow-up Actions"
            value={draft.follow_up_actions ?? ''}
            placeholder="Next steps or reminders..."
            multiline
            rows={3}
            highlighted={isHighlighted('follow_up_actions')}
          />

          <InteractionField
            id="additional-notes"
            label="Additional Notes"
            value={draft.additional_notes ?? ''}
            placeholder="Any additional notes..."
            multiline
            rows={3}
            highlighted={isHighlighted('additional_notes')}
          />

          {validationErrors.length > 0 ? (
            <div
              className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
              role="alert"
            >
              <p className="font-medium">Validation notes from AI</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {validationErrors.map((error) => (
                  <li key={error}>{error}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {saveError ? (
            <div
              className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              role="alert"
            >
              {saveError}
            </div>
          ) : null}

          {status === 'completed' && lastSavedInteractionId ? (
            <div
              className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
              role="status"
            >
              Interaction saved successfully. Reference ID: {lastSavedInteractionId}
            </div>
          ) : null}
        </div>
      </div>

      <footer className="flex justify-end gap-3 border-t border-slate-200 bg-white px-5 py-3 lg:px-6">
        {status === 'completed' && onStartNew ? (
          <Button type="button" variant="outline" onClick={onStartNew}>
            Start New Interaction
          </Button>
        ) : null}
        <SaveButton onClick={onSave} isSaving={isSaving} disabled={!canSave} />
      </footer>
    </div>
  )
})
