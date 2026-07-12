const DEFAULT_DEVICE_DEV_BASE = 'http://192.168.1.23:8000/api/v1';

export function resolveApiBase(value?: string): string {
  return (value || DEFAULT_DEVICE_DEV_BASE).replace(/\/+$/, '');
}
