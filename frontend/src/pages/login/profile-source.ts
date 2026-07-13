export type ProfileSource = 'wechat' | 'custom' | 'default';
export type OnboardingStep = 'agreement' | 'profile' | 'goal' | 'complete';

export function onboardingStepIndex(step: OnboardingStep): number {
  return { agreement: 1, profile: 2, goal: 3, complete: 4 }[step];
}

export function isProfileComplete(_source: ProfileSource, nickname: string, avatarUrl: string) {
  return !!nickname.trim() && !!avatarUrl;
}

export function profilePayload(source: ProfileSource, nickname: string, avatarUrl: string) {
  return {
    nickname: nickname.trim(),
    avatar_url: avatarUrl,
  };
}
