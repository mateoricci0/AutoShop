export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface TaskResponse {
  task_id: string
  status: 'pending' | 'started' | 'success' | 'failure'
  progress: number
  result: unknown | null
  error: string | null
  created_at: string
  completed_at: string | null
}
