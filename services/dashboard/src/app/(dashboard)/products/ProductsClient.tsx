'use client'

import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { productsApi } from '@/services/api/products'
import { queryKeys } from '@/services/query-keys'
import { useStoreSelectorStore } from '@/stores/store-selector.store'
import { type ProductCandidate, SOURCE_LABELS, STATUS_COLORS } from '@/types/product'
import { formatCurrency, formatDate } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Card } from '@/components/ui/card'
import { toast } from 'sonner'
import {
  Search,
  RefreshCw,
  MoreHorizontal,
  Play,
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Trash2,
  ExternalLink,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pendiente',
  analyzing: 'Analizando',
  approved: 'Aprobado',
  rejected: 'Rechazado',
  publishing: 'Publicando',
  published: 'Publicado',
  archived: 'Archivado',
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-muted-foreground text-xs">—</span>
  const color =
    score >= 75
      ? 'bg-green-100 text-green-800'
      : score >= 60
        ? 'bg-orange-100 text-orange-800'
        : score >= 40
          ? 'bg-yellow-100 text-yellow-800'
          : 'bg-red-100 text-red-800'
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold',
        color,
      )}
    >
      {score.toFixed(1)}
    </span>
  )
}

interface HuntDialogProps {
  open: boolean
  onClose: () => void
  taskId: string | null
}

function HuntDialog({ open, onClose, taskId }: HuntDialogProps) {
  const [progress, setProgress] = useState(0)
  const [statusText, setStatusText] = useState('Iniciando escaneo...')
  const [done, setDone] = useState(false)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!taskId || !open) return
    setProgress(0)
    setStatusText('Iniciando escaneo...')
    setDone(false)

    let interval: ReturnType<typeof setInterval>

    const poll = async () => {
      try {
        const res = await productsApi.getJobStatus(taskId)
        const job = res.data
        if (job.progress !== undefined) {
          setProgress(job.progress)
        }
        if (job.status === 'started') {
          setStatusText('Escaneando fuentes...')
        } else if (job.status === 'success') {
          setProgress(100)
          setStatusText('Escaneo completado')
          setDone(true)
          clearInterval(interval)
          queryClient.invalidateQueries({ queryKey: queryKeys.products.all })
        } else if (job.status === 'failure') {
          setStatusText(`Error: ${job.error ?? 'desconocido'}`)
          setDone(true)
          clearInterval(interval)
        }
      } catch {
        // ignore transient errors
      }
    }

    poll()
    interval = setInterval(poll, 2000)
    return () => clearInterval(interval)
  }, [taskId, open, queryClient])

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Escaneando productos</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <p className="text-sm text-muted-foreground">{statusText}</p>
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground text-right">{progress}%</p>
          {!done && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Esto puede tardar unos minutos...</span>
            </div>
          )}
          {done && (
            <Button className="w-full" onClick={onClose}>
              Cerrar
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export function ProductsClient() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const { activeStoreId } = useStoreSelectorStore()

  // Filter state
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [sourceFilter, setSourceFilter] = useState<string>('all')
  const [minScore, setMinScore] = useState<string>('')
  const [sort, setSort] = useState<string>('created_desc')

  // Pagination
  const [page, setPage] = useState(0)
  const limit = 20

  // Hunt dialog
  const [huntDialogOpen, setHuntDialogOpen] = useState(false)
  const [huntTaskId, setHuntTaskId] = useState<string | null>(null)

  const filters = {
    status: statusFilter !== 'all' ? statusFilter : undefined,
    source: sourceFilter !== 'all' ? sourceFilter : undefined,
    min_score: minScore ? Number(minScore) : undefined,
    store_id: activeStoreId ?? undefined,
    sort: sort === 'score_desc' ? 'success_score:desc' : 'created_at:desc',
    limit,
    offset: page * limit,
  }

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: queryKeys.products.candidates(filters as Record<string, unknown>),
    queryFn: async () => {
      const res = await productsApi.listCandidates(filters)
      return res.data
    },
    staleTime: 30_000,
  })

  const approveMutation = useMutation({
    mutationFn: (id: string) =>
      productsApi.approveCandidate(id, activeStoreId ?? undefined),
    onSuccess: () => {
      toast.success('Producto aprobado')
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all })
    },
    onError: () => toast.error('Error al aprobar el producto'),
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      productsApi.rejectCandidate(id, reason),
    onSuccess: () => {
      toast.success('Producto rechazado')
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all })
    },
    onError: () => toast.error('Error al rechazar el producto'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => productsApi.deleteCandidate(id),
    onSuccess: () => {
      toast.success('Candidato eliminado')
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all })
    },
    onError: () => toast.error('Error al eliminar el candidato'),
  })

  const huntMutation = useMutation({
    mutationFn: () =>
      productsApi.triggerHunt(activeStoreId ?? undefined),
    onSuccess: (res) => {
      setHuntTaskId(res.data.task_id)
      setHuntDialogOpen(true)
      toast.info('Escaneo iniciado')
    },
    onError: () => toast.error('Error al iniciar el escaneo'),
  })

  const candidates = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / limit)

  // Client-side title search (the API may not support it)
  const filtered = search
    ? candidates.filter((c) => c.title.toLowerCase().includes(search.toLowerCase()))
    : candidates

  const handleRowClick = useCallback(
    (id: string) => {
      router.push(`/products/${id}`)
    },
    [router],
  )

  const handleHuntClose = useCallback(() => {
    setHuntDialogOpen(false)
    setHuntTaskId(null)
  }, [])

  return (
    <div className="space-y-4">
      {/* Filters row */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por título..."
            className="pl-9"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(0)
            }}
          />
        </div>

        <Select
          value={statusFilter}
          onValueChange={(v) => {
            setStatusFilter(v)
            setPage(0)
          }}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los estados</SelectItem>
            <SelectItem value="pending">Pendiente</SelectItem>
            <SelectItem value="analyzing">Analizando</SelectItem>
            <SelectItem value="approved">Aprobado</SelectItem>
            <SelectItem value="rejected">Rechazado</SelectItem>
            <SelectItem value="publishing">Publicando</SelectItem>
            <SelectItem value="published">Publicado</SelectItem>
            <SelectItem value="archived">Archivado</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={sourceFilter}
          onValueChange={(v) => {
            setSourceFilter(v)
            setPage(0)
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Fuente" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas las fuentes</SelectItem>
            {Object.entries(SOURCE_LABELS).map(([key, label]) => (
              <SelectItem key={key} value={key}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={sort}
          onValueChange={(v) => {
            setSort(v)
            setPage(0)
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Ordenar" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="created_desc">Más recientes primero</SelectItem>
            <SelectItem value="score_desc">Mejor score primero</SelectItem>
          </SelectContent>
        </Select>

        <Input
          type="number"
          placeholder="Score mín."
          className="w-[120px]"
          value={minScore}
          min={0}
          max={100}
          onChange={(e) => {
            setMinScore(e.target.value)
            setPage(0)
          }}
        />

        <div className="flex gap-2 ml-auto">
          <Button
            variant="outline"
            size="icon"
            onClick={() => refetch()}
            disabled={isFetching}
            title="Actualizar"
          >
            <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
          </Button>
          <Button
            onClick={() => huntMutation.mutate()}
            disabled={huntMutation.isPending}
          >
            <Play className="mr-2 h-4 w-4" />
            Scan ahora
          </Button>
        </div>
      </div>

      {/* Table */}
      <Card>
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-sm font-medium text-muted-foreground">
              No hay candidatos
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Usa &quot;Scan ahora&quot; para que el Product Hunter descubra productos
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead>Fuente</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Coste</TableHead>
                <TableHead>Precio recom.</TableHead>
                <TableHead>Creado</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((candidate) => (
                <TableRow
                  key={candidate.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleRowClick(candidate.id)}
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div>
                        <p className="line-clamp-1 max-w-[200px] font-medium text-sm">
                          {candidate.title}
                        </p>
                        {candidate.category && (
                          <p className="text-xs text-muted-foreground">
                            {candidate.category}
                          </p>
                        )}
                      </div>
                      {candidate.source_url && (
                        <a
                          href={candidate.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="shrink-0 text-muted-foreground hover:text-foreground"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs whitespace-nowrap">
                      {SOURCE_LABELS[candidate.source] ?? candidate.source}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <ScoreBadge score={candidate.success_score} />
                  </TableCell>
                  <TableCell>
                    <span
                      className={cn(
                        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                        STATUS_COLORS[candidate.status] ?? 'bg-gray-100 text-gray-800',
                      )}
                    >
                      {STATUS_LABELS[candidate.status] ?? candidate.status}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm">
                    {candidate.cost != null ? formatCurrency(candidate.cost) : '—'}
                  </TableCell>
                  <TableCell className="text-sm">
                    {candidate.recommended_price != null
                      ? formatCurrency(candidate.recommended_price)
                      : '—'}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatDate(candidate.created_at)}
                  </TableCell>
                  <TableCell
                    onClick={(e) => e.stopPropagation()}
                  >
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => handleRowClick(candidate.id)}
                        >
                          Ver detalle
                        </DropdownMenuItem>
                        {(candidate.status === 'pending' ||
                          candidate.status === 'analyzing') && (
                          <>
                            <DropdownMenuItem
                              className="text-green-600 focus:text-green-600"
                              onClick={() => approveMutation.mutate(candidate.id)}
                              disabled={approveMutation.isPending}
                            >
                              <CheckCircle className="mr-2 h-4 w-4" />
                              Aprobar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-destructive focus:text-destructive"
                              onClick={() =>
                                rejectMutation.mutate({
                                  id: candidate.id,
                                  reason: 'Rechazado manualmente',
                                })
                              }
                              disabled={rejectMutation.isPending}
                            >
                              <XCircle className="mr-2 h-4 w-4" />
                              Rechazar
                            </DropdownMenuItem>
                          </>
                        )}
                        <DropdownMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => deleteMutation.mutate(candidate.id)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-muted-foreground">
            {total} candidatos en total · página {page + 1} de {totalPages}
          </p>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
              const pageNum =
                totalPages <= 7
                  ? i
                  : page < 4
                    ? i
                    : page > totalPages - 4
                      ? totalPages - 7 + i
                      : page - 3 + i
              if (pageNum < 0 || pageNum >= totalPages) return null
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === page ? 'default' : 'outline'}
                  size="icon"
                  className="h-8 w-8 text-xs"
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum + 1}
                </Button>
              )
            })}
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Hunt progress dialog */}
      <HuntDialog
        open={huntDialogOpen}
        onClose={handleHuntClose}
        taskId={huntTaskId}
      />
    </div>
  )
}
