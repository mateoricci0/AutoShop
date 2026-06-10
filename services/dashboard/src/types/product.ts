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
  source_product_id: string | null
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
  ai_analysis: {
    analysis?: string
    error?: string
  }
  ai_model: string | null
  ai_tokens_used: number | null
  ai_cost: number | null
  status: ProductStatus
  rejection_reason: string | null
  approved_at: string | null
  scraped_at: string | null
  analyzed_at: string | null
  created_at: string
  updated_at: string
}

export interface CandidateFilters {
  status?: string
  source?: string
  min_score?: number
  store_id?: string
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

export const SOURCE_LABELS: Record<string, string> = {
  google_trends: 'Google Trends',
  reddit: 'Reddit',
  amazon: 'Amazon',
  aliexpress: 'AliExpress',
  tiktok_creative: 'TikTok Creative',
  tiktok_shop: 'TikTok Shop',
  facebook_ads: 'Facebook Ads',
  temu: 'Temu',
}

export const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  analyzing: 'bg-blue-100 text-blue-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  publishing: 'bg-purple-100 text-purple-800',
  published: 'bg-emerald-100 text-emerald-800',
  archived: 'bg-gray-100 text-gray-800',
}
