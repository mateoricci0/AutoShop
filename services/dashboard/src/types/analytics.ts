export type AnalyticsDecision = 'scale' | 'optimize' | 'pause' | 'insufficient_data'

export interface AnalyticsSummary {
  total_revenue: number
  total_cost: number
  total_profit: number
  total_orders: number
  overall_roas: number
  total_impressions: number
  total_clicks: number
  active_campaigns: number
}

export interface TimeSeriesPoint {
  date: string
  value: number
}

export interface ProductAnalytics {
  product_id: string
  product_title: string
  revenue: number
  cost: number
  profit: number
  orders: number
  roas: number
  impressions: number
  clicks: number
  decision: AnalyticsDecision
  period_start: string
  period_end: string
}
