from datetime import date, datetime, timedelta
from types import SimpleNamespace

from app.services.schedule import resolve_today_day


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
