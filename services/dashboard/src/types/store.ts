export interface Store {
  id: string
  name: string
  shopify_domain: string
  shopify_plan: string | null
  currency: string
  timezone: string
  is_active: boolean
  last_synced_at: string | null
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface StoreCreate {
  name: string
  shopify_domain: string
  shopify_access_token: string
  currency?: string
  timezone?: string
}
