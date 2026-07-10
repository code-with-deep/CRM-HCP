import { apiClient } from '@/services/apiClient'
import type { ApiResponse, PaginatedResponse } from '@/types/api.types'
import type {
  HcpHistoryResponse,
  HcpRecord,
  HcpSearchParams,
} from '@/types/hcp.types'

/**
 * HCP API service — prepared for /hcp/search and /hcp/{id}/history integration.
 * Not wired to Redux thunks in this phase.
 */
export class HcpService {
  async searchHcps(
    params: HcpSearchParams,
  ): Promise<PaginatedResponse<HcpRecord>> {
    const response = await apiClient.get<
      ApiResponse<PaginatedResponse<HcpRecord>>
    >('/hcp/search', { params })
    return response.data.data
  }

  async getHcpHistory(hcpId: string): Promise<HcpHistoryResponse> {
    const response = await apiClient.get<ApiResponse<HcpHistoryResponse>>(
      `/hcp/${hcpId}/history`,
    )
    return response.data.data
  }
}

export const hcpService = new HcpService()
