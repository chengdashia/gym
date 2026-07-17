from sqlalchemy.orm import Session

from app.models import (
    DietPreference,
    DietRecord,
    FoodRecognitionLog,
    NutritionGoal,
    OperationLog,
    SavedMealTemplate,
    TrainingPlan,
    TrainingPlanDay,
    TrainingPlanExercise,
    TrainingSession,
    TrainingSessionExercise,
    TrainingSessionSet,
    UploadedFile,
    User,
    UserCustomExercise,
    UserCustomFood,
    UserDietProgram,
    UserProfile,
    UserReminder,
    WeightRecord,
)


PERSONAL_DATA_MODELS = (
    DietPreference,
    DietRecord,
    SavedMealTemplate,
    WeightRecord,
    UserCustomFood,
    UserCustomExercise,
    UserDietProgram,
    TrainingPlan,
    TrainingSession,
    FoodRecognitionLog,
    UploadedFile,
    NutritionGoal,
    UserReminder,
    UserProfile,
)


def clear_personal_data(db: Session, user: User) -> list[str]:
    user_id = user.id
    upload_paths = [
        row.file_url
        for row in db.query(UploadedFile).filter(UploadedFile.user_id == user_id).all()
    ]

    session_ids = db.query(TrainingSession.id).filter(TrainingSession.user_id == user_id)
    session_exercise_ids = db.query(TrainingSessionExercise.id).filter(
        TrainingSessionExercise.session_id.in_(session_ids)
    )
    db.query(TrainingSessionSet).filter(
        TrainingSessionSet.session_exercise_id.in_(session_exercise_ids)
    ).delete(synchronize_session=False)
    db.query(TrainingSessionExercise).filter(
        TrainingSessionExercise.session_id.in_(session_ids)
    ).delete(synchronize_session=False)
    db.query(TrainingSession).filter(TrainingSession.user_id == user_id).delete(
        synchronize_session=False
    )

    plan_ids = db.query(TrainingPlan.id).filter(TrainingPlan.user_id == user_id)
    plan_day_ids = db.query(TrainingPlanDay.id).filter(TrainingPlanDay.plan_id.in_(plan_ids))
    db.query(TrainingPlanExercise).filter(
        TrainingPlanExercise.plan_day_id.in_(plan_day_ids)
    ).delete(synchronize_session=False)
    db.query(TrainingPlanDay).filter(TrainingPlanDay.plan_id.in_(plan_ids)).delete(
        synchronize_session=False
    )

    for model in PERSONAL_DATA_MODELS:
        if model in (TrainingSession,):
            continue
        db.query(model).filter(model.user_id == user_id).delete(synchronize_session=False)

    db.query(OperationLog).filter(OperationLog.user_id == user_id).delete(
        synchronize_session=False
    )
    return upload_paths


def anonymize_account(user: User) -> None:
    user.status = "cancelled"
    user.phone = None
    user.openid = None
    user.password_hash = None
    user.nickname = None
    user.avatar_url = None
