import { cn } from '@/lib/utils'
import type { VariantProps } from 'class-variance-authority'

import { badgeVariants } from '@/components/ui/badge'

interface StatusBadgeProps {
  label: string
  variant?: VariantProps<typeof badgeVariants>['variant']
  className?: string
}

export function StatusBadge({
  label,
  variant = 'secondary',
  className,
}: StatusBadgeProps) {
  return (
    <span
      className={cn(badgeVariants({ variant }), 'capitalize', className)}
      role="status"
      aria-label={label}
    >
      {label}
    </span>
  )
}
