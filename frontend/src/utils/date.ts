// 日期工具

export function today(): string {
  return formatDate(new Date());
}

export function formatDate(d: Date | string | number): string {
  const dt = d instanceof Date ? d : new Date(d);
  const y = dt.getFullYear();
  const m = String(dt.getMonth() + 1).padStart(2, '0');
  const day = String(dt.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function formatTime(d: Date | string | number): string {
  const dt = d instanceof Date ? d : new Date(d);
  const h = String(dt.getHours()).padStart(2, '0');
  const m = String(dt.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
}

export function formatDateTime(d: Date | string | number | null | undefined): string {
  if (!d) return '-';
  const dt = d instanceof Date ? d : new Date(d);
  if (isNaN(dt.getTime())) return '-';
  return `${formatDate(dt)} ${formatTime(dt)}`;
}

export function isToday(dateStr: string): boolean {
  return dateStr === today();
}

export function addDays(d: Date | string, n: number): Date {
  const dt = d instanceof Date ? new Date(d.getTime()) : new Date(d);
  dt.setDate(dt.getDate() + n);
  return dt;
}

export function diffDays(a: string, b: string): number {
  const da = new Date(a).getTime();
  const db = new Date(b).getTime();
  return Math.round((da - db) / 86400000);
}

export function rangeDays(end: string, n: number): string[] {
  const endDt = new Date(end);
  const list: string[] = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(endDt);
    d.setDate(endDt.getDate() - i);
    list.push(formatDate(d));
  }
  return list;
}

export function weekdayCN(dateStr: string): string {
  const d = new Date(dateStr);
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()];
}

export function dateMD(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

export function humanizeDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '0秒';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const parts: string[] = [];
  if (h) parts.push(`${h}小时`);
  if (m) parts.push(`${m}分`);
  if (!h && s) parts.push(`${s}秒`);
  return parts.join('') || '0秒';
}

export function formatCountdown(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}