from consumer import apply_check_event


class DummyCheck:
    def __init__(self, target_id, status_code, response_time_ms, success, checked_at):
        self.target_id = target_id
        self.status_code = status_code
        self.response_time_ms = response_time_ms
        self.success = success
        self.checked_at = checked_at


class DummyIncident:
    def __init__(self, target_id, status):
        self.target_id = target_id
        self.status = status
        self.resolved_at = None


class DummySession:
    def __init__(self):
        self.added = []
        self.committed = False

    def query(self, model):
        class Query:
            def __init__(self, parent):
                self.parent = parent

            def filter(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def first(self):
                if model.__name__ == "Check":
                    return DummyCheck(1, 200, 123.0, True, "2024-01-01T00:00:00+00:00")
                if model.__name__ == "Incident":
                    return DummyIncident(1, "open")
                return None

        return Query(self)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True


class DummyTarget:
    def __init__(self):
        self.id = 1
        self.name = "Example"


def test_apply_check_event_opens_incident_on_failure_transition():
    session = DummySession()
    target = DummyTarget()

    result = apply_check_event(session, target, {
        "target_id": 1,
        "status_code": 500,
        "response_time_ms": 250.0,
        "success": False,
        "checked_at": "2024-01-01T00:01:00+00:00",
    }, previous_success=True)

    assert result["incident_opened"] is True
    assert any(getattr(item, "status", None) == "open" for item in session.added)
