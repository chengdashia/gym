export interface NumberBounds { min: number; max: number; integer?: boolean }

export const PROFILE_BOUNDS = {
  age: { min: 10, max: 120, integer: true },
  height: { min: 50, max: 250 },
  weight: { min: 20, max: 250 },
} as const;

export function normalizeOptionalNumber(value: unknown, bounds: NumberBounds): number | null | undefined {
  if (value === '' || value === null || value === undefined) return null;
  const number = Number(value);
  if (!Number.isFinite(number) || number < bounds.min || number > bounds.max) return undefined;
  if (bounds.integer && !Number.isInteger(number)) return undefined;
  return number;
}
