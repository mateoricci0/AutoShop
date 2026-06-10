export type ProductStatus =
  | 'pending'
  | 'analyzing'
  | 'approved'
  | 'rejected'
  | 'publishing'
  | 'published'
  | 'archived'

export interface ProductCandidate {
  id: string
  store_id: string | null
  title: string
  description: string | null
  source: string
  source_url: string | null
  cost: number | null
  recommended_price: number | null
  estimated_margin: number | null
  demand_score: number | null
  competition_score: number | null
  trend_score: number | null
  engagement_score: number | null
  saturation_score: number | null
  branding_score: number | null
  margin_score: number | null
  success_score: number | null
  category: string | null
  tags: string[]
  images: Array<{ url: string; alt: string }>
  ai_analysis: Record<string, unknown>
  status: ProductStatus
  rejection_reason: string | null
  approved_at: string | null
  scraped_at: string | null
  analyzed_at: string | null
  created_at: string
  updated_at: string
}

export interface PublishedProduct {
  id: string
  store_id: string
  candidate_id: string
  shopify_product_id: string
  shopify_variant_id: string | null
  title: string
  status: 'active' | 'draft' | 'archived'
  price: number
  compare_at_price: number | null
  inventory_quantity: number
  published_at: string
  created_at: string
  updated_at: string
}
