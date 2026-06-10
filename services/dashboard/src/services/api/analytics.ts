import apiClient from '@/services/api/client'
import type { AnalyticsSummary, ProductAnalytics, TimeSeriesPoint } from '@/types/analytics'

export const analyticsApi = {
  getSummary: (storeId: string, range: string) =>
    apiClient.get<AnalyticsSummary>('/analytics/v1/summary', {
      params: { store_id: storeId, range },
    }),

  getProductAnalytics: (storeId: string, range: string) =>
    apiClient.get<ProductAnalytics[]>('/analytics/v1/products', {
      params: { store_id: storeId, range },
    }),

  getTimeSeries: (storeId: string, metric: string, range: string) =>
    apiClient.get<TimeSeriesPoint[]>('/analytics/v1/timeseries', {
      params: { store_id: storeId, metric, range },
    }),
}
