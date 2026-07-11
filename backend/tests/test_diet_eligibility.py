import pytest

from app.services.diet_eligibility import check_eligibility


SAFE = {
    "under_18": False,
    "pregnant_or_breastfeeding": False,
    "diabetes": False,
    "serious_liver_kidney_gallbladder": False,
    "eating_disorder_history": False,
}


@pytest.mark.parametrize("field", list(SAFE))
def test_risk_flags_block_program_generation(field):
    result = check_eligibility({**SAFE, field: True})
    assert result.eligible is False
    assert result.reasons == ["存在不适合自动生成饮食方案的健康条件"]
    assert result.next_action == "仅使用普通饮食记录，并咨询医生或注册营养师"


def test_safe_answers_allow_program_generation():
    result = check_eligibility(SAFE)
    assert result.eligible is True
    assert result.reasons == []
    assert result.next_action == "可以继续设置饮食偏好"


def test_eligibility_requires_every_answer():
    with pytest.raises(ValueError, match="缺少资格筛查项"):
        check_eligibility({})
