import { describe, expect, it } from 'vitest';
import { resolveApiBase } from './api-base';

describe('resolveApiBase', () => {
  it('uses localhost in WeChat DevTools to avoid the system proxy intercepting the LAN address', () => {
    expect(resolveApiBase(undefined, 'devtools')).toBe('http://127.0.0.1:8000/api/v1');
  });

  it('uses the LAN address on a real device', () => {
    expect(resolveApiBase(undefined, 'ios')).toBe('http://192.168.1.23:8000/api/v1');
  });

  it('uses the configured LAN URL for real-device development', () => {
    expect(resolveApiBase('http://192.168.1.23:8000/api/v1', 'devtools')).toBe('http://192.168.1.23:8000/api/v1');
  });

  it('removes a trailing slash so request paths do not contain double slashes', () => {
    expect(resolveApiBase('http://192.168.1.23:8000/api/v1/')).toBe('http://192.168.1.23:8000/api/v1');
  });
});
