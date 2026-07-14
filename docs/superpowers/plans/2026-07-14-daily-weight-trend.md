# Daily Weight Trend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the weight chart from the last record of each recorded day and label it as a seven-day trend.

**Architecture:** Keep `weightRecords` unchanged for the record list. Add a small pure frontend utility that consumes API-descending records and returns the first record from each date, capped at seven then reversed for chart chronology. `account.vue` uses this utility only for `weightHistory`.

**Tech Stack:** Vue 3, TypeScript, Vitest, uni-app canvas.

## Global Constraints

- Preserve all manual and profile-synced records in the recent-records list.
- Use the API's descending date/time order; do not add a backend endpoint or dependency.
- Work on `main` and create Chinese Git commits.

---

### Task 1: Daily chart-series selector

**Files:**
- Create: `frontend/src/utils/weight-trend.ts`
- Create: `frontend/src/utils/weight-trend.test.ts`

**Interfaces:**
- Consumes: `WeightRecord[]`, sorted newest to oldest by `record_date` and `record_time`.
- Produces: `selectDailyWeightTrend(records: WeightRecord[], limit?: number): WeightRecord[]`, sorted oldest to newest with at most `limit` distinct dates.

- [ ] **Step 1: Write the failing test**

```ts
it('keeps the latest record for each day and returns chronological points', () => {
  expect(selectDailyWeightTrend([
    record('2026-07-14', '20:00', 71),
    record('2026-07-14', '08:00', 70),
    record('2026-07-13', '09:00', 69),
  ])).toMatchObject([
    { record_date: '2026-07-13', weight_kg: 69 },
    { record_date: '2026-07-14', weight_kg: 71 },
  ]);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run src/utils/weight-trend.test.ts`

Expected: FAIL because `selectDailyWeightTrend` does not exist.

- [ ] **Step 3: Write minimal implementation**

```ts
export function selectDailyWeightTrend(records: WeightRecord[], limit = 7) {
  const dates = new Set<string>();
  return records.filter((record) => {
    if (dates.has(record.record_date)) return false;
    dates.add(record.record_date);
    return true;
  }).slice(0, limit).reverse();
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --run src/utils/weight-trend.test.ts`

Expected: PASS.

### Task 2: Connect the daily series to the chart

**Files:**
- Modify: `frontend/src/pages/mine/account.vue:37,195-260`
- Test: `frontend/src/utils/weight-trend.test.ts`

**Interfaces:**
- Consumes: `selectDailyWeightTrend(items)`.
- Produces: `weightHistory` with one value per day and the label `近 7 天趋势`.

- [ ] **Step 1: Import and use the selector**

```ts
import { selectDailyWeightTrend } from '@/utils/weight-trend';

weightHistory.value = selectDailyWeightTrend(items);
```

Replace `近 7 次趋势` with `近 7 天趋势`.

- [ ] **Step 2: Run verification**

Run: `npm test -- --run && npx vue-tsc --noEmit && npm run build:mp-weixin`

Expected: all frontend tests pass, no type errors, and the mini-program build completes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/mine/account.vue frontend/src/utils/weight-trend.ts frontend/src/utils/weight-trend.test.ts
git commit -m "优化：按天展示体重趋势"
```
