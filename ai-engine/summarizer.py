"""Best-effort Loki correlation and Anthropic summarization."""
import json
import logging

import httpx

from config import config

logger = logging.getLogger(__name__)
FALLBACK = "AI summary unavailable; inspect the target's recent latency and error logs."


def fetch_loki_logs(target_id: int, checked_at: str) -> str:
    """Fetch a bounded log excerpt; Loki failures never block incident publication."""
    try:
        response = httpx.get(
            f"{config.LOKI_URL.rstrip('/')}/loki/api/v1/query_range",
            params={"query": f'{{namespace="pulsepoint"}} |= "target {target_id}"', "limit": 40, "direction": "backward"},
            timeout=2.0,
        )
        response.raise_for_status()
        streams = response.json().get("data", {}).get("result", [])
        lines = [line for stream in streams for _, line in stream.get("values", [])]
        return "\n".join(lines[-40:])[:12000] or f"No recent Loki logs found near {checked_at} for target {target_id}."
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Loki lookup failed for target %s: %s", target_id, exc)
        return "No correlated logs were available."


def summarize_incident(event: dict) -> str:
    """Generate a short explanation, returning a useful fallback on any provider failure."""
    logs = fetch_loki_logs(event["target_id"], event["timestamp"])
    if not config.ANTHROPIC_API_KEY:
        return FALLBACK
    prompt = (
        "Explain this uptime degradation in 2-3 cautious sentences. Do not invent causes; "
        "say when evidence is insufficient.\nEvent:\n"
        f"{json.dumps(event, sort_keys=True)}\nRecent logs:\n{logs}"
    )
    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": config.ANTHROPIC_MODEL, "max_tokens": 180, "temperature": 0, "messages": [{"role": "user", "content": prompt}]},
            timeout=config.LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json().get("content", [])
        text = " ".join(part.get("text", "") for part in content).strip()
        return text or FALLBACK
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("LLM summarization failed: %s", exc)
        return FALLBACK
