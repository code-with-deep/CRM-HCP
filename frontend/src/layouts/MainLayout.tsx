import type { ReactNode } from 'react'
import { Activity, LogOut } from 'lucide-react'
import { Link } from 'react-router-dom'

import { getCurrentUserId } from '@/services/apiClient'
import { logout } from '@/services/authService'

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

          <nav className="flex items-center gap-4" aria-label="Main navigation">
            <Link
              to="/foundation"
              className="text-sm font-medium text-slate-600 transition hover:text-blue-600"
            >
              System Status
            </Link>
            <div className="h-4 w-px bg-slate-200" aria-hidden="true" />
            <span className="max-w-[120px] truncate text-xs text-slate-400" title={getCurrentUserId()}>
              {getCurrentUserId().slice(0, 8)}…
            </span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 text-sm font-medium text-slate-600 transition hover:text-red-600"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </nav>
        </div>
      </header>

      <main className="min-h-[calc(100vh-4rem)]">{children}</main>
    </div>
  )
}
