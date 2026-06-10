export const queryKeys = {
  stores: {
    all: ['stores'] as const,
    list: () => [...queryKeys.stores.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.stores.all, id] as const,
  },
  products: {
    all: ['products'] as const,
    candidates: (filters?: Record<string, unknown>) =>
      [...queryKeys.products.all, 'candidates', filters] as const,
    published: (storeId?: string) =>
      [...queryKeys.products.all, 'published', storeId] as const,
  },
  analytics: {
    all: ['analytics'] as const,
    summary: (storeId: string, range: string) =>
      [...queryKeys.analytics.all, 'summary', storeId, range] as const,
    timeSeries: (storeId: string, metric: string, range: string) =>
      [...queryKeys.analytics.all, 'timeseries', storeId, metric, range] as const,
    products: (storeId: string, range: string) =>
      [...queryKeys.analytics.all, 'products', storeId, range] as const,
  },
  agents: {
    all: ['agents'] as const,
    list: () => [...queryKeys.agents.all, 'list'] as const,
  },
  notifications: {
    all: ['notifications'] as const,
    list: () => [...queryKeys.notifications.all, 'list'] as const,
    unread: () => [...queryKeys.notifications.all, 'unread'] as const,
  },
}
