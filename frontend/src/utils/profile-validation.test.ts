import { describe, expect, it } from 'vitest';
import { PROFILE_BOUNDS, normalizeOptionalNumber } from './profile-validation';

describe('optional profile number validation', () => {
  it.each([undefined, null, ''])('keeps %s empty', (value) => {
    expect(normalizeOptionalNumber(value, PROFILE_BOUNDS.age)).toBeNull();
  });

  it('accepts inclusive boundaries', () => {
    expect(normalizeOptionalNumber('10', PROFILE_BOUNDS.age)).toBe(10);
    expect(normalizeOptionalNumber(120, PROFILE_BOUNDS.age)).toBe(120);
  });

  it('rejects invalid and out-of-range values', () => {
    expect(normalizeOptionalNumber('abc', PROFILE_BOUNDS.age)).toBeUndefined();
    expect(normalizeOptionalNumber(9, PROFILE_BOUNDS.age)).toBeUndefined();
    expect(normalizeOptionalNumber(121, PROFILE_BOUNDS.age)).toBeUndefined();
  });
});
