import { describe, expect, it } from 'vitest';
import { hasTrainingData, validWeightPoints } from './stats';

describe('stats data states', () => {
  it('detects a real training session even with zero weighted volume', () => {
    expect(hasTrainingData([{ date: '2026-07-10', session_count: 1, total_volume: 0, duration_seconds: 60 }])).toBe(true);
  });
  it('removes missing weight dates instead of converting them to zero', () => {
    const points = validWeightPoints([
      { date: 'a', weight_kg: null, target_weight_kg: null, diff_kg: null, change_from_start: null, average_7d: null },
      { date: 'b', weight_kg: 74, target_weight_kg: null, diff_kg: null, change_from_start: null, average_7d: null },
    ]);
    expect(points).toHaveLength(1);
    expect(points[0].weight_kg).toBe(74);
  });
});
