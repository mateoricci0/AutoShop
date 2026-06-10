import { PublishedClient } from './PublishedClient'

export const metadata = { title: 'Publicados — ASE' }

export default function PublishedPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Publicados</h1>
        <p className="text-muted-foreground">
          Productos activos en tus tiendas Shopify
        </p>
      </div>
      <PublishedClient />
    </div>
  )
}
