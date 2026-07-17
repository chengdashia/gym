import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

const mocks = vi.hoisted(() => ({
  getToken: vi.fn(() => 'saved-token'),
  clearAuth: vi.fn(),
  setStorageSync: vi.fn(),
  getMe: vi.fn(async () => ({
    id: 1,
    nickname: '测试',
    avatar_url: null,
    phone: '13800138000',
    agreement_confirmed: true,
    onboarding_step: 'complete' as const,
    agreement_version: 'v1.0',
    agreement_confirmed_at: '2026-07-10T00:00:00Z',
    is_member: false,
    member_expired_at: null,
    experimental_features: [],
    profile: null,
  })),
}));

vi.mock('@/utils/request', () => ({
  getToken: mocks.getToken,
  setToken: vi.fn(),
  clearAuth: mocks.clearAuth,
}));

vi.mock('@/api/user', () => ({
  userApi: { getMe: mocks.getMe },
}));

describe('auth bootstrap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getToken.mockReturnValue('saved-token');
    mocks.getMe.mockResolvedValue({
      id: 1,
      nickname: '测试',
      avatar_url: null,
      phone: '13800138000',
      agreement_confirmed: true,
      onboarding_step: 'complete' as const,
      agreement_version: 'v1.0',
      agreement_confirmed_at: '2026-07-10T00:00:00Z',
      is_member: false,
      member_expired_at: null,
      experimental_features: [],
      profile: null,
    });
    setActivePinia(createPinia());
    vi.stubGlobal('uni', {
      getStorageSync: vi.fn(() => ({ id: 1, agreement_confirmed: true })),
      setStorageSync: mocks.setStorageSync,
      removeStorageSync: vi.fn(),
    });
  });

  it('restores a saved token instead of clearing it', async () => {
    const { useAuthStore } = await import('./auth');
    const auth = useAuthStore();

    await auth.bootstrap();

    expect(auth.token).toBe('saved-token');
    expect(mocks.clearAuth).not.toHaveBeenCalled();
  });

  it('refreshes and synchronizes the current user into both stores and cache', async () => {
    const me = await mocks.getMe();
    mocks.getMe.mockClear();
    mocks.getMe.mockResolvedValueOnce({
      ...me,
      experimental_features: ['food_recognition'] as any,
    });
    const { STORAGE_KEYS } = await import('@/utils/constants');
    const { useAuthStore } = await import('./auth');
    const { useUserStore } = await import('./user');
    const auth = useAuthStore();
    const user = useUserStore();

    await auth.bootstrap();

    expect(mocks.getMe).toHaveBeenCalledOnce();
    expect(user.me).toEqual(expect.objectContaining({
      id: 1,
      phone: '13800138000',
      agreement_confirmed: true,
    }));
    expect(auth.user).toEqual(expect.objectContaining({
      id: 1,
      nickname: '测试',
      agreement_confirmed: true,
      is_member: false,
      experimental_features: ['food_recognition'],
    }));
    expect(mocks.setStorageSync).toHaveBeenCalledWith(STORAGE_KEYS.user, auth.user);
  });

  it('uses the server onboarding step instead of agreement alone', async () => {
    mocks.getMe.mockResolvedValueOnce({
      ...(await mocks.getMe()),
      agreement_confirmed: false,
      onboarding_step: 'agreement' as any,
    });
    const { useAuthStore } = await import('./auth');
    const auth = useAuthStore();

    await auth.bootstrap();

    expect(auth.needOnboarding).toBe(true);
    expect(auth.user?.onboarding_step).toBe('agreement');
  });

  it('keeps the saved token when refreshing the user fails with a network error', async () => {
    mocks.getMe.mockRejectedValueOnce(new Error('network unavailable'));
    const { useAuthStore } = await import('./auth');
    const auth = useAuthStore();

    await auth.bootstrap();

    expect(auth.token).toBe('saved-token');
    expect(auth.ready).toBe(true);
    expect(mocks.clearAuth).not.toHaveBeenCalled();
  });

  it('clears the saved token when refreshing the user returns 40101', async () => {
    mocks.getMe.mockRejectedValueOnce({ code: 40101 });
    const { useAuthStore } = await import('./auth');
    const auth = useAuthStore();

    await auth.bootstrap();

    expect(mocks.getMe).toHaveBeenCalledOnce();
    expect(auth.token).toBe('');
    expect(mocks.clearAuth).toHaveBeenCalledOnce();
  });

  it('clears the saved token for an HTTP 401 without a business code', async () => {
    mocks.getMe.mockRejectedValueOnce({ statusCode: 401 });
    const { useAuthStore } = await import('./auth');
    const auth = useAuthStore();

    await auth.bootstrap();

    expect(auth.token).toBe('');
    expect(mocks.clearAuth).toHaveBeenCalledOnce();
  });
});

describe('user reset', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('clears account-scoped business state', async () => {
    const { useUserStore } = await import('./user');
    const user = useUserStore();
    user.me = { id: 1 } as any;
    user.goal = { calories_kcal: 1800, carbs_g: 200, protein_g: 120, fat_g: 55 };
    user.reminders = [{ reminder_type: 'diet', enabled: true, reminder_time: '08:00', weekdays: '1' }];

    user.reset();

    expect(user.me).toBeNull();
    expect(user.goal).toEqual({ calories_kcal: 0, carbs_g: 0, protein_g: 0, fat_g: 0 });
    expect(user.reminders).toEqual([]);
  });
});
