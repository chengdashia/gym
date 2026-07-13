import { describe, expect, it } from 'vitest';
import type { ReminderItem } from '@/api/user';
import { validateReminderItems } from './reminders';

const reminder = (patch: Partial<ReminderItem> = {}): ReminderItem => ({
  reminder_type: 'diet',
  enabled: false,
  reminder_time: '08:30',
  weekdays: '',
  ...patch,
});

describe('reminder validation', () => {
  it('allows a disabled reminder without weekdays', () => {
    expect(validateReminderItems([reminder()])).toBeNull();
  });

  it('requires a weekday when a reminder is enabled', () => {
    expect(validateReminderItems([reminder({ enabled: true })])).toBe('请至少选择一天');
  });

  it('accepts an enabled reminder with a weekday', () => {
    expect(validateReminderItems([reminder({ enabled: true, weekdays: '1' })])).toBeNull();
  });
});
