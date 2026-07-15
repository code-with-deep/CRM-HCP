import { lazy, Suspense } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
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

const LoginPage = lazy(() =>
  import('@/pages/LoginPage').then((module) => ({
    default: module.LoginPage,
  })),
)

const RegisterPage = lazy(() =>
  import('@/pages/RegisterPage').then((module) => ({
    default: module.RegisterPage,
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
    path: '/login',
    element: (
      <Suspense fallback={<PageLoader />}>
        <LoginPage />
      </Suspense>
    ),
  },
  {
    path: '/register',
    element: (
      <Suspense fallback={<PageLoader />}>
        <RegisterPage />
      </Suspense>
    ),
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout>
          <Suspense fallback={<PageLoader />}>
            <LogInteractionPage />
          </Suspense>
        </MainLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '/foundation',
    element: (
      <ProtectedRoute>
        <MainLayout>
          <Suspense fallback={<PageLoader />}>
            <HomePage />
          </Suspense>
        </MainLayout>
      </ProtectedRoute>
    ),
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])
