import { describe, expect, it } from 'vitest';
import type { WeightRecord } from '@/api/weight';
import { selectDailyWeightTrend } from './weight-trend';

function record(record_date: string, record_time: string, weight_kg: number): WeightRecord {
  return { id: 1, user_id: 1, record_date, record_time, weight_kg };
}

describe('daily weight trend', () => {
  it('keeps the latest record for each day and returns chronological points', () => {
    expect(selectDailyWeightTrend([
      record('2026-07-14', '20:00:00', 71),
      record('2026-07-14', '08:00:00', 70),
      record('2026-07-13', '09:00:00', 69),
    ])).toMatchObject([
      { record_date: '2026-07-13', weight_kg: 69 },
      { record_date: '2026-07-14', weight_kg: 71 },
    ]);
  });
});
