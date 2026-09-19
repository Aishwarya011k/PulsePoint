#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
SELF_EMAIL="${SELF_MONITOR_EMAIL:-pulsepoint-self-monitor@example.com}"
: "${SELF_MONITOR_PASSWORD:?Set SELF_MONITOR_PASSWORD before registering self-monitoring targets}"
SELF_PASSWORD="$SELF_MONITOR_PASSWORD"

register_response=$(curl -fsS -X POST "${API_BASE_URL}/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${SELF_EMAIL}\",\"password\":\"${SELF_PASSWORD}\"}" || true)
if [[ -z "$register_response" ]]; then
  register_response=$(curl -fsS -X POST "${API_BASE_URL}/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${SELF_EMAIL}\",\"password\":\"${SELF_PASSWORD}\"}")
fi

access_token=$(printf '%s' "$register_response" | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
curl -fsS -X POST "${API_BASE_URL}/targets" \
  -H "Authorization: Bearer ${access_token}" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"PulsePoint backend health\",\"url\":\"${API_BASE_URL}/health\",\"check_interval_seconds\":60}" \
  || echo "Self target may already exist or could not be created. Verify with GET ${API_BASE_URL}/targets."
printf '\nSelf-monitor target registration complete.\n'
