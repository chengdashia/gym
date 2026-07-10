from types import SimpleNamespace

from app.services.schedule import next_sequence_day_index


def day(index: int, *, rest: bool = False, order: int | None = None):
    return SimpleNamespace(day_index=index, is_rest_day=rest, sort_order=order or index)


def test_sequence_uses_real_day_index_and_wraps():
    days = [day(10), day(20), day(30)]
    assert next_sequence_day_index(days, 10) == 20
    assert next_sequence_day_index(days, 30) == 10


def test_sequence_skips_rest_days():
    days = [day(1), day(2, rest=True), day(3)]
    assert next_sequence_day_index(days, 1) == 3
    assert next_sequence_day_index(days, 3) == 1


def test_sequence_handles_missing_pointer_and_all_rest():
    assert next_sequence_day_index([day(4), day(8)], 999) == 4
    assert next_sequence_day_index([day(1, rest=True), day(2, rest=True)], 1) == 1
    assert next_sequence_day_index([], 1) is None
