import apiClient from '@/services/api/client'
import type { Store, StoreCreate } from '@/types/store'

export const authApi = {
  login: (password: string) =>
    apiClient.post('/auth/login', { password }),

  logout: () =>
    apiClient.post('/auth/logout'),

  getStores: () =>
    apiClient.get<Store[]>('/auth/stores'),

  createStore: (data: StoreCreate) =>
    apiClient.post<Store>('/auth/stores', data),

  updateStore: (id: string, data: Partial<Store>) =>
    apiClient.put<Store>(`/auth/stores/${id}`, data),

  deleteStore: (id: string) =>
    apiClient.delete(`/auth/stores/${id}`),

  testConnection: (id: string) =>
    apiClient.post(`/auth/stores/${id}/test-connection`),
}
