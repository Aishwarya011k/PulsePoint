export interface Target {
  id: number
  name: string
  url: string
  check_interval_seconds: number
  created_at: string
  group_id: number | null
  group: Group | null
  uptime_percentage: number | null
}

export interface Group {
  id: number
  name: string
  color: string | null
  created_at: string
}

export interface Check {
  id: number
  target_id: number
  status_code: number
  response_time_ms: number
  success: boolean
  checked_at: string
}

export interface TargetDetail extends Target {
  recent_checks: Check[]
  incidents: Incident[]
}

export interface Incident {
  id: number
  target_id: number
  status: 'open' | 'resolved'
  started_at: string
  resolved_at: string | null
  summary: string | null
  postmortem_note: string | null
  postmortem_author: string | null
  postmortem_updated_at: string | null
  has_postmortem: boolean
}

export interface CheckHistory {
  total: number
  limit: number
  offset: number
  checks: Check[]
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
