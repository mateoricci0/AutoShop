'use client'

import { useQuery } from '@tanstack/react-query'
import {
  Package,
  CheckCircle,
  ShoppingBag,
  TrendingUp,
  DollarSign,
  BarChart3,
  ArrowUpRight,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { AgentCard } from '@/components/agents/AgentCard'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { queryKeys } from '@/services/query-keys'
import { productsApi } from '@/services/api/products'
import { analyticsApi } from '@/services/api/analytics'
import apiClient from '@/services/api/client'
import { useActiveStore } from '@/hooks/useActiveStore'
import { formatCurrency, formatROAS, formatNumber, formatDate } from '@/lib/format'
import type { Agent } from '@/types/agent'
import type { AnalyticsSummary } from '@/types/analytics'

// Mock agents for Phase 1 (will come from a real API in Phase 2)
const MOCK_AGENTS: Agent[] = [
  {
    id: 'product-hunter',
    name: 'product-hunter',
    display_name: 'Product Hunter',
    description: 'Scraping y scoring de productos ganadores',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://product-hunter:8002',
  },
  {
    id: 'marketing',
    name: 'marketing',
    display_name: 'Marketing Agent',
    description: 'Generación de copy y assets de marketing',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://marketing:8003',
  },
  {
    id: 'image-pipeline',
    name: 'image-pipeline',
    display_name: 'Image Pipeline',
    description: 'Generación de imágenes de producto',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://image-pipeline:8004',
  },
  {
    id: 'shopify-publisher',
    name: 'shopify-publisher',
    display_name: 'Shopify Publisher',
    description: 'Publicación de productos en Shopify',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://shopify-publisher:8005',
  },
  {
    id: 'analytics',
    name: 'analytics',
    display_name: 'Analytics Agent',
    description: 'Recolección de métricas y decisiones ROAS',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://analytics:8006',
  },
  {
    id: 'notifications',
    name: 'notifications',
    display_name: 'Notifications',
    description: 'Envío de notificaciones multicanal',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://notifications:8007',
  },
]

const statusColors: Record<string, string> = {
  pending: 'secondary',
  analyzing: 'info',
  approved: 'success',
  rejected: 'destructive',
  publishing: 'warning',
  published: 'default',
  archived: 'outline',
}

const statusLabels: Record<string, string> = {
  pending: 'Pendiente',
  analyzing: 'Analizando',
  approved: 'Aprobado',
  rejected: 'Rechazado',
  publishing: 'Publicando',
  published: 'Publicado',
  archived: 'Archivado',
}

interface StatCardProps {
  title: string
  value: string
  icon: React.ComponentType<{ className?: string }>
  description?: string
  trend?: number
  loading?: boolean
}

function StatCard({ title, value, icon: Icon, description, trend, loading }: StatCardProps) {
  if (loading) return <Skeleton className="h-32 rounded-lg" />
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {(description || trend !== undefined) && (
          <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
            {trend !== undefined && trend > 0 && (
              <ArrowUpRight className="h-3 w-3 text-green-500" />
            )}
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function OverviewClient() {
  const { activeStoreId } = useActiveStore()

  // Candidates summary
  const { data: candidatesData, isLoading: candidatesLoading } = useQuery({
    queryKey: queryKeys.products.candidates({ limit: 5 }),
    queryFn: async () => {
      const res = await productsApi.getCandidates({ limit: 5 })
      return res.data
    },
    staleTime: 30_000,
  })

  // All candidates for counts
  const { data: allCandidates } = useQuery({
    queryKey: queryKeys.products.candidates({}),
    queryFn: async () => {
      const res = await productsApi.getCandidates({ limit: 100 })
      return res.data
    },
    staleTime: 30_000,
  })

  // Published products
  const { data: publishedData, isLoading: publishedLoading } = useQuery({
    queryKey: queryKeys.products.published(activeStoreId ?? undefined),
    queryFn: async () => {
      const res = await productsApi.getPublished(activeStoreId ?? undefined)
      return res.data
    },
    enabled: true,
    staleTime: 30_000,
  })

  // Analytics summary
  const { data: analyticsSummary, isLoading: analyticsLoading } = useQuery<AnalyticsSummary>({
    queryKey: queryKeys.analytics.summary(activeStoreId ?? 'all', '30d'),
    queryFn: async () => {
      if (!activeStoreId) throw new Error('No store selected')
      const res = await analyticsApi.getSummary(activeStoreId, '30d')
      return res.data
    },
    enabled: !!activeStoreId,
    staleTime: 60_000,
  })

  // Agents status
  const { data: agents = MOCK_AGENTS, isLoading: agentsLoading } = useQuery<Agent[]>({
    queryKey: queryKeys.agents.list(),
    queryFn: async () => {
      try {
        const res = await apiClient.get<Agent[]>('/hunter/v1/agents')
        return res.data
      } catch {
        return MOCK_AGENTS
      }
    },
    staleTime: 30_000,
  })

  const totalCandidates = allCandidates?.total ?? 0
  const approvedCandidates =
    allCandidates?.items.filter((c) => c.status === 'approved').length ?? 0
  const totalPublished = publishedData?.total ?? 0

  const statsLoading = candidatesLoading || publishedLoading || analyticsLoading

  const stats = [
    {
      title: 'Total Candidatos',
      value: formatNumber(totalCandidates),
      icon: Package,
      description: 'Productos descubiertos',
    },
    {
      title: 'Aprobados',
      value: formatNumber(approvedCandidates),
      icon: CheckCircle,
      description: 'Listos para publicar',
    },
    {
      title: 'Publicados',
      value: formatNumber(totalPublished),
      icon: ShoppingBag,
      description: 'En tiendas Shopify',
    },
    {
      title: 'ROAS Promedio',
      value: analyticsSummary ? formatROAS(analyticsSummary.overall_roas) : '—',
      icon: TrendingUp,
      description: 'Últimos 30 días',
    },
    {
      title: 'Revenue Total',
      value: analyticsSummary
        ? formatCurrency(analyticsSummary.total_revenue)
        : '—',
      icon: DollarSign,
      description: 'Últimos 30 días',
    },
    {
      title: 'Beneficio',
      value: analyticsSummary
        ? formatCurrency(analyticsSummary.total_profit)
        : '—',
      icon: BarChart3,
      description: 'Últimos 30 días',
    },
  ]

  const recentCandidates = candidatesData?.items ?? []

  return (
    <div className="space-y-6">
      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => (
          <StatCard key={stat.title} {...stat} loading={statsLoading} />
        ))}
      </div>

      {/* Agents grid */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Estado de Agentes</h2>
        {agentsLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-44 rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        )}
      </div>

      {/* Recent candidates table */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Candidatos Recientes</h2>
        <Card>
          {candidatesLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : recentCandidates.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
              No hay candidatos todavía. Los agentes los descubrirán automáticamente.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead>Fuente</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Creado</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentCandidates.map((candidate) => (
                  <TableRow key={candidate.id}>
                    <TableCell className="font-medium">
                      <span className="line-clamp-1 max-w-[200px]">
                        {candidate.title}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {candidate.source}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {candidate.success_score !== null ? (
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
                            <div
                              className="h-full rounded-full bg-primary"
                              style={{ width: `${candidate.success_score}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {candidate.success_score.toFixed(0)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          (statusColors[candidate.status] as 'default' | 'secondary' | 'destructive' | 'outline') ??
                          'secondary'
                        }
                        className="text-xs"
                      >
                        {statusLabels[candidate.status] ?? candidate.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDate(candidate.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </div>
    </div>
  )
}
