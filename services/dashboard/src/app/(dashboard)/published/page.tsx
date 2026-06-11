import { Suspense } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import PublishedClient from './PublishedClient'

export const metadata = { title: 'Publicados — ASE' }

export default function PublishedPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Productos Publicados</h1>
        <p className="text-muted-foreground">
          Productos publicados en Shopify con su estado de sincronización
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-48 w-full" />}>
        <PublishedClient />
      </Suspense>
    </div>
  )
}
