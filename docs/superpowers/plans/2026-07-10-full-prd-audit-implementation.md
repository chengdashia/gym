# 健身饮食记录小程序完整需求审计 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以完整汇总文档为验收标准，保留手机号登录/注册主流程，补齐饮食、训练、体重、统计、合规闭环并修复现有缺陷。

**Architecture:** 保持 uni-app + Vue 3 + Pinia 前端和 FastAPI + SQLAlchemy 后端结构。业务约束、日期边界、排期、容量和数据清理由后端统一裁决；前端复用现有页面和组件完成即时校验、交互状态与刷新。数据库迁移直接应用当前 MySQL，接口联调用唯一测试账号并在结束时清理。

**Tech Stack:** TypeScript、Vue 3、uni-app、Pinia、Vitest、vue-tsc、Python 3.11、FastAPI、SQLAlchemy 2、MySQL、Alembic、Pillow。

## Global Constraints

- 手机号登录/注册是本轮主流程；微信授权登录只保留接口，不增加主入口。
- 未登录允许浏览空首页；个人数据入口必须登录。
- token 冷启动恢复，只在明确 `401/40101` 时清除。
- 数据库变更直接执行 Alembic `upgrade head`，不创建隔离测试数据库。
- 联调测试使用唯一前缀账号并在 `finally` 中清理。
- 按日查询使用 `[00:00:00, 次日 00:00:00)` 半开区间。
- 统计范围只支持 `7/30/90` 天。
- API 继续返回 `{code, message, data}`。
- 不实现真实微信授权、正式数据导出、付费、真实 AI 识别或管理后台。
- 不覆盖或暂存任务范围外的现有未跟踪文件。

---

### Task 1: 建立可重复的前后端检查入口

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `backend/requirements.txt`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_nutrition.py`
- Create: `frontend/src/utils/nutrition.test.ts`

**Interfaces:**
- Consumes: 现有 `calc_nutrition_per_100g()`、`calc_nutrition_per_serving()` 和 `calcNutrition()`。
- Produces: `npm test`、`npm run typecheck`、`python -m unittest discover -s tests -v` 三个稳定检查入口。

- [ ] **Step 1: 写后端营养计算测试**

```python
from decimal import Decimal
import unittest

from app.services.nutrition import calc_nutrition_per_100g, calc_nutrition_per_serving


class NutritionTest(unittest.TestCase):
    def setUp(self):
        self.food = {
            "calories_per_100g": 130,
            "carbs_per_100g": 28,
            "protein_per_100g": 2.7,
            "fat_per_100g": 0.3,
        }

    def test_grams_scale_all_nutrients(self):
        result = calc_nutrition_per_100g(self.food, 150)
        self.assertEqual(result["calories_kcal"], Decimal("195.00"))
        self.assertEqual(result["carbs_g"], Decimal("42.00"))

    def test_servings_return_actual_grams(self):
        result = calc_nutrition_per_serving(self.food, 50, 2)
        self.assertEqual(result["amount_g"], Decimal("100.00"))
        self.assertEqual(result["calories_kcal"], Decimal("130.00"))
```

- [ ] **Step 2: 写前端营养预览测试并确认初始检查入口缺失**

```typescript
import { describe, expect, it } from 'vitest';
import { calcNutrition } from './nutrition';

describe('calcNutrition', () => {
  it('按克数计算营养快照', () => {
    const result = calcNutrition(
      { calories_per_100g: 130, carbs_per_100g: 28, protein_per_100g: 2.7, fat_per_100g: 0.3 },
      { unit_type: 'g', amount_g: 150, serving_count: null },
    );
    expect(result.calories).toBe(195);
    expect(result.carbs).toBe(42);
  });
});
```

Run: `cd frontend && npm test`  
Expected: FAIL，提示 `Missing script: test`。

- [ ] **Step 3: 增加最小测试和类型检查依赖**

```json
{
  "scripts": {
    "test": "vitest run",
    "typecheck": "vue-tsc --noEmit"
  },
  "devDependencies": {
    "vitest": "^2.1.9",
    "vue-tsc": "^2.2.0"
  }
}
```

Run: `cd frontend && npm install -D vitest@^2.1.9 vue-tsc@^2.2.0`  
Expected: `package.json` 与 `package-lock.json` 更新，安装成功。

在 `backend/requirements.txt` 增加 TestClient 所需依赖：

```text
httpx==0.28.1
```

- [ ] **Step 4: 运行基础检查**

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest discover -s tests -v`  
Expected: 2 tests PASS。

Run: `cd frontend && npm test && npm run typecheck`  
Expected: 营养测试 PASS；类型检查列出现有错误时记录完整清单，Task 2–9 逐项消除。

- [ ] **Step 5: 提交**

```bash
git add backend/tests backend/requirements.txt frontend/package.json frontend/package-lock.json frontend/src/utils/nutrition.test.ts
git commit -m "test: add baseline business checks"
```

### Task 2: 恢复持久登录并正确清理账户状态

**Files:**
- Create: `frontend/src/store/auth.test.ts`
- Modify: `frontend/src/store/auth.ts:1-128`
- Modify: `frontend/src/store/user.ts:18-74`
- Modify: `frontend/src/pages/mine/account.vue:558-587`
- Modify: `frontend/src/App.vue:1-27`

**Interfaces:**
- Consumes: `getToken()`、`setToken()`、`clearAuth()`、`userApi.getMe()`。
- Produces: `auth.bootstrap(): Promise<void>`，明确 401 清理、网络错误保留缓存；`resetUserState()` 清理业务 store。

- [ ] **Step 1: 写失败测试：冷启动保留有效 token**

```typescript
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

const mocks = vi.hoisted(() => ({
  getToken: vi.fn(() => 'saved-token'),
  clearAuth: vi.fn(),
}));
vi.mock('@/utils/request', () => ({
  getToken: mocks.getToken,
  setToken: vi.fn(),
  clearAuth: mocks.clearAuth,
}));
vi.mock('@/api/user', () => ({
  userApi: { getMe: vi.fn(async () => ({ id: 1, nickname: '测试', agreement_confirmed: true, is_member: false })) },
}));

describe('auth bootstrap', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.stubGlobal('uni', {
      getStorageSync: vi.fn(() => ({ id: 1, agreement_confirmed: true })),
      setStorageSync: vi.fn(), removeStorageSync: vi.fn(),
    });
  });

  it('restores a saved token instead of clearing it', async () => {
    const { useAuthStore } = await import('./auth');
    const auth = useAuthStore();
    await auth.bootstrap();
    expect(auth.token).toBe('saved-token');
    expect(mocks.clearAuth).not.toHaveBeenCalled();
  });
});
```

Run: `cd frontend && npm test -- src/store/auth.test.ts`  
Expected: FAIL，当前实现把 `auth.token` 清空。

- [ ] **Step 2: 实现 token 恢复与错误分类**

```typescript
async _doBootstrap() {
  const savedToken = getToken();
  if (savedToken) this.token = savedToken;
  try {
    const cached = uni.getStorageSync(STORAGE_KEYS.user) as UserBrief | null;
    if (cached) this.user = cached;
  } catch { /* storage unavailable */ }

  this.bootstrapped = true;
  if (!this.token) { this.ready = true; return; }

  try {
    const me = await (await import('@/api/user')).userApi.getMe();
    const userStore = (await import('@/store/user')).useUserStore();
    userStore.me = me;
    this.setUser({
      id: me.id, nickname: me.nickname, avatar_url: me.avatar_url,
      is_new_user: false, agreement_confirmed: me.agreement_confirmed,
      is_member: me.is_member,
    });
  } catch (error: any) {
    if (error?.code === 40101 || error?.statusCode === 401) this.logout();
  } finally {
    this.ready = true;
  }
}
```

- [ ] **Step 3: 注销和删除数据后重置本地业务状态**

```typescript
reset() {
  this.me = null;
  this.goal = { calories_kcal: 0, carbs_g: 0, protein_g: 0, fat_g: 0 };
  this.reminders = [];
}
```

在注销成功分支调用 `userStore.reset()`、`useDietStore().$reset()`、`useTrainingStore().$reset()` 和 `auth.logout()`；删除个人数据后重置业务 store 并保留登录账号。

注册表单中的《用户协议》和《隐私政策》分别可点击进入现有协议页面，点击链接不能误切换勾选框状态。

- [ ] **Step 4: 验证红绿循环**

Run: `cd frontend && npm test -- src/store/auth.test.ts && npm run typecheck`  
Expected: PASS，且无新的类型错误。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/store/auth.ts frontend/src/store/auth.test.ts frontend/src/store/user.ts frontend/src/pages/mine/account.vue frontend/src/App.vue
git commit -m "fix: persist authenticated sessions"
```

### Task 3: 集中业务校验、日期边界与目标提醒规则

**Files:**
- Create: `backend/tests/test_business_rules.py`
- Create: `backend/app/services/validation.py`
- Modify: `backend/app/utils/date.py:1-25`
- Modify: `backend/app/schemas/__init__.py:122-420`

**Interfaces:**
- Produces: `day_bounds(d) -> tuple[datetime, datetime]`、`validate_diet_quantity(...)`、`validate_plan_days(...)`、`should_reassess_goal(...) -> bool`。

- [ ] **Step 1: 写失败测试**

```python
from datetime import date, datetime
import unittest

from app.services.validation import should_reassess_goal, validate_diet_quantity, validate_plan_days
from app.utils.date import day_bounds


class BusinessRulesTest(unittest.TestCase):
    def test_day_bounds_are_half_open(self):
        start, end = day_bounds(date(2026, 7, 10))
        self.assertEqual(start, datetime(2026, 7, 10))
        self.assertEqual(end, datetime(2026, 7, 11))

    def test_diet_quantity_requires_positive_selected_unit(self):
        with self.assertRaises(ValueError):
            validate_diet_quantity('g', None, None)
        self.assertEqual(validate_diet_quantity('serving', None, 1), ('serving', None, 1))

    def test_weekly_plan_rejects_duplicate_weekdays(self):
        days = [
            {'day_name': '胸', 'weekday': 1, 'is_rest_day': False, 'exercises': [1]},
            {'day_name': '背', 'weekday': 1, 'is_rest_day': False, 'exercises': [1]},
        ]
        with self.assertRaises(ValueError):
            validate_plan_days('weekly', days)

    def test_reassessment_rule(self):
        self.assertTrue(should_reassess_goal('fat_loss', 70, 70.2, 14))
        self.assertFalse(should_reassess_goal('shaping', 70, 72, 30))
```

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_business_rules -v`  
Expected: FAIL，目标模块不存在。

- [ ] **Step 2: 实现纯业务规则**

```python
def should_reassess_goal(goal: str | None, first: float, latest: float, span_days: int) -> bool:
    if span_days < 14 or first <= 0:
        return False
    if goal == "fat_loss":
        return latest >= first
    if goal == "muscle_gain":
        return latest <= first
    if goal == "maintain":
        return abs(latest - first) / first > 0.02
    return False
```

`validate_diet_quantity` 对 `g` 要求 `amount_g > 0`，对 `serving` 要求 `serving_count > 0`；`validate_plan_days` 验证非空训练日、非休息日动作非空和 weekly 星期唯一。

- [ ] **Step 3: 在 Pydantic schema 中调用规则**

使用 `@model_validator(mode="after")` 校验 `DietRecordIn`、`DietRecordUpdateIn`、`PlanIn` 和提醒星期字符串。更新饮食时只有涉及单位/数量字段才做组合校验，并允许后端结合原记录补齐旧值。

- [ ] **Step 4: 运行测试**

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_business_rules -v`  
Expected: 全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/validation.py backend/app/utils/date.py backend/app/schemas/__init__.py backend/tests/test_business_rules.py
git commit -m "feat: enforce core business rules"
```

### Task 4: 完成饮食三种添加方式和图片生命周期

**Files:**
- Create: `backend/app/services/uploads.py`
- Create: `backend/tests/test_uploads.py`
- Modify: `backend/app/api/v1/uploads.py:1-72`
- Modify: `backend/app/api/v1/diet.py:23-234`
- Modify: `backend/app/schemas/__init__.py:157-252`
- Modify: `frontend/src/api/diet.ts:39-70`
- Modify: `frontend/src/pages/diet/add.vue:1-301`
- Modify: `frontend/src/pages/diet/custom-food.vue:1-115`
- Modify: `frontend/src/pages/diet/photo-recognize.vue:88-203`
- Modify: `frontend/src/pages/diet/record-edit.vue:80-177`

**Interfaces:**
- Produces: `DietRecordIn.image_file_id?: int`、`finalize_upload(db, user_id, file_id, keep)`、所有添加页面统一提交日期/时间/餐次/数量。

- [ ] **Step 1: 写失败测试：真实图片校验与文件清理路径**

```python
import unittest
from app.services.uploads import validate_image_bytes


class UploadTest(unittest.TestCase):
    def test_rejects_fake_png(self):
        with self.assertRaises(ValueError):
            validate_image_bytes(b"not an image", ".png")
```

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_uploads -v`  
Expected: FAIL，上传服务不存在。

- [ ] **Step 2: 实现上传校验和 24 小时过期**

```python
def validate_image_bytes(contents: bytes, extension: str) -> str:
    if not contents:
        raise ValueError("图片内容为空")
    with Image.open(io.BytesIO(contents)) as image:
        image.verify()
        fmt = (image.format or "").lower()
    allowed = {"jpeg", "png", "webp", "gif"}
    if fmt not in allowed:
        raise ValueError("不支持的图片内容")
    return fmt
```

上传记录写入 `expired_at=datetime.utcnow()+timedelta(hours=24)`；每次上传前查询并删除过期临时文件。`usage_type` 只接受 `food_recognition/diet_record`。

- [ ] **Step 3: 饮食创建时完成图片确认**

前端始终提交 `image_file_id`。后端校验文件属于当前用户：`keep=True` 时设 `is_temporary=0, usage_type='diet_record', expired_at=None`；`keep=False` 时提交业务事务后删除数据库文件记录和磁盘文件。记录的 `image_url` 仅在 `save_image=True` 时保存。

- [ ] **Step 4: 补齐前端表单**

搜索、自定义和拍照页面统一加入原生日期/时间 picker。自定义食物页面保存食物后立即调用：

```typescript
const food = await foodApi.createCustom(foodPayload);
await dietApi.create({
  record_date: form.record_date,
  record_time: form.record_time,
  meal_type: form.meal_type,
  food_source: 'custom',
  custom_food_id: food.id,
  unit_type: form.unit_type,
  amount_g: form.unit_type === 'g' ? form.amount : null,
  serving_count: form.unit_type === 'serving' ? form.amount : null,
});
```

记录编辑页拒绝零数量；拍照页校验候选和数量并传 `image_file_id`。

- [ ] **Step 5: 验证**

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_uploads tests.test_business_rules -v`  
Expected: PASS。

Run: `cd frontend && npm test && npm run typecheck && npm run build:h5`  
Expected: PASS，H5 构建退出码 0。

- [ ] **Step 6: 提交**

```bash
git add backend/app/services/uploads.py backend/app/api/v1/uploads.py backend/app/api/v1/diet.py backend/app/schemas/__init__.py backend/tests/test_uploads.py frontend/src/api/diet.ts frontend/src/pages/diet/add.vue frontend/src/pages/diet/custom-food.vue frontend/src/pages/diet/photo-recognize.vue frontend/src/pages/diet/record-edit.vue
git commit -m "feat: complete diet entry flows"
```

### Task 5: 约束训练计划并支持自定义动作

**Files:**
- Modify: `backend/app/api/v1/training.py:113-330`
- Modify: `frontend/src/pages/training/plan-edit.vue:1-569`
- Modify: `frontend/src/api/training.ts:1-156`
- Modify: `frontend/src/api/exercises.ts:1-22`
- Create: `frontend/src/utils/training-plan.ts`
- Create: `frontend/src/utils/training-plan.test.ts`

**Interfaces:**
- Produces: `validateTrainingPlan(plan): string | null`；自定义动作创建后返回 `ExerciseItem` 并写入当前动作编辑器。

- [ ] **Step 1: 写失败测试：不可执行计划不能保存**

```typescript
import { describe, expect, it } from 'vitest';
import { validateTrainingPlan } from './training-plan';

describe('validateTrainingPlan', () => {
  it('rejects a workout day with no exercises', () => {
    expect(validateTrainingPlan({
      name: '计划', schedule_type: 'sequence',
      days: [{ day_name: 'Day1', is_rest_day: false, weekday: null, exercises: [] }],
    } as any)).toBe('训练日“Day1”至少需要一个动作');
  });
});
```

Run: `cd frontend && npm test -- src/utils/training-plan.test.ts`  
Expected: FAIL，模块不存在。

- [ ] **Step 2: 实现前端计划校验并接入保存**

校验计划名称、训练日、weekly 星期唯一、非休息日动作、组数 `1..20`、次数 `1..100`、重量 `>=0`、休息 `10..600`。`save()` 在发请求前展示第一条错误。

- [ ] **Step 3: 增加自定义动作创建**

动作搜索为空时显示“创建自定义动作”，部位使用 `胸/背/肩/腿/手臂/核心/有氧/其他` picker。创建成功后设置：

```typescript
const created = await exerciseApi.createCustom({ name, body_part, description });
selectExerciseFromSearch({ ...created, source: 'custom' });
```

- [ ] **Step 4: 后端复用同一规则语义**

`create_plan()`、`update_plan()` 在任何删除或写入前调用 `validate_plan_days()`；系统动作必须 `status='active'`，自定义动作必须属于当前用户且未删除。

- [ ] **Step 5: 验证与提交**

Run: `cd frontend && npm test -- src/utils/training-plan.test.ts && npm run typecheck`  
Expected: PASS。

```bash
git add backend/app/api/v1/training.py frontend/src/pages/training/plan-edit.vue frontend/src/api/training.ts frontend/src/api/exercises.ts frontend/src/utils/training-plan.ts frontend/src/utils/training-plan.test.ts
git commit -m "feat: validate training plans and custom exercises"
```

### Task 6: 修复训练排期、session 状态和倒计时退出流程

**Files:**
- Create: `backend/tests/test_training_rules.py`
- Modify: `backend/app/services/schedule.py:1-64`
- Modify: `backend/app/api/v1/training.py:332-679`
- Modify: `backend/app/api/v1/home.py:66-110`
- Modify: `frontend/src/pages/training/execute.vue:1-491`
- Modify: `frontend/src/pages/training/index.vue:1-317`
- Modify: `frontend/src/components/RestTimer.vue:1-102`
- Create: `frontend/src/static/audio/timer-done.wav`

**Interfaces:**
- Produces: `next_sequence_day_index(days, current) -> int`；session 更新支持 `completed=False`；同用户已有未完成 session 时创建接口返回该 session。

- [ ] **Step 1: 写失败测试：顺序推进跳过休息日**

```python
import unittest
from types import SimpleNamespace
from app.services.schedule import next_sequence_day_index


class TrainingRulesTest(unittest.TestCase):
    def test_sequence_advances_and_skips_rest(self):
        days = [
            SimpleNamespace(day_index=1, sort_order=1, is_rest_day=0),
            SimpleNamespace(day_index=2, sort_order=2, is_rest_day=1),
            SimpleNamespace(day_index=3, sort_order=3, is_rest_day=0),
        ]
        self.assertEqual(next_sequence_day_index(days, 1), 3)
        self.assertEqual(next_sequence_day_index(days, 3), 1)
```

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_training_rules -v`  
Expected: FAIL，函数不存在。

- [ ] **Step 2: 修复 sequence 推进与今日状态**

`finish_session()` 完成事务内调用 `advance_sequence_plan()`。`today()` 和首页先查询当前用户任意 `in_progress/paused` session；存在时返回其 session ID、名称和动作数，即使用户之后切换了计划。当天已完成 session 时返回 `completed/today_completed`，再练一次使用已推进后的训练日。

- [ ] **Step 3: 防止重复 session 并修复组状态重算**

`create_session()` 首先返回已有未完成 session。更新每组时始终执行：

```python
row.completed = 1 if set_in.completed else 0
row.completed_at = datetime.utcnow() if set_in.completed else None
row.volume = Decimal(str(row.actual_weight_kg or 0)) * Decimal(str(row.actual_reps or 0)) if row.completed else 0
```

每个动作处理完后从数据库对象全集重算 `completed_sets`；session 容量从所有已完成组重算。

- [ ] **Step 4: 前端保存取消勾选并补齐退出动作**

`toggleSet()` 无论勾选还是取消都调用 `schedulePersist()`。退出使用 `uni.showActionSheet` 提供“保存进度 / 标记完成 / 放弃训练”，取消 action sheet 即继续训练；放弃需要二次确认。

- [ ] **Step 5: 补齐倒计时开关、手动开始和声音**

增加 `autoRestEnabled`，关闭后勾组不自动弹出；页面提供“开始休息”按钮。使用 0.3 秒本地 WAV，倒计时结束时 `InnerAudioContext` 播放；播放失败保留 toast 和震动。组件卸载时销毁音频和计时器。

Run: `cd frontend && mkdir -p src/static/audio && ffmpeg -f lavfi -i "sine=frequency=880:duration=0.3" -ar 22050 -ac 1 -y src/static/audio/timer-done.wav`  
Expected: 生成可播放的单声道 WAV，时长约 0.3 秒。

- [ ] **Step 6: 验证与提交**

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_training_rules -v`  
Expected: PASS。

Run: `cd frontend && npm test && npm run typecheck && npm run build:mp-weixin`  
Expected: PASS，微信小程序构建退出码 0。

```bash
git add backend/app/services/schedule.py backend/app/api/v1/training.py backend/app/api/v1/home.py backend/tests/test_training_rules.py frontend/src/pages/training/execute.vue frontend/src/pages/training/index.vue frontend/src/components/RestTimer.vue frontend/src/static/audio/timer-done.wav
git commit -m "fix: close training execution loop"
```

### Task 7: 完成体重记录 CRUD 与资料同步

**Files:**
- Create: `backend/tests/test_weight_rules.py`
- Modify: `backend/app/api/v1/weight.py:1-105`
- Modify: `backend/app/services/stats_service.py:78-111`
- Modify: `frontend/src/pages/mine/account.vue:1-850`
- Modify: `frontend/src/api/weight.ts:1-24`

**Interfaces:**
- Produces: `sync_profile_current_weight(db, user_id)`；体重表单支持新增/编辑，历史行支持删除。

- [ ] **Step 1: 写失败测试：最新记录排序键确定**

```python
import unittest
from datetime import date, time
from app.api.v1.weight import weight_sort_key


class WeightRulesTest(unittest.TestCase):
    def test_latest_weight_uses_date_time_and_id(self):
        older = type('R', (), {'record_date': date(2026, 7, 10), 'record_time': time(8), 'id': 1})()
        newer = type('R', (), {'record_date': date(2026, 7, 10), 'record_time': time(8), 'id': 2})()
        self.assertGreater(weight_sort_key(newer), weight_sort_key(older))
```

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_weight_rules -v`  
Expected: FAIL，排序 helper 不存在。

- [ ] **Step 2: 后端在 CRUD 后同步资料当前体重**

新增或更新后将最新有效记录写入 `UserProfile.current_weight_kg`；删除最新记录后回退到下一条有效记录，没有记录时保留资料原值。查询排序增加 `WeightRecord.id.desc()`，同日统计按 `record_time` 选择最新。

- [ ] **Step 3: 前端补齐日期、时间、备注、编辑和删除**

账号页复用一个响应式表单：

```typescript
const weightForm = reactive({ id: 0, weight_kg: '', record_date: today(), record_time: nowTime(), note: '' });
```

`id===0` 调用 create，否则 update。历史记录显示日期、时间、重量和备注；点击编辑回填表单；删除使用 `ModalConfirm` 并在成功后 `loadWeight()`。

- [ ] **Step 4: 验证与提交**

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_weight_rules -v`  
Expected: PASS。

Run: `cd frontend && npm run typecheck && npm run build:h5`  
Expected: PASS。

```bash
git add backend/app/api/v1/weight.py backend/app/services/stats_service.py backend/tests/test_weight_rules.py frontend/src/pages/mine/account.vue frontend/src/api/weight.ts
git commit -m "feat: complete weight record CRUD"
```

### Task 8: 修复首页聚合并补充训练重量趋势和目标提醒

**Files:**
- Create: `backend/tests/test_stats_rules.py`
- Modify: `backend/app/services/stats_service.py:1-111`
- Modify: `backend/app/api/v1/stats.py:1-67`
- Modify: `backend/app/api/v1/home.py:1-137`
- Modify: `backend/app/schemas/__init__.py:493-568`
- Modify: `frontend/src/api/home.ts:1-43`
- Modify: `frontend/src/api/stats.ts:1-38`
- Modify: `frontend/src/pages/home/index.vue:1-260`
- Modify: `frontend/src/pages/stats/index.vue:1-387`

**Interfaces:**
- Produces: `exercise_weight_trends: [{exercise_name, points:[{date,max_weight_kg}]}]`；首页 `goal_reassessment_suggested: boolean`。

- [ ] **Step 1: 写失败测试：动作重量按日取已完成组最大值**

```python
import unittest
from app.services.stats_service import build_exercise_weight_trends


class StatsRulesTest(unittest.TestCase):
    def test_exercise_trend_uses_daily_max(self):
        rows = [
            ('卧推', '2026-07-01', 60),
            ('卧推', '2026-07-01', 65),
            ('卧推', '2026-07-08', 67.5),
        ]
        self.assertEqual(build_exercise_weight_trends(rows), [{
            'exercise_name': '卧推',
            'points': [
                {'date': '2026-07-01', 'max_weight_kg': 65.0},
                {'date': '2026-07-08', 'max_weight_kg': 67.5},
            ],
        }])
```

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_stats_rules -v`  
Expected: FAIL，helper 不存在。

- [ ] **Step 2: 后端实现动作重量趋势和首页提醒**

只查询 `completed` session 与 `completed=1` 的组，按动作快照、日期聚合最大实际重量。首页读取至少相隔 14 天的首末体重，调用 `should_reassess_goal()`；没有足够数据返回 `False`。

- [ ] **Step 3: 修复首页显示与刷新**

首页饮食面板加入记录数量、“添加饮食”按钮和目标缺失提示；训练状态显示 paused/completed；`onShow` 同时刷新用户目标和首页 summary。目标提醒点击进入 `/pages/mine/goals`。

- [ ] **Step 4: 数据页展示动作趋势**

训练统计响应保留 `items` 并增加 `exercise_weight_trends`。数据页增加动作选择药丸和重量折线；无完成重量时显示明确空状态。

- [ ] **Step 5: 验证与提交**

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_stats_rules tests.test_business_rules -v`  
Expected: PASS。

Run: `cd frontend && npm test && npm run typecheck && npm run build:h5`  
Expected: PASS。

```bash
git add backend/app/services/stats_service.py backend/app/api/v1/stats.py backend/app/api/v1/home.py backend/app/schemas/__init__.py backend/tests/test_stats_rules.py frontend/src/api/home.ts frontend/src/api/stats.ts frontend/src/pages/home/index.vue frontend/src/pages/stats/index.vue
git commit -m "feat: complete dashboard and progress statistics"
```

### Task 9: 完整个人数据清理与提醒校验

**Files:**
- Create: `backend/app/services/user_data.py`
- Create: `backend/tests/test_user_data.py`
- Modify: `backend/app/api/v1/users.py:192-290`
- Modify: `backend/app/api/v1/auth.py:112-186`
- Modify: `frontend/src/pages/mine/reminders.vue:67-146`
- Modify: `frontend/src/pages/mine/account.vue:126-181`

**Interfaces:**
- Produces: `delete_user_data(db, user_id, keep_account=True)`；注销调用同一服务并将账号设为 cancelled。

- [ ] **Step 1: 写失败测试：清理清单完整**

```python
import unittest
from app.services.user_data import PERSONAL_DATA_MODELS
from app.models import DietRecord, NutritionGoal, TrainingPlan, TrainingSession, UserProfile, UserReminder, WeightRecord


class UserDataTest(unittest.TestCase):
    def test_cleanup_covers_core_personal_models(self):
        required = {DietRecord, NutritionGoal, TrainingPlan, TrainingSession, UserProfile, UserReminder, WeightRecord}
        self.assertTrue(required.issubset(set(PERSONAL_DATA_MODELS)))
```

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_user_data -v`  
Expected: FAIL，清理服务不存在。

- [ ] **Step 2: 实现单一清理服务**

按外键依赖顺序硬删除 session sets/exercises、计划 exercises/days，再删除或软删除顶层业务记录。删除 `UploadedFile` 前收集文件路径，事务成功后删除物理文件。`delete-data` 保留用户账号、协议和手机号；删除 profile、目标和提醒。`cancel-account` 调用同一清理服务，再清空手机号、昵称、头像并设 `status='cancelled', deleted_at=utcnow()`。

- [ ] **Step 3: 校验提醒并修复账户页面反馈**

提醒启用时必须有合法 `HH:MM`；weekdays 只允许不重复的 `1..7`。账号页将当前手机号按 `173****1234` 形式显示，增加最近一次成功请求对应的“数据已同步”状态，并继续保留数据导出占位入口。删除数据成功后页面清空图表和记录并提示重新完善资料；注销成功后调用本地 logout。

- [ ] **Step 4: 验证与提交**

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest tests.test_user_data tests.test_business_rules -v`  
Expected: PASS。

```bash
git add backend/app/services/user_data.py backend/app/api/v1/users.py backend/app/api/v1/auth.py backend/tests/test_user_data.py frontend/src/pages/mine/reminders.vue frontend/src/pages/mine/account.vue
git commit -m "fix: fully remove personal data"
```

### Task 10: 同步数据库并执行真实闭环验收

**Files:**
- Create: `backend/scripts/smoke_full.py`
- Modify: `backend/README.md`
- Modify: `frontend/README.md`
- Modify: `docs/健身饮食记录小程序_完整汇总文档.md` only if implementation-specific command documentation is inaccurate

**Interfaces:**
- Consumes: 当前 `settings.db_url`、FastAPI TestClient、全部业务 API。
- Produces: 一次性完整 smoke 结果和 `finally` 清理；最终需求覆盖清单。

- [ ] **Step 1: 检查模型与数据库 revision**

Run: `cd backend && alembic -c alembic.ini current`  
Expected: 输出当前 revision；记录是否已包含手机号和 `password_hash` 迁移。

Run: `cd backend && alembic -c alembic.ini heads`  
Expected: 仅一个 head。

- [ ] **Step 2: 如存在模型差异，生成并审阅最小迁移**

Run: `cd backend && alembic -c alembic.ini revision --autogenerate -m "sync prd audit schema"`  
Expected: 迁移只包含本轮必需字段；如果无差异，不保留空迁移。

- [ ] **Step 3: 直接同步当前数据库**

Run: `cd backend && alembic -c alembic.ini upgrade head`  
Expected: 退出码 0，`alembic current` 等于唯一 head。

- [ ] **Step 4: 编写真实数据库 smoke 脚本**

脚本使用 `smoke_<timestamp>` 唯一手机号/昵称，通过 TestClient 覆盖：captcha 注册、登录态、协议、资料、推荐与手动目标、自定义食物与饮食 CRUD、上传与 mock 识别、计划与自定义动作、session 保存/取消勾选/暂停/继续/完成、体重 CRUD、首页、三类统计、提醒、删除数据和注销。`finally` 调用数据库清理服务并删除测试用户及上传文件。

- [ ] **Step 5: 运行完整后端验证**

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m compileall -q app tests scripts`  
Expected: 退出码 0。

Run: `cd backend && PYTHONPYCACHEPREFIX=/tmp/gym-pycache python3 -m unittest discover -s tests -v`  
Expected: 0 failures，0 errors。

Run: `cd backend && python3 scripts/smoke_full.py`  
Expected: 每个闭环打印 PASS，最终打印 `cleanup: PASS`。

- [ ] **Step 6: 运行完整前端验证**

Run: `cd frontend && npm test`  
Expected: 0 failed tests。

Run: `cd frontend && npm run typecheck`  
Expected: 退出码 0。

Run: `cd frontend && npm run build:h5`  
Expected: `DONE Build complete.`。

Run: `cd frontend && npm run build:mp-weixin`  
Expected: `DONE Build complete.` 且 postbuild patch 成功。

- [ ] **Step 7: 浏览器验证关键流程**

启动 H5 与后端，使用移动视口验证：应用非空、登录/注册、首次引导、五个主页面、添加饮食、自定义食物、训练计划、训练执行与退出、体重新增编辑删除、7/30/90 天切换、提醒和删除数据确认。每次交互后检查 URL/可见状态，并读取 error/warn 日志；只允许说明清楚的框架依赖警告。

- [ ] **Step 8: 更新文档并提交**

```bash
git add backend/scripts/smoke_full.py backend/README.md frontend/README.md
git commit -m "test: verify complete product workflows"
```

- [ ] **Step 9: 最终需求覆盖复核**

逐条重读设计文档第 3、6、7 节，将每项映射到测试、构建或浏览器证据。未在真实微信开发者工具验证的相机、震动、声音和自定义 tabBar 明确列为人工验收项，不用 H5 结果替代。
