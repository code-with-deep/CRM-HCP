import { Activity, Database, RefreshCw, Server } from 'lucide-react'

import { useAppBootstrap } from '@/hooks/useAppBootstrap'
import { cn } from '@/lib/utils'

function StatusBadge({
  label,
  value,
  variant = 'default',
}: {
  label: string
  value: string
  variant?: 'default' | 'success' | 'warning' | 'error'
}) {
  const variantClasses = {
    default: 'bg-slate-100 text-slate-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-amber-100 text-amber-700',
    error: 'bg-red-100 text-red-700',
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p
        className={cn(
          'mt-2 inline-flex rounded-full px-3 py-1 text-sm font-semibold capitalize',
          variantClasses[variant],
        )}
      >
        {value}
      </p>
    </div>
  )
}

/**
 * Foundation landing page used to verify project scaffolding.
 */
export function HomePage() {
  const { applicationInfo, healthCheck, isLoading, error, refreshStatus } =
    useAppBootstrap()

  return (
    <section className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">
              Project Foundation
            </h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Enterprise-ready scaffolding for the AI-First Healthcare CRM. This
              page verifies frontend, backend, and database connectivity.
            </p>
            <a
              href="/"
              className="mt-3 inline-flex text-sm font-medium text-blue-600 hover:text-blue-700"
            >
              ← Back to HCP Interaction Logging
            </a>
          </div>

          <button
            type="button"
            onClick={() => void refreshStatus()}
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatusBadge
          label="Application"
          value={applicationInfo?.name ?? (isLoading ? 'loading' : 'unavailable')}
        />
        <StatusBadge
          label="Version"
          value={applicationInfo?.version ?? (isLoading ? 'loading' : 'unavailable')}
        />
        <StatusBadge
          label="API Status"
          value={healthCheck?.status ?? (isLoading ? 'loading' : 'unavailable')}
          variant={
            healthCheck?.status === 'healthy'
              ? 'success'
              : healthCheck?.status === 'degraded'
                ? 'warning'
                : 'default'
          }
        />
        <StatusBadge
          label="Database"
          value={healthCheck?.database ?? (isLoading ? 'loading' : 'unavailable')}
          variant={
            healthCheck?.database === 'connected'
              ? 'success'
              : healthCheck?.database === 'disconnected'
                ? 'error'
                : 'default'
          }
        />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <Server className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold text-slate-900">Frontend</h3>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            React 19, Vite, TypeScript, TailwindCSS, Redux Toolkit, and React
            Router are configured with path aliases and shared theme styles.
          </p>
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold text-slate-900">Backend</h3>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            FastAPI is running with structured logging, global exception
            handling, dependency injection, and health endpoints.
          </p>
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-blue-600" />
            <h3 className="font-semibold text-slate-900">Database</h3>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            PostgreSQL, SQLAlchemy 2.x async engine, and Alembic migration
            tooling are configured and ready for model creation.
          </p>
        </article>
      </div>
    </section>
  )
}
