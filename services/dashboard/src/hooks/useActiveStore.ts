'use client'

import { useQuery } from '@tanstack/react-query'
import { useStoreSelectorStore } from '@/stores/store-selector.store'
import { authApi } from '@/services/api/auth'
import { queryKeys } from '@/services/query-keys'
import type { Store } from '@/types/store'

export function useActiveStore() {
  const { activeStoreId, setActiveStoreId } = useStoreSelectorStore()

  const { data: stores = [], isLoading } = useQuery<Store[]>({
    queryKey: queryKeys.stores.list(),
    queryFn: async () => {
      const res = await authApi.getStores()
      return res.data
    },
    staleTime: 60_000,
  })

  const activeStore = stores.find((s) => s.id === activeStoreId) ?? stores[0] ?? null

  // Auto-select first store if none selected
  if (!activeStoreId && stores.length > 0 && stores[0]) {
    setActiveStoreId(stores[0].id)
  }

  return {
    activeStore,
    activeStoreId: activeStore?.id ?? null,
    stores,
    isLoading,
    setActiveStoreId,
  }
}
