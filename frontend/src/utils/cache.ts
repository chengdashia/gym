import { STORAGE_KEYS } from './constants';

interface CacheItem<T> {
  data: T;
  expireAt: number;
}

export function setCache<T>(key: string, data: T, ttlMs?: number) {
  const item: CacheItem<T> = {
    data,
    expireAt: ttlMs ? Date.now() + ttlMs : 0,
  };
  uni.setStorageSync(STORAGE_KEYS.cachePrefix + key, item);
}

export function getCache<T>(key: string): T | null {
  try {
    const raw = uni.getStorageSync(STORAGE_KEYS.cachePrefix + key);
    if (!raw) return null;
    const item = raw as CacheItem<T>;
    if (item.expireAt && item.expireAt < Date.now()) {
      uni.removeStorageSync(STORAGE_KEYS.cachePrefix + key);
      return null;
    }
    return item.data;
  } catch {
    return null;
  }
}

export function removeCache(key: string) {
  uni.removeStorageSync(STORAGE_KEYS.cachePrefix + key);
}

export function clearAllCache() {
  try {
    const info = uni.getStorageInfoSync();
    info.keys.forEach((k) => {
      if (k.startsWith(STORAGE_KEYS.cachePrefix)) uni.removeStorageSync(k);
    });
  } catch {}
}

export function clearAll() {
  try {
    uni.clearStorageSync();
  } catch {}
}