import apiClient from './client'
import type { MarketingAsset, GeneratedImage } from '@/types/marketing'
import type { PaginatedResponse, TaskResponse } from '@/types/api'

export const marketingApi = {
  // Assets
  listAssets: (params?: { candidate_id?: string; store_id?: string; status?: string; limit?: number; offset?: number }) =>
    apiClient.get<PaginatedResponse<MarketingAsset>>('/marketing/v1/assets', { params }),

  getAsset: (id: string) =>
    apiClient.get<MarketingAsset>(`/marketing/v1/assets/${id}`),

  updateAsset: (id: string, data: Partial<MarketingAsset>) =>
    apiClient.patch<MarketingAsset>(`/marketing/v1/assets/${id}`, data),

  approveAsset: (id: string) =>
    apiClient.patch<MarketingAsset>(`/marketing/v1/assets/${id}/approve`, {}),

  deleteAsset: (id: string) =>
    apiClient.delete(`/marketing/v1/assets/${id}`),

  // Generation
  generateAsset: (candidateId: string, storeId?: string) =>
    apiClient.post<{ job_id: string; status: string; candidate_id: string }>(
      '/marketing/v1/generate',
      { candidate_id: candidateId, store_id: storeId ?? null },
    ),

  getGenerationJob: (jobId: string) =>
    apiClient.get<TaskResponse>(`/marketing/v1/generate/jobs/${jobId}`),

  // Images
  listImages: (params?: { candidate_id?: string; store_id?: string; image_type?: string; status?: string; limit?: number }) =>
    apiClient.get<PaginatedResponse<GeneratedImage>>('/images/v1/images', { params }),

  getImage: (id: string) =>
    apiClient.get<GeneratedImage>(`/images/v1/images/${id}`),

  approveImage: (id: string) =>
    apiClient.patch<GeneratedImage>(`/images/v1/images/${id}/approve`, {}),

  deleteImage: (id: string) =>
    apiClient.delete(`/images/v1/images/${id}`),

  generateImages: (candidateId: string, storeId?: string, imageTypes?: string[]) =>
    apiClient.post<{ job_id: string; status: string; candidate_id: string }>(
      '/images/v1/generate',
      { candidate_id: candidateId, store_id: storeId ?? null, image_types: imageTypes ?? null },
    ),

  regenerateImage: (imageId: string) =>
    apiClient.post<{ job_id: string; status: string; image_id: string }>(
      '/images/v1/generate/regenerate',
      { image_id: imageId },
    ),

  getImageJob: (jobId: string) =>
    apiClient.get<TaskResponse>(`/images/v1/generate/jobs/${jobId}`),
}
