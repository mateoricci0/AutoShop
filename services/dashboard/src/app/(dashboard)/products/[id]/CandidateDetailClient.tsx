'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { productsApi } from '@/services/api/products'
import { marketingApi } from '@/services/api/marketing'
import { publisherApi } from '@/services/api/publisher'
import { queryKeys } from '@/services/query-keys'
import { SOURCE_LABELS, STATUS_COLORS } from '@/types/product'
import { formatCurrency, formatPercent, formatDate } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from 'sonner'
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  ExternalLink,
  Brain,
  DollarSign,
  Tag,
  ChevronDown,
  ChevronUp,
  Megaphone,
  ImageIcon,
  Loader2,
  ShoppingCart,
} from 'lucide-react'
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts'
import { cn } from '@/lib/utils'

const SCORE_LABELS: Record<string, string> = {
  demand_score: 'Demanda',
  trend_score: 'Tendencia',
  engagement_score: 'Engagement',
  margin_score: 'Margen',
  competition_score: 'Competencia',
  saturation_score: 'Saturación',
  branding_score: 'Branding',
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  analyzing: 'Analizando',
  approved: 'Aprobado',
  rejected: 'Rechazado',
  publishing: 'Publicando',
  published: 'Publicado',
  archived: 'Archivado',
}

function ScoreBar({
  label,
  score,
}: {
  label: string
  score: number | null
}) {
  if (score === null) {
    return (
      <div className="flex items-center justify-between gap-4">
        <span className="w-28 shrink-0 text-sm text-muted-foreground">{label}</span>
        <div className="flex-1 h-2 rounded-full bg-muted" />
        <span className="w-10 text-right text-xs text-muted-foreground">—</span>
      </div>
    )
  }
  const color =
    score >= 75
      ? 'bg-green-500'
      : score >= 60
        ? 'bg-orange-400'
        : score >= 40
          ? 'bg-yellow-400'
          : 'bg-red-400'
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="w-28 shrink-0 text-sm text-muted-foreground">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', color)}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
      <span className="w-10 text-right text-xs font-medium">{score.toFixed(1)}</span>
    </div>
  )
}

function SuccessScoreCircle({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <div className="flex flex-col items-center justify-center h-28 w-28 rounded-full border-4 border-muted">
        <span className="text-2xl font-bold text-muted-foreground">—</span>
        <span className="text-xs text-muted-foreground">Score</span>
      </div>
    )
  }
  const borderColor =
    score >= 75
      ? 'border-green-500'
      : score >= 60
        ? 'border-orange-400'
        : score >= 40
          ? 'border-yellow-400'
          : 'border-red-400'
  const textColor =
    score >= 75
      ? 'text-green-600'
      : score >= 60
        ? 'text-orange-500'
        : score >= 40
          ? 'text-yellow-600'
          : 'text-red-500'
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center h-28 w-28 rounded-full border-4',
        borderColor,
      )}
    >
      <span className={cn('text-2xl font-bold', textColor)}>{score.toFixed(0)}</span>
      <span className="text-xs text-muted-foreground">Score</span>
    </div>
  )
}

interface RejectDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: (reason: string) => void
  isPending: boolean
}

function RejectDialog({ open, onClose, onConfirm, isPending }: RejectDialogProps) {
  const [reason, setReason] = useState('')
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Rechazar candidato</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <p className="text-sm text-muted-foreground">
            Indica el motivo del rechazo (opcional):
          </p>
          <Input
            placeholder="Ej: Margen insuficiente, alta competencia..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>
            Cancelar
          </Button>
          <Button
            variant="destructive"
            onClick={() => onConfirm(reason || 'Rechazado manualmente')}
            disabled={isPending}
          >
            <XCircle className="mr-2 h-4 w-4" />
            Rechazar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface PublishDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: (price: number, compareAtPrice: number | null, vendor: string) => void
  isPending: boolean
  defaultPrice: number | null
}

function PublishDialog({ open, onClose, onConfirm, isPending, defaultPrice }: PublishDialogProps) {
  const [price, setPrice] = useState(defaultPrice?.toString() ?? '')
  const [compareAt, setCompareAt] = useState('')
  const [vendor, setVendor] = useState('')
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Publicar en Shopify</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Precio de venta *</p>
            <Input
              type="number"
              placeholder="29.99"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              step="0.01"
              min="0.01"
            />
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Precio tachado (opcional)</p>
            <Input
              type="number"
              placeholder="59.99"
              value={compareAt}
              onChange={(e) => setCompareAt(e.target.value)}
              step="0.01"
              min="0"
            />
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Vendor (opcional)</p>
            <Input
              placeholder="Mi Tienda"
              value={vendor}
              onChange={(e) => setVendor(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>
            Cancelar
          </Button>
          <Button
            onClick={() =>
              onConfirm(
                parseFloat(price),
                compareAt ? parseFloat(compareAt) : null,
                vendor,
              )
            }
            disabled={isPending || !price || isNaN(parseFloat(price))}
          >
            {isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <ShoppingCart className="mr-2 h-4 w-4" />
            )}
            Publicar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function CandidateDetailClient({ id }: { id: string }) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false)
  const [rawDataOpen, setRawDataOpen] = useState(false)
  const [generatingMarketing, setGeneratingMarketing] = useState(false)
  const [generatingImages, setGeneratingImages] = useState(false)
  const [publishDialogOpen, setPublishDialogOpen] = useState(false)
  const [publishing, setPublishing] = useState(false)

  const { data: candidate, isLoading, error } = useQuery({
    queryKey: queryKeys.products.candidates({ id }),
    queryFn: async () => {
      const res = await productsApi.getCandidate(id)
      return res.data
    },
    staleTime: 30_000,
  })

  const approveMutation = useMutation({
    mutationFn: () => productsApi.approveCandidate(id),
    onSuccess: () => {
      toast.success('Producto aprobado')
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all })
      router.push('/products')
    },
    onError: () => toast.error('Error al aprobar el producto'),
  })

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => productsApi.rejectCandidate(id, reason),
    onSuccess: () => {
      toast.success('Producto rechazado')
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all })
      setRejectDialogOpen(false)
      router.push('/products')
    },
    onError: () => toast.error('Error al rechazar el producto'),
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (error || !candidate) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <p className="text-sm text-muted-foreground">No se encontró el candidato.</p>
        <Button variant="outline" onClick={() => router.push('/products')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver
        </Button>
      </div>
    )
  }

  const radarData = Object.entries(SCORE_LABELS).map(([key, label]) => ({
    subject: label,
    value: (candidate[key as keyof typeof candidate] as number | null) ?? 0,
    fullMark: 100,
  }))

  const canAction =
    candidate.status === 'pending' || candidate.status === 'analyzing'

  const handleGenerateMarketing = async () => {
    setGeneratingMarketing(true)
    try {
      await marketingApi.generateAsset(id, candidate.store_id ?? undefined)
      toast.success('Generando marketing y copy con IA...')
    } catch {
      toast.error('Error al iniciar generación de marketing')
    } finally {
      setGeneratingMarketing(false)
    }
  }

  const handleGenerateImages = async () => {
    setGeneratingImages(true)
    try {
      await marketingApi.generateImages(id, candidate.store_id ?? undefined)
      toast.success('Generando 7 imágenes con IA...')
    } catch {
      toast.error('Error al iniciar generación de imágenes')
    } finally {
      setGeneratingImages(false)
    }
  }

  const handlePublish = async (price: number, compareAtPrice: number | null, vendor: string) => {
    if (!candidate.store_id) {
      toast.error('Este candidato no tiene tienda asignada')
      return
    }
    setPublishing(true)
    try {
      await publisherApi.publish({
        candidate_id: id,
        store_id: candidate.store_id,
        price,
        compare_at_price: compareAtPrice,
        vendor: vendor || undefined,
      })
      toast.success('Publicación iniciada en Shopify')
      setPublishDialogOpen(false)
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all })
      router.push('/published')
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Error al publicar'
      toast.error(msg)
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push('/products')}
        className="-ml-2"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Volver
      </Button>

      {/* Hero section */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl font-bold tracking-tight">{candidate.title}</h1>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {SOURCE_LABELS[candidate.source] ?? candidate.source}
            </Badge>
            <span
              className={cn(
                'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                STATUS_COLORS[candidate.status] ?? 'bg-gray-100 text-gray-800',
              )}
            >
              {STATUS_LABELS[candidate.status] ?? candidate.status}
            </span>
            {candidate.category && (
              <span className="text-xs text-muted-foreground">{candidate.category}</span>
            )}
            <span className="text-xs text-muted-foreground">
              Creado {formatDate(candidate.created_at)}
            </span>
          </div>
          {candidate.source_url && (
            <a
              href={candidate.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <ExternalLink className="h-3 w-3" />
              Ver fuente original
            </a>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2 shrink-0">
          {canAction && (
            <>
              <Button
                variant="outline"
                className="text-destructive border-destructive hover:bg-destructive hover:text-destructive-foreground"
                onClick={() => setRejectDialogOpen(true)}
                disabled={rejectMutation.isPending || approveMutation.isPending}
              >
                <XCircle className="mr-2 h-4 w-4" />
                Rechazar
              </Button>
              <Button
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={() => approveMutation.mutate()}
                disabled={approveMutation.isPending || rejectMutation.isPending}
              >
                <CheckCircle className="mr-2 h-4 w-4" />
                Aprobar
              </Button>
            </>
          )}
          {candidate.status === 'approved' && (
            <>
              <Button
                variant="outline"
                onClick={handleGenerateMarketing}
                disabled={generatingMarketing}
              >
                {generatingMarketing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Megaphone className="mr-2 h-4 w-4" />
                )}
                Generar copy
              </Button>
              <Button
                variant="outline"
                onClick={handleGenerateImages}
                disabled={generatingImages}
              >
                {generatingImages ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <ImageIcon className="mr-2 h-4 w-4" />
                )}
                Generar imágenes
              </Button>
              <Button
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
                onClick={() => setPublishDialogOpen(true)}
                disabled={publishing}
              >
                {publishing ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <ShoppingCart className="mr-2 h-4 w-4" />
                )}
                Publicar en Shopify
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Image gallery */}
      {candidate.images && candidate.images.length > 0 && (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {candidate.images.slice(0, 6).map((img, i) => (
            <img
              key={i}
              src={img.url}
              alt={img.alt || candidate.title}
              className="h-36 w-36 shrink-0 rounded-lg object-cover border"
            />
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Score section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Puntuaciones</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="flex items-center gap-6">
              <SuccessScoreCircle score={candidate.success_score} />
              <div className="flex-1 space-y-3">
                {Object.entries(SCORE_LABELS).map(([key, label]) => (
                  <ScoreBar
                    key={key}
                    label={label}
                    score={candidate[key as keyof typeof candidate] as number | null}
                  />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Radar chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Radar de Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
                <PolarGrid />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 100]}
                  tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }}
                />
                <Radar
                  name="Score"
                  dataKey="value"
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--primary))"
                  fillOpacity={0.25}
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Pricing section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <DollarSign className="h-4 w-4" />
            Precio y Margen
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <p className="text-xs text-muted-foreground mb-1">Coste</p>
              <p className="text-xl font-bold">
                {candidate.cost != null ? formatCurrency(candidate.cost) : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Precio recomendado</p>
              <p className="text-xl font-bold">
                {candidate.recommended_price != null
                  ? formatCurrency(candidate.recommended_price)
                  : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Margen estimado</p>
              <p className="text-xl font-bold">
                {candidate.estimated_margin != null
                  ? formatPercent(candidate.estimated_margin)
                  : '—'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Analysis */}
      {(candidate.ai_analysis?.analysis || candidate.ai_analysis?.error) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Brain className="h-4 w-4" />
              Análisis IA
              {candidate.ai_model && (
                <span className="ml-auto text-xs font-normal text-muted-foreground">
                  {candidate.ai_model}
                  {candidate.ai_tokens_used != null &&
                    ` · ${candidate.ai_tokens_used.toLocaleString()} tokens`}
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {candidate.ai_analysis.error ? (
              <p className="text-sm text-destructive">
                Error en el análisis: {candidate.ai_analysis.error}
              </p>
            ) : (
              <p className="text-sm leading-relaxed whitespace-pre-wrap text-muted-foreground">
                {candidate.ai_analysis.analysis}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tags */}
      {candidate.tags && candidate.tags.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Tag className="h-4 w-4" />
            Etiquetas
          </div>
          <div className="flex flex-wrap gap-2">
            {candidate.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Rejection reason */}
      {candidate.rejection_reason && (
        <Card className="border-destructive/30 bg-destructive/5">
          <CardContent className="pt-4">
            <p className="text-sm font-medium text-destructive mb-1">Motivo de rechazo</p>
            <p className="text-sm text-muted-foreground">{candidate.rejection_reason}</p>
          </CardContent>
        </Card>
      )}

      {/* Raw data accordion */}
      <div className="border rounded-lg">
        <button
          className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium hover:bg-muted/50 transition-colors"
          onClick={() => setRawDataOpen((v) => !v)}
        >
          <span>Datos completos</span>
          {rawDataOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        {rawDataOpen && (
          <>
            <Separator />
            <pre className="overflow-x-auto p-4 text-xs text-muted-foreground leading-relaxed">
              {JSON.stringify(candidate, null, 2)}
            </pre>
          </>
        )}
      </div>

      {/* Reject dialog */}
      <RejectDialog
        open={rejectDialogOpen}
        onClose={() => setRejectDialogOpen(false)}
        onConfirm={(reason) => rejectMutation.mutate(reason)}
        isPending={rejectMutation.isPending}
      />

      {/* Publish dialog */}
      <PublishDialog
        open={publishDialogOpen}
        onClose={() => setPublishDialogOpen(false)}
        onConfirm={handlePublish}
        isPending={publishing}
        defaultPrice={candidate.recommended_price ? parseFloat(String(candidate.recommended_price)) : null}
      />
    </div>
  )
}
