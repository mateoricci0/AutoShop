import apiClient from '@/services/api/client'
import type { ProductCandidate, PublishedProduct } from '@/types/product'
import type { PaginatedResponse } from '@/types/api'

export interface CandidateFilters {
  status?: string
  store_id?: string
  limit?: number
  offset?: number
}

export const productsApi = {
  getCandidates: (filters?: CandidateFilters) =>
    apiClient.get<PaginatedResponse<ProductCandidate>>('/hunter/v1/candidates', {
      params: filters,
    }),

  getCandidate: (id: string) =>
    apiClient.get<ProductCandidate>(`/hunter/v1/candidates/${id}`),

  approveCandidate: (id: string) =>
    apiClient.post(`/hunter/v1/candidates/${id}/approve`),

  rejectCandidate: (id: string, reason: string) =>
    apiClient.post(`/hunter/v1/candidates/${id}/reject`, { reason }),

  getPublished: (storeId?: string) =>
    apiClient.get<PaginatedResponse<PublishedProduct>>('/publisher/v1/products', {
      params: storeId ? { store_id: storeId } : undefined,
    }),
}
