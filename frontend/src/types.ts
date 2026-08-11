export interface Target {
  id: number
  name: string
  url: string
  check_interval_seconds: number
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
