import { Suspense } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import CandidateDetailClient from './CandidateDetailClient'

export default async function CandidatePage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <div className="p-6">
      <Suspense
        fallback={
          <div className="space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-96 w-full" />
          </div>
        }
      >
        <CandidateDetailClient id={id} />
      </Suspense>
    </div>
  )
}
