import { useCallback, useEffect } from 'react'

import { healthService } from '@/services/healthService'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import {
  setApplicationInfo,
  setError,
  setHealthCheck,
  setLoading,
} from '@/store/slices/appSlice'

/**
 * Load application metadata and infrastructure health status.
 */
export function useAppBootstrap() {
  const dispatch = useAppDispatch()
  const { applicationInfo, healthCheck, isLoading, error } = useAppSelector(
    (state) => state.app,
  )

  const refreshStatus = useCallback(async () => {
    dispatch(setLoading(true))

    try {
      const [application, health] = await Promise.all([
        healthService.getApplicationInfo(),
        healthService.getHealthCheck(),
      ])

      dispatch(setApplicationInfo(application))
      dispatch(setHealthCheck(health))
    } catch (bootstrapError) {
      const message =
        bootstrapError instanceof Error
          ? bootstrapError.message
          : 'Failed to load application status.'

      dispatch(setError(message))
    } finally {
      dispatch(setLoading(false))
    }
  }, [dispatch])

  useEffect(() => {
    void refreshStatus()
  }, [refreshStatus])

  return {
    applicationInfo,
    healthCheck,
    isLoading,
    error,
    refreshStatus,
  }
}
