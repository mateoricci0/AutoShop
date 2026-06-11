import { Suspense } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import MarketingClient from './MarketingClient'

export const metadata = { title: 'Marketing — ASE' }

export default function MarketingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Marketing</h1>
        <p className="text-muted-foreground">
          Copy, SEO y anuncios generados por IA para cada producto
        </p>
      </div>
      <Suspense fallback={<Skeleton className="h-48 w-full" />}>
        <MarketingClient />
      </Suspense>
    </div>
  )
}
