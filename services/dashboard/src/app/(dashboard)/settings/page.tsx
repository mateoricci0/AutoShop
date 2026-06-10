import { SettingsClient } from './SettingsClient'

export const metadata = { title: 'Ajustes — ASE' }

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Ajustes</h1>
        <p className="text-muted-foreground">
          Configura tus tiendas Shopify, notificaciones y agentes
        </p>
      </div>
      <SettingsClient />
    </div>
  )
}
