export type NotificationType =
  | 'product_found'
  | 'product_approved'
  | 'product_published'
  | 'analytics_alert'
  | 'agent_error'
  | 'system'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  read: boolean
  data: Record<string, unknown> | null
  created_at: string
}
