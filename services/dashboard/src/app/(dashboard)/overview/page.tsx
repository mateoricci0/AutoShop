import { Suspense } from 'react'
import { OverviewClient } from './OverviewClient'
import { Skeleton } from '@/components/ui/skeleton'

export const metadata = { title: 'Overview — ASE' }

export default function OverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Overview</h1>
        <p className="text-muted-foreground">
          Resumen del sistema y estado de los agentes
        </p>
      </div>
      <Suspense fallback={<OverviewSkeleton />}>
        <OverviewClient />
      </Suspense>
    </div>
  )
}

function OverviewSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-64 rounded-lg" />
    </div>
  )
}
