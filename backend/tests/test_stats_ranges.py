import pytest

from app.api.v1.stats import _normalize_range, _parse_optional_date
from app.core.exceptions import BizException


@pytest.mark.parametrize("days", [7, 30, 90])
def test_stats_accepts_visible_ranges(days):
    assert _normalize_range(days) == days


def test_stats_rejects_removed_15_day_range():
    with pytest.raises(BizException):
        _normalize_range(15)


def test_invalid_optional_date_is_a_business_error():
    with pytest.raises(BizException) as error:
        _parse_optional_date("undefined")

    assert error.value.code == 40001
