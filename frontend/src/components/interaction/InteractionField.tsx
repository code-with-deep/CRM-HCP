import type { KeyboardEvent, MouseEvent, ReactNode } from 'react'
import { motion } from 'framer-motion'
import { CalendarDays, ChevronDown, Clock3, Search } from 'lucide-react'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { notifyManualFormEditBlocked } from '@/utils/manualEditGuard'
import { cn } from '@/lib/utils'

const fieldShell =
  'flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 shadow-none placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500'

function blockManualEdit(
  event: MouseEvent | KeyboardEvent,
  fieldLabel: string,
) {
  event.preventDefault()
  event.stopPropagation()
  notifyManualFormEditBlocked(fieldLabel)
}

interface InteractionFieldProps {
  id: string
  label: string
  value: string
  placeholder?: string
  highlighted?: boolean
  multiline?: boolean
  icon?: ReactNode
  iconRight?: ReactNode
  className?: string
  rows?: number
}

export function InteractionField({
  id,
  label,
  value,
  placeholder = '—',
  highlighted = false,
  multiline = false,
  icon,
  iconRight,
  className,
  rows = 3,
}: InteractionFieldProps) {
  const displayValue = value || ''

  return (
    <motion.div
      layout
      className={cn('space-y-1.5', className)}
      animate={
        highlighted
          ? {
              boxShadow: '0 0 0 2px rgb(37 99 235 / 0.2)',
              backgroundColor: 'rgb(239 246 255 / 0.7)',
            }
          : { boxShadow: '0 0 0 0px transparent', backgroundColor: 'transparent' }
      }
      transition={{ duration: 0.35, ease: 'easeOut' }}
      style={{ borderRadius: '0.5rem', padding: highlighted ? '0.4rem' : '0' }}
    >
      <Label htmlFor={id} className="text-sm font-semibold text-slate-800">
        {label}
      </Label>
      <div
        className="relative"
        onMouseDown={(event) => blockManualEdit(event, label)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            blockManualEdit(event, label)
          }
        }}
      >
        {icon ? (
          <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
            {icon}
          </div>
        ) : null}
        {iconRight ? (
          <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
            {iconRight}
          </div>
        ) : null}
        {multiline ? (
          <textarea
            id={id}
            readOnly
            tabIndex={0}
            aria-readonly="true"
            value={displayValue}
            placeholder={placeholder}
            rows={rows}
            onFocus={() => notifyManualFormEditBlocked(label)}
            className={cn(
              'min-h-[88px] w-full cursor-pointer resize-none rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400',
              icon && 'pl-10',
              iconRight && 'pr-10',
            )}
          />
        ) : (
          <Input
            id={id}
            readOnly
            tabIndex={0}
            aria-readonly="true"
            value={displayValue}
            placeholder={placeholder}
            onFocus={() => notifyManualFormEditBlocked(label)}
            className={cn(
              fieldShell,
              'cursor-pointer',
              icon && 'pl-10',
              iconRight && 'pr-10',
            )}
          />
        )}
      </div>
    </motion.div>
  )
}

interface HcpNameFieldProps {
  value: string
  highlighted?: boolean
}

export function HcpNameField({ value, highlighted }: HcpNameFieldProps) {
  return (
    <InteractionField
      id="hcp-name"
      label="HCP Name"
      value={value}
      placeholder="Search or select HCP..."
      highlighted={highlighted}
      icon={<Search className="h-4 w-4" aria-hidden="true" />}
    />
  )
}

interface InteractionTypeFieldProps {
  value: string
  highlighted?: boolean
}

export function InteractionTypeField({
  value,
  highlighted,
}: InteractionTypeFieldProps) {
  return (
    <InteractionField
      id="interaction-type"
      label="Interaction Type"
      value={value}
      placeholder="Meeting"
      highlighted={highlighted}
      iconRight={<ChevronDown className="h-4 w-4" aria-hidden="true" />}
    />
  )
}

interface DateFieldProps {
  value: string
  highlighted?: boolean
  disabled?: boolean
  onChange?: (value: string) => void
}

export function DateField({
  value,
  highlighted = false,
}: DateFieldProps) {
  return (
    <motion.div
      layout
      className="space-y-1.5"
      animate={
        highlighted
          ? {
              boxShadow: '0 0 0 2px rgb(37 99 235 / 0.2)',
              backgroundColor: 'rgb(239 246 255 / 0.7)',
            }
          : { boxShadow: '0 0 0 0px transparent', backgroundColor: 'transparent' }
      }
      transition={{ duration: 0.35, ease: 'easeOut' }}
      style={{ borderRadius: '0.5rem', padding: highlighted ? '0.4rem' : '0' }}
    >
      <Label htmlFor="interaction-date" className="text-sm font-semibold text-slate-800">
        Date
      </Label>
      <div
        className="relative"
        onMouseDown={(event) => blockManualEdit(event, 'Date')}
      >
        <Input
          id="interaction-date"
          type="date"
          readOnly
          tabIndex={0}
          aria-readonly="true"
          value={value || ''}
          onFocus={() => notifyManualFormEditBlocked('Date')}
          className={cn(fieldShell, 'cursor-pointer pr-10')}
          aria-label="Date"
        />
        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
          <CalendarDays className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>
    </motion.div>
  )
}

interface TimeFieldProps {
  value: string
  highlighted?: boolean
  disabled?: boolean
  onChange?: (value: string) => void
}

function toTimeInputValue(value: string): string {
  if (!value) return ''
  const trimmed = value.trim()
  if (/^\d{2}:\d{2}$/.test(trimmed)) return trimmed
  if (/^\d{2}:\d{2}:\d{2}$/.test(trimmed)) return trimmed.slice(0, 5)

  const match = trimmed.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)?$/i)
  if (!match) return ''

  let hours = Number(match[1])
  const minutes = match[2]
  const meridiem = match[3]?.toUpperCase()
  if (meridiem === 'PM' && hours < 12) hours += 12
  if (meridiem === 'AM' && hours === 12) hours = 0
  return `${String(hours).padStart(2, '0')}:${minutes}`
}

export function TimeField({
  value,
  highlighted = false,
}: TimeFieldProps) {
  return (
    <motion.div
      layout
      className="space-y-1.5"
      animate={
        highlighted
          ? {
              boxShadow: '0 0 0 2px rgb(37 99 235 / 0.2)',
              backgroundColor: 'rgb(239 246 255 / 0.7)',
            }
          : { boxShadow: '0 0 0 0px transparent', backgroundColor: 'transparent' }
      }
      transition={{ duration: 0.35, ease: 'easeOut' }}
      style={{ borderRadius: '0.5rem', padding: highlighted ? '0.4rem' : '0' }}
    >
      <Label htmlFor="interaction-time" className="text-sm font-semibold text-slate-800">
        Time
      </Label>
      <div
        className="relative"
        onMouseDown={(event) => blockManualEdit(event, 'Time')}
      >
        <Input
          id="interaction-time"
          type="time"
          readOnly
          tabIndex={0}
          aria-readonly="true"
          value={toTimeInputValue(value)}
          onFocus={() => notifyManualFormEditBlocked('Time')}
          className={cn(fieldShell, 'cursor-pointer pr-10')}
          aria-label="Time"
        />
        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
          <Clock3 className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>
    </motion.div>
  )
}

interface TagListFieldProps {
  id: string
  label: string
  items: string[]
  highlighted?: boolean
  placeholder?: string
}

export function TagListField({
  id,
  label,
  items,
  highlighted,
  placeholder = '—',
}: TagListFieldProps) {
  return (
    <motion.div
      layout
      className="space-y-1.5"
      animate={
        highlighted
          ? {
              boxShadow: '0 0 0 2px rgb(37 99 235 / 0.2)',
              backgroundColor: 'rgb(239 246 255 / 0.7)',
            }
          : { boxShadow: '0 0 0 0px transparent', backgroundColor: 'transparent' }
      }
      transition={{ duration: 0.35, ease: 'easeOut' }}
      style={{ borderRadius: '0.5rem', padding: highlighted ? '0.4rem' : '0' }}
      onMouseDown={(event) => blockManualEdit(event, label)}
    >
      <Label htmlFor={id} className="text-sm font-semibold text-slate-800">
        {label}
      </Label>
      <div
        id={id}
        role="button"
        tabIndex={0}
        aria-readonly="true"
        onFocus={() => notifyManualFormEditBlocked(label)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            blockManualEdit(event, label)
          }
        }}
        className="min-h-10 cursor-pointer rounded-md border border-slate-300 bg-white px-3 py-2"
      >
        {items.length > 0 ? (
          <ul className="flex flex-wrap gap-2" role="list">
            {items.map((item, index) => (
              <li
                key={`${item}-${index}`}
                className="rounded-full bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200"
              >
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <span className="text-sm text-slate-400">{placeholder}</span>
        )}
      </div>
    </motion.div>
  )
}

interface MaterialsSamplesSectionProps {
  materials: string[]
  samples: string[]
  materialsHighlighted?: boolean
  samplesHighlighted?: boolean
  onSearchAddMaterials?: () => void
  onAddSample?: () => void
}

export function MaterialsSamplesSection({
  materials,
  samples,
  materialsHighlighted,
  samplesHighlighted,
  onSearchAddMaterials,
  onAddSample,
}: MaterialsSamplesSectionProps) {
  return (
    <div className="space-y-4 border-t border-slate-200 pt-5">
      <h3 className="text-sm font-bold text-slate-800">
        Materials Shared / Samples Distributed
      </h3>

      <motion.div
        layout
        className="space-y-2"
        animate={
          materialsHighlighted
            ? { backgroundColor: 'rgb(239 246 255 / 0.7)' }
            : { backgroundColor: 'transparent' }
        }
        style={{ borderRadius: '0.5rem', padding: materialsHighlighted ? '0.4rem' : '0' }}
      >
        <div className="flex items-start justify-between gap-3">
          <div
            className="min-w-0 flex-1 cursor-pointer"
            onMouseDown={(event) => blockManualEdit(event, 'Materials Shared')}
          >
            <p className="text-sm font-semibold text-slate-800">Materials Shared</p>
            {materials.length > 0 ? (
              <ul className="mt-1 space-y-0.5 text-sm text-slate-600">
                {materials.map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-1 text-sm text-slate-400">No materials added.</p>
            )}
          </div>
          <button
            type="button"
            onClick={onSearchAddMaterials}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-violet-300 px-2.5 py-1.5 text-xs font-medium text-violet-700 transition hover:bg-violet-50"
          >
            <Search className="h-3.5 w-3.5" aria-hidden="true" />
            Search/Add
          </button>
        </div>
      </motion.div>

      <motion.div
        layout
        className="space-y-2"
        animate={
          samplesHighlighted
            ? { backgroundColor: 'rgb(239 246 255 / 0.7)' }
            : { backgroundColor: 'transparent' }
        }
        style={{ borderRadius: '0.5rem', padding: samplesHighlighted ? '0.4rem' : '0' }}
      >
        <div className="flex items-start justify-between gap-3">
          <div
            className="min-w-0 flex-1 cursor-pointer"
            onMouseDown={(event) => blockManualEdit(event, 'Samples Distributed')}
          >
            <p className="text-sm font-semibold text-slate-800">Samples Distributed</p>
            {samples.length > 0 ? (
              <ul className="mt-1 space-y-0.5 text-sm text-slate-600">
                {samples.map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-1 text-sm text-slate-400">No samples added.</p>
            )}
          </div>
          <button
            type="button"
            onClick={onAddSample}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-violet-300 px-2.5 py-1.5 text-xs font-medium text-violet-700 transition hover:bg-violet-50"
          >
            <span aria-hidden="true">+</span>
            Add Sample
          </button>
        </div>
      </motion.div>
    </div>
  )
}
