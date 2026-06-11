'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { marketingApi } from '@/services/api/marketing'
import { queryKeys } from '@/services/query-keys'
import { IMAGE_TYPE_LABELS, ASSET_STATUS_COLORS } from '@/types/marketing'
import type { GeneratedImage } from '@/types/marketing'
import { formatDate } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import { Separator } from '@/components/ui/separator'
import { toast } from 'sonner'
import {
  ArrowLeft,
  CheckCircle,
  RefreshCw,
  Cpu,
  ImageIcon,
  FileText,
  Search,
  Megaphone,
  Loader2,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const STATUS_LABEL: Record<string, string> = {
  draft: 'Borrador',
  generating: 'Generando...',
  approved: 'Aprobado',
  active: 'Activo',
  archived: 'Archivado',
}

const IMAGE_STATUS_COLORS: Record<string, string> = {
  pending: 'border-gray-200',
  generating: 'border-blue-300 animate-pulse',
  approved: 'border-green-400',
  needs_review: 'border-yellow-400',
  failed: 'border-red-400',
}

function ImageCard({ image, onRegenerate, onApprove }: {
  image: GeneratedImage
  onRegenerate: (id: string) => void
  onApprove: (id: string) => void
}) {
  return (
    <div className={cn('rounded-lg border-2 overflow-hidden', IMAGE_STATUS_COLORS[image.status])}>
      {image.storage_url ? (
        <img
          src={image.storage_url}
          alt={IMAGE_TYPE_LABELS[image.type]}
          className="w-full object-cover aspect-square bg-muted"
        />
      ) : (
        <div className="w-full aspect-square bg-muted flex items-center justify-center">
          {image.status === 'generating' ? (
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          ) : image.status === 'failed' ? (
            <p className="text-xs text-destructive text-center px-2">{image.error_message ?? 'Error'}</p>
          ) : (
            <ImageIcon className="h-8 w-8 text-muted-foreground" />
          )}
        </div>
      )}
      <div className="p-2 space-y-1">
        <p className="text-xs font-medium">{IMAGE_TYPE_LABELS[image.type]}</p>
        {image.clip_score != null && (
          <p className="text-xs text-muted-foreground">CLIP: {Number(image.clip_score).toFixed(2)}</p>
        )}
        {image.generation_time_ms && (
          <p className="text-xs text-muted-foreground">{(image.generation_time_ms / 1000).toFixed(1)}s</p>
        )}
        <div className="flex gap-1 pt-1">
          {image.status !== 'approved' && image.storage_url && (
            <Button size="sm" variant="outline" className="h-6 text-xs px-2 flex-1" onClick={() => onApprove(image.id)}>
              <CheckCircle className="h-3 w-3 mr-1" />
              Aprobar
            </Button>
          )}
          <Button size="sm" variant="outline" className="h-6 text-xs px-2 flex-1" onClick={() => onRegenerate(image.id)}>
            <RefreshCw className="h-3 w-3 mr-1" />
            Regenerar
          </Button>
        </div>
      </div>
    </div>
  )
}

function CopySection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">{title}</h3>
      {children}
    </div>
  )
}

function CopyText({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null
  return (
    <div className="rounded-md border bg-muted/30 p-3 space-y-1">
      <p className="text-xs text-muted-foreground font-medium">{label}</p>
      <p className="text-sm leading-relaxed">{value}</p>
    </div>
  )
}

function CopyList({ label, items }: { label: string; items: string[] | undefined }) {
  if (!items?.length) return null
  return (
    <div className="rounded-md border bg-muted/30 p-3 space-y-1">
      <p className="text-xs text-muted-foreground font-medium">{label}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm flex gap-2">
            <span className="text-muted-foreground">{i + 1}.</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function PlatformSection({ title, data }: { title: string; data: Record<string, string> }) {
  const entries = Object.entries(data).filter(([, v]) => v)
  if (!entries.length) return null
  return (
    <div className="rounded-md border bg-muted/30 p-3 space-y-2">
      <p className="text-xs text-muted-foreground font-medium">{title}</p>
      {entries.map(([key, value]) => (
        <div key={key}>
          <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</p>
          <p className="text-sm">{value}</p>
        </div>
      ))}
    </div>
  )
}

export default function AssetDetailClient({ id }: { id: string }) {
  const router = useRouter()
  const queryClient = useQueryClient()

  const { data: asset, isLoading } = useQuery({
    queryKey: queryKeys.marketing.asset(id),
    queryFn: async () => {
      const res = await marketingApi.getAsset(id)
      return res.data
    },
    staleTime: 30_000,
  })

  const { data: imagesData, refetch: refetchImages } = useQuery({
    queryKey: queryKeys.images.list({ candidate_id: asset?.candidate_id }),
    queryFn: async () => {
      if (!asset?.candidate_id) return { items: [] }
      const res = await marketingApi.listImages({ candidate_id: asset.candidate_id, limit: 20 })
      return res.data
    },
    enabled: !!asset?.candidate_id,
    staleTime: 15_000,
  })

  const approveMutation = useMutation({
    mutationFn: () => marketingApi.approveAsset(id),
    onSuccess: () => {
      toast.success('Asset aprobado')
      queryClient.invalidateQueries({ queryKey: queryKeys.marketing.all })
    },
    onError: () => toast.error('Error al aprobar'),
  })

  const regenerateAllMutation = useMutation({
    mutationFn: async () => {
      if (!asset?.candidate_id) throw new Error('No candidate_id')
      return marketingApi.generateImages(asset.candidate_id, asset.store_id ?? undefined)
    },
    onSuccess: () => {
      toast.success('Regenerando imágenes...')
      setTimeout(() => refetchImages(), 3000)
    },
    onError: () => toast.error('Error al regenerar imágenes'),
  })

  const regenerateImageMutation = useMutation({
    mutationFn: (imageId: string) => marketingApi.regenerateImage(imageId),
    onSuccess: () => {
      toast.success('Regenerando imagen...')
      setTimeout(() => refetchImages(), 3000)
    },
    onError: () => toast.error('Error al regenerar la imagen'),
  })

  const approveImageMutation = useMutation({
    mutationFn: (imageId: string) => marketingApi.approveImage(imageId),
    onSuccess: () => {
      toast.success('Imagen aprobada')
      refetchImages()
    },
    onError: () => toast.error('Error al aprobar la imagen'),
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!asset) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <p className="text-sm text-muted-foreground">Asset no encontrado.</p>
        <Button variant="outline" onClick={() => router.push('/marketing')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver
        </Button>
      </div>
    )
  }

  const images = imagesData?.items ?? []

  return (
    <div className="space-y-6 max-w-5xl">
      <Button variant="ghost" size="sm" onClick={() => router.push('/marketing')} className="-ml-2">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Volver
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">
            {asset.brand_name ?? 'Asset de Marketing'}
          </h1>
          {asset.tagline && (
            <p className="text-muted-foreground italic">"{asset.tagline}"</p>
          )}
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                ASSET_STATUS_COLORS[asset.status] ?? 'bg-gray-100 text-gray-700',
              )}
            >
              {STATUS_LABEL[asset.status] ?? asset.status}
            </span>
            {asset.ai_model && (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Cpu className="h-3 w-3" />
                {asset.ai_model}
              </span>
            )}
            {asset.tokens_used && (
              <span className="text-xs text-muted-foreground">
                {asset.tokens_used.toLocaleString()} tokens
              </span>
            )}
            {asset.generation_cost != null && (
              <span className="text-xs text-muted-foreground">
                ${Number(asset.generation_cost).toFixed(4)} coste
              </span>
            )}
          </div>
        </div>
        {asset.status === 'draft' && (
          <Button
            className="bg-green-600 hover:bg-green-700 text-white"
            onClick={() => approveMutation.mutate()}
            disabled={approveMutation.isPending}
          >
            <CheckCircle className="mr-2 h-4 w-4" />
            Aprobar asset
          </Button>
        )}
      </div>

      <Tabs defaultValue="copy">
        <TabsList>
          <TabsTrigger value="copy" className="flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            Copy
          </TabsTrigger>
          <TabsTrigger value="seo" className="flex items-center gap-1.5">
            <Search className="h-3.5 w-3.5" />
            SEO
          </TabsTrigger>
          <TabsTrigger value="ads" className="flex items-center gap-1.5">
            <Megaphone className="h-3.5 w-3.5" />
            Anuncios
          </TabsTrigger>
          <TabsTrigger value="images" className="flex items-center gap-1.5">
            <ImageIcon className="h-3.5 w-3.5" />
            Imágenes{images.length > 0 && ` (${images.length})`}
          </TabsTrigger>
        </TabsList>

        {/* Copy Tab */}
        <TabsContent value="copy" className="space-y-4 mt-4">
          <CopySection title="Descripción">
            <CopyText label="Descripción corta" value={asset.short_description} />
            {asset.long_description && (
              <div className="rounded-md border bg-muted/30 p-3 space-y-1">
                <p className="text-xs text-muted-foreground font-medium">Descripción larga</p>
                <div
                  className="text-sm leading-relaxed prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: asset.long_description }}
                />
              </div>
            )}
          </CopySection>

          {asset.bullet_points?.length > 0 && (
            <CopySection title="Puntos clave">
              <div className="rounded-md border bg-muted/30 p-3">
                <ul className="space-y-1">
                  {asset.bullet_points.map((bp, i) => (
                    <li key={i} className="text-sm flex gap-2">
                      <span className="text-primary font-bold">✓</span>
                      <span>{bp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </CopySection>
          )}

          {asset.faqs?.length > 0 && (
            <CopySection title="FAQs">
              <div className="rounded-md border bg-muted/30 p-3 space-y-3">
                {asset.faqs.map((faq, i) => (
                  <div key={i}>
                    <p className="text-sm font-medium">{faq.question}</p>
                    <p className="text-sm text-muted-foreground mt-0.5">{faq.answer}</p>
                    {i < asset.faqs.length - 1 && <Separator className="mt-3" />}
                  </div>
                ))}
              </div>
            </CopySection>
          )}
        </TabsContent>

        {/* SEO Tab */}
        <TabsContent value="seo" className="space-y-4 mt-4">
          <CopySection title="Meta Tags">
            <CopyText label="Meta Title" value={asset.meta_title} />
            <CopyText label="Meta Description" value={asset.meta_description} />
          </CopySection>

          {asset.keywords?.length > 0 && (
            <CopySection title="Keywords">
              <div className="flex flex-wrap gap-2">
                {asset.keywords.map((kw) => (
                  <Badge key={kw} variant="secondary" className="text-xs">
                    {kw}
                  </Badge>
                ))}
              </div>
            </CopySection>
          )}
        </TabsContent>

        {/* Ads Tab */}
        <TabsContent value="ads" className="space-y-6 mt-4">
          <CopySection title="Hooks y Headlines">
            <CopyList label="Hooks" items={asset.hooks} />
            <CopyList label="Headlines" items={asset.headlines} />
            <CopyList label="CTAs" items={asset.ctas} />
          </CopySection>

          {asset.ad_copies?.length > 0 && (
            <CopySection title="Copies generales">
              {asset.ad_copies.map((copy, i) => (
                <div key={i} className="rounded-md border bg-muted/30 p-3 space-y-1">
                  <p className="text-xs text-muted-foreground font-medium capitalize">{copy.format}</p>
                  <p className="text-sm leading-relaxed">{copy.copy}</p>
                </div>
              ))}
            </CopySection>
          )}

          <CopySection title="Por plataforma">
            <PlatformSection title="Facebook" data={asset.facebook_ads as Record<string, string>} />
            <PlatformSection title="TikTok" data={asset.tiktok_ads as Record<string, string>} />
            <PlatformSection title="Email" data={asset.email_campaigns as Record<string, string>} />
          </CopySection>
        </TabsContent>

        {/* Images Tab */}
        <TabsContent value="images" className="space-y-4 mt-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {images.length === 0
                ? 'No hay imágenes generadas todavía'
                : `${images.length} imagen${images.length !== 1 ? 'es' : ''} generada${images.length !== 1 ? 's' : ''}`}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => regenerateAllMutation.mutate()}
              disabled={regenerateAllMutation.isPending || !asset.candidate_id}
            >
              {regenerateAllMutation.isPending ? (
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-3.5 w-3.5" />
              )}
              Regenerar todas
            </Button>
          </div>

          {images.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <ImageIcon className="mb-3 h-8 w-8 text-muted-foreground" />
                <p className="text-sm font-medium">Sin imágenes generadas</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Las imágenes se generan automáticamente junto con los assets de marketing.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {images.map((img) => (
                <ImageCard
                  key={img.id}
                  image={img}
                  onRegenerate={(imgId) => regenerateImageMutation.mutate(imgId)}
                  onApprove={(imgId) => approveImageMutation.mutate(imgId)}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
