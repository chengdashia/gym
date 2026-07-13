import { describe, expect, it } from 'vitest';
import { hasWeightChartData } from './weight-chart';

describe('weight chart availability', () => {
  it('shows a chart for a single weight record', () => {
    expect(hasWeightChartData(0)).toBe(false);
    expect(hasWeightChartData(1)).toBe(true);
  });
});
