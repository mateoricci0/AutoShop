import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Megaphone } from 'lucide-react'

export const metadata = { title: 'Marketing — ASE' }

export default function MarketingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Marketing</h1>
        <p className="text-muted-foreground">
          Assets de marketing generados para tus productos
        </p>
      </div>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Megaphone className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-base">Assets de Marketing</CardTitle>
          </div>
          <CardDescription>
            Copy, SEO, anuncios y assets visuales generados por el Marketing Agent
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Megaphone className="mb-3 h-10 w-10 text-muted-foreground" />
            <p className="text-sm font-medium">Disponible en Phase 2</p>
            <p className="mt-1 max-w-sm text-xs text-muted-foreground">
              El Marketing Agent generará copy SEO-optimizado, textos de anuncios
              para Facebook/TikTok, y assets visuales automáticamente cuando se implemente.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
