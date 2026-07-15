import { Navigate, useLocation } from 'react-router-dom'

import { getToken } from '@/services/apiClient'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * Wraps any route that requires authentication.
 * If no JWT token is found in localStorage, the user is redirected to /login.
 * The original destination is saved in location state so the user is sent
 * back after a successful login.
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation()
  const token = getToken()

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
