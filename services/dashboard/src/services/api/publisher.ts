import apiClient from './client'
import type {
  PublishedProduct,
  PublishedProductDetail,
  ChecklistResult,
  PublishJobResult,
} from '@/types/publisher'
import type { PaginatedResponse } from '@/types/api'

export interface PublishRequest {
  candidate_id: string
  store_id: string
  price: number
  compare_at_price?: number | null
  vendor?: string | null
  product_type?: string | null
  publish_status?: string
}

export const publisherApi = {
  // Pre-publish checklist
  getChecklist: (candidateId: string, storeId: string) =>
    apiClient.get<ChecklistResult>('/publisher/v1/publish/checklist', {
      params: { candidate_id: candidateId, store_id: storeId },
    }),

  // Trigger publish job
  publish: (data: PublishRequest) =>
    apiClient.post<{ job_id: string; status: string; candidate_id: string; store_id: string }>(
      '/publisher/v1/publish',
      data,
    ),

  // Poll job status
  getJob: (jobId: string) =>
    apiClient.get<PublishJobResult>(`/publisher/v1/publish/jobs/${jobId}`),

  // Published products list
  listPublished: (params?: { store_id?: string; status?: string; limit?: number; offset?: number }) =>
    apiClient.get<PaginatedResponse<PublishedProduct>>('/publisher/v1/published', { params }),

  // Single published product
  getPublished: (id: string) =>
    apiClient.get<PublishedProductDetail>(`/publisher/v1/published/${id}`),

  // Sync from Shopify
  syncFromShopify: (id: string) =>
    apiClient.post<{ status: string; shopify_status: string }>(
      `/publisher/v1/published/${id}/sync`,
      {},
    ),

  // Archive
  archivePublished: (id: string, reason?: string) =>
    apiClient.patch(`/publisher/v1/published/${id}/archive`, { reason }),
}
