export type AgentStatus = 'idle' | 'running' | 'error' | 'disabled'

export interface Agent {
  id: string
  name: string
  display_name: string
  description: string
  status: AgentStatus
  last_run_at: string | null
  last_error: string | null
  service_url: string
}

export interface AgentLog {
  id: string
  agent_id: string
  level: 'info' | 'warning' | 'error'
  message: string
  ai_cost: number | null
  created_at: string
}
