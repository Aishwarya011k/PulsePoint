from bot import format_alert


def test_format_alert_contains_required_context():
    alert = format_alert({"target_id": 7, "anomaly_type": "latency_spike", "severity": "high", "confidence": 0.9, "summary": "Latency is rising."})
    assert "Target #7" in alert["text"]
    assert "LATENCY_SPIKE" in alert["text"]
    assert "Latency is rising." in alert["text"]
