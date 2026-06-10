import { ProductsClient } from './ProductsClient'

export const metadata = { title: 'Productos — ASE' }

export default function ProductsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Productos</h1>
        <p className="text-muted-foreground">
          Candidatos descubiertos por el Product Hunter
        </p>
      </div>
      <ProductsClient />
    </div>
  )
}
