from typing import Literal

from app.models import User, UserProfile


OnboardingStep = Literal["agreement", "profile", "goal", "complete"]


def onboarding_step(user: User, profile: UserProfile | None = None) -> OnboardingStep:
    if user.agreement_confirmed_at is None:
        return "agreement"
    if not (user.nickname or "").strip() or not (user.avatar_url or "").strip():
        return "profile"
    current_profile = profile if profile is not None else getattr(user, "profile", None)
    if not getattr(current_profile, "fitness_goal", None):
        return "goal"
    return "complete"
