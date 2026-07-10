from app.models import (
    DietRecord,
    FoodRecognitionLog,
    NutritionGoal,
    TrainingPlan,
    TrainingSession,
    UploadedFile,
    UserCustomExercise,
    UserCustomFood,
    UserProfile,
    UserReminder,
    WeightRecord,
)
from app.services.account_data import PERSONAL_DATA_MODELS, anonymize_account


class FakeUser:
    status = "active"
    phone = "13800000000"
    openid = "openid"
    password_hash = "hash"
    nickname = "昵称"
    avatar_url = "/static/avatar.jpg"


def test_clear_personal_data_covers_all_user_owned_models():
    assert set(PERSONAL_DATA_MODELS) == {
        DietRecord,
        WeightRecord,
        UserCustomFood,
        UserCustomExercise,
        TrainingPlan,
        TrainingSession,
        FoodRecognitionLog,
        UploadedFile,
        NutritionGoal,
        UserReminder,
        UserProfile,
    }


def test_cancel_account_clears_identifiers_and_status():
    user = FakeUser()

    anonymize_account(user)

    assert user.status == "cancelled"
    assert user.phone is None
    assert user.openid is None
    assert user.password_hash is None
    assert user.nickname is None
    assert user.avatar_url is None
