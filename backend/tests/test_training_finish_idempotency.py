from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.api.v1.training import finish_session


def test_finishing_completed_session_returns_existing_result_without_writing():
    session = SimpleNamespace(
        id=9, user_id=1, plan_id=2, plan_day_id=3,
        session_date=datetime(2026, 7, 13), session_name="胸部训练",
        status="completed", started_at=datetime(2026, 7, 13, 10),
        ended_at=datetime(2026, 7, 13, 11), duration_seconds=3600,
        total_volume=1000, note=None, exercises=[], deleted_at=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = session

    result = finish_session(9, SimpleNamespace(id=1), db)

    assert result["data"]["status"] == "completed"
    db.add.assert_not_called()
    db.commit.assert_not_called()
