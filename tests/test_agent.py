from app.planner import understand, make_plan


def test_understand_acme():
    ctx = understand("Find the latest invoice from Acme Corporation, extract the amount and due date, enter it into our internal system.")
    assert ctx["vendor"] == "Acme Corporation"
    assert ctx["needs_latest"] is True
    assert ctx["enter_internal_system"] is True


def test_plan_has_verification():
    plan = make_plan("Find the latest invoice from Acme, extract the amount and due date, and enter it into our internal system.", 10000)
    ids = [x["id"] for x in plan.actions]
    assert ids[:3] == ["open_inbox", "find_invoice", "extract_fields"]
    assert "verify" in ids
