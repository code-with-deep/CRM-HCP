import type { ReactNode } from 'react'
import { Activity } from 'lucide-react'
import { Link } from 'react-router-dom'

interface MainLayoutProps {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 shadow-sm backdrop-blur">
        <div className="flex items-center justify-between gap-4 px-4 py-3 lg:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white shadow-sm">
              <Activity className="h-4 w-4" aria-hidden="true" />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                Healthcare CRM
              </p>
              <h1 className="text-base font-semibold text-slate-900">
                HCP Interaction Logging
              </h1>
            </div>
          </div>

          <nav aria-label="Main navigation">
            <Link
              to="/foundation"
              className="text-sm font-medium text-slate-600 transition hover:text-blue-600"
            >
              System Status
            </Link>
          </nav>
        </div>
      </header>

      <main className="min-h-[calc(100vh-4rem)]">{children}</main>
    </div>
  )
}
