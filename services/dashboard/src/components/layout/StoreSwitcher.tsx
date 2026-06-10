'use client'

import { useState } from 'react'
import { Store, ChevronDown, Plus, Check, Loader2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { authApi } from '@/services/api/auth'
import { queryKeys } from '@/services/query-keys'
import { useStoreSelectorStore } from '@/stores/store-selector.store'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import type { Store as StoreType } from '@/types/store'

interface StoreSwitcherProps {
  onAddStore?: () => void
}

export function StoreSwitcher({ onAddStore }: StoreSwitcherProps) {
  const { activeStoreId, setActiveStoreId } = useStoreSelectorStore()

  const { data: stores = [], isLoading } = useQuery<StoreType[]>({
    queryKey: queryKeys.stores.list(),
    queryFn: async () => {
      const res = await authApi.getStores()
      return res.data
    },
    staleTime: 60_000,
  })

  const activeStore = stores.find((s) => s.id === activeStoreId) ?? stores[0]

  if (isLoading) {
    return (
      <Button variant="outline" size="sm" disabled>
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="ml-2">Cargando...</span>
      </Button>
    )
  }

  if (stores.length === 0) {
    return (
      <Button variant="outline" size="sm" onClick={onAddStore}>
        <Plus className="h-4 w-4" />
        <span className="ml-2">Agregar tienda</span>
      </Button>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="max-w-[200px]">
          <Store className="h-4 w-4 shrink-0" />
          <span className="ml-2 truncate">
            {activeStore?.name ?? 'Seleccionar tienda'}
          </span>
          <ChevronDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        <DropdownMenuLabel>Tiendas Shopify</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {stores.map((store) => (
          <DropdownMenuItem
            key={store.id}
            onClick={() => setActiveStoreId(store.id)}
            className="flex items-center gap-2"
          >
            <Store className="h-4 w-4" />
            <div className="flex-1 truncate">
              <p className="truncate text-sm font-medium">{store.name}</p>
              <p className="truncate text-xs text-muted-foreground">
                {store.shopify_domain}
              </p>
            </div>
            {activeStore?.id === store.id && (
              <Check className="h-4 w-4 shrink-0 text-primary" />
            )}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onAddStore} className="gap-2">
          <Plus className="h-4 w-4" />
          Agregar tienda
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
