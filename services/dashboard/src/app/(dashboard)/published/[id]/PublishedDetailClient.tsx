'use client'

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { publisherApi } from '@/services/api/publisher'
import { queryKeys } from '@/services/query-keys'
import { PUBLISHED_STATUS_COLORS, PUBLISHED_STATUS_LABELS } from '@/types/publisher'
import type { PublishedStatus } from '@/types/publisher'
import { formatDate, formatCurrency } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import {
  ArrowLeft,
  ExternalLink,
  RefreshCw,
  Archive,
  Tag,
  DollarSign,
  ImageIcon,
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

export default function PublishedDetailClient({ id }: { id: string }) {
  const router = useRouter()
  const queryClient = useQueryClient()

  const { data: product, isLoading, error } = useQuery({
    queryKey: queryKeys.publisher.detail(id),
    queryFn: async () => {
      const res = await publisherApi.getPublished(id)
      return res.data
    },
    staleTime: 30_000,
  })

  const syncMutation = useMutation({
    mutationFn: () => publisherApi.syncFromShopify(id),
    onSuccess: () => {
      toast.success('Sincronizado con Shopify')
      queryClient.invalidateQueries({ queryKey: queryKeys.publisher.all })
    },
    onError: () => toast.error('Error al sincronizar'),
  })

  const archiveMutation = useMutation({
    mutationFn: () => publisherApi.archivePublished(id),
    onSuccess: () => {
      toast.success('Producto archivado')
      queryClient.invalidateQueries({ queryKey: queryKeys.publisher.all })
      router.push('/published')
    },
    onError: () => toast.error('Error al archivar'),
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <p className="text-sm text-muted-foreground">No se encontró el producto publicado.</p>
        <Button variant="outline" onClick={() => router.push('/published')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <Button variant="ghost" size="sm" onClick={() => router.push('/published')} className="-ml-2">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Volver
      </Button>

      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">{product.title}</h1>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={product.status} />
            {product.shopify_handle && (
              <span className="text-xs text-muted-foreground">/{product.shopify_handle}</span>
            )}
            <span className="text-xs text-muted-foreground">
              Publicado {product.published_at ? formatDate(product.published_at) : '—'}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 shrink-0">
          {product.shopify_product_id && (
            <a
              href={`https://admin.shopify.com/products/${product.shopify_product_id}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="outline" size="sm">
                <ExternalLink className="mr-2 h-4 w-4" />
                Ver en Shopify
              </Button>
            </a>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RefreshCw className={cn('mr-2 h-4 w-4', syncMutation.isPending && 'animate-spin')} />
            Sincronizar
          </Button>
          {product.status !== 'archived' && (
            <Button
              variant="outline"
              size="sm"
              className="text-destructive border-destructive hover:bg-destructive hover:text-destructive-foreground"
              onClick={() => archiveMutation.mutate()}
              disabled={archiveMutation.isPending}
            >
              <Archive className="mr-2 h-4 w-4" />
              Archivar
            </Button>
          )}
        </div>
      </div>

      {/* Images */}
      {product.images && product.images.length > 0 && (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {product.images.map((img, i) => (
            <img
              key={i}
              src={img.src}
              alt={`${product.title} ${i + 1}`}
              className="h-36 w-36 shrink-0 rounded-lg object-cover border"
            />
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pricing */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <DollarSign className="h-4 w-4" />
              Precios
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Precio venta</p>
                <p className="text-xl font-bold">{formatCurrency(parseFloat(product.price))}</p>
              </div>
              {product.compare_at_price && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Precio comparación</p>
                  <p className="text-xl font-bold line-through text-muted-foreground">
                    {formatCurrency(parseFloat(product.compare_at_price))}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* SEO */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">SEO</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {product.seo_title && (
              <div>
                <p className="text-xs text-muted-foreground mb-0.5">Meta título</p>
                <p className="font-medium">{product.seo_title}</p>
              </div>
            )}
            {product.seo_description && (
              <div>
                <p className="text-xs text-muted-foreground mb-0.5">Meta descripción</p>
                <p className="text-muted-foreground">{product.seo_description}</p>
              </div>
            )}
            {!product.seo_title && !product.seo_description && (
              <p className="text-muted-foreground text-xs">Sin datos SEO</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Description */}
      {product.description_html && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Descripción</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="prose prose-sm max-w-none text-muted-foreground"
              dangerouslySetInnerHTML={{ __html: product.description_html }}
            />
          </CardContent>
        </Card>
      )}

      {/* Tags */}
      {product.tags && product.tags.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Tag className="h-4 w-4" />
            Etiquetas
          </div>
          <div className="flex flex-wrap gap-2">
            {product.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Shopify IDs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Shopify</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Product ID</span>
            <code className="text-xs">{product.shopify_product_id ?? '—'}</code>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Handle</span>
            <code className="text-xs">{product.shopify_handle ?? '—'}</code>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Última sync</span>
            <span className="text-xs">{product.last_synced_at ? formatDate(product.last_synced_at) : '—'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Colecciones</span>
            <span className="text-xs">{product.shopify_collection_ids.length} asignadas</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
