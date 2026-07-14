import { beforeEach, describe, expect, it, vi } from 'vitest';

const auth = { isLogged: false };
const showModal = vi.fn();
const showToast = vi.fn();
const navigateTo = vi.fn();
const reLaunch = vi.fn();

vi.mock('@/store/auth', () => ({ useAuthStore: () => auth }));

import { requireAuth } from './auth-guard';

beforeEach(() => {
  vi.clearAllMocks();
  (globalThis as any).uni = { showModal, showToast, navigateTo, reLaunch };
});

describe('requireAuth', () => {
  it('keeps guests on the current page when login is cancelled', () => {
    requireAuth({ redirect: '/pages/mine/profile' });
    showModal.mock.calls[0][0].success({ confirm: false });

    expect(navigateTo).not.toHaveBeenCalled();
    expect(reLaunch).not.toHaveBeenCalled();
  });

  it('opens onboarding only after confirmation', () => {
    requireAuth({ redirect: '/pages/mine/profile' });
    showModal.mock.calls[0][0].success({ confirm: true });

    expect(navigateTo).toHaveBeenCalledWith({
      url: expect.stringContaining('redirect='),
    });
  });

  it('does not stack login prompts', () => {
    requireAuth();
    requireAuth();

    expect(showModal).toHaveBeenCalledTimes(1);
    showModal.mock.calls[0][0].success({ confirm: false });
  });
});
