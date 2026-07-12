from datetime import date, datetime, timedelta
from types import SimpleNamespace

from app.services.schedule import resolve_today_day
from app.services.training_sessions import can_resume_session
from app.api.v1.training import _close_previous_sequence_day


def test_sequence_moves_by_calendar_day_even_when_previous_session_is_unfinished():
    plan = SimpleNamespace(
        schedule_type="sequence",
        created_at=datetime(2026, 7, 10, 9, 0),
        current_day_index=1,
        days=[
            SimpleNamespace(day_index=1, sort_order=1, day_name="背部", is_rest_day=False),
            SimpleNamespace(day_index=2, sort_order=2, day_name="肩部", is_rest_day=False),
            SimpleNamespace(day_index=3, sort_order=3, day_name="休息", is_rest_day=True),
            SimpleNamespace(day_index=4, sort_order=4, day_name="腿部", is_rest_day=False),
        ],
    )

    assert resolve_today_day(None, plan, date(2026, 7, 10)).day_name == "背部"
    assert resolve_today_day(None, plan, date(2026, 7, 11)).day_name == "肩部"
    assert resolve_today_day(None, plan, date(2026, 7, 12)).day_name == "休息"
    assert resolve_today_day(None, plan, date(2026, 7, 13)).day_name == "腿部"


def test_sequence_anchor_keeps_existing_plan_on_its_current_day_after_upgrade():
    plan = SimpleNamespace(
        schedule_type="sequence", created_at=datetime(2026, 6, 1, 9, 0), current_day_index=1,
        sequence_anchor_date=date(2026, 7, 12), sequence_anchor_day_index=2,
        days=[
            SimpleNamespace(day_index=1, sort_order=1, day_name="背部", is_rest_day=False),
            SimpleNamespace(day_index=2, sort_order=2, day_name="肩部", is_rest_day=False),
            SimpleNamespace(day_index=3, sort_order=3, day_name="休息", is_rest_day=True),
        ],
    )
    assert resolve_today_day(None, plan, date(2026, 7, 12)).day_name == "肩部"
    assert resolve_today_day(None, plan, date(2026, 7, 13)).day_name == "休息"


def test_previous_day_session_cannot_be_resumed_for_today():
    old = SimpleNamespace(plan_id=1, plan_day_id=10, session_date=datetime(2026, 7, 11))
    assert can_resume_session(old, plan_id=1, plan_day_id=11, session_date=date(2026, 7, 12)) is False


def test_same_day_same_plan_session_can_be_resumed():
    current = SimpleNamespace(plan_id=1, plan_day_id=11, session_date=datetime(2026, 7, 12))
    assert can_resume_session(current, plan_id=1, plan_day_id=11, session_date=date(2026, 7, 12)) is True


def test_new_sequence_plan_does_not_create_a_missed_session_for_yesterday():
    class QueryMustNotRun:
        def query(self, _model):
            raise AssertionError("a new plan must not query or archive yesterday")

    plan = SimpleNamespace(
        schedule_type="sequence",
        sequence_anchor_date=date(2026, 7, 12),
        created_at=datetime(2026, 7, 12, 9, 0),
        current_day_index=1,
        days=[SimpleNamespace(day_index=1, sort_order=1, is_rest_day=False)],
    )

    assert _close_previous_sequence_day(QueryMustNotRun(), 1, plan, date(2026, 7, 12)) is None
