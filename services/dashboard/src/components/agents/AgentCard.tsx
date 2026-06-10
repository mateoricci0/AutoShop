'use client'

import { Play, Loader2, AlertCircle, Clock } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { formatDistanceToNow, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import apiClient from '@/services/api/client'
import { queryKeys } from '@/services/query-keys'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { Agent, AgentStatus } from '@/types/agent'

const statusConfig: Record<
  AgentStatus,
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'info' | 'warning' | 'success' }
> = {
  idle: { label: 'Inactivo', variant: 'secondary' },
  running: { label: 'Ejecutando', variant: 'info' },
  error: { label: 'Error', variant: 'destructive' },
  disabled: { label: 'Desactivado', variant: 'outline' },
}

interface AgentCardProps {
  agent: Agent
}

export function AgentCard({ agent }: AgentCardProps) {
  const queryClient = useQueryClient()
  const { label, variant } = statusConfig[agent.status]

  const triggerMutation = useMutation({
    mutationFn: async () => {
      const serviceMap: Record<string, string> = {
        'product-hunter': '/hunter/v1/run',
        marketing: '/marketing/v1/run',
        'image-pipeline': '/images/v1/run',
        'shopify-publisher': '/publisher/v1/run',
        analytics: '/analytics/v1/run',
        notifications: '/notifications/v1/run',
      }
      const endpoint = serviceMap[agent.id] ?? `/hunter/v1/run`
      await apiClient.post(endpoint)
    },
    onSuccess: () => {
      toast.success(`${agent.display_name} iniciado`)
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.all })
    },
    onError: () => {
      toast.error(`Error al iniciar ${agent.display_name}`)
    },
  })

  return (
    <Card className="relative overflow-hidden">
      {/* Running pulse indicator */}
      {agent.status === 'running' && (
        <div className="absolute inset-x-0 top-0 h-0.5 animate-pulse bg-blue-500" />
      )}

      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-sm font-semibold">{agent.display_name}</CardTitle>
          <Badge variant={variant as 'default' | 'secondary' | 'destructive' | 'outline'}>
            {agent.status === 'running' && (
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            )}
            {agent.status === 'error' && (
              <AlertCircle className="mr-1 h-3 w-3" />
            )}
            {label}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">{agent.description}</p>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Last run */}
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {agent.last_run_at ? (
            <span>
              Última ejecución:{' '}
              {formatDistanceToNow(parseISO(agent.last_run_at), {
                addSuffix: true,
                locale: es,
              })}
            </span>
          ) : (
            <span>Nunca ejecutado</span>
          )}
        </div>

        {/* Error message */}
        {agent.status === 'error' && agent.last_error && (
          <div className="rounded-md bg-destructive/10 px-2 py-1.5">
            <p className="line-clamp-2 text-xs text-destructive">{agent.last_error}</p>
          </div>
        )}

        {/* Trigger button */}
        <Button
          size="sm"
          variant="outline"
          className="w-full"
          disabled={agent.status === 'running' || agent.status === 'disabled' || triggerMutation.isPending}
          onClick={() => triggerMutation.mutate()}
        >
          {triggerMutation.isPending || agent.status === 'running' ? (
            <Loader2 className="mr-2 h-3 w-3 animate-spin" />
          ) : (
            <Play className="mr-2 h-3 w-3" />
          )}
          Ejecutar
        </Button>
      </CardContent>
    </Card>
  )
}
