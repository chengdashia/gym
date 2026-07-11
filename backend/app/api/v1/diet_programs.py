from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok, utcnow
from app.models import (
    DietPreference, DietProgramStage, DietProgramTemplate, DietRecord,
    NutritionGoal, User, UserDietProgram, UserProfile, WeightRecord,
)
from app.schemas import DietEligibilityIn, DietPreferenceIn, DietProgramCreateIn, DietProgramEvaluateIn
from app.services.diet_eligibility import check_eligibility
from app.services.diet_program_engine import DietSafetyError, create_initial_targets, estimate_tdee, evaluate_532
from app.services.diet_templates import get_active_templates


router = APIRouter(prefix="/diet-programs", tags=["diet-programs"])


def _preference_data(row: DietPreference) -> dict:
    rules = row.preference_rules_json or {}
    body = DietPreferenceIn(meal_count=row.meal_count, allergens=row.allergens_json, **rules)
    return {**body.model_dump(mode="json"), "snapshot": body.to_snapshot()}


@router.get("/templates")
def list_templates(user: User = Depends(get_current_user)):
    return ok({"items": get_active_templates()})


@router.post("/eligibility")
def eligibility(body: DietEligibilityIn, user: User = Depends(get_current_user)):
    return ok(check_eligibility(body.model_dump()).__dict__)


@router.get("/preferences")
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(DietPreference).filter(DietPreference.user_id == user.id).first()
    return ok(_preference_data(row) if row else None)


@router.put("/preferences")
def put_preferences(
    body: DietPreferenceIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(DietPreference).filter(DietPreference.user_id == user.id).first()
    if row is None:
        row = DietPreference(user_id=user.id, meal_count=body.meal_count, allergens_json=[])
        db.add(row)
    values = body.model_dump(mode="json")
    row.meal_count = values.pop("meal_count")
    row.allergens_json = values.pop("allergens")
    row.preference_rules_json = values
    db.commit()
    db.refresh(row)
    return ok(_preference_data(row))


def _program_template(db: Session, code: str) -> DietProgramTemplate:
    data = next((item for item in get_active_templates() if item["code"] == code), None)
    if data is None:
        raise BizException(40401, "饮食方案不存在", 404)
    row = db.query(DietProgramTemplate).filter(
        DietProgramTemplate.code == code, DietProgramTemplate.version == data["version"],
    ).first()
    if row is None:
        row = DietProgramTemplate(
            code=data["code"], name=data["name"], version=data["version"],
            description=data["description"], rules_json=data["rules"],
            applicability_json=data["applicability"], status="active",
        )
        db.add(row)
        db.flush()
    return row


def _program_or_404(db: Session, user_id: int, program_id: int) -> UserDietProgram:
    row = db.query(UserDietProgram).filter(
        UserDietProgram.id == program_id, UserDietProgram.user_id == user_id,
    ).first()
    if row is None:
        raise BizException(40401, "饮食方案不存在", 404)
    return row


def _stage_dict(stage: DietProgramStage) -> dict:
    return {
        "id": stage.id, "stage_number": stage.stage_number, "status": stage.status,
        "start_date": stage.start_date, "end_date": stage.end_date,
        "calories_kcal": stage.calories_kcal, "carbs_g": stage.carbs_g,
        "protein_g": stage.protein_g, "fat_g": stage.fat_g,
        "observation_days": stage.observation_days,
        "evaluation_snapshot_json": stage.evaluation_snapshot_json,
    }


@router.post("")
def create_program(
    body: DietProgramCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Task 5 only has an engine for the carb-taper program.  Rejecting the
    # other templates is intentional until their target-generation contracts
    # (16:8 window allocation, keto net-carbs/fibre) are implemented.
    if body.template_code != "carb_taper_532":
        raise BizException(40039, "当前版本仅支持创建 532 碳水渐降方案；其他方案需使用各自的目标生成规则")
    eligibility_result = check_eligibility(body.eligibility.model_dump())
    if not eligibility_result.eligible:
        raise BizException(40031, "当前健康情况不适合创建自动饮食方案，请仅使用普通记录并咨询医生或营养师")
    preference = db.query(DietPreference).filter(DietPreference.user_id == user.id).first()
    if preference is None:
        raise BizException(40032, "请先完成饮食偏好设置")
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    tdee = estimate_tdee(profile, body.activity_level) if profile else {
        "status": "needs_profile", "missing_fields": ["gender", "age", "height_cm", "current_weight_kg"],
    }
    if isinstance(tdee, dict):
        message = "请补充完整的性别、年龄、身高和当前体重后再创建方案"
        if tdee["status"] == "unsupported_profile":
            message = "当前性别资料无法使用 Mifflin–St Jeor 公式估算，请咨询专业人员后使用普通记录"
        raise BizException(40033, message, data=tdee)
    try:
        targets = create_initial_targets(body.calories_kcal, ratio=body.macro_ratio)
    except DietSafetyError as exc:
        raise BizException(40034, str(exc)) from exc
    template = _program_template(db, body.template_code)
    program = UserDietProgram(
        user_id=user.id, template_id=template.id, template_version=template.version, status="pending",
        eligibility_snapshot_json={**body.eligibility.model_dump(), "eligible": True},
        preference_snapshot_json=_preference_data(preference)["snapshot"],
    )
    db.add(program)
    db.flush()
    stage = DietProgramStage(program_id=program.id, stage_number=1, status="pending", observation_days=14, **targets)
    db.add(stage)
    db.commit()
    db.refresh(program)
    db.refresh(stage)
    return ok({"id": program.id, "status": program.status, "estimated_tdee_kcal": tdee, "stage": _stage_dict(stage)})


@router.post("/{program_id}/confirm")
def confirm_program(
    program_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Serialising on the user row also serialises first-time NutritionGoal
    # creation, avoiding a unique-key race between duplicate confirms.
    db.query(User).filter(User.id == user.id).with_for_update().one()
    program = db.query(UserDietProgram).filter(
        UserDietProgram.id == program_id, UserDietProgram.user_id == user.id,
    ).with_for_update().first()
    if program is None:
        raise BizException(40401, "饮食方案不存在", 404)
    stage = db.query(DietProgramStage).filter(
        DietProgramStage.program_id == program.id, DietProgramStage.stage_number == 1,
    ).with_for_update().first()
    if program.status == "active":
        if stage is None:
            raise BizException(40036, "初始阶段不存在")
        return ok({"id": program.id, "status": program.status, "stage": _stage_dict(stage)})
    if program.status != "pending":
        raise BizException(40035, "只有待确认方案可以确认")
    existing_active = db.query(UserDietProgram.id).filter(
        UserDietProgram.user_id == user.id, UserDietProgram.status == "active",
        UserDietProgram.id != program.id,
    ).first()
    if existing_active:
        raise BizException(40040, "请先暂停或结束当前饮食方案")
    if stage is None or stage.status != "pending":
        raise BizException(40036, "待确认初始阶段不存在")
    program.status, program.start_date = "active", date.today()
    stage.status, stage.start_date, stage.confirmed_at = "active", date.today(), utcnow()
    goal = db.query(NutritionGoal).filter(NutritionGoal.user_id == user.id).first()
    if goal is None:
        goal = NutritionGoal(user_id=user.id, source="diet_program")
        db.add(goal)
    goal.calories_kcal, goal.carbs_g = stage.calories_kcal, stage.carbs_g
    goal.protein_g, goal.fat_g, goal.source = stage.protein_g, stage.fat_g, "diet_program"
    db.commit()
    return ok({"id": program.id, "status": program.status, "stage": _stage_dict(stage)})


def _daily_weights(db: Session, user_id: int, start: date, end: date) -> list[Decimal]:
    rows = db.query(WeightRecord).filter(
        WeightRecord.user_id == user_id, WeightRecord.deleted_at.is_(None),
        WeightRecord.record_date >= datetime.combine(start, time.min),
        WeightRecord.record_date <= datetime.combine(end, time.max),
    ).order_by(WeightRecord.record_date.desc(), WeightRecord.record_time.desc(), WeightRecord.id.desc()).all()
    by_day: dict[date, Decimal] = {}
    for row in rows:
        by_day.setdefault(row.record_date.date(), row.weight_kg)
    return list(by_day.values())


def _adherence_rate(db: Session, user_id: int, start: date, end: date, target_calories: Decimal) -> Decimal:
    rows = db.query(DietRecord).filter(
        DietRecord.user_id == user_id, DietRecord.deleted_at.is_(None),
        DietRecord.record_date >= datetime.combine(start, time.min),
        DietRecord.record_date <= datetime.combine(end, time.max),
    ).all()
    totals: dict[date, Decimal] = {}
    for row in rows:
        day = row.record_date.date()
        totals[day] = totals.get(day, Decimal("0")) + row.calories_kcal
    on_target = sum(Decimal("1") for total in totals.values() if target_calories * Decimal("0.8") <= total <= target_calories * Decimal("1.2"))
    return on_target / Decimal("7")


@router.post("/{program_id}/evaluate")
def evaluate_program(
    program_id: int,
    body: DietProgramEvaluateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    program = _program_or_404(db, user.id, program_id)
    if program.status != "active":
        raise BizException(40037, "只有进行中的方案可以评估")
    if program.template.code != "carb_taper_532":
        raise BizException(40041, "当前方案不适用 532 碳水渐降评估")
    stage = db.query(DietProgramStage).filter(
        DietProgramStage.program_id == program.id, DietProgramStage.status == "active",
    ).order_by(DietProgramStage.stage_number.desc()).first()
    if stage is None:
        raise BizException(40038, "当前阶段不存在")
    current_start = body.end_date - timedelta(days=6)
    previous_start = current_start - timedelta(days=7)
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    result = evaluate_532(
        previous_weights=_daily_weights(db, user.id, previous_start, current_start - timedelta(days=1)),
        current_weights=_daily_weights(db, user.id, current_start, body.end_date),
        adherence_rate=_adherence_rate(db, user.id, current_start, body.end_date, stage.calories_kcal),
        target_loss_rate=body.target_loss_rate,
        stage=_stage_dict(stage), observation_days=(body.end_date - stage.start_date).days + 1 if stage.start_date else 0,
        target_weight_kg=profile.target_weight_kg if profile else None, reduction_g=body.reduction_g,
    )
    # Evaluation never changes the active target; confirmation creates any next stage.
    stage.evaluation_snapshot_json = result.to_dict()
    db.commit()
    return ok(result.to_dict())
