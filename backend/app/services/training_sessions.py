from datetime import date, datetime


def can_resume_session(session, *, plan_id: int, plan_day_id: int, session_date: date) -> bool:
    actual_date = session.session_date.date() if isinstance(session.session_date, datetime) else session.session_date
    return (
        session.plan_id == plan_id
        and session.plan_day_id == plan_day_id
        and actual_date == session_date
    )
