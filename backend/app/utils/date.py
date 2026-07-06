from __future__ import annotations

from datetime import date, datetime, timedelta


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def today_date() -> date:
    return datetime.now().date()


def range_dates(days: int, end: date | None = None):
    end = end or today_date()
    return [end - timedelta(days=i) for i in range(days - 1, -1, -1)]


def date_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")