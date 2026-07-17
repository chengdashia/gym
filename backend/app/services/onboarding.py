from typing import Literal

from app.models import User


OnboardingStep = Literal["agreement", "profile", "complete"]


def onboarding_step(user: User) -> OnboardingStep:
    if user.agreement_confirmed_at is None:
        return "agreement"
    if not (user.nickname or "").strip() or not (user.avatar_url or "").strip():
        return "profile"
    return "complete"
