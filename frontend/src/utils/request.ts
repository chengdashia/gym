import { API_BASE, STORAGE_KEYS } from './constants';

type Method = 'GET' | 'POST' | 'PUT' | 'DELETE';

interface RequestOptions {
  url: string;
  method?: Method;
  data?: any;
  header?: Record<string, string>;
  showLoading?: boolean;
  silent?: boolean;
  raw?: boolean; // 不解包 code/data
}

interface BizResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

let token: string | null = null;

export function setToken(t: string | null) {
  token = t;
  if (t) {
    uni.setStorageSync(STORAGE_KEYS.token, t);
  } else {
    uni.removeStorageSync(STORAGE_KEYS.token);
  }
}

export function getToken(): string | null {
  if (token) return token;
  try {
    token = (uni.getStorageSync(STORAGE_KEYS.token) as string) || null;
  } catch {
    token = null;
  }
  return token;
}

export function clearAuth() {
  setToken(null);
  uni.removeStorageSync(STORAGE_KEYS.user);
}

let authInvalidated = false;
function onUnauthorized() {
  if (authInvalidated) return;
  authInvalidated = true;
  clearAuth();
  uni.showToast({ title: '登录已失效，请重新登录', icon: 'none' });
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/login/onboarding' });
    authInvalidated = false;
  }, 600);
}

function buildHeaders(extra?: Record<string, string>) {
  const h: Record<string, string> = { 'Content-Type': 'application/json', ...extra };
  const t = getToken();
  if (t) h['Authorization'] = `Bearer ${t}`;
  return h;
}

export function request<T = any>(opts: RequestOptions): Promise<T> {
  const {
    url,
    method = 'GET',
    data,
    header,
    showLoading = false,
    silent = false,
    raw = false,
  } = opts;

  if (showLoading) {
    uni.showLoading({ title: '加载中...', mask: true });
  }

  return new Promise<T>((resolve, reject) => {
    uni.request({
      url: url.startsWith('http') ? url : `${API_BASE}${url}`,
      method,
      data,
      header: buildHeaders(header),
      success: (res: any) => {
        if (showLoading) uni.hideLoading();
        const body = res.data as BizResponse<T>;
        if (!raw && body && typeof body === 'object' && 'code' in body) {
          if (body.code === 0) {
            resolve(body.data as T);
            return;
          }
          if (body.code === 40101) {
            onUnauthorized();
            reject(body);
            return;
          }
          if (!silent) {
            uni.showToast({ title: body.message || '请求失败', icon: 'none' });
          }
          reject(body);
          return;
        }
        resolve(res.data as T);
      },
      fail: (err: any) => {
        if (showLoading) uni.hideLoading();
        if (!silent) {
          uni.showToast({ title: '网络异常', icon: 'none' });
        }
        reject(err);
      },
    });
  });
}

export const http = {
  get: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'GET', data, ...opts }),
  post: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'POST', data, ...opts }),
  put: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'PUT', data, ...opts }),
  del: <T = any>(url: string, data?: any, opts?: Partial<RequestOptions>) =>
    request<T>({ url, method: 'DELETE', data, ...opts }),
};

export function uploadFile(filePath: string, formData: Record<string, any> = {}): Promise<{ file_id: number; file_url: string; is_temporary: boolean }> {
  return new Promise((resolve, reject) => {
    const t = getToken();
    uni.uploadFile({
      url: `${API_BASE}/uploads/image`,
      filePath,
      name: 'file',
      formData,
      header: t ? { Authorization: `Bearer ${t}` } : {},
      success: (res) => {
        try {
          const body = JSON.parse(res.data);
          if (body.code === 0) resolve(body.data);
          else {
            uni.showToast({ title: body.message || '上传失败', icon: 'none' });
            reject(body);
          }
        } catch (e) {
          reject(e);
        }
      },
      fail: (err) => {
        uni.showToast({ title: '上传失败', icon: 'none' });
        reject(err);
      },
    });
  });
}