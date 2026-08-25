import json

from worker import build_check_event


def test_build_check_event_includes_expected_fields():
    event = build_check_event(target_id=7, check_result={
        "status_code": 500,
        "response_time_ms": 234.5,
        "success": False,
    })

    assert event["target_id"] == 7
    assert event["status_code"] == 500
    assert event["response_time_ms"] == 234.5
    assert event["success"] is False
    assert "checked_at" in event
    assert isinstance(event["checked_at"], str)
    json.dumps(event)
