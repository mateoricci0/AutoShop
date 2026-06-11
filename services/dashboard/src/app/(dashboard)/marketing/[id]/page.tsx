import AssetDetailClient from './AssetDetailClient'

export const metadata = { title: 'Asset de Marketing — ASE' }

export default function AssetDetailPage({ params }: { params: { id: string } }) {
  return <AssetDetailClient id={params.id} />
}
