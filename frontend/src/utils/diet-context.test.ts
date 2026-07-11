import { describe, expect, it } from 'vitest';
import { buildDietEntryUrl, parseDietContext, type DietRecordContext } from './diet-context';

describe('diet record context', () => {
  const fallback: DietRecordContext = {
    date: '2026-07-11',
    meal: 'lunch',
    time: '12:10',
  };

  it('passes date and meal to every diet entry', () => {
    expect(buildDietEntryUrl('/pages/diet/photo-recognize', {
      date: '2026-07-11', meal: 'lunch', time: '12:10',
    })).toBe('/pages/diet/photo-recognize?date=2026-07-11&meal=lunch&time=12%3A10');
  });

  it('rejects an invalid meal and keeps the fallback', () => {
    expect(parseDietContext({ meal: 'unknown' }, fallback).meal).toBe(fallback.meal);
  });
});
