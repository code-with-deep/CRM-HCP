import { Save } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface SaveButtonProps {
  onClick: () => void
  isSaving?: boolean
  disabled?: boolean
  className?: string
}

export function SaveButton({
  onClick,
  isSaving = false,
  disabled = false,
  className,
}: SaveButtonProps) {
  return (
    <Button
      type="button"
      onClick={onClick}
      disabled={disabled || isSaving}
      className={cn('min-w-[160px]', className)}
      aria-label="Save interaction"
    >
      <Save className={cn('h-4 w-4', isSaving && 'animate-pulse')} />
      {isSaving ? 'Saving...' : 'Save Interaction'}
    </Button>
  )
}
