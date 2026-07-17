export type ProfileSource = 'wechat' | 'custom' | 'default';
export type OnboardingStep = 'agreement' | 'profile' | 'complete';

export function onboardingStepIndex(step: OnboardingStep): number {
  return { agreement: 1, profile: 2, complete: 3 }[step];
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
