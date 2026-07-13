import type { ReminderItem } from '@/api/user';

export function validateReminderItems(items: ReminderItem[]): string | null {
  return items.some((item) => item.enabled && !item.weekdays.trim()) ? '请至少选择一天' : null;
}
