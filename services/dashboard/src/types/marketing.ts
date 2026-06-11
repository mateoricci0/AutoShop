export type AssetStatus = 'draft' | 'generating' | 'approved' | 'active' | 'archived'

export type ImageType =
  | 'hero'
  | 'lifestyle'
  | 'infographic'
  | 'before_after'
  | 'banner'
  | 'ad_square'
  | 'ad_story'

export type ImageStatus = 'pending' | 'generating' | 'approved' | 'needs_review' | 'failed'

export interface MarketingAsset {
  id: string
  candidate_id: string | null
  store_id: string | null
  brand_name: string | null
  tagline: string | null
  short_description: string | null
  long_description: string | null
  bullet_points: string[]
  faqs: Array<{ question: string; answer: string }>
  meta_title: string | null
  meta_description: string | null
  keywords: string[]
  hooks: string[]
  headlines: string[]
  ctas: string[]
  ad_copies: Array<{ format: string; copy: string }>
  facebook_ads: Record<string, string>
  instagram_ads: Record<string, unknown>
  tiktok_ads: Record<string, string>
  google_ads: Record<string, unknown>
  email_campaigns: Record<string, string>
  ai_model: string | null
  generation_cost: number | null
  tokens_used: number | null
  status: AssetStatus
  created_at: string
  updated_at: string
}

export interface GeneratedImage {
  id: string
  candidate_id: string | null
  store_id: string | null
  type: ImageType
  prompt: string
  negative_prompt: string | null
  storage_key: string | null
  storage_url: string | null
  thumbnail_url: string | null
  width: number | null
  height: number | null
  format: string | null
  file_size_bytes: number | null
  model: string | null
  provider: string | null
  generation_cost: number | null
  generation_time_ms: number | null
  clip_score: number | null
  status: ImageStatus
  error_message: string | null
  retry_count: number
  created_at: string
  updated_at: string
}

export const IMAGE_TYPE_LABELS: Record<ImageType, string> = {
  hero: 'Hero',
  lifestyle: 'Lifestyle',
  infographic: 'Infografía',
  before_after: 'Antes/Después',
  banner: 'Banner',
  ad_square: 'Ad Cuadrado',
  ad_story: 'Ad Story',
}

export const ASSET_STATUS_COLORS: Record<AssetStatus, string> = {
  draft: 'bg-gray-100 text-gray-700',
  generating: 'bg-blue-100 text-blue-700',
  approved: 'bg-green-100 text-green-700',
  active: 'bg-emerald-100 text-emerald-700',
  archived: 'bg-gray-100 text-gray-500',
}
