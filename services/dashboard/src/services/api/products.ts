import apiClient from './client'
import type { ProductCandidate, CandidateFilters, PublishedProduct } from '@/types/product'
import type { PaginatedResponse, TaskResponse } from '@/types/api'

export const productsApi = {
  // Candidates
  listCandidates: (filters: CandidateFilters & { limit?: number; offset?: number; sort?: string }) =>
    apiClient.get<PaginatedResponse<ProductCandidate>>('/hunter/candidates', { params: filters }),

  getCandidate: (id: string) =>
    apiClient.get<ProductCandidate>(`/hunter/candidates/${id}`),

  approveCandidate: (id: string, storeId?: string) =>
    apiClient.patch<ProductCandidate>(`/hunter/candidates/${id}/approve`, { store_id: storeId ?? null }),

  rejectCandidate: (id: string, reason: string) =>
    apiClient.patch<ProductCandidate>(`/hunter/candidates/${id}/reject`, { reason }),

  deleteCandidate: (id: string) =>
    apiClient.delete(`/hunter/candidates/${id}`),

  // Jobs
  triggerHunt: (storeId?: string, sources?: string[]) =>
    apiClient.post<{ task_id: string; status: string }>('/hunter/jobs/hunt', {
      store_id: storeId ?? null,
      sources: sources ?? null,
      force: false,
    }),

  getJobStatus: (taskId: string) =>
    apiClient.get<TaskResponse>(`/hunter/jobs/${taskId}`),

  // Compat aliases
  getCandidates: (filters?: CandidateFilters & { limit?: number; offset?: number }) =>
    apiClient.get<PaginatedResponse<ProductCandidate>>('/hunter/candidates', { params: filters }),

  getPublished: (storeId?: string) =>
    apiClient.get<PaginatedResponse<PublishedProduct>>('/publisher/products', {
      params: storeId ? { store_id: storeId } : undefined,
    }),
}
