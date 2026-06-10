'use client'

import { useQuery } from '@tanstack/react-query'
import apiClient from '@/services/api/client'
import { queryKeys } from '@/services/query-keys'
import { AgentCard } from '@/components/agents/AgentCard'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/format'
import type { Agent, AgentLog } from '@/types/agent'

const MOCK_AGENTS: Agent[] = [
  {
    id: 'product-hunter',
    name: 'product-hunter',
    display_name: 'Product Hunter',
    description: 'Scraping y scoring de productos ganadores desde TikTok, AliExpress, Amazon',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://product-hunter:8002',
  },
  {
    id: 'marketing',
    name: 'marketing',
    display_name: 'Marketing Agent',
    description: 'Generación de copy SEO, textos de anuncios y assets de marketing con DeepSeek',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://marketing:8003',
  },
  {
    id: 'image-pipeline',
    name: 'image-pipeline',
    display_name: 'Image Pipeline',
    description: 'Generación de 7 tipos de imágenes de producto con DALL·E / Stability AI',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://image-pipeline:8004',
  },
  {
    id: 'shopify-publisher',
    name: 'shopify-publisher',
    display_name: 'Shopify Publisher',
    description: 'Publicación automatizada de productos en Shopify Admin API',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://shopify-publisher:8005',
  },
  {
    id: 'analytics',
    name: 'analytics',
    display_name: 'Analytics Agent',
    description: 'Recolección de métricas, cálculo de ROAS y motor de decisiones',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://analytics:8006',
  },
  {
    id: 'notifications',
    name: 'notifications',
    display_name: 'Notifications',
    description: 'Envío de notificaciones por Email, Discord, Telegram y Slack',
    status: 'idle',
    last_run_at: null,
    last_error: null,
    service_url: 'http://notifications:8007',
  },
]

const logLevelVariant: Record<string, 'default' | 'secondary' | 'destructive'> = {
  info: 'secondary',
  warning: 'default',
  error: 'destructive',
}

export function AgentsClient() {
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
    refetchInterval: 15_000,
  })

  const { data: logs = [], isLoading: logsLoading } = useQuery<AgentLog[]>({
    queryKey: ['agent-logs'],
    queryFn: async () => {
      try {
        const res = await apiClient.get<AgentLog[]>('/hunter/v1/logs', {
          params: { limit: 20 },
        })
        return res.data
      } catch {
        return []
      }
    },
    staleTime: 15_000,
    refetchInterval: 30_000,
  })

  return (
    <div className="space-y-8">
      {/* Agent cards */}
      <div>
        <h2 className="mb-4 text-base font-semibold">Estado actual</h2>
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

      {/* Logs */}
      <div>
        <h2 className="mb-4 text-base font-semibold">Logs recientes</h2>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Últimas 20 entradas
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {logsLoading ? (
              <div className="p-4 space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : logs.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
                No hay logs disponibles
              </div>
            ) : (
              <div className="divide-y">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-start gap-3 px-4 py-3 text-xs"
                  >
                    <Badge
                      variant={logLevelVariant[log.level] ?? 'secondary'}
                      className="shrink-0 text-[10px] uppercase"
                    >
                      {log.level}
                    </Badge>
                    <p className="flex-1 text-muted-foreground">{log.message}</p>
                    {log.ai_cost !== null && (
                      <span className="shrink-0 text-muted-foreground">
                        ${log.ai_cost.toFixed(4)}
                      </span>
                    )}
                    <span className="shrink-0 text-muted-foreground">
                      {formatDate(log.created_at)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
