const DEFAULT_DEVICE_DEV_BASE = 'http://192.168.1.23:8000/api/v1';
const DEFAULT_DEVTOOLS_BASE = 'http://127.0.0.1:8000/api/v1';

export function resolveApiBase(value?: string, platform?: string): string {
  const fallback = platform === 'devtools' ? DEFAULT_DEVTOOLS_BASE : DEFAULT_DEVICE_DEV_BASE;
  return (value || fallback).replace(/\/+$/, '');
}
