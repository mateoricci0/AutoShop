'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { publisherApi } from '@/services/api/publisher'
import { queryKeys } from '@/services/query-keys'
import { PUBLISHED_STATUS_COLORS, PUBLISHED_STATUS_LABELS } from '@/types/publisher'
import type { PublishedProduct, PublishedStatus } from '@/types/publisher'
import { formatDate, formatCurrency } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import {
  ExternalLink,
  RefreshCw,
  Archive,
  ChevronRight,
  ShoppingBag,
} from 'lucide-react'
import { cn } from '@/lib/utils'

function StatusBadge({ status }: { status: PublishedStatus }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        PUBLISHED_STATUS_COLORS[status] ?? 'bg-gray-100 text-gray-700',
      )}
    >
      {PUBLISHED_STATUS_LABELS[status] ?? status}
    </span>
  )
}

function ProductRow({ product }: { product: PublishedProduct }) {
  const queryClient = useQueryClient()

  const syncMutation = useMutation({
    mutationFn: () => publisherApi.syncFromShopify(product.id),
    onSuccess: () => {
      toast.success('Sincronizado con Shopify')
      queryClient.invalidateQueries({ queryKey: queryKeys.publisher.all })
    },
    onError: () => toast.error('Error al sincronizar'),
  })

  return (
    <div className="flex items-center gap-4 rounded-lg border bg-card px-4 py-3 hover:bg-accent/30 transition-colors">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/10">
        <ShoppingBag className="h-5 w-5 text-primary" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Link
            href={`/published/${product.id}`}
            className="font-medium text-sm hover:underline truncate"
          >
            {product.title}
          </Link>
          <StatusBadge status={product.status} />
        </div>
        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
          <span>{formatCurrency(parseFloat(product.price))}</span>
          {product.shopify_handle && (
            <span className="truncate max-w-[200px]">/{product.shopify_handle}</span>
          )}
          <span>Publicado {product.published_at ? formatDate(product.published_at) : '—'}</span>
          {product.last_synced_at && (
            <span>Sync {formatDate(product.last_synced_at)}</span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {product.shopify_product_id && (
          <a
            href={`https://admin.shopify.com/products/${product.shopify_product_id}`}
            target="_blank"
            rel="noopener noreferrer"
            title="Ver en Shopify"
          >
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ExternalLink className="h-4 w-4" />
            </Button>
          </a>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          title="Sincronizar desde Shopify"
        >
          <RefreshCw className={cn('h-4 w-4', syncMutation.isPending && 'animate-spin')} />
        </Button>
        <Link href={`/published/${product.id}`}>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <ChevronRight className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </div>
  )
}

export default function PublishedClient() {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.publisher.published(),
    queryFn: async () => {
      const res = await publisherApi.listPublished({ limit: 100 })
      return res.data
    },
    staleTime: 30_000,
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <p className="text-sm text-muted-foreground">
        Error al cargar productos publicados.
      </p>
    )
  }

  const items = data?.items ?? []

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
        <ShoppingBag className="h-12 w-12 text-muted-foreground/30" />
        <p className="text-sm font-medium">No hay productos publicados</p>
        <p className="text-xs text-muted-foreground max-w-xs">
          Aprueba un candidato, genera su copy e imágenes, y luego usa el botón
          "Publicar en Shopify" en el detalle del producto.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">{data?.total ?? items.length} productos</p>
      {items.map((p) => (
        <ProductRow key={p.id} product={p} />
      ))}
    </div>
  )
}
