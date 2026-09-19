"""Small, explainable anomaly detector for recent checks."""
from statistics import mean, pstdev


def detect_anomalies(window: list[dict], latency_zscore: float = 2.0, failure_rate_threshold: float = 0.3) -> list[dict]:
    """Return predictive signals from a newest-first rolling check window."""
    if len(window) < 3:
        return []

    response_times = [float(item.get("response_time_ms", 0)) for item in window if item.get("success")]
    signals = []
    latest = window[0]
    latest_latency = float(latest.get("response_time_ms", 0))

    if len(response_times) >= 3:
        baseline = response_times[1:]
        average = mean(baseline)
        deviation = pstdev(baseline)
        threshold = average + latency_zscore * max(deviation, average * 0.1, 1.0)
        if latest.get("success") and latest_latency > threshold:
            confidence = min(0.99, 0.5 + (latest_latency - threshold) / max(threshold, 1.0))
            signals.append({
                "anomaly_type": "latency_spike",
                "confidence": round(confidence, 3),
                "severity": "high" if latest_latency > threshold * 1.5 else "medium",
                "details": {"baseline_mean_ms": round(average, 2), "threshold_ms": round(threshold, 2)},
            })

    recent_failures = sum(1 for item in window[:5] if not item.get("success", False))
    sample_size = min(5, len(window))
    failure_rate = recent_failures / sample_size
    if failure_rate > failure_rate_threshold:
        signals.append({
            "anomaly_type": "failure_rate_increase",
            "confidence": round(min(0.99, 0.5 + failure_rate / 2), 3),
            "severity": "critical" if failure_rate >= 0.8 else "high",
            "details": {"failure_rate": round(failure_rate, 3), "sample_size": sample_size},
        })
    return signals
