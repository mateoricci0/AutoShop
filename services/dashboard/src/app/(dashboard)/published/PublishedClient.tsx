'use client'

import { useQuery } from '@tanstack/react-query'
import { ExternalLink, ShoppingBag } from 'lucide-react'
import { queryKeys } from '@/services/query-keys'
import { productsApi } from '@/services/api/products'
import { useActiveStore } from '@/hooks/useActiveStore'
import { formatCurrency, formatDate } from '@/lib/format'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

const statusVariant: Record<string, 'default' | 'secondary' | 'outline'> = {
  active: 'default',
  draft: 'secondary',
  archived: 'outline',
}

const statusLabel: Record<string, string> = {
  active: 'Activo',
  draft: 'Borrador',
  archived: 'Archivado',
}

export function PublishedClient() {
  const { activeStoreId } = useActiveStore()

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.products.published(activeStoreId ?? undefined),
    queryFn: async () => {
      const res = await productsApi.getPublished(activeStoreId ?? undefined)
      return res.data
    },
    staleTime: 30_000,
  })

  const products = data?.items ?? []

  if (isLoading) {
    return (
      <Card className="p-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </Card>
    )
  }

  if (products.length === 0) {
    return (
      <Card className="flex flex-col items-center justify-center py-16 text-center">
        <ShoppingBag className="mb-3 h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium">No hay productos publicados</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Aprueba candidatos para publicarlos en Shopify
        </p>
      </Card>
    )
  }

  return (
    <Card>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Producto</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Precio</TableHead>
            <TableHead>Inventario</TableHead>
            <TableHead>Publicado</TableHead>
            <TableHead>Shopify</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {products.map((product) => (
            <TableRow key={product.id}>
              <TableCell className="font-medium">
                <span className="line-clamp-1 max-w-[200px]">{product.title}</span>
              </TableCell>
              <TableCell>
                <Badge variant={statusVariant[product.status] ?? 'secondary'} className="text-xs">
                  {statusLabel[product.status] ?? product.status}
                </Badge>
              </TableCell>
              <TableCell className="text-sm">
                <div>
                  <p>{formatCurrency(product.price)}</p>
                  {product.compare_at_price && (
                    <p className="text-xs text-muted-foreground line-through">
                      {formatCurrency(product.compare_at_price)}
                    </p>
                  )}
                </div>
              </TableCell>
              <TableCell className="text-sm">{product.inventory_quantity}</TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {formatDate(product.published_at)}
              </TableCell>
              <TableCell>
                <a
                  href={`https://admin.shopify.com/products/${product.shopify_product_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                >
                  Ver <ExternalLink className="h-3 w-3" />
                </a>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  )
}
