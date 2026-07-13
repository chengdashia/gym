import { describe, expect, it } from 'vitest';
import { isProfileComplete, onboardingStepIndex, profilePayload } from './profile-source';

describe('onboarding step resume', () => {
  it.each([
    ['agreement', 1],
    ['profile', 2],
    ['goal', 3],
    ['complete', 4],
  ] as const)('maps %s to page step %s', (step, expected) => {
    expect(onboardingStepIndex(step)).toBe(expected);
  });
});

describe('profile source completion', () => {
  it('requires nickname and uploaded avatar for WeChat source', () => {
    expect(isProfileComplete('wechat', '小明', '')).toBe(false);
    expect(isProfileComplete('wechat', '', '/uploads/avatar.jpg')).toBe(false);
    expect(isProfileComplete('wechat', '小明', '/uploads/avatar.jpg')).toBe(true);
  });

  it('accepts a custom album or camera avatar after both fields are set', () => {
    expect(isProfileComplete('custom', '小明', '')).toBe(false);
    expect(isProfileComplete('custom', '小明', '/uploads/avatar.jpg')).toBe(true);
    expect(profilePayload('custom', ' 小明 ', '/uploads/avatar.jpg')).toEqual({
      nickname: '小明',
      avatar_url: '/uploads/avatar.jpg',
    });
  });

  it('does not allow a default profile without a chosen avatar', () => {
    expect(isProfileComplete('default', '健身伙伴', '')).toBe(false);
  });

  it('always saves the chosen avatar', () => {
    expect(profilePayload('default', '自定义昵称', '/uploads/avatar.jpg')).toEqual({
      nickname: '自定义昵称',
      avatar_url: '/uploads/avatar.jpg',
    });
    expect(profilePayload('wechat', ' 小明 ', '/uploads/avatar.jpg')).toEqual({
      nickname: '小明',
      avatar_url: '/uploads/avatar.jpg',
    });
  });
});
