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
  marketing: {
    all: ['marketing'] as const,
    assets: (filters?: Record<string, unknown>) =>
      [...queryKeys.marketing.all, 'assets', filters] as const,
    asset: (id: string) => [...queryKeys.marketing.all, 'asset', id] as const,
  },
  images: {
    all: ['images'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.images.all, 'list', filters] as const,
  },
  publisher: {
    all: ['publisher'] as const,
    published: (filters?: Record<string, unknown>) =>
      [...queryKeys.publisher.all, 'published', filters] as const,
    detail: (id: string) => [...queryKeys.publisher.all, 'published', id] as const,
    checklist: (candidateId: string, storeId: string) =>
      [...queryKeys.publisher.all, 'checklist', candidateId, storeId] as const,
  },
}
