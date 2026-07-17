from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok, utcnow
from app.models import (
    DietPreference, DietProgramStage, DietProgramTemplate, DietRecord, Food,
    MealPlanDay, MealPlanItem, MealPlanMeal, NutritionGoal, User, UserDietProgram, UserProfile, WeightRecord,
)
from app.schemas import DietEligibilityIn, DietPreferenceIn, DietProgramCreateIn, DietProgramEvaluateIn, MealPlanItemAmountIn, MealPlanItemReplaceIn, MealPlanMealReplaceIn
from app.services.diet_eligibility import check_eligibility
from app.services.diet_program_engine import (
    DietSafetyError, TargetLossRateError, create_program_initial_targets, estimate_tdee,
    evaluate_532, validate_target_loss_rate,
)
from app.services.diet_templates import get_active_templates
from app.services.meal_planner import MealPlanConflict, generate_seven_day_plan, replace_item, validate_meal_plan
from app.services.feature_access import experimental_features


def require_diet_program_access(user: User = Depends(get_current_user)) -> None:
    if "diet_programs" not in experimental_features(user.id):
        raise BizException(40301, "该实验功能尚未向当前账号开放", 403)


router = APIRouter(
    prefix="/diet-programs", tags=["diet-programs"],
    dependencies=[Depends(require_diet_program_access)],
)
meal_plan_router = APIRouter(
    prefix="/meal-plan", tags=["meal-plan"],
    dependencies=[Depends(require_diet_program_access)],
)


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


@router.get("/active")
def get_active_program(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    program = db.query(UserDietProgram).filter(
        UserDietProgram.user_id == user.id, UserDietProgram.status == "active",
    ).order_by(UserDietProgram.id.desc()).first()
    if program is None:
        return ok(None)
    stage = _active_stage(program, db)
    preferences = program.preference_snapshot_json or {}
    return ok({
        "id": program.id, "template_code": program.template.code, "template_name": program.template.name,
        "stage": _stage_dict(stage), "meal_count": preferences.get("meal_count", 3),
        "eating_window_start": (preferences.get("preferences") or {}).get("eating_window_start"),
        "eating_window_end": (preferences.get("preferences") or {}).get("eating_window_end"),
    })


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


def _meal_dict(meal: MealPlanMeal) -> dict:
    return {
        "id": meal.id, "meal_type": meal.meal_type, "planned_time": meal.planned_time,
        "recorded": False,
        "items": [{
            "id": item.id, "name": item.food_snapshot_json["name"], "role": item.food_snapshot_json["role"],
            "amount_g": item.amount_g, "nutrition": item.nutrition_snapshot_json,
            "allergens": (item.constraint_snapshot_json or {}).get("allergens", []),
        } for item in meal.items],
    }


def _day_dict(day: MealPlanDay, recorded_meal_ids: set[int]) -> dict:
    meals = [_meal_dict(meal) for meal in day.meals]
    for meal in meals:
        meal["recorded"] = meal["id"] in recorded_meal_ids
    totals = {key: sum((Decimal(str(item.nutrition_snapshot_json.get(key, 0))) for meal in day.meals for item in meal.items), Decimal("0")) for key in ("calories_kcal", "carbs_g", "protein_g", "fat_g")}
    return {"id": day.id, "plan_date": day.plan_date, "totals": totals, "meals": meals}


def _food_library(db: Session) -> list[dict]:
    # The template catalogue only uses these names.  Reading their live values
    # here makes the saved snapshot traceable to the active system food data.
    from app.services.meal_templates import default_foods
    library = []
    for template_food in default_foods():
        row = db.query(Food).filter(Food.name == template_food["name"], Food.status == "active", Food.is_system == 1).first()
        if row is None:
            continue
        food = dict(template_food)
        for key in ("calories_per_100g", "carbs_per_100g", "protein_per_100g", "fat_per_100g", "fiber_per_100g"):
            food[key] = getattr(row, key)
        food["food_id"] = row.id
        library.append(food)
    return library


def _active_stage(program: UserDietProgram, db: Session) -> DietProgramStage:
    stage = db.query(DietProgramStage).filter(DietProgramStage.program_id == program.id, DietProgramStage.status == "active").order_by(DietProgramStage.stage_number.desc()).first()
    if stage is None:
        raise BizException(40038, "当前阶段不存在")
    return stage


def _conflict(exc: MealPlanConflict):
    raise BizException(40901, str(exc), 409, data=exc.to_dict())


@router.get("/{program_id}/meal-plan")
def get_meal_plan(
    program_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    program = _program_or_404(db, user.id, program_id)
    if program.status != "active":
        raise BizException(40037, "只有进行中的方案可以生成菜单")
    stage = _active_stage(program, db)
    days = db.query(MealPlanDay).options(joinedload(MealPlanDay.meals).joinedload(MealPlanMeal.items)).filter(
        MealPlanDay.program_id == program.id, MealPlanDay.stage_id == stage.id,
    ).order_by(MealPlanDay.plan_date).all()
    if not days:
        try:
            generated = generate_seven_day_plan({
                "calories_kcal": stage.calories_kcal, "carbs_g": stage.carbs_g,
                "protein_g": stage.protein_g, "fat_g": stage.fat_g,
            }, program.preference_snapshot_json, code=program.template.code, foods=_food_library(db))
        except MealPlanConflict as exc:
            _conflict(exc)
        for generated_day in generated["days"]:
            day = MealPlanDay(program_id=program.id, stage_id=stage.id, plan_date=generated_day["plan_date"], target_snapshot_json=jsonable_encoder(_stage_dict(stage)))
            db.add(day); db.flush()
            for generated_meal in generated_day["meals"]:
                meal = MealPlanMeal(day_id=day.id, meal_type=generated_meal["meal_type"], planned_time=generated_meal["planned_time"], target_snapshot_json={})
                db.add(meal); db.flush()
                for generated_item in generated_meal["items"]:
                    food = generated_item["food"]
                    db.add(MealPlanItem(
                        meal_id=meal.id, food_source="system", food_id=food.get("food_id"),
                        food_snapshot_json={"name": generated_item["name"], "role": generated_item["role"]},
                        amount_g=generated_item["amount_g"], nutrition_snapshot_json=jsonable_encoder(generated_item["nutrition"]),
                        constraint_snapshot_json={"allergens": generated_item["allergens"]},
                    ))
        db.commit()
        days = db.query(MealPlanDay).options(joinedload(MealPlanDay.meals).joinedload(MealPlanMeal.items)).filter(
            MealPlanDay.program_id == program.id, MealPlanDay.stage_id == stage.id,
        ).order_by(MealPlanDay.plan_date).all()
    meal_ids = [meal.id for day in days for meal in day.meals]
    recorded_ids = {row[0] for row in db.query(DietRecord.plan_meal_id).filter(DietRecord.plan_meal_id.in_(meal_ids)).distinct()} if meal_ids else set()
    return ok({"program_id": program.id, "stage_id": stage.id, "days": [_day_dict(day, recorded_ids) for day in days]})


def _owned_meal(db: Session, user_id: int, meal_id: int, *, lock: bool = False) -> MealPlanMeal:
    query = db.query(MealPlanMeal).join(MealPlanDay).join(UserDietProgram).filter(
        MealPlanMeal.id == meal_id, UserDietProgram.user_id == user_id,
    )
    if lock:
        query = query.with_for_update()
    meal = query.first()
    if meal is None:
        raise BizException(40401, "计划餐不存在", 404)
    return meal


def _owned_item(db: Session, user_id: int, item_id: int) -> tuple[MealPlanItem, UserDietProgram]:
    result = db.query(MealPlanItem, UserDietProgram).join(MealPlanMeal).join(MealPlanDay).join(UserDietProgram).filter(
        MealPlanItem.id == item_id, UserDietProgram.user_id == user_id,
    ).first()
    if result is None:
        raise BizException(40401, "计划食物不存在", 404)
    return result


def _candidate_food(db: Session, food_id: int) -> dict:
    candidate = next((food for food in _food_library(db) if food.get("food_id") == food_id), None)
    if candidate is None:
        raise BizException(40901, "该食物缺少菜单所需的过敏原、素食或纤维约束数据", 409, data={"fields": ["food_id"], "suggestions": ["请选择菜单支持的同角色食物"]})
    return candidate


@meal_plan_router.post("/items/{item_id}/replace")
def replace_plan_item(item_id: int, body: MealPlanItemReplaceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item, program = _owned_item(db, user.id, item_id)
    candidate = _candidate_food(db, body.food_id)
    try:
        replacement = replace_item({"role": item.food_snapshot_json["role"], "name": item.food_snapshot_json["name"], "amount_g": item.amount_g, "allergens": (item.constraint_snapshot_json or {}).get("allergens", [])}, candidate, program.preference_snapshot_json)
    except MealPlanConflict as exc:
        _conflict(exc)
    item.food_id, item.food_source = candidate["food_id"], "system"
    item.food_snapshot_json = {"name": replacement["name"], "role": replacement["role"]}
    item.constraint_snapshot_json = {"allergens": replacement["allergens"]}
    item.nutrition_snapshot_json = jsonable_encoder(replacement["nutrition"])
    db.commit()
    return ok({"id": item.id, "name": replacement["name"], "amount_g": item.amount_g})


@meal_plan_router.put("/items/{item_id}")
def update_plan_item_amount(item_id: int, body: MealPlanItemAmountIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item, program = _owned_item(db, user.id, item_id)
    old_amount = Decimal(item.amount_g)
    ratio = body.amount_g / old_amount
    old_nutrition = dict(item.nutrition_snapshot_json)
    item.amount_g = body.amount_g
    item.nutrition_snapshot_json = {key: Decimal(str(value)) * ratio for key, value in old_nutrition.items()}
    stage = _active_stage(program, db)
    day = item.meal.day
    day_data = {"totals": {key: sum((Decimal(str(plan_item.nutrition_snapshot_json.get(key, 0))) for meal in day.meals for plan_item in meal.items), Decimal("0")) for key in ("calories_kcal", "carbs_g", "protein_g", "fat_g")}}
    try:
        validate_meal_plan(day_data, {"calories_kcal": stage.calories_kcal, "protein_g": stage.protein_g, "fat_g": stage.fat_g}, code=program.template.code)
    except MealPlanConflict as exc:
        db.rollback(); _conflict(exc)
    item.nutrition_snapshot_json = jsonable_encoder(item.nutrition_snapshot_json)
    db.commit()
    return ok({"id": item.id, "amount_g": item.amount_g, "nutrition": item.nutrition_snapshot_json})


@meal_plan_router.post("/meals/{meal_id}/replace")
def replace_plan_meal(meal_id: int, body: MealPlanMealReplaceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meal = _owned_meal(db, user.id, meal_id)
    program = meal.day.program
    candidates = [_candidate_food(db, value.food_id) for value in body.items]
    by_role = {candidate["role"]: candidate for candidate in candidates}
    changes: list[tuple[MealPlanItem, dict]] = []
    try:
        for item in meal.items:
            candidate = by_role.get(item.food_snapshot_json["role"])
            if candidate is None:
                continue
            replacement = replace_item({"role": item.food_snapshot_json["role"], "name": item.food_snapshot_json["name"], "amount_g": item.amount_g, "allergens": (item.constraint_snapshot_json or {}).get("allergens", [])}, candidate, program.preference_snapshot_json)
            changes.append((item, replacement))
    except MealPlanConflict as exc:
        _conflict(exc)
    if not changes:
        raise BizException(40901, "替换餐必须包含至少一个相同营养角色的食物", 409, data={"fields": ["items"], "suggestions": ["选择主食、蛋白质或脂肪角色相同的食物"]})
    for item, replacement in changes:
        item.food_id = replacement["food"].get("food_id")
        item.food_snapshot_json = {"name": replacement["name"], "role": replacement["role"]}
        item.constraint_snapshot_json = {"allergens": replacement["allergens"]}
        item.nutrition_snapshot_json = jsonable_encoder(replacement["nutrition"])
    db.commit()
    return ok(_meal_dict(meal))


@meal_plan_router.post("/meals/{meal_id}/record")
def record_planned_meal(
    meal_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meal = _owned_meal(db, user.id, meal_id, lock=True)
    if db.query(DietRecord.id).filter(DietRecord.plan_meal_id == meal.id).first():
        raise BizException(40902, "这份计划餐已经加入实际记录", 409)
    # The plan stores immutable nutrient snapshots.  Recording copies those
    # snapshots in one transaction; merely generating/viewing a plan has no
    # side effect on the user's actual intake.
    created = []
    for item in meal.items:
        nutrient = item.nutrition_snapshot_json
        record = DietRecord(
            user_id=user.id, plan_meal_id=meal.id, record_date=meal.day.plan_date,
            record_time=meal.planned_time or time(12), meal_type=meal.meal_type,
            food_source=item.food_source, food_id=item.food_id, custom_food_id=item.custom_food_id,
            food_name_snapshot=item.food_snapshot_json["name"], unit_type="g", amount_g=item.amount_g,
            calories_kcal=nutrient["calories_kcal"], carbs_g=nutrient["carbs_g"],
            protein_g=nutrient["protein_g"], fat_g=nutrient["fat_g"], note="来自饮食方案菜单",
        )
        db.add(record); created.append(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BizException(40902, "这份计划餐已经加入实际记录", 409) from exc
    return ok({"meal_id": meal.id, "created_count": len(created)})


@router.post("")
def create_program(
    body: DietProgramCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
        weekly_loss_kg = validate_target_loss_rate(body.target_loss_rate, profile.current_weight_kg)
        targets = create_program_initial_targets(
            body.template_code, body.calories_kcal, ratio=body.macro_ratio,
        )
    except TargetLossRateError as exc:
        raise BizException(40042, str(exc), data={
            "status": "target_loss_rate_exceeds_cap",
            "target_loss_rate": body.target_loss_rate,
            "reference_weight_kg": profile.current_weight_kg,
            "weekly_loss_kg": exc.weekly_loss_kg,
            "max_weekly_loss_kg": Decimal("0.90"),
        }) from exc
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
    stage = DietProgramStage(
        program_id=program.id, stage_number=1, status="pending", observation_days=14,
        evaluation_snapshot_json={
            "target_loss_rate": str(body.target_loss_rate), "weekly_loss_kg": str(weekly_loss_kg),
        }, **targets,
    )
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
    try:
        result = evaluate_532(
            previous_weights=_daily_weights(db, user.id, previous_start, current_start - timedelta(days=1)),
            current_weights=_daily_weights(db, user.id, current_start, body.end_date),
            adherence_rate=_adherence_rate(db, user.id, current_start, body.end_date, stage.calories_kcal),
            target_loss_rate=body.target_loss_rate,
            stage=_stage_dict(stage), observation_days=(body.end_date - stage.start_date).days + 1 if stage.start_date else 0,
            target_weight_kg=profile.target_weight_kg if profile else None,
            reference_weight_kg=profile.current_weight_kg if profile else None, reduction_g=body.reduction_g,
        )
    except TargetLossRateError as exc:
        raise BizException(40042, str(exc), data={
            "status": "target_loss_rate_exceeds_cap",
            "target_loss_rate": body.target_loss_rate,
            "reference_weight_kg": profile.current_weight_kg if profile else None,
            "weekly_loss_kg": exc.weekly_loss_kg,
            "max_weekly_loss_kg": Decimal("0.90"),
        }) from exc
    # Evaluation never changes the active target; confirmation creates any next stage.
    stage.evaluation_snapshot_json = result.to_dict()
    db.commit()
    return ok(result.to_dict())
