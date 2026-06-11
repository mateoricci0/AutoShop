export type PublishedStatus = 'active' | 'draft' | 'archived' | 'deleted'

export interface PublishedProduct {
  id: string
  candidate_id: string | null
  store_id: string
  shopify_product_id: string | null
  shopify_handle: string | null
  title: string
  price: string
  compare_at_price: string | null
  status: PublishedStatus
  published_at: string | null
  last_synced_at: string | null
  created_at: string
  updated_at: string
}

export interface PublishedProductDetail extends PublishedProduct {
  description_html: string | null
  vendor: string | null
  product_type: string | null
  tags: string[]
  seo_title: string | null
  seo_description: string | null
  shopify_variant_ids: string[]
  shopify_collection_ids: string[]
  variants: unknown[]
  options: unknown[]
  images: Array<{ id: string | number; src: string }>
}

export interface ChecklistItem {
  key: string
  label: string
  passed: boolean
  detail: string | null
}

export interface ChecklistResult {
  candidate_id: string
  store_id: string
  passed: boolean
  items: ChecklistItem[]
}

export interface PublishJobResult {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  step?: string
  result?: {
    published_id: string
    shopify_product_id: string
    shopify_handle: string
    candidate_id: string
  }
  error?: string
}

export const PUBLISHED_STATUS_COLORS: Record<PublishedStatus, string> = {
  active: 'bg-green-100 text-green-700',
  draft: 'bg-gray-100 text-gray-700',
  archived: 'bg-gray-100 text-gray-500',
  deleted: 'bg-red-100 text-red-600',
}

export const PUBLISHED_STATUS_LABELS: Record<PublishedStatus, string> = {
  active: 'Activo',
  draft: 'Borrador',
  archived: 'Archivado',
  deleted: 'Eliminado',
}
