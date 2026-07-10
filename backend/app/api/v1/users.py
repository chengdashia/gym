from datetime import datetime, time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import (
    DietRecord,
    FoodRecognitionLog,
    NutritionGoal,
    OperationLog,
    TrainingPlan,
    TrainingSession,
    UploadedFile,
    User,
    UserCustomExercise,
    UserCustomFood,
    UserProfile,
    UserReminder,
    WeightRecord,
)
from app.schemas import (
    AgreementConfirmIn,
    NutritionGoalIn,
    NutritionGoalOut,
    NutritionRecommendOut,
    RemindersOut,
    RemindersUpdateIn,
    UserMeIn,
    UserMeOut,
    UserProfileOut,
)
from app.services.recommend import recommend
from app.services.account_data import anonymize_account, clear_personal_data
from app.services.uploads import delete_local_file


router = APIRouter(prefix="/users", tags=["users"])


def _upsert_today_weight(db: Session, user_id: int, weight_kg) -> WeightRecord:
    now = datetime.now()
    start = datetime.combine(now.date(), time.min)
    end = datetime.combine(now.date(), time.max)
    record = db.query(WeightRecord).filter(
        WeightRecord.user_id == user_id,
        WeightRecord.deleted_at.is_(None),
        WeightRecord.record_date >= start,
        WeightRecord.record_date <= end,
    ).order_by(WeightRecord.record_time.desc(), WeightRecord.id.desc()).first()
    if record:
        record.weight_kg = weight_kg
        record.record_time = now.time().replace(microsecond=0)
    else:
        record = WeightRecord(
            user_id=user_id,
            record_date=datetime.combine(now.date(), time.min),
            record_time=now.time().replace(microsecond=0),
            weight_kg=weight_kg,
            note="基础资料同步",
        )
        db.add(record)
    return record


def _to_user_me(user: User, profile: UserProfile | None) -> dict:
    profile_out = UserProfileOut.model_validate(profile).model_dump() if profile else None
    return {
        "id": user.id,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "phone": user.phone,
        "is_member": bool(user.is_member),
        "member_expired_at": user.member_expired_at,
        "agreement_confirmed": user.agreement_confirmed_at is not None,
        "agreement_version": user.agreement_version,
        "agreement_confirmed_at": user.agreement_confirmed_at,
        "profile": profile_out,
    }


def _apply_latest_weight(db: Session, user_id: int, profile: UserProfile | None) -> None:
    if not profile:
        return
    latest = db.query(WeightRecord).filter(
        WeightRecord.user_id == user_id,
        WeightRecord.deleted_at.is_(None),
    ).order_by(WeightRecord.record_date.desc(), WeightRecord.record_time.desc(), WeightRecord.id.desc()).first()
    if latest:
        profile.current_weight_kg = latest.weight_kg


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    _apply_latest_weight(db, user.id, profile)
    return ok(_to_user_me(user, profile))


@router.put("/me")
def update_me(
    body: UserMeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url

    if body.profile is not None:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
        p = body.profile
        if p.gender is not None:
            profile.gender = p.gender
        if p.age is not None:
            profile.age = p.age
        if p.height_cm is not None:
            profile.height_cm = p.height_cm
        if p.current_weight_kg is not None:
            profile.current_weight_kg = p.current_weight_kg
            _upsert_today_weight(db, user.id, p.current_weight_kg)
        if p.target_weight_kg is not None:
            profile.target_weight_kg = p.target_weight_kg
        if p.fitness_goal is not None:
            profile.fitness_goal = p.fitness_goal
        if p.training_frequency is not None:
            profile.training_frequency = p.training_frequency

    db.add(OperationLog(user_id=user.id, action="users.update_me"))
    db.commit()
    db.refresh(user)
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    _apply_latest_weight(db, user.id, profile)
    return ok(_to_user_me(user, profile))


@router.post("/agreement-confirm")
def agreement_confirm(
    body: AgreementConfirmIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.agreement_version = body.agreement_version
    user.agreement_confirmed_at = datetime.utcnow()
    db.add(OperationLog(
        user_id=user.id, action="users.agreement_confirm",
        detail_json={"agreement_version": body.agreement_version, "privacy_version": body.privacy_version},
    ))
    db.commit()
    return ok({"agreement_confirmed": True})


# ---- nutrition goal ----
def _goal_dict(g: NutritionGoal) -> dict:
    return {
        "user_id": g.user_id,
        "calories_kcal": g.calories_kcal,
        "carbs_g": g.carbs_g,
        "protein_g": g.protein_g,
        "fat_g": g.fat_g,
        "source": g.source,
    }


@router.get("/nutrition-goal")
def get_nutrition_goal(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    g = db.query(NutritionGoal).filter(NutritionGoal.user_id == user.id).first()
    if not g:
        return ok(None)
    return ok(_goal_dict(g))


@router.put("/nutrition-goal")
def put_nutrition_goal(
    body: NutritionGoalIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy.dialects.mysql import insert as mysql_insert
    stmt = mysql_insert(NutritionGoal).values(
        user_id=user.id,
        calories_kcal=body.calories_kcal,
        carbs_g=body.carbs_g,
        protein_g=body.protein_g,
        fat_g=body.fat_g,
        source="manual",
    )
    stmt = stmt.on_duplicate_key_update(
        calories_kcal=stmt.inserted.calories_kcal,
        carbs_g=stmt.inserted.carbs_g,
        protein_g=stmt.inserted.protein_g,
        fat_g=stmt.inserted.fat_g,
        source="manual",
    )
    db.execute(stmt)
    db.add(OperationLog(user_id=user.id, action="users.nutrition_goal.update"))
    db.commit()
    g = db.query(NutritionGoal).filter(NutritionGoal.user_id == user.id).first()
    return ok(_goal_dict(g))


@router.post("/nutrition-goal/recommend", response_model=None)
def recommend_nutrition_goal(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    p = None
    if profile:
        p = {
            "gender": profile.gender,
            "age": profile.age,
            "height_cm": float(profile.height_cm) if profile.height_cm is not None else None,
            "current_weight_kg": float(profile.current_weight_kg) if profile.current_weight_kg is not None else None,
            "target_weight_kg": float(profile.target_weight_kg) if profile.target_weight_kg is not None else None,
            "fitness_goal": profile.fitness_goal,
            "training_frequency": profile.training_frequency,
        }
    r = recommend(p)
    return ok(r)


# ---- reminders ----
VALID_TYPES = {"diet", "training", "weight"}


@router.get("/reminders")
def get_reminders(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(UserReminder).filter(UserReminder.user_id == user.id).all()
    items = []
    by_type = {r.reminder_type: r for r in rows}
    for t in ("diet", "training", "weight"):
        r = by_type.get(t)
        if not r:
            items.append({"reminder_type": t, "enabled": False, "reminder_time": None, "weekdays": None})
            continue
        items.append({
            "reminder_type": r.reminder_type,
            "enabled": bool(r.enabled),
            "reminder_time": r.reminder_time.strftime("%H:%M") if r.reminder_time else None,
            "weekdays": r.weekdays,
        })
    return ok({"items": items})


@router.put("/reminders")
def put_reminders(
    body: RemindersUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for it in body.items:
        if it.reminder_type not in VALID_TYPES:
            raise BizException(40001, f"不支持的 reminder_type: {it.reminder_type}")
        r = db.query(UserReminder).filter(
            UserReminder.user_id == user.id, UserReminder.reminder_type == it.reminder_type
        ).first()
        if not r:
            r = UserReminder(user_id=user.id, reminder_type=it.reminder_type)
            db.add(r)
        r.enabled = 1 if it.enabled else 0
        if it.reminder_time:
            try:
                hh, mm = it.reminder_time.split(":")
                r.reminder_time = time(int(hh), int(mm))
            except Exception:
                raise BizException(40001, "reminder_time 格式错误，应为 HH:MM")
        else:
            r.reminder_time = None
        r.weekdays = it.weekdays
    db.add(OperationLog(user_id=user.id, action="users.reminders.update"))
    db.commit()
    rows = db.query(UserReminder).filter(UserReminder.user_id == user.id).all()
    items = []
    by_type = {r.reminder_type: r for r in rows}
    for t in ("diet", "training", "weight"):
        r = by_type.get(t)
        items.append({
            "reminder_type": t,
            "enabled": bool(r.enabled) if r else False,
            "reminder_time": r.reminder_time.strftime("%H:%M") if r and r.reminder_time else None,
            "weekdays": r.weekdays if r else None,
        })
    return ok({"items": items})


# ---- delete data / cancel account ----
@router.post("/delete-data")
def delete_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = user.id
    uploaded_paths = clear_personal_data(db, user)
    db.add(OperationLog(user_id=uid, action="users.clear_fitness_data"))
    db.commit()
    for path in uploaded_paths:
        delete_local_file(path)
    return ok({"deleted": True})


@router.post("/cancel-account")
def cancel_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = user.id
    uploaded_paths = clear_personal_data(db, user)
    anonymize_account(user)
    db.add(OperationLog(user_id=uid, action="users.cancel_account"))
    db.commit()
    for path in uploaded_paths:
        delete_local_file(path)
    return ok({"cancelled": True})
