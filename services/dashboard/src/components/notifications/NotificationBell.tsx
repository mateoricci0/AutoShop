'use client'

import { useState } from 'react'
import { Bell, Check, ExternalLink, X } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formatDistanceToNow, parseISO } from 'date-fns'
import { es } from 'date-fns/locale'
import { queryKeys } from '@/services/query-keys'
import apiClient from '@/services/api/client'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import type { Notification } from '@/types/notification'

const notificationTypeLabels: Record<string, string> = {
  product_found: 'Nuevo producto',
  product_approved: 'Producto aprobado',
  product_published: 'Producto publicado',
  analytics_alert: 'Alerta ROAS',
  agent_error: 'Error de agente',
  system: 'Sistema',
}

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: notifications = [] } = useQuery<Notification[]>({
    queryKey: queryKeys.notifications.list(),
    queryFn: async () => {
      try {
        const res = await apiClient.get<Notification[]>('/notifications/v1/notifications', {
          params: { limit: 20 },
        })
        return res.data
      } catch {
        return []
      }
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  })

  const unreadCount = notifications.filter((n) => !n.read).length

  const markReadMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.patch(`/notifications/v1/notifications/${id}/read`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: async () => {
      await apiClient.post('/notifications/v1/notifications/mark-all-read')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all })
    },
  })

  const recent = notifications.slice(0, 5)

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setOpen(!open)}
        className="relative"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-[10px] font-bold text-destructive-foreground">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
          />
          {/* Popover */}
          <div className="absolute right-0 top-full z-50 mt-2 w-80 rounded-lg border bg-popover text-popover-foreground shadow-lg">
            {/* Header */}
            <div className="flex items-center justify-between border-b px-4 py-3">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold">Notificaciones</h3>
                {unreadCount > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {unreadCount}
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-1">
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => markAllReadMutation.mutate()}
                  >
                    <Check className="mr-1 h-3 w-3" />
                    Marcar todas
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setOpen(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Notifications list */}
            <div className="max-h-80 overflow-y-auto">
              {recent.length === 0 ? (
                <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
                  No hay notificaciones
                </div>
              ) : (
                recent.map((notif, idx) => (
                  <div key={notif.id}>
                    <button
                      className={`w-full px-4 py-3 text-left transition-colors hover:bg-accent ${
                        !notif.read ? 'bg-muted/30' : ''
                      }`}
                      onClick={() => {
                        if (!notif.read) markReadMutation.mutate(notif.id)
                      }}
                    >
                      <div className="flex items-start gap-2">
                        {!notif.read && (
                          <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
                        )}
                        <div className={`flex-1 ${notif.read ? 'pl-4' : ''}`}>
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-xs font-medium text-muted-foreground">
                              {notificationTypeLabels[notif.type] ?? notif.type}
                            </p>
                            <p className="shrink-0 text-xs text-muted-foreground">
                              {formatDistanceToNow(parseISO(notif.created_at), {
                                addSuffix: true,
                                locale: es,
                              })}
                            </p>
                          </div>
                          <p className="mt-0.5 text-sm font-medium">{notif.title}</p>
                          <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                            {notif.message}
                          </p>
                        </div>
                      </div>
                    </button>
                    {idx < recent.length - 1 && <Separator />}
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            {notifications.length > 5 && (
              <div className="border-t p-2">
                <Button variant="ghost" className="w-full text-xs" size="sm">
                  <ExternalLink className="mr-1 h-3 w-3" />
                  Ver todas las notificaciones
                </Button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
