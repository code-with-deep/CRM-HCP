import { cn } from '@/lib/utils'

interface SectionHeaderProps {
  title: string
  description?: string
  className?: string
}

export function SectionHeader({
  title,
  description,
  className,
}: SectionHeaderProps) {
  return (
    <div className={cn('space-y-1', className)}>
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      {description ? (
        <p className="text-xs text-slate-500">{description}</p>
      ) : null}
    </div>
  )
}
