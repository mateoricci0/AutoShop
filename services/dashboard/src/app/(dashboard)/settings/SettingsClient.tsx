'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Store,
  Plus,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Loader2,
  Bell,
  Bot,
} from 'lucide-react'
import { toast } from 'sonner'
import { formatDate } from '@/lib/format'
import { authApi } from '@/services/api/auth'
import { queryKeys } from '@/services/query-keys'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import type { Store as StoreType } from '@/types/store'

// ---- Store form schema ----
const storeSchema = z.object({
  name: z.string().min(1, 'El nombre es requerido'),
  shopify_domain: z
    .string()
    .min(1, 'El dominio es requerido')
    .regex(
      /^[a-zA-Z0-9-]+\.myshopify\.com$/,
      'Formato: tu-tienda.myshopify.com'
    ),
  shopify_access_token: z
    .string()
    .min(1, 'El token de acceso es requerido')
    .startsWith('shpat_', 'El token debe empezar por shpat_'),
  currency: z.string().optional(),
  timezone: z.string().optional(),
})

type StoreFormData = z.infer<typeof storeSchema>

// ---- Store Form Dialog ----
function StoreFormDialog({
  onSuccess,
}: {
  onSuccess?: () => void
}) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const form = useForm<StoreFormData>({
    resolver: zodResolver(storeSchema),
    defaultValues: {
      name: '',
      shopify_domain: '',
      shopify_access_token: '',
      currency: 'USD',
      timezone: 'UTC',
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: StoreFormData) => authApi.createStore(data),
    onSuccess: () => {
      toast.success('Tienda conectada exitosamente')
      queryClient.invalidateQueries({ queryKey: queryKeys.stores.all })
      form.reset()
      setOpen(false)
      onSuccess?.()
    },
    onError: () => {
      toast.error('Error al conectar la tienda. Verifica el dominio y el token.')
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="mr-2 h-4 w-4" />
          Agregar tienda
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Conectar tienda Shopify</DialogTitle>
          <DialogDescription>
            Ingresa los datos de tu tienda Shopify para conectarla al sistema.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((data) => createMutation.mutate(data))}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nombre de la tienda</FormLabel>
                  <FormControl>
                    <Input placeholder="Mi tienda de dropshipping" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="shopify_domain"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Dominio Shopify</FormLabel>
                  <FormControl>
                    <Input placeholder="mi-tienda.myshopify.com" {...field} />
                  </FormControl>
                  <FormDescription>
                    El dominio .myshopify.com de tu tienda
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="shopify_access_token"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Access Token</FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder="shpat_xxxxxxxxxxxxxxxxx"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Token de acceso de la Admin API de Shopify
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="currency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Moneda</FormLabel>
                    <FormControl>
                      <Input placeholder="USD" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="timezone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Zona horaria</FormLabel>
                    <FormControl>
                      <Input placeholder="UTC" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Conectar tienda
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

// ---- Delete confirmation dialog ----
function DeleteStoreDialog({
  store,
  onSuccess,
}: {
  store: StoreType
  onSuccess?: () => void
}) {
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const deleteMutation = useMutation({
    mutationFn: () => authApi.deleteStore(store.id),
    onSuccess: () => {
      toast.success('Tienda eliminada')
      queryClient.invalidateQueries({ queryKey: queryKeys.stores.all })
      setOpen(false)
      onSuccess?.()
    },
    onError: () => {
      toast.error('Error al eliminar la tienda')
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive">
          <Trash2 className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>¿Eliminar tienda?</DialogTitle>
          <DialogDescription>
            Esta acción eliminará <strong>{store.name}</strong> del sistema. Los
            datos históricos de la tienda también se borrarán. Esta acción no se
            puede deshacer.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button
            variant="destructive"
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Eliminar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ---- Store card with test-connection ----
function StoreCard({ store }: { store: StoreType }) {
  const [connectionStatus, setConnectionStatus] = useState<
    'idle' | 'testing' | 'ok' | 'error'
  >('idle')

  const testMutation = useMutation({
    mutationFn: () => authApi.testConnection(store.id),
    onMutate: () => setConnectionStatus('testing'),
    onSuccess: () => setConnectionStatus('ok'),
    onError: () => setConnectionStatus('error'),
  })

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
              <Store className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-sm">{store.name}</CardTitle>
              <CardDescription className="text-xs">
                {store.shopify_domain}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant={store.is_active ? 'success' : 'secondary'} className="text-xs">
              {store.is_active ? 'Activa' : 'Inactiva'}
            </Badge>
            <DeleteStoreDialog store={store} />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <p className="text-muted-foreground">Moneda</p>
            <p className="font-medium">{store.currency}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Zona horaria</p>
            <p className="font-medium">{store.timezone}</p>
          </div>
          {store.shopify_plan && (
            <div>
              <p className="text-muted-foreground">Plan</p>
              <p className="font-medium capitalize">{store.shopify_plan}</p>
            </div>
          )}
          {store.last_synced_at && (
            <div>
              <p className="text-muted-foreground">Última sincronización</p>
              <p className="font-medium">{formatDate(store.last_synced_at)}</p>
            </div>
          )}
        </div>

        {/* Connection test */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="flex-1"
            onClick={() => testMutation.mutate()}
            disabled={connectionStatus === 'testing'}
          >
            {connectionStatus === 'testing' ? (
              <Loader2 className="mr-2 h-3 w-3 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-3 w-3" />
            )}
            Probar conexión
          </Button>
          {connectionStatus === 'ok' && (
            <div className="flex items-center gap-1 text-xs text-green-600">
              <CheckCircle className="h-4 w-4" />
              OK
            </div>
          )}
          {connectionStatus === 'error' && (
            <div className="flex items-center gap-1 text-xs text-destructive">
              <XCircle className="h-4 w-4" />
              Error
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// ---- Stores tab ----
function StoresTab() {
  const { data: stores = [], isLoading } = useQuery<StoreType[]>({
    queryKey: queryKeys.stores.list(),
    queryFn: async () => {
      const res = await authApi.getStores()
      return res.data
    },
    staleTime: 60_000,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-medium">Tiendas conectadas</h3>
          <p className="text-xs text-muted-foreground">
            Gestiona tus tiendas Shopify
          </p>
        </div>
        <StoreFormDialog />
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <Card key={i} className="h-48 animate-pulse bg-muted" />
          ))}
        </div>
      ) : stores.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-12 text-center">
          <Store className="mb-3 h-8 w-8 text-muted-foreground" />
          <p className="text-sm font-medium">No hay tiendas conectadas</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Agrega tu primera tienda Shopify para comenzar
          </p>
          <div className="mt-4">
            <StoreFormDialog />
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {stores.map((store) => (
            <StoreCard key={store.id} store={store} />
          ))}
        </div>
      )}
    </div>
  )
}

// ---- Notifications tab (placeholder) ----
function NotificationsTab() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-base">Notificaciones</CardTitle>
        </div>
        <CardDescription>
          Configura los canales de notificación: Email, Discord, Telegram, Slack
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center py-8 text-center">
          <div>
            <Bell className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium">Disponible en Phase 5</p>
            <p className="mt-1 text-xs text-muted-foreground">
              La configuración de notificaciones estará disponible cuando se
              implemente el servicio de notificaciones.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ---- Agents tab (placeholder) ----
function AgentsTab() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-muted-foreground" />
          <CardTitle className="text-base">Configuración de Agentes</CardTitle>
        </div>
        <CardDescription>
          Horarios, umbrales y parámetros de cada agente autónomo
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center py-8 text-center">
          <div>
            <Bot className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium">Disponible en Phase 2</p>
            <p className="mt-1 text-xs text-muted-foreground">
              La configuración de agentes (schedules, thresholds, etc.) estará
              disponible cuando se implementen los agentes en Phase 2.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ---- Main component ----
export function SettingsClient() {
  return (
    <Tabs defaultValue="stores">
      <TabsList>
        <TabsTrigger value="stores">Tiendas</TabsTrigger>
        <TabsTrigger value="notifications">Notificaciones</TabsTrigger>
        <TabsTrigger value="agents">Agentes</TabsTrigger>
      </TabsList>
      <TabsContent value="stores" className="mt-4">
        <StoresTab />
      </TabsContent>
      <TabsContent value="notifications" className="mt-4">
        <NotificationsTab />
      </TabsContent>
      <TabsContent value="agents" className="mt-4">
        <AgentsTab />
      </TabsContent>
    </Tabs>
  )
}
