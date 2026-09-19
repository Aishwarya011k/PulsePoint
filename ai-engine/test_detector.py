from detector import detect_anomalies


def test_detects_latency_spike_before_failure():
    window = [{"success": True, "response_time_ms": 180}] + [
        {"success": True, "response_time_ms": 20} for _ in range(4)
    ]
    signals = detect_anomalies(window)
    assert signals[0]["anomaly_type"] == "latency_spike"


def test_detects_rising_failure_rate():
    window = [
        {"success": False, "response_time_ms": 100},
        {"success": False, "response_time_ms": 100},
        {"success": True, "response_time_ms": 20},
    ]
    assert any(signal["anomaly_type"] == "failure_rate_increase" for signal in detect_anomalies(window))


def test_requires_history():
    assert detect_anomalies([{"success": True, "response_time_ms": 20}] * 2) == []
