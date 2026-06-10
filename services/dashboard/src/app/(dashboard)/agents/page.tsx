import { AgentsClient } from './AgentsClient'

export const metadata = { title: 'Agentes — ASE' }

export default function AgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Agentes</h1>
        <p className="text-muted-foreground">
          Estado, ejecución y logs de los agentes autónomos
        </p>
      </div>
      <AgentsClient />
    </div>
  )
}
