# Nine Issue Quality Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复九项已确认的导航、资料、体重、训练、统计、饮食和账号页面问题，并以自动化测试和微信小程序构建验证。

**Architecture:** 保持现有 uni-app + Vue 3 前端与 FastAPI + SQLAlchemy 后端结构。把可测试的数据计算提取为小型纯函数，页面只负责交互与渲染；后端在上传用途和动作聚合的数据源处修复根因。

**Tech Stack:** Vue 3、TypeScript、uni-app、Vitest、FastAPI、SQLAlchemy、pytest、微信小程序自定义 tabBar。

## Global Constraints

- 不新增第三方依赖。
- 头像继续使用后端本地上传目录，数据库仅保存文件地址。
- 不实现图片裁剪、对象存储、手机号授权或数据导出后端能力。
- 统计空数据与接口失败必须分别展示。
- 所有生产代码修改先有失败测试；纯样式修复通过构建和页面回归验证。

---

### Task 1: 底部导航状态与“我的”线性图标

**Files:**
- Create: `frontend/src/utils/tabbar.ts`
- Create: `frontend/src/utils/tabbar.test.ts`
- Modify: `frontend/src/custom-tab-bar/index.js`
- Modify: `frontend/src/custom-tab-bar/index.wxml`
- Modify: `frontend/src/custom-tab-bar/index.wxss`
- Modify: `frontend/src/components/LiquidGlassTabBar.vue`
- Modify: `frontend/src/pages/mine/index.vue`

**Interfaces:**
- Produces: `tabIndexForRoute(route: string): number` and `pillTransform(index: number): string`.
- Consumes: existing five fixed tab routes and `LineIcon`.

- [ ] **Step 1: Write failing utility tests**

```ts
import { describe, expect, it } from 'vitest';
import { pillTransform, tabIndexForRoute } from './tabbar';

describe('tabbar state', () => {
  it('maps normalized routes to the correct tab', () => {
    expect(tabIndexForRoute('pages/home/index')).toBe(0);
    expect(tabIndexForRoute('/pages/stats/index')).toBe(3);
    expect(tabIndexForRoute('pages/mine/index')).toBe(4);
  });
  it('uses valid percentage transforms', () => {
    expect(pillTransform(0)).toBe('translateX(0%)');
    expect(pillTransform(3)).toBe('translateX(300%)');
  });
});
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npm test -- --run src/utils/tabbar.test.ts`
Expected: FAIL because `./tabbar` does not exist.

- [ ] **Step 3: Implement the utilities and route-driven component state**

```ts
export const TAB_ROUTES = [
  'pages/home/index', 'pages/diet/index', 'pages/training/index',
  'pages/stats/index', 'pages/mine/index',
] as const;

export function tabIndexForRoute(route: string) {
  return TAB_ROUTES.indexOf(route.replace(/^\//, '') as typeof TAB_ROUTES[number]);
}

export function pillTransform(index: number) {
  return `translateX(${Math.max(0, index) * 100}%)`;
}
```

Update both tab-bar implementations so `onSwitch` sets a navigation lock, calls `switchTab`, and relies on page `show`/route sync to update `activeIdx`; unlock in both success and fail callbacks. Apply the transform as `translateX(${activeIdx * 100}%)`. Replace `GlassIcon` instances in the “我的” grid/menu with `LineIcon` using existing icon names.

- [ ] **Step 4: Verify GREEN and build**

Run: `cd frontend && npm test -- --run src/utils/tabbar.test.ts && npm run build:mp-weixin`
Expected: tests PASS and build exits 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/tabbar.ts frontend/src/utils/tabbar.test.ts frontend/src/custom-tab-bar frontend/src/components/LiquidGlassTabBar.vue frontend/src/pages/mine/index.vue
git commit -m "fix: stabilize tab navigation and icons"
```

### Task 2: 本地永久头像上传

**Files:**
- Modify: `backend/app/api/v1/uploads.py`
- Modify: `backend/tests/test_uploads.py`
- Modify: `frontend/src/api/uploads.ts`
- Modify: `frontend/src/pages/mine/profile.vue`

**Interfaces:**
- Produces: `uploadApi.avatar(filePath: string)` returning `{ file_id, file_url, is_temporary }`.
- Consumes: existing `uploadFile`, `avatar_url` profile field, and `/static/...` serving.

- [ ] **Step 1: Write failing backend and frontend contract tests**

Add an upload policy helper assertion:

```py
from app.api.v1.uploads import upload_policy

def test_avatar_upload_is_allowed_and_permanent():
    assert upload_policy('avatar', False) == ('avatar', False)

def test_avatar_upload_rejects_temporary_storage():
    with pytest.raises(BizException):
        upload_policy('avatar', True)
```

Add a Vitest assertion that `uploadApi.avatar('/tmp/a.png')` delegates with `usage_type='avatar'` and `temporary=false`.

- [ ] **Step 2: Verify RED**

Run: `cd backend && pytest tests/test_uploads.py -q; cd ../frontend && npm test -- --run src/api/uploads.test.ts`
Expected: FAIL because `upload_policy` and `avatar` do not exist.

- [ ] **Step 3: Implement upload policy and profile picker**

```py
ALLOWED_USAGE = {'food_recognition', 'diet_record', 'avatar'}

def upload_policy(usage_type: str, temporary: bool):
    if usage_type not in ALLOWED_USAGE:
        raise BizException(40001, '不支持的图片用途')
    if usage_type == 'avatar' and temporary:
        raise BizException(40001, '头像必须永久保存')
    return usage_type, temporary
```

```ts
avatar(filePath: string) {
  return uploadFile(filePath, { usage_type: 'avatar', temporary: false });
}
```

In `profile.vue`, replace the URL input with a circular image/fallback initial and a button that calls `uni.chooseImage({ count: 1 })`, uploads the selected path, and only then assigns `form.avatar_url`. Disable repeated selection while uploading and keep the old value on failure.

- [ ] **Step 4: Verify GREEN**

Run: `cd backend && pytest tests/test_uploads.py -q; cd ../frontend && npm test -- --run src/api/uploads.test.ts && npm run build:mp-weixin`
Expected: all commands exit 0.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/uploads.py backend/tests/test_uploads.py frontend/src/api/uploads.ts frontend/src/api/uploads.test.ts frontend/src/pages/mine/profile.vue
git commit -m "feat: upload profile avatars locally"
```

### Task 3: 体重记录交互与账号页信息架构

**Files:**
- Create: `frontend/src/utils/weight-record.ts`
- Create: `frontend/src/utils/weight-record.test.ts`
- Modify: `frontend/src/pages/mine/account.vue`

**Interfaces:**
- Produces: `weightRecordToForm(record: WeightRecord)` returning `{ weight, date, time, note }`.
- Consumes: `weightApi.create`, `weightApi.update`, `weightApi.remove`.

- [ ] **Step 1: Write failing edit-mapping test**

```ts
it('maps the selected record into the edit form', () => {
  expect(weightRecordToForm({
    id: 2, user_id: 1, record_date: '2026-07-08', record_time: '08:30',
    weight_kg: 74, note: '晨起',
  })).toEqual({ weight: '74', date: '2026-07-08', time: '08:30', note: '晨起' });
});
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npm test -- --run src/utils/weight-record.test.ts`
Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement mapping, folding, and independent actions**

```ts
export function weightRecordToForm(record: WeightRecord) {
  return { weight: String(record.weight_kg), date: record.record_date,
    time: record.record_time.slice(0, 5), note: record.note || '' };
}
```

Add `recordsExpanded=false`; render records only when expanded. `editWeight(record)` loads all mapped fields and scrolls to the input. `requestDelete(record)` stores a pending record and opens a confirmation whose confirm callback only calls `weightApi.remove`. The save button calls update only when `editingWeightId` is non-null.

For normal account mode, delete the weight section and weight-loading lifecycle calls. Render four explicit groups: account security, data/storage, privacy/agreement, danger. Disabled features have no tap handler and show “开发中”. Keep weight-only mode isolated behind `action=weight`.

- [ ] **Step 4: Verify GREEN and build**

Run: `cd frontend && npm test -- --run src/utils/weight-record.test.ts && npm run build:mp-weixin`
Expected: PASS and build exits 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/weight-record.ts frontend/src/utils/weight-record.test.ts frontend/src/pages/mine/account.vue
git commit -m "fix: separate weight records from account settings"
```

### Task 4: 训练计划输入控件可读性

**Files:**
- Modify: `frontend/src/pages/training/plan-edit.vue`

**Interfaces:**
- Consumes: existing form state only.
- Produces: no new code interface; consistent input box sizing across MP-WEIXIN and H5.

- [ ] **Step 1: Capture the failing layout criteria**

Record before-change screenshots for action name, body part, sets/reps, weight and rest inputs at the supplied viewport. Acceptance: each input has at least `72rpx` rendered height, `box-sizing:border-box`, visible text line-height, and no label overlap.

- [ ] **Step 2: Apply the minimal scoped style fix**

```scss
.input, .day-name-input, .ex-edit-input, .ex-search-input {
  box-sizing: border-box;
  min-width: 0;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 $gap-2;
}
.ex-edit-field { min-width: 0; }
```

Use a left-aligned value for action name/body part and retain right alignment only for compact numeric fields if the existing template distinguishes them.

- [ ] **Step 3: Verify build and layout**

Run: `cd frontend && npm run build:mp-weixin`
Expected: build exits 0. Compare after-change screenshots against the acceptance criteria at the same viewport.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/training/plan-edit.vue
git commit -m "fix: show complete training plan input values"
```

### Task 5: 动作聚合与数据图表

**Files:**
- Create: `backend/app/services/exercise_stats.py`
- Create: `backend/tests/test_stats_service.py`
- Modify: `backend/app/api/v1/stats.py`
- Create: `frontend/src/utils/stats.ts`
- Create: `frontend/src/utils/stats.test.ts`
- Modify: `frontend/src/pages/stats/index.vue`

**Interfaces:**
- Produces: `aggregate_exercise_sets(rows) -> list[dict]`, `hasTrainingData(points)`, and `validWeightPoints(points)`.
- Consumes: completed `TrainingSessionSet` rows and existing stats API types.

- [ ] **Step 1: Write failing aggregation tests**

```py
def test_exercise_stats_prefers_actual_values_and_computes_volume():
    rows = [(exercise('卧推'), training_set(actual_weight_kg=60, actual_reps=8,
             target_weight_kg=50, target_reps=10, completed=1))]
    assert aggregate_exercise_sets(rows)[0]['max_weight_kg'] == 60
    assert aggregate_exercise_sets(rows)[0]['total_volume'] == 480

def test_exercise_stats_falls_back_to_targets_for_legacy_rows():
    rows = [(exercise('卧推'), training_set(actual_weight_kg=None, actual_reps=None,
             target_weight_kg=40, target_reps=12, completed=1))]
    assert aggregate_exercise_sets(rows)[0]['total_volume'] == 480
```

```ts
expect(hasTrainingData([{ date: '2026-07-10', session_count: 1, total_volume: 0, duration_seconds: 1 }])).toBe(true);
expect(validWeightPoints([{ date: 'a', weight_kg: null }, { date: 'b', weight_kg: 74 }])).toHaveLength(1);
```

- [ ] **Step 2: Verify RED**

Run: `cd backend && pytest tests/test_stats_service.py -q; cd ../frontend && npm test -- --run src/utils/stats.test.ts`
Expected: FAIL because the helpers do not exist.

- [ ] **Step 3: Implement backend aggregation**

For each completed set, choose actual values when non-null and non-negative; otherwise choose targets. Compute volume directly from chosen values instead of persisted `set_row.volume`. Group by exercise name and round the final total. Move this logic out of the API route into `exercise_stats.py`.

- [ ] **Step 4: Implement frontend data-state helpers and rendering**

```ts
export const hasTrainingData = (items: TrainingStatPoint[]) =>
  items.some(item => item.session_count > 0 || item.total_volume > 0);
export const validWeightPoints = (items: WeightStatPoint[]) =>
  items.filter(item => item.weight_kg !== null);
```

Only mount training/weight charts when the corresponding helper reports data. Build weight x-axis and series from the same filtered point list. Add `loadFailed` and a retry control; do not clear successfully loaded data on a later failed refresh. Render self-weight/no-weight exercise labels rather than meaningful-looking `0 kg`.

- [ ] **Step 5: Verify GREEN**

Run: `cd backend && pytest tests/test_stats_service.py tests/test_business_rules.py -q; cd ../frontend && npm test -- --run src/utils/stats.test.ts && npm run build:mp-weixin`
Expected: all tests PASS and build exits 0.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/exercise_stats.py backend/app/api/v1/stats.py backend/tests/test_stats_service.py frontend/src/utils/stats.ts frontend/src/utils/stats.test.ts frontend/src/pages/stats/index.vue
git commit -m "fix: calculate and render real training statistics"
```

### Task 6: 饮食日期重新设计与全量回归

**Files:**
- Create: `frontend/src/utils/diet-date.ts`
- Create: `frontend/src/utils/diet-date.test.ts`
- Modify: `frontend/src/pages/diet/index.vue`

**Interfaces:**
- Produces: `dietDateHeading(selected: string, today: string): string` and `compactDateLabel(date: string, month: number): string`.
- Consumes: existing selected date and seven-day strip.

- [ ] **Step 1: Write failing date-label tests**

```ts
expect(dietDateHeading('2026-07-10', '2026-07-10')).toBe('7月10日 · 今天');
expect(dietDateHeading('2026-07-09', '2026-07-10')).toBe('7月9日 · 星期四');
expect(compactDateLabel('2026-08-01', 7)).toBe('8/1');
expect(compactDateLabel('2026-07-09', 7)).toBe('9');
```

- [ ] **Step 2: Verify RED**

Run: `cd frontend && npm test -- --run src/utils/diet-date.test.ts`
Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement labels and two-level date header**

Add a prominent heading above the strip using `dietDateHeading`. In the strip display weekday plus `compactDateLabel`, visibly distinguish today from selected day, and show month/day for cross-month cells. Keep existing date selection handlers.

- [ ] **Step 4: Run complete verification**

Run: `cd backend && pytest -q`
Expected: all backend tests PASS.

Run: `cd frontend && npm test -- --run && npm run build:mp-weixin`
Expected: all frontend tests PASS and MP-WEIXIN build exits 0.

Inspect the nine reported flows in the built mini-program: direct tab jumps, Mine icons, avatar selection/save, folded weight records/edit/delete, plan inputs, training and weight charts, exercise metrics, diet date, and account groups.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/diet-date.ts frontend/src/utils/diet-date.test.ts frontend/src/pages/diet/index.vue
git commit -m "fix: clarify diet date navigation"
```
