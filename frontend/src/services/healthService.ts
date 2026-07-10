import { apiClient } from '@/services/apiClient'
import type { ApiResponse, ApplicationInfo, HealthCheck } from '@/types/api.types'

export const healthService = {
  async getApplicationInfo(): Promise<ApplicationInfo> {
    const response = await apiClient.get<ApiResponse<ApplicationInfo>>('/')
    return response.data.data
  },

  async getHealthCheck(): Promise<HealthCheck> {
    const response = await apiClient.get<ApiResponse<HealthCheck>>('/health')
    return response.data.data
  },
}
