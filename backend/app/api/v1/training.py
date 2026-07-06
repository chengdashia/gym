from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import (
    Exercise,
    OperationLog,
    TrainingPlan,
    TrainingPlanDay,
    TrainingPlanExercise,
    TrainingSession,
    TrainingSessionExercise,
    TrainingSessionSet,
    TrainingTemplate,
    TrainingTemplateDay,
    TrainingTemplateExercise,
    User,
    UserCustomExercise,
)
from app.schemas import (
    PlanDayIn,
    PlanDayOut,
    PlanExerciseIn,
    PlanExerciseOut,
    PlanIn,
    PlanListOut,
    PlanOut,
    SessionCreateIn,
    SessionExerciseOut,
    SessionOut,
    SessionSetIn,
    SessionUpdateIn,
    TemplateDayOut,
    TemplateExerciseOut,
    TemplateListOut,
    TemplateOut,
    TrainingTodayOut,
)
from app.services.schedule import resolve_today_day, advance_sequence_plan
from app.utils.date import date_str


router = APIRouter(prefix="/training", tags=["training"])


# ================== Templates ==================
def _tpl_day_to_dict(d: TrainingTemplateDay) -> dict:
    return {
        "id": d.id,
        "day_index": d.day_index,
        "day_name": d.day_name,
        "is_rest_day": bool(d.is_rest_day),
        "weekday": d.weekday,
        "exercises": [
            {
                "id": te.id,
                "exercise_id": te.exercise_id,
                "name": te.exercise.name,
                "body_part": te.exercise.body_part,
                "sort_order": te.sort_order,
                "target_sets": te.target_sets,
                "target_reps": te.target_reps,
                "target_weight_kg": te.target_weight_kg,
                "rest_seconds": te.rest_seconds,
                "note": te.note,
            } for te in sorted(d.exercises, key=lambda x: x.sort_order or 0)
        ],
    }


@router.get("/templates")
def list_templates(db: Session = Depends(get_db)):
    tpls = db.query(TrainingTemplate).filter(TrainingTemplate.status == "active").order_by(TrainingTemplate.id.asc()).all()
    items = [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "split_type": t.split_type,
            "difficulty": t.difficulty,
            "goal": t.goal,
            "days": [_tpl_day_to_dict(d) for d in sorted(t.days, key=lambda x: x.day_index)],
        } for t in tpls
    ]
    return ok({"items": items})


@router.get("/templates/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    t = db.query(TrainingTemplate).filter(TrainingTemplate.id == template_id).first()
    if not t:
        raise BizException(40401, "模板不存在")
    return ok({
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "split_type": t.split_type,
        "difficulty": t.difficulty,
        "goal": t.goal,
        "days": [_tpl_day_to_dict(d) for d in sorted(t.days, key=lambda x: x.day_index)],
    })


# ================== Plans ==================
def _ensure_exercise(db: Session, user_id: int, source: str, exercise_id: Optional[int], custom_id: Optional[int]):
    if source == "custom":
        e = db.query(UserCustomExercise).filter(
            UserCustomExercise.id == custom_id, UserCustomExercise.user_id == user_id,
            UserCustomExercise.deleted_at.is_(None),
        ).first()
    else:
        e = db.query(Exercise).filter(Exercise.id == exercise_id, Exercise.is_system == 1).first()
    if not e:
        raise BizException(40401, "动作不存在")
    return e


def _plan_day_to_dict(d: TrainingPlanDay) -> dict:
    return {
        "id": d.id,
        "day_index": d.day_index,
        "day_name": d.day_name,
        "is_rest_day": bool(d.is_rest_day),
        "weekday": d.weekday,
        "sort_order": d.sort_order,
        "exercises": [
            {
                "id": pe.id,
                "exercise_source": pe.exercise_source,
                "exercise_id": pe.exercise_id,
                "custom_exercise_id": pe.custom_exercise_id,
                "exercise_name_snapshot": pe.exercise_name_snapshot,
                "body_part_snapshot": pe.body_part_snapshot,
                "sort_order": pe.sort_order,
                "target_sets": pe.target_sets,
                "target_reps": pe.target_reps,
                "target_weight_kg": pe.target_weight_kg,
                "rest_seconds": pe.rest_seconds,
                "note": pe.note,
            } for pe in sorted(d.exercises, key=lambda x: x.sort_order or 0)
        ],
    }


def _plan_to_dict(p: TrainingPlan, include_days: bool = True) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "schedule_type": p.schedule_type,
        "source_template_id": p.source_template_id,
        "current_day_index": p.current_day_index,
        "is_active": bool(p.is_active),
        "status": p.status,
        "days": [_plan_day_to_dict(d) for d in sorted(p.days, key=lambda x: x.sort_order or 0)] if include_days else [],
    }


@router.get("/plans")
def list_plans(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(TrainingPlan).filter(
        TrainingPlan.user_id == user.id, TrainingPlan.deleted_at.is_(None)
    ).order_by(TrainingPlan.id.desc()).all()
    return ok({"items": [_plan_to_dict(p) for p in rows]})


@router.post("/plans")
def create_plan(body: PlanIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = TrainingPlan(
        user_id=user.id,
        name=body.name,
        schedule_type=body.schedule_type,
        source_template_id=body.source_template_id,
        current_day_index=1,
        is_active=1,
    )
    db.add(plan)
    db.flush()
    for d in body.days:
        day = TrainingPlanDay(
            plan_id=plan.id, day_index=d.day_index, day_name=d.day_name,
            is_rest_day=1 if d.is_rest_day else 0, weekday=d.weekday,
            sort_order=d.sort_order if d.sort_order else d.day_index,
        )
        db.add(day)
        db.flush()
        for pe_in in d.exercises:
            ex = _ensure_exercise(db, user.id, pe_in.exercise_source, pe_in.exercise_id, pe_in.custom_exercise_id)
            pe = TrainingPlanExercise(
                plan_day_id=day.id,
                exercise_source=pe_in.exercise_source,
                exercise_id=pe_in.exercise_id if pe_in.exercise_source == "system" else None,
                custom_exercise_id=pe_in.custom_exercise_id if pe_in.exercise_source == "custom" else None,
                exercise_name_snapshot=ex.name,
                body_part_snapshot=ex.body_part,
                sort_order=pe_in.sort_order,
                target_sets=pe_in.target_sets,
                target_reps=pe_in.target_reps,
                target_weight_kg=pe_in.target_weight_kg,
                rest_seconds=pe_in.rest_seconds,
                note=pe_in.note,
            )
            db.add(pe)
    db.add(OperationLog(user_id=user.id, action="training.plan.create", target_type="plan", target_id=plan.id))
    db.commit()
    db.refresh(plan)
    return ok(_plan_to_dict(plan))


@router.get("/plans/{plan_id}")
def get_plan(plan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(TrainingPlan).filter(
        TrainingPlan.id == plan_id, TrainingPlan.user_id == user.id, TrainingPlan.deleted_at.is_(None)
    ).first()
    if not p:
        raise BizException(40401, "计划不存在")
    return ok(_plan_to_dict(p))


@router.put("/plans/{plan_id}")
def update_plan(
    plan_id: int,
    body: PlanIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.query(TrainingPlan).filter(
        TrainingPlan.id == plan_id, TrainingPlan.user_id == user.id, TrainingPlan.deleted_at.is_(None)
    ).first()
    if not p:
        raise BizException(40401, "计划不存在")
    p.name = body.name
    p.schedule_type = body.schedule_type
    p.source_template_id = body.source_template_id
    # Re-create days + exercises
    db.query(TrainingPlanExercise).filter(
        TrainingPlanExercise.plan_day_id.in_([d.id for d in p.days])
    ).delete(synchronize_session=False)
    db.query(TrainingPlanDay).filter(TrainingPlanDay.plan_id == p.id).delete()

    for d in body.days:
        day = TrainingPlanDay(
            plan_id=p.id, day_index=d.day_index, day_name=d.day_name,
            is_rest_day=1 if d.is_rest_day else 0, weekday=d.weekday,
            sort_order=d.sort_order if d.sort_order else d.day_index,
        )
        db.add(day)
        db.flush()
        for pe_in in d.exercises:
            ex = _ensure_exercise(db, user.id, pe_in.exercise_source, pe_in.exercise_id, pe_in.custom_exercise_id)
            pe = TrainingPlanExercise(
                plan_day_id=day.id,
                exercise_source=pe_in.exercise_source,
                exercise_id=pe_in.exercise_id if pe_in.exercise_source == "system" else None,
                custom_exercise_id=pe_in.custom_exercise_id if pe_in.exercise_source == "custom" else None,
                exercise_name_snapshot=ex.name,
                body_part_snapshot=ex.body_part,
                sort_order=pe_in.sort_order,
                target_sets=pe_in.target_sets,
                target_reps=pe_in.target_reps,
                target_weight_kg=pe_in.target_weight_kg,
                rest_seconds=pe_in.rest_seconds,
                note=pe_in.note,
            )
            db.add(pe)
    db.add(OperationLog(user_id=user.id, action="training.plan.update", target_type="plan", target_id=p.id))
    db.commit()
    db.refresh(p)
    return ok(_plan_to_dict(p))


@router.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(TrainingPlan).filter(
        TrainingPlan.id == plan_id, TrainingPlan.user_id == user.id, TrainingPlan.deleted_at.is_(None)
    ).first()
    if not p:
        raise BizException(40401, "计划不存在")
    p.deleted_at = datetime.utcnow()
    p.is_active = 0
    db.add(OperationLog(user_id=user.id, action="training.plan.delete", target_type="plan", target_id=p.id))
    db.commit()
    return ok({"deleted": plan_id})


# ================== Today ==================
@router.get("/today")
def today(
    date: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = datetime.strptime(date, "%Y-%m-%d").date()
    active_plan = db.query(TrainingPlan).filter(
        TrainingPlan.user_id == user.id, TrainingPlan.deleted_at.is_(None),
        TrainingPlan.is_active == 1,
    ).order_by(TrainingPlan.id.desc()).first()

    incomplete = db.query(TrainingSession).filter(
        TrainingSession.user_id == user.id,
        TrainingSession.deleted_at.is_(None),
        TrainingSession.status.in_(("in_progress", "paused")),
    ).order_by(TrainingSession.started_at.desc()).first()

    out = {
        "date": date_str(d),
        "plan_id": active_plan.id if active_plan else None,
        "plan": _plan_to_dict(active_plan) if active_plan else None,
        "today_day": None,
        "is_rest_day": False,
        "incomplete_session": _session_to_dict(incomplete) if incomplete else None,
    }

    if active_plan:
        today_day = resolve_today_day(db, active_plan, d)
        if today_day:
            out["today_day"] = _plan_day_to_dict(today_day)
            out["is_rest_day"] = bool(today_day.is_rest_day)
        else:
            out["is_rest_day"] = True
    return ok(out)


# ================== Sessions ==================
def _session_to_dict(s: TrainingSession) -> dict:
    return {
        "id": s.id,
        "plan_id": s.plan_id,
        "plan_day_id": s.plan_day_id,
        "session_date": s.session_date.date(),
        "session_name": s.session_name,
        "status": s.status,
        "started_at": s.started_at,
        "ended_at": s.ended_at,
        "duration_seconds": s.duration_seconds,
        "total_volume": s.total_volume,
        "note": s.note,
        "exercises": [_session_exercise_to_dict(e) for e in sorted(s.exercises, key=lambda x: x.sort_order or 0)],
    }


def _session_exercise_to_dict(e: TrainingSessionExercise) -> dict:
    return {
        "id": e.id,
        "exercise_name_snapshot": e.exercise_name_snapshot,
        "body_part_snapshot": e.body_part_snapshot,
        "sort_order": e.sort_order,
        "planned_sets": e.planned_sets,
        "completed_sets": e.completed_sets,
        "rest_seconds": e.rest_seconds,
        "note": e.note,
        "sets": [
            {
                "id": st.id,
                "set_index": st.set_index,
                "target_reps": st.target_reps,
                "target_weight_kg": st.target_weight_kg,
                "actual_reps": st.actual_reps,
                "actual_weight_kg": st.actual_weight_kg,
                "completed": bool(st.completed),
                "completed_at": st.completed_at,
                "volume": st.volume,
                "note": st.note,
            } for st in sorted(e.sets, key=lambda x: x.set_index)
        ],
    }


@router.post("/sessions")
def create_session(body: SessionCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.query(TrainingPlan).filter(
        TrainingPlan.id == body.plan_id, TrainingPlan.user_id == user.id, TrainingPlan.deleted_at.is_(None)
    ).first()
    if not plan:
        raise BizException(40401, "计划不存在")
    day = db.query(TrainingPlanDay).filter(
        TrainingPlanDay.id == body.plan_day_id, TrainingPlanDay.plan_id == plan.id
    ).first()
    if not day:
        raise BizException(40401, "训练日不存在")

    s = TrainingSession(
        user_id=user.id, plan_id=plan.id, plan_day_id=day.id,
        session_date=datetime.combine(body.session_date, datetime.min.time()),
        session_name=day.day_name,
        status="in_progress",
        started_at=datetime.utcnow(),
    )
    db.add(s)
    db.flush()

    for pe in sorted(day.exercises, key=lambda x: x.sort_order or 0):
        se = TrainingSessionExercise(
            session_id=s.id,
            exercise_name_snapshot=pe.exercise_name_snapshot,
            body_part_snapshot=pe.body_part_snapshot,
            sort_order=pe.sort_order,
            planned_sets=pe.target_sets,
            completed_sets=0,
            rest_seconds=pe.rest_seconds,
            note=pe.note,
        )
        db.add(se)
        db.flush()
        for i in range(1, pe.target_sets + 1):
            st = TrainingSessionSet(
                session_exercise_id=se.id,
                set_index=i,
                target_reps=pe.target_reps,
                target_weight_kg=pe.target_weight_kg,
                completed=0,
                volume=0,
            )
            db.add(st)
    db.add(OperationLog(user_id=user.id, action="training.session.create", target_type="session", target_id=s.id))
    db.commit()
    db.refresh(s)
    return ok(_session_to_dict(s))


@router.get("/sessions")
def list_sessions_history(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(TrainingSession).filter(
        TrainingSession.user_id == user.id, TrainingSession.deleted_at.is_(None),
    )
    if start_date:
        sd = datetime.strptime(start_date, "%Y-%m-%d")
        q = q.filter(TrainingSession.session_date >= sd)
    if end_date:
        ed = datetime.strptime(end_date, "%Y-%m-%d")
        # include the entire end_date day
        q = q.filter(TrainingSession.session_date <= ed.replace(hour=23, minute=59, second=59))
    q = q.order_by(TrainingSession.started_at.desc()).limit(200)
    return ok({"items": [_session_to_dict(s) for s in q.all()]})


@router.get("/sessions/{session_id}")
def get_session(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(TrainingSession).filter(
        TrainingSession.id == session_id, TrainingSession.user_id == user.id,
        TrainingSession.deleted_at.is_(None),
    ).first()
    if not s:
        raise BizException(40401, "训练记录不存在")
    return ok(_session_to_dict(s))


@router.put("/sessions/{session_id}")
def update_session(
    session_id: int, body: SessionUpdateIn,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    s = db.query(TrainingSession).filter(
        TrainingSession.id == session_id, TrainingSession.user_id == user.id,
        TrainingSession.deleted_at.is_(None),
    ).first()
    if not s:
        raise BizException(40401, "训练记录不存在")
    if s.status not in ("in_progress", "paused"):
        raise BizException(40901, "该训练已结束，不能更新")

    if body.status:
        s.status = body.status

    for ex_in in body.exercises:
        se = db.query(TrainingSessionExercise).filter(
            TrainingSessionExercise.id == ex_in.session_exercise_id,
            TrainingSessionExercise.session_id == s.id,
        ).first()
        if not se:
            continue
        completed = 0
        for set_in in ex_in.sets:
            row = None
            if set_in.set_id:
                row = db.query(TrainingSessionSet).filter(
                    TrainingSessionSet.id == set_in.set_id,
                    TrainingSessionSet.session_exercise_id == se.id,
                ).first()
            if not row and set_in.set_index:
                row = db.query(TrainingSessionSet).filter(
                    TrainingSessionSet.session_exercise_id == se.id,
                    TrainingSessionSet.set_index == set_in.set_index,
                ).first()
            if not row:
                continue
            if set_in.actual_reps is not None:
                row.actual_reps = set_in.actual_reps
            if set_in.actual_weight_kg is not None:
                row.actual_weight_kg = set_in.actual_weight_kg
            if set_in.completed:
                row.completed = 1
                row.completed_at = datetime.utcnow()
                try:
                    weight = float(row.actual_weight_kg or 0)
                except Exception:
                    weight = 0.0
                reps = int(row.actual_reps or 0)
                row.volume = weight * reps
                completed += 1
        se.completed_sets = completed

    # Recompute session volume
    total = 0
    for se in s.exercises:
        for st in se.sets:
            try:
                total += float(st.volume or 0)
            except Exception:
                pass
    s.total_volume = total
    db.add(OperationLog(user_id=user.id, action="training.session.update", target_type="session", target_id=s.id))
    db.commit()
    db.refresh(s)
    return ok(_session_to_dict(s))


@router.post("/sessions/{session_id}/finish")
def finish_session(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(TrainingSession).filter(
        TrainingSession.id == session_id, TrainingSession.user_id == user.id,
        TrainingSession.deleted_at.is_(None),
    ).first()
    if not s:
        raise BizException(40401, "训练记录不存在")
    if s.status not in ("in_progress", "paused"):
        raise BizException(40901, "该训练已结束")

    s.ended_at = datetime.utcnow()
    s.duration_seconds = int((s.ended_at - s.started_at).total_seconds())
    s.status = "completed"
    # advance sequence plans
    if s.plan_id:
        plan = db.query(TrainingPlan).filter(TrainingPlan.id == s.plan_id).first()
        if plan and plan.schedule_type == "sequence" and plan.is_active:
            advance_sequence_plan(db, plan)

    db.add(OperationLog(user_id=user.id, action="training.session.finish", target_type="session", target_id=s.id))
    db.commit()
    db.refresh(s)
    return ok(_session_to_dict(s))


@router.post("/sessions/{session_id}/cancel")
def cancel_session(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(TrainingSession).filter(
        TrainingSession.id == session_id, TrainingSession.user_id == user.id,
        TrainingSession.deleted_at.is_(None),
    ).first()
    if not s:
        raise BizException(40401, "训练记录不存在")
    s.status = "cancelled"
    s.ended_at = datetime.utcnow()
    s.duration_seconds = int((s.ended_at - s.started_at).total_seconds())
    db.add(OperationLog(user_id=user.id, action="training.session.cancel", target_type="session", target_id=s.id))
    db.commit()
    return ok(_session_to_dict(s))