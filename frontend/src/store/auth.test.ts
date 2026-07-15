import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

const mocks = vi.hoisted(() => ({
  getMe: vi.fn(async () => ({
    id: 1,
    nickname: '本地用户',
    avatar_url: null,
    phone: null,
    agreement_confirmed: true,
    onboarding_step: 'complete' as const,
    agreement_version: null,
    agreement_confirmed_at: null,
    is_member: false,
    member_expired_at: null,
    profile: null,
  })),
}));

vi.mock('@/api/user', () => ({ userApi: { getMe: mocks.getMe } }));

describe('local single-user bootstrap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it('loads the fixed local user without a token', async () => {
    const { useAuthStore } = await import('./auth');
    const auth = useAuthStore();

    await auth.bootstrap();

    expect(auth.ready).toBe(true);
    expect(auth.isLogged).toBe(true);
    expect(auth.token).toBe('local');
    expect(auth.user).toEqual(expect.objectContaining({ id: 1, nickname: '本地用户' }));
  });

  it('uses the local onboarding step', async () => {
    mocks.getMe.mockResolvedValueOnce({
      ...(await mocks.getMe()),
      onboarding_step: 'profile',
    } as any);
    const { useAuthStore } = await import('./auth');
    const auth = useAuthStore();

    await auth.bootstrap();

    expect(auth.needOnboarding).toBe(true);
  });
});

describe('user reset', () => {
  it('clears account-scoped business state', async () => {
    setActivePinia(createPinia());
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
