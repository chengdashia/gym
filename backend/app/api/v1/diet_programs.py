from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.response import ok
from app.models import DietPreference, User
from app.schemas import DietEligibilityIn, DietPreferenceIn
from app.services.diet_eligibility import check_eligibility
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
    return ok(asdict(check_eligibility(body.model_dump())))


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
