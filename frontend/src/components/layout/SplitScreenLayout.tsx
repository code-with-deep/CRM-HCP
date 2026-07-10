import type { ReactNode } from 'react'
import { useSelector } from 'react-redux'

import { MobilePanelToggle } from '@/components/layout/MobilePanelToggle'
import type { RootState } from '@/store'
import { cn } from '@/lib/utils'

interface SplitScreenLayoutProps {
  leftPanel: ReactNode
  rightPanel: ReactNode
  className?: string
}

export function SplitScreenLayout({
  leftPanel,
  rightPanel,
  className,
}: SplitScreenLayoutProps) {
  const activePanel = useSelector((state: RootState) => state.ui.activePanel)

  return (
    <div className={cn('flex min-h-[calc(100vh-4rem)] flex-col', className)}>
      <MobilePanelToggle />

      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        <section
          className={cn(
            'flex min-h-0 flex-1 flex-col border-b border-slate-200 bg-white md:w-[62%] md:border-b-0 md:border-r lg:w-[68%]',
            activePanel !== 'form' && 'hidden md:flex',
          )}
          aria-label="HCP Interaction Form"
        >
          {leftPanel}
        </section>

        <aside
          className={cn(
            'flex min-h-[420px] flex-col bg-white md:w-[38%] md:min-h-0 lg:w-[32%]',
            activePanel !== 'chat' && 'hidden md:flex',
          )}
          aria-label="AI Assistant"
        >
          {rightPanel}
        </aside>
      </div>
    </div>
  )
}
