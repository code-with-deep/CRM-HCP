import { cn } from '@/lib/utils'

interface LoadingSkeletonProps {
  className?: string
  lines?: number
}

export function LoadingSkeleton({ className, lines = 3 }: LoadingSkeletonProps) {
  return (
    <div className={cn('space-y-3', className)} aria-hidden="true">
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="h-10 animate-pulse rounded-lg bg-slate-100"
          style={{ width: `${100 - index * 12}%` }}
        />
      ))}
    </div>
  )
}
