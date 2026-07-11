from dataclasses import dataclass


RISK_FIELDS = (
    "under_18",
    "pregnant_or_breastfeeding",
    "diabetes",
    "serious_liver_kidney_gallbladder",
    "eating_disorder_history",
)


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    reasons: list[str]
    next_action: str


def check_eligibility(payload: dict) -> EligibilityResult:
    missing = [field for field in RISK_FIELDS if field not in payload]
    if missing:
        raise ValueError("缺少资格筛查项")
    if any(payload[field] is True for field in RISK_FIELDS):
        return EligibilityResult(
            eligible=False,
            reasons=["存在不适合自动生成饮食方案的健康条件"],
            next_action="仅使用普通饮食记录，并咨询医生或注册营养师",
        )
    return EligibilityResult(True, [], "可以继续设置饮食偏好")
