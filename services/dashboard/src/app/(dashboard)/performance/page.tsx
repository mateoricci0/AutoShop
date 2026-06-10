import { PerformanceClient } from './PerformanceClient'

export const metadata = { title: 'Performance — ASE' }

export default function PerformancePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Performance</h1>
        <p className="text-muted-foreground">
          Métricas de rendimiento, ROAS y recomendaciones
        </p>
      </div>
      <PerformanceClient />
    </div>
  )
}
