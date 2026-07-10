export interface HcpRecord {
  id: string
  name: string
  specialization: string | null
  hospital: string | null
  city: string | null
  state: string | null
  email: string | null
  phone: string | null
  status: string
  previous_interaction_count?: number
}

export interface HcpSearchParams {
  doctor_name?: string
  hospital?: string
  city?: string
  specialization?: string
  page?: number
  page_size?: number
}

export interface HcpHistoryItem {
  interaction_id: string
  interaction_date: string
  status: string
  summary: string | null
  sentiment: string | null
  outcome: string | null
  follow_up: string | null
}

export interface HcpHistoryResponse {
  hcp_id: string
  hcp_name: string
  interactions: HcpHistoryItem[]
}
