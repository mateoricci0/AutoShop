import PublishedDetailClient from './PublishedDetailClient'

export const metadata = { title: 'Producto Publicado — ASE' }

export default function PublishedDetailPage({ params }: { params: { id: string } }) {
  return <PublishedDetailClient id={params.id} />
}
