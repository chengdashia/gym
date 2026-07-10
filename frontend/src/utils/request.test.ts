import { beforeEach, describe, expect, it, vi } from 'vitest';

describe('request HTTP errors', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal('getCurrentPages', vi.fn(() => []));
  });

  it('rejects a bare HTTP 401 with statusCode while preserving server details', async () => {
    const removeStorageSync = vi.fn();
    const showToast = vi.fn();
    const reLaunch = vi.fn();
    vi.stubGlobal('uni', {
      getStorageSync: vi.fn(() => ''),
      removeStorageSync,
      showToast,
      reLaunch,
      request: vi.fn((options: any) => {
        options.success({
          statusCode: 401,
          data: { code: 49999, message: '服务端令牌失效' },
        });
      }),
    });
    const { request } = await import('./request');

    const result = request({ url: '/users/me' });

    await expect(result).rejects.toEqual(expect.objectContaining({
      statusCode: 401,
      code: 49999,
      message: '服务端令牌失效',
    }));
    expect(removeStorageSync).toHaveBeenCalled();
    expect(showToast).toHaveBeenCalledWith({ title: '登录已失效，请重新登录', icon: 'none' });

    await vi.advanceTimersByTimeAsync(600);
    expect(reLaunch).toHaveBeenCalledWith({ url: '/pages/login/onboarding' });
  });

  it('serializes multipart values as strings for mini-program uploads', async () => {
    const { normalizeUploadFormData } = await import('./request');
    expect(normalizeUploadFormData({ usage_type: 'avatar', temporary: false, count: 1, empty: null }))
      .toEqual({ usage_type: 'avatar', temporary: 'false', count: '1' });
  });
});
