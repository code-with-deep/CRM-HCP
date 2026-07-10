export interface ApiResponseMeta {
  request_id?: string | null
  correlation_id?: string | null
  execution_time_ms?: number | null
  selected_tool?: string | null
  conversation_id?: string | null
  page?: number
  page_size?: number
  total_items?: number
}

export interface ApiResponse<T> {
  success: boolean
  message: string
  data: T
  errors: string[]
  meta: ApiResponseMeta
}

export interface ApiErrorResponse {
  success: false
  message: string
  errors: string[]
  detail?: unknown
  meta?: ApiResponseMeta
}

export interface ApplicationInfo {
  name: string
  version: string
  status: string
}

export interface HealthCheck {
  name: string
  version: string
  status: string
  database: string
}

export interface PaginationMeta {
  page: number
  page_size: number
  total_items: number
  total_pages: number
  has_next: boolean
  has_previous: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  meta: PaginationMeta
}
