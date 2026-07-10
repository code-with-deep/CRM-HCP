import { lazy, Suspense } from 'react'
import { createBrowserRouter } from 'react-router-dom'

import { LoadingSkeleton } from '@/components/common/LoadingSkeleton'
import { MainLayout } from '@/layouts/MainLayout'

const LogInteractionPage = lazy(() =>
  import('@/pages/LogInteractionPage').then((module) => ({
    default: module.LogInteractionPage,
  })),
)

const HomePage = lazy(() =>
  import('@/pages/HomePage').then((module) => ({
    default: module.HomePage,
  })),
)

function PageLoader() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center p-8">
      <LoadingSkeleton lines={4} className="w-full max-w-lg" />
    </div>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <MainLayout>
        <Suspense fallback={<PageLoader />}>
          <LogInteractionPage />
        </Suspense>
      </MainLayout>
    ),
  },
  {
    path: '/foundation',
    element: (
      <MainLayout>
        <Suspense fallback={<PageLoader />}>
          <HomePage />
        </Suspense>
      </MainLayout>
    ),
  },
])
