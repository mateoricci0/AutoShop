'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { TrendingUp, DollarSign, ShoppingCart, BarChart3 } from 'lucide-react'
import { queryKeys } from '@/services/query-keys'
import { analyticsApi } from '@/services/api/analytics'
import { useActiveStore } from '@/hooks/useActiveStore'
import { formatCurrency, formatROAS, formatNumber, formatDate } from '@/lib/format'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
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
import type { AnalyticsDecision } from '@/types/analytics'

const decisionConfig: Record<
  AnalyticsDecision,
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }
> = {
  scale: { label: 'Escalar', variant: 'default' },
  optimize: { label: 'Optimizar', variant: 'secondary' },
  pause: { label: 'Pausar', variant: 'destructive' },
  insufficient_data: { label: 'Sin datos', variant: 'outline' },
}

export function PerformanceClient() {
  const { activeStoreId } = useActiveStore()
  const [range, setRange] = useState('30d')

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: queryKeys.analytics.summary(activeStoreId ?? 'all', range),
    queryFn: async () => {
      if (!activeStoreId) return null
      const res = await analyticsApi.getSummary(activeStoreId, range)
      return res.data
    },
    enabled: !!activeStoreId,
    staleTime: 60_000,
  })

  const { data: productAnalytics = [], isLoading: productsLoading } = useQuery({
    queryKey: queryKeys.analytics.products(activeStoreId ?? 'all', range),
    queryFn: async () => {
      if (!activeStoreId) return []
      const res = await analyticsApi.getProductAnalytics(activeStoreId, range)
      return res.data
    },
    enabled: !!activeStoreId,
    staleTime: 60_000,
  })

  const { data: revenueSeries = [] } = useQuery({
    queryKey: queryKeys.analytics.timeSeries(activeStoreId ?? 'all', 'revenue', range),
    queryFn: async () => {
      if (!activeStoreId) return []
      const res = await analyticsApi.getTimeSeries(activeStoreId, 'revenue', range)
      return res.data
    },
    enabled: !!activeStoreId,
    staleTime: 60_000,
  })

  const chartData = revenueSeries.map((p) => ({
    date: formatDate(p.date),
    revenue: p.value,
  }))

  if (!activeStoreId) {
    return (
      <Card className="flex items-center justify-center py-16 text-center">
        <div>
          <BarChart3 className="mx-auto mb-3 h-8 w-8 text-muted-foreground" />
          <p className="text-sm font-medium">Selecciona una tienda</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Elige una tienda en el selector de arriba para ver las métricas
          </p>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Range selector */}
      <div className="flex items-center justify-between">
        <Select value={range} onValueChange={setRange}>
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Últimos 7 días</SelectItem>
            <SelectItem value="30d">Últimos 30 días</SelectItem>
            <SelectItem value="90d">Últimos 90 días</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Summary stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {summaryLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))
        ) : summary ? (
          <>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Revenue</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{formatCurrency(summary.total_revenue)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Beneficio</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{formatCurrency(summary.total_profit)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">ROAS</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{formatROAS(summary.overall_roas)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Pedidos</CardTitle>
                <ShoppingCart className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{formatNumber(summary.total_orders)}</p>
              </CardContent>
            </Card>
          </>
        ) : (
          <div className="col-span-4 flex items-center justify-center py-8 text-sm text-muted-foreground">
            No hay datos para el período seleccionado
          </div>
        )}
      </div>

      {/* Revenue chart */}
      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Revenue por día</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), 'Revenue']}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  name="Revenue"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Per-product analytics */}
      <div>
        <h2 className="mb-3 text-base font-semibold">Rendimiento por producto</h2>
        <Card>
          {productsLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : productAnalytics.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
              No hay datos de analíticas para este período
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead>Revenue</TableHead>
                  <TableHead>Beneficio</TableHead>
                  <TableHead>Pedidos</TableHead>
                  <TableHead>ROAS</TableHead>
                  <TableHead>Decisión</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {productAnalytics.map((pa) => {
                  const decision = decisionConfig[pa.decision]
                  return (
                    <TableRow key={pa.product_id}>
                      <TableCell className="font-medium">
                        <span className="line-clamp-1 max-w-[180px]">
                          {pa.product_title}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm">{formatCurrency(pa.revenue)}</TableCell>
                      <TableCell className="text-sm">{formatCurrency(pa.profit)}</TableCell>
                      <TableCell className="text-sm">{formatNumber(pa.orders)}</TableCell>
                      <TableCell className="text-sm font-medium">{formatROAS(pa.roas)}</TableCell>
                      <TableCell>
                        <Badge variant={decision.variant} className="text-xs">
                          {decision.label}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </Card>
      </div>
    </div>
  )
}
