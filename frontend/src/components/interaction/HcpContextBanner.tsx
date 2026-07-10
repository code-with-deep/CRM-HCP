import { Building2, MapPin, Stethoscope } from 'lucide-react'
import { useSelector } from 'react-redux'

import type { RootState } from '@/store'
import { cn } from '@/lib/utils'

interface HcpContextBannerProps {
  className?: string
}

export function HcpContextBanner({ className }: HcpContextBannerProps) {
  const currentHcp = useSelector(
    (state: RootState) => state.interaction.currentHcp,
  )
  const selectedName = useSelector(
    (state: RootState) => state.hcp.selectedHcpName,
  )

  if (!currentHcp && !selectedName) return null

  const name = (currentHcp?.name as string | undefined) ?? selectedName
  const hospital = currentHcp?.hospital as string | undefined
  const city = currentHcp?.city as string | undefined
  const specialization = currentHcp?.specialization as string | undefined

  return (
    <div
      className={cn(
        'rounded-lg border border-blue-100 bg-blue-50/80 px-4 py-3 text-sm text-slate-700',
        className,
      )}
      role="status"
      aria-label="Selected healthcare professional context"
    >
      <p className="font-medium text-slate-900">{name}</p>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
        {specialization ? (
          <span className="inline-flex items-center gap-1">
            <Stethoscope className="h-3.5 w-3.5" aria-hidden="true" />
            {specialization}
          </span>
        ) : null}
        {hospital ? (
          <span className="inline-flex items-center gap-1">
            <Building2 className="h-3.5 w-3.5" aria-hidden="true" />
            {hospital}
          </span>
        ) : null}
        {city ? (
          <span className="inline-flex items-center gap-1">
            <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
            {city}
          </span>
        ) : null}
      </div>
    </div>
  )
}
