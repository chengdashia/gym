import type { WeightRecord } from '@/api/weight';

/** Input is newest-first; the first record for each date is that day's latest. */
export function selectDailyWeightTrend(records: WeightRecord[], limit = 7): WeightRecord[] {
  const dates = new Set<string>();
  return records.filter((record) => {
    if (dates.has(record.record_date)) return false;
    dates.add(record.record_date);
    return true;
  }).slice(0, limit).reverse();
}
