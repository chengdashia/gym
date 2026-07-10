import pytest

from app.api.v1.stats import _normalize_range
from app.core.exceptions import BizException


@pytest.mark.parametrize("days", [7, 30, 90])
def test_stats_accepts_visible_ranges(days):
    assert _normalize_range(days) == days


def test_stats_rejects_removed_15_day_range():
    with pytest.raises(BizException):
        _normalize_range(15)
