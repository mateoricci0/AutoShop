'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle, XCircle, ExternalLink, Search, Filter } from 'lucide-react'
import { toast } from 'sonner'
import { queryKeys } from '@/services/query-keys'
import { productsApi, type CandidateFilters } from '@/services/api/products'
import { formatCurrency, formatDate } from '@/lib/format'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { ProductStatus } from '@/types/product'

const statusColors: Record<ProductStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'secondary',
  analyzing: 'secondary',
  approved: 'default',
  rejected: 'destructive',
  publishing: 'secondary',
  published: 'default',
  archived: 'outline',
}

const statusLabels: Record<ProductStatus, string> = {
  pending: 'Pendiente',
  analyzing: 'Analizando',
  approved: 'Aprobado',
  rejected: 'Rechazado',
  publishing: 'Publicando',
  published: 'Publicado',
  archived: 'Archivado',
}

export function ProductsClient() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [page, setPage] = useState(0)
  const limit = 20

  const filters: CandidateFilters = {
    status: statusFilter !== 'all' ? statusFilter : undefined,
    limit,
    offset: page * limit,
  }

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.products.candidates(filters as Record<string, unknown>),
    queryFn: async () => {
      const res = await productsApi.getCandidates(filters)
      return res.data
    },
    staleTime: 30_000,
  })

  const approveMutation = useMutation({
    mutationFn: (id: string) => productsApi.approveCandidate(id),
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

  const candidates = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / limit)

  const filtered = search
    ? candidates.filter((c) =>
        c.title.toLowerCase().includes(search.toLowerCase())
      )
    : candidates

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar productos..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="pending">Pendiente</SelectItem>
            <SelectItem value="analyzing">Analizando</SelectItem>
            <SelectItem value="approved">Aprobado</SelectItem>
            <SelectItem value="rejected">Rechazado</SelectItem>
            <SelectItem value="published">Publicado</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-sm font-medium text-muted-foreground">
              No hay productos candidatos
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              El Product Hunter descubrirá productos automáticamente
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead>Fuente</TableHead>
                <TableHead>Coste</TableHead>
                <TableHead>Precio recom.</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Creado</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((candidate) => (
                <TableRow key={candidate.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div>
                        <p className="line-clamp-1 max-w-[180px] font-medium text-sm">
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
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">
                      {candidate.source}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {candidate.cost ? formatCurrency(candidate.cost) : '—'}
                  </TableCell>
                  <TableCell className="text-sm">
                    {candidate.recommended_price
                      ? formatCurrency(candidate.recommended_price)
                      : '—'}
                  </TableCell>
                  <TableCell>
                    {candidate.success_score !== null ? (
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-12 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-primary"
                            style={{ width: `${candidate.success_score}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium">
                          {candidate.success_score.toFixed(0)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusColors[candidate.status]} className="text-xs">
                      {statusLabels[candidate.status]}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {formatDate(candidate.created_at)}
                  </TableCell>
                  <TableCell>
                    {candidate.status === 'pending' || candidate.status === 'analyzing' ? (
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 w-7 p-0 text-green-600 hover:text-green-700"
                          onClick={() => approveMutation.mutate(candidate.id)}
                          disabled={approveMutation.isPending}
                          title="Aprobar"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                          onClick={() =>
                            rejectMutation.mutate({
                              id: candidate.id,
                              reason: 'Rechazado manualmente',
                            })
                          }
                          disabled={rejectMutation.isPending}
                          title="Rechazar"
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      </div>
                    ) : null}
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
            {total} productos en total
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              Anterior
            </Button>
            <span className="text-muted-foreground">
              {page + 1} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              Siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
