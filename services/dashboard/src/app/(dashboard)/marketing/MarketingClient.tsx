'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { marketingApi } from '@/services/api/marketing'
import { queryKeys } from '@/services/query-keys'
import { ASSET_STATUS_COLORS } from '@/types/marketing'
import { formatDate } from '@/lib/format'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
  Megaphone,
  ChevronRight,
  Cpu,
  DollarSign,
  FileText,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const STATUS_LABELS: Record<string, string> = {
  draft: 'Borrador',
  generating: 'Generando...',
  approved: 'Aprobado',
  active: 'Activo',
  archived: 'Archivado',
}

export default function MarketingClient() {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.marketing.assets(),
    queryFn: async () => {
      const res = await marketingApi.listAssets({ limit: 50 })
      return res.data
    },
    staleTime: 30_000,
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  const items = data?.items ?? []

  if (items.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16 text-center">
          <Megaphone className="mb-3 h-10 w-10 text-muted-foreground" />
          <p className="text-sm font-medium">Sin assets de marketing todavía</p>
          <p className="mt-1 max-w-sm text-xs text-muted-foreground">
            Aprueba un producto desde la página de Productos para generar automáticamente copy,
            SEO y anuncios con IA.
          </p>
          <Link href="/products">
            <Button variant="outline" size="sm" className="mt-4">
              Ver candidatos
            </Button>
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      {items.map((asset) => (
        <Link key={asset.id} href={`/marketing/${asset.id}`}>
          <Card className="hover:border-primary/40 transition-colors cursor-pointer">
            <CardContent className="flex items-center gap-4 py-4">
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-sm truncate">
                    {asset.brand_name ?? 'Sin nombre de marca'}
                  </span>
                  <span
                    className={cn(
                      'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                      ASSET_STATUS_COLORS[asset.status] ?? 'bg-gray-100 text-gray-700',
                    )}
                  >
                    {STATUS_LABELS[asset.status] ?? asset.status}
                  </span>
                </div>
                {asset.tagline && (
                  <p className="text-xs text-muted-foreground italic">"{asset.tagline}"</p>
                )}
                {asset.short_description && (
                  <p className="text-xs text-muted-foreground line-clamp-1">
                    {asset.short_description}
                  </p>
                )}
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  {asset.ai_model && (
                    <span className="flex items-center gap-1">
                      <Cpu className="h-3 w-3" />
                      {asset.ai_model}
                    </span>
                  )}
                  {asset.tokens_used && (
                    <span>{asset.tokens_used.toLocaleString()} tokens</span>
                  )}
                  {asset.generation_cost != null && (
                    <span className="flex items-center gap-1">
                      <DollarSign className="h-3 w-3" />
                      ${Number(asset.generation_cost).toFixed(4)}
                    </span>
                  )}
                  <span>{formatDate(asset.created_at)}</span>
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  )
}
