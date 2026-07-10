import { MessageSquare, PanelLeft } from 'lucide-react'
import { useDispatch, useSelector } from 'react-redux'

import { Button } from '@/components/ui/button'
import type { AppDispatch, RootState } from '@/store'
import { setActivePanel } from '@/store/slices/uiSlice'
import { cn } from '@/lib/utils'

export function MobilePanelToggle({ className }: { className?: string }) {
  const dispatch = useDispatch<AppDispatch>()
  const activePanel = useSelector((state: RootState) => state.ui.activePanel)

  return (
    <div
      className={cn(
        'flex gap-2 border-b border-slate-200 bg-white px-4 py-2 md:hidden',
        className,
      )}
      role="tablist"
      aria-label="Panel navigation"
    >
      <Button
        type="button"
        variant={activePanel === 'form' ? 'default' : 'outline'}
        size="sm"
        className="flex-1"
        onClick={() => dispatch(setActivePanel('form'))}
        role="tab"
        aria-selected={activePanel === 'form'}
      >
        <PanelLeft className="h-4 w-4" />
        Interaction Form
      </Button>
      <Button
        type="button"
        variant={activePanel === 'chat' ? 'default' : 'outline'}
        size="sm"
        className="flex-1"
        onClick={() => dispatch(setActivePanel('chat'))}
        role="tab"
        aria-selected={activePanel === 'chat'}
      >
        <MessageSquare className="h-4 w-4" />
        AI Assistant
      </Button>
    </div>
  )
}
