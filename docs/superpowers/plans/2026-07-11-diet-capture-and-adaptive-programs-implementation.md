# Diet Capture and Adaptive Programs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构饮食记录与拍照确认流程，并交付资格筛查、四类饮食方案、532 阶段评估、七日菜单、替换和加入实际记录的完整闭环。

**Architecture:** 保持 FastAPI + SQLAlchemy 与 uni-app + Vue 3 + Pinia。规则引擎是热量、安全边界、方案状态和过敏约束的唯一裁决者；版本化菜单模板提供可执行餐食，前端只展示和提交用户选择。现有 `DietRecord`、`WeightRecord` 和营养目标继续作为实际执行数据，方案阶段与菜单保存快照。

**Tech Stack:** Python 3、FastAPI、SQLAlchemy 2、Alembic、Pydantic 2、MySQL、Vue 3、TypeScript、uni-app、Pinia、pytest、Vitest。

## Global Constraints

- 不实现真实 AI provider；mock 识别必须显著标记。
- 不满足资格的用户只保留普通记录，不生成方案。
- 过敏、素食、忌口是后端硬约束。
- 532 只允许改变碳水；蛋白质和脂肪阶段间保持不变。
- 方案建议必须由用户确认后生效。
- 不引入优化器、队列、Redis 或新前端 UI 框架。
- 不暂存、删除或覆盖任务范围外的现有文件。

---

### Task 1: 统一饮食记录上下文并重构拍摄前页面

**Files:**
- Create: `frontend/src/utils/diet-context.ts`
- Create: `frontend/src/utils/diet-context.test.ts`
- Modify: `frontend/src/pages/diet/index.vue`
- Modify: `frontend/src/pages/diet/add.vue`
- Modify: `frontend/src/pages/diet/custom-food.vue`
- Modify: `frontend/src/pages/diet/photo-recognize.vue`

**Interfaces:**
- Produces: `DietRecordContext { date: string; meal: MealType; time: string }`、`buildDietEntryUrl(path, context)`、`parseDietContext(options, fallback)`。

- [ ] **Step 1: 写失败测试**

```typescript
it('passes date and meal to every diet entry', () => {
  expect(buildDietEntryUrl('/pages/diet/photo-recognize', {
    date: '2026-07-11', meal: 'lunch', time: '12:10',
  })).toBe('/pages/diet/photo-recognize?date=2026-07-11&meal=lunch&time=12%3A10');
});

it('rejects an invalid meal and keeps the fallback', () => {
  expect(parseDietContext({ meal: 'unknown' }, fallback).meal).toBe(fallback.meal);
});
```

- [ ] **Step 2: 运行并确认 helper 不存在而失败**

Run: `cd frontend && npm test -- src/utils/diet-context.test.ts`  
Expected: FAIL。

- [ ] **Step 3: 实现最小 helper 并改造所有入口**

饮食页的餐次内添加按钮传递当前日期与餐次；全局添加弹层先显示四餐选择，搜索、自定义和拍照均使用同一个 URL helper。各目标页使用 `parseDietContext` 初始化，不再自行推断或丢失参数。

- [ ] **Step 4: 重构拍摄前状态**

按已批准视觉稿实现日期、四餐选择、相机框、主按钮“拍照识别”、次按钮“从相册选择”和隐私说明；移除大面积空白。按钮保持 44px 以上触控区域和安全区底部留白。

- [ ] **Step 5: 验证**

Run: `cd frontend && npm test -- src/utils/diet-context.test.ts && npm run typecheck`  
Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/utils/diet-context.ts frontend/src/utils/diet-context.test.ts frontend/src/pages/diet/index.vue frontend/src/pages/diet/add.vue frontend/src/pages/diet/custom-food.vue frontend/src/pages/diet/photo-recognize.vue
git commit -m "fix: preserve meal context across diet entry flows"
```

### Task 2: 把识别结果升级为可编辑多食物确认

**Files:**
- Modify: `backend/app/schemas/__init__.py`
- Modify: `backend/app/api/v1/ai.py`
- Create: `backend/tests/test_food_recognition_items.py`
- Modify: `frontend/src/api/ai.ts`
- Modify: `frontend/src/pages/diet/photo-recognize.vue`
- Create: `frontend/src/utils/recognized-meal.ts`
- Create: `frontend/src/utils/recognized-meal.test.ts`

**Interfaces:**
- Produces: `recognized_items[]`，每项包含 `food_id/source/name/confidence/estimated_amount_g`；前端 `RecognizedMealItem` 和营养汇总函数。

- [ ] **Step 1: 写后端失败测试**

```python
def test_mock_recognition_returns_editable_items(recognition_payload):
    items = recognition_payload["recognized_items"]
    assert items
    assert set(items[0]) >= {"food_id", "source", "name", "confidence", "estimated_amount_g"}
```

Run: `cd backend && pytest -q tests/test_food_recognition_items.py`  
Expected: FAIL，当前仅返回 `candidates`。

- [ ] **Step 2: 写前端失败测试**

```typescript
it('sums nutrition for edited recognized items', () => {
  expect(summarizeRecognizedMeal(items).calories).toBe(526);
});
```

- [ ] **Step 3: 后端兼容升级**

mock provider 从系统食物中生成 1–3 个 `recognized_items`，保留 `provider: mock`；迁移期可同时返回旧 `candidates`，但前端只消费新结构。日志保存完整 items JSON。

- [ ] **Step 4: 实现确认状态页面**

显示照片、目标餐次、可编辑食物列表、克数输入、删除/替换、模拟提示、整餐营养汇总和“保存到{餐次}”。保存时逐项创建 DietRecord；所有项成功后返回，部分失败时保留草稿并显示失败项，不清空用户输入。

- [ ] **Step 5: 验证并提交**

Run: `cd backend && pytest -q tests/test_food_recognition_items.py && pytest -q`  
Run: `cd frontend && npm test && npm run typecheck`  
Expected: PASS。

```bash
git add backend/app/schemas/__init__.py backend/app/api/v1/ai.py backend/tests/test_food_recognition_items.py frontend/src/api/ai.ts frontend/src/pages/diet/photo-recognize.vue frontend/src/utils/recognized-meal.ts frontend/src/utils/recognized-meal.test.ts
git commit -m "feat: confirm recognized meals as editable food items"
```

### Task 3: 增加饮食方案模型、纤维字段和数据库迁移

**Files:**
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/20260711_1200_add_diet_programs.py`
- Create: `backend/tests/test_diet_program_models.py`
- Modify: `backend/app/api/v1/foods.py`
- Modify: `backend/app/seed/seed_data.py`

**Interfaces:**
- Produces: `DietPreference`、`DietProgramTemplate`、`UserDietProgram`、`DietProgramStage`、`MealPlanDay`、`MealPlanMeal`、`MealPlanItem`；`Food.fiber_per_100g` 与 `UserCustomFood.fiber_per_100g`。

- [ ] **Step 1: 写模型元数据失败测试**

```python
def test_diet_program_tables_exist_in_metadata():
    expected = {"diet_preferences", "diet_program_templates", "user_diet_programs",
                "diet_program_stages", "meal_plan_days", "meal_plan_meals", "meal_plan_items"}
    assert expected <= set(Base.metadata.tables)

def test_foods_include_fiber():
    assert "fiber_per_100g" in Food.__table__.columns
```

- [ ] **Step 2: 实现聚焦模型**

JSON 仅保存偏好/规则/筛查快照；可查询的状态、日期、阶段序号和宏量目标使用独立列。关系使用 `cascade="all, delete-orphan"`；所有用户资源增加 `user_id` 可索引过滤或通过 program 关系确定所有权。

- [ ] **Step 3: 编写 Alembic 迁移**

迁移只新增字段、表、索引和外键，不改写已有饮食记录。纤维字段 nullable；downgrade 以子表到父表顺序删除。

- [ ] **Step 4: 更新食物输出和种子**

食物 API 返回 fiber；种子只给有可靠数据的基础食物填充纤维，未知值保持 null，不伪造 0。

- [ ] **Step 5: 验证迁移**

Run: `cd backend && pytest -q tests/test_diet_program_models.py`  
Run: `cd backend && alembic upgrade head`  
Run: `cd backend && alembic current`  
Expected: revision 为 `20260711_1200`。

- [ ] **Step 6: 提交**

```bash
git add backend/app/models/__init__.py backend/alembic/versions/20260711_1200_add_diet_programs.py backend/tests/test_diet_program_models.py backend/app/api/v1/foods.py backend/app/seed/seed_data.py
git commit -m "feat: add adaptive diet program data model"
```

### Task 4: 实现资格筛查、偏好和方案模板

**Files:**
- Create: `backend/app/api/v1/diet_programs.py`
- Create: `backend/app/services/diet_eligibility.py`
- Create: `backend/app/services/diet_templates.py`
- Create: `backend/tests/test_diet_eligibility.py`
- Create: `backend/tests/test_diet_preferences.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/schemas/__init__.py`

**Interfaces:**
- Produces: `check_eligibility(payload) -> EligibilityResult`；`GET /diet-programs/templates`；`POST /eligibility`；`GET/PUT /preferences`。

- [ ] **Step 1: 写筛查失败测试**

```python
@pytest.mark.parametrize("field", ["under_18", "pregnant_or_breastfeeding", "diabetes",
                                    "serious_liver_kidney_gallbladder", "eating_disorder_history"])
def test_risk_flags_block_program_generation(field):
    payload = safe_payload | {field: True}
    assert check_eligibility(payload).eligible is False
```

- [ ] **Step 2: 实现纯规则筛查**

返回 `eligible/reasons/next_action`，不在原因中暴露不必要的健康详情。失败时 next_action 固定为普通记录与专业咨询。

- [ ] **Step 3: 实现偏好校验**

每日餐数限制 2–6；过敏原和餐数必填；时间窗、预算、厨具和枚举值后端校验。保存时覆盖当前偏好，但创建方案时复制偏好快照。

- [ ] **Step 4: 提供四个版本化模板**

模板代码为 `balanced_cut`、`time_restricted_16_8`、`carb_taper_532`、`ketogenic`。生酮模板标记 `strict=true` 与 `requires_fiber=true`。

- [ ] **Step 5: 验证并提交**

Run: `cd backend && pytest -q tests/test_diet_eligibility.py tests/test_diet_preferences.py && pytest -q`  
Expected: PASS。

```bash
git add backend/app/api/v1/diet_programs.py backend/app/services/diet_eligibility.py backend/app/services/diet_templates.py backend/tests/test_diet_eligibility.py backend/tests/test_diet_preferences.py backend/app/main.py backend/app/schemas/__init__.py
git commit -m "feat: add diet eligibility and preferences"
```

### Task 5: 实现热量、宏量营养和 532 阶段规则引擎

**Files:**
- Create: `backend/app/services/diet_program_engine.py`
- Create: `backend/tests/test_diet_program_engine.py`
- Modify: `backend/app/api/v1/diet_programs.py`
- Modify: `backend/app/schemas/__init__.py`

**Interfaces:**
- Produces: `estimate_tdee(profile, activity_level)`、`create_initial_targets(...)`、`evaluate_532(...) -> EvaluationResult`。

- [ ] **Step 1: 写公式与边界失败测试**

```python
def test_532_macros_use_442_or_532_energy_conversion():
    result = create_initial_targets(2000, ratio="532")
    assert result == {"calories_kcal": 2000, "carbs_g": 250, "protein_g": 150, "fat_g": 44.44}

def test_low_calorie_plan_is_rejected():
    with pytest.raises(DietSafetyError):
        create_initial_targets(1100, ratio="532")

def test_532_adjustment_only_reduces_carbs():
    next_stage = apply_carb_reduction(stage, grams=20)
    assert next_stage.protein_g == stage.protein_g
    assert next_stage.fat_g == stage.fat_g
    assert next_stage.carbs_g == stage.carbs_g - 20
```

- [ ] **Step 2: 实现 Mifflin–St Jeor 与活动系数**

活动系数枚举固定为 sedentary/light/moderate/very_active；资料缺失时返回需要补充的字段，不猜测默认性别、年龄、身高或体重。

- [ ] **Step 3: 实现评估状态机**

输入两个七日窗口、有效称重数、执行率、目标速度和当前阶段；依次判断数据不足、执行率不足、已达标、安全停止、继续、建议降低碳水。默认减少 20g，可选 15/20/25g，碳水不得低于 100g。

- [ ] **Step 4: 接入创建与评估 API**

`POST /diet-programs` 创建 `draft` 方案和初始阶段；`confirm` 后同步 NutritionGoal 快照；`evaluate` 只生成 pending adjustment，不直接修改阶段。

- [ ] **Step 5: 验证并提交**

Run: `cd backend && pytest -q tests/test_diet_program_engine.py && pytest -q`  
Expected: PASS。

```bash
git add backend/app/services/diet_program_engine.py backend/tests/test_diet_program_engine.py backend/app/api/v1/diet_programs.py backend/app/schemas/__init__.py
git commit -m "feat: implement adaptive diet stage engine"
```

### Task 6: 实现菜单模板、生成、缩放和替换

**Files:**
- Create: `backend/app/services/meal_planner.py`
- Create: `backend/app/services/meal_templates.py`
- Create: `backend/tests/test_meal_planner.py`
- Modify: `backend/app/api/v1/diet_programs.py`

**Interfaces:**
- Produces: `generate_seven_day_plan(...)`、`replace_item(...)`、`replace_meal(...)`、`validate_meal_plan(...)`。

- [ ] **Step 1: 写硬约束失败测试**

```python
def test_allergens_never_appear_in_plan():
    plan = generate_seven_day_plan(targets, preferences(allergens=["milk"]))
    assert all("milk" not in item.allergens for item in plan.items)

def test_16_8_meals_stay_inside_window():
    plan = generate_seven_day_plan(targets, preferences(window="10:00-18:00"), code="time_restricted_16_8")
    assert all(time(10) <= meal.planned_time <= time(18) for meal in plan.meals)

def test_keto_rejects_unknown_fiber():
    with pytest.raises(MealPlanConflict):
        generate_keto_plan(food_with_unknown_fiber)
```

- [ ] **Step 2: 建立最小可用模板库**

每种餐数至少提供家常中餐、轻食、便利外卖和低预算候选。模板只引用当前种子食物或明确营养快照；记录熟重/生重、过敏原、预算、厨具和营养角色。

- [ ] **Step 3: 实现生成与缩放**

硬约束先过滤，软约束排序；固定蛋白质和脂肪角色后缩放碳水。全天热量误差超过 5% 或硬约束冲突时抛出结构化 `MealPlanConflict(fields, suggestions)`。

- [ ] **Step 4: 实现替换与加入记录**

替换优先同角色并重新校验全天目标；`POST /meal-plan/meals/{id}/record` 在单事务中创建当前用户 DietRecord 快照，并防止同一计划餐重复加入同一日期。

- [ ] **Step 5: 验证并提交**

Run: `cd backend && pytest -q tests/test_meal_planner.py && pytest -q`  
Expected: PASS。

```bash
git add backend/app/services/meal_planner.py backend/app/services/meal_templates.py backend/tests/test_meal_planner.py backend/app/api/v1/diet_programs.py
git commit -m "feat: generate and adapt seven day meal plans"
```

### Task 7: 完成方案生命周期、阶段确认和个人数据清理

**Files:**
- Modify: `backend/app/api/v1/diet_programs.py`
- Modify: `backend/app/services/account_data.py`
- Create: `backend/tests/test_diet_program_lifecycle.py`
- Modify: `backend/tests/test_account_data.py`

**Interfaces:**
- Produces: active/pause/resume/finish；pending adjustment confirm/reject；完整阶段历史。

- [ ] **Step 1: 写状态转换失败测试**

```python
def test_adjustment_confirmation_creates_new_stage_without_overwriting_old():
    confirmed = confirm_adjustment(program, pending)
    assert len(program.stages) == 2
    assert program.stages[0].ended_at is not None
    assert confirmed.stage_index == 2

def test_rejected_adjustment_keeps_current_stage():
    reject_adjustment(program, pending)
    assert program.current_stage_id == original_stage.id
```

- [ ] **Step 2: 实现允许的状态转换表**

仅允许 draft→active、active↔paused、active/paused→finished。finished 不恢复；创建新方案前结束旧 active 方案必须显式确认。

- [ ] **Step 3: 扩展个人数据清理**

清空健身数据和注销必须按子项→餐次→日期→阶段→方案→偏好顺序删除新增数据；测试更新 `PERSONAL_DATA_MODELS` 覆盖范围。

- [ ] **Step 4: 验证并提交**

Run: `cd backend && pytest -q tests/test_diet_program_lifecycle.py tests/test_account_data.py && pytest -q`  
Expected: PASS。

```bash
git add backend/app/api/v1/diet_programs.py backend/app/services/account_data.py backend/tests/test_diet_program_lifecycle.py backend/tests/test_account_data.py
git commit -m "feat: complete diet program lifecycle"
```

### Task 8: 增加前端方案 API、store 和页面路由

**Files:**
- Create: `frontend/src/api/diet-programs.ts`
- Create: `frontend/src/store/diet-program.ts`
- Create: `frontend/src/store/diet-program.test.ts`
- Create: `frontend/src/pages/diet/programs.vue`
- Create: `frontend/src/pages/diet/program-setup.vue`
- Create: `frontend/src/pages/diet/program-detail.vue`
- Create: `frontend/src/pages/diet/meal-plan.vue`
- Modify: `frontend/src/pages.json`

**Interfaces:**
- Produces: `useDietProgramStore`；模板、资格、偏好、创建、当前方案、菜单、评估与调整 API types。

- [ ] **Step 1: 写 store 失败测试**

```typescript
it('does not create a program when eligibility is blocked', async () => {
  await store.checkEligibility(blockedAnswers);
  await expect(store.createProgram(payload)).rejects.toThrow('不符合方案资格');
});

it('keeps the active stage when adjustment is rejected', async () => {
  const stageId = store.active!.current_stage.id;
  await store.rejectAdjustment(adjustmentId);
  expect(store.active!.current_stage.id).toBe(stageId);
});
```

- [ ] **Step 2: 实现类型安全 API 与 store**

不使用 `any` 作为领域 payload；store 保存 templates/preferences/active/mealPlan/loading/error，并提供 reset 供注销调用。

- [ ] **Step 3: 实现四个页面**

方案列表显示适合人群、限制与严格标识；setup 分为资格、偏好、方案参数和确认四步并保存草稿；detail 匹配批准视觉稿；meal-plan 展示 7 天、餐次、食物克数、替换和加入记录。

- [ ] **Step 4: 验证并提交**

Run: `cd frontend && npm test -- src/store/diet-program.test.ts && npm run typecheck`  
Expected: PASS。

```bash
git add frontend/src/api/diet-programs.ts frontend/src/store/diet-program.ts frontend/src/store/diet-program.test.ts frontend/src/pages/diet/programs.vue frontend/src/pages/diet/program-setup.vue frontend/src/pages/diet/program-detail.vue frontend/src/pages/diet/meal-plan.vue frontend/src/pages.json
git commit -m "feat: add adaptive diet program experience"
```

### Task 9: 把方案状态和计划菜单接入饮食首页

**Files:**
- Modify: `frontend/src/pages/diet/index.vue`
- Modify: `frontend/src/store/diet.ts`
- Modify: `frontend/src/store/user.ts`
- Create: `frontend/src/utils/diet-program-view.test.ts`
- Create: `frontend/src/utils/diet-program-view.ts`

**Interfaces:**
- Produces: 饮食首页的“今日执行 + 当前方案”布局；菜单加入记录后统一刷新。

- [ ] **Step 1: 写视图状态失败测试**

```typescript
it('shows setup CTA without an active program', () => {
  expect(programCardState(null).action).toBe('选择饮食方案');
});

it('shows pending adjustment before ordinary stage text', () => {
  expect(programCardState(activeWithPending).action).toBe('确认阶段调整');
});
```

- [ ] **Step 2: 重排饮食首页**

保留日期与实际餐次记录；摘要下增加当前方案区域。无方案、草稿、观察中、待调整、暂停分别使用明确状态和唯一主操作。拍照入口文案不再称“AI 智能识别”，改为“拍照候选”。

- [ ] **Step 3: 统一刷新与本地 reset**

计划餐加入记录后刷新目标日期、周总结和方案执行率；清空数据/注销同时 reset diet-program store。

- [ ] **Step 4: 验证并提交**

Run: `cd frontend && npm test && npm run typecheck`  
Expected: PASS。

```bash
git add frontend/src/pages/diet/index.vue frontend/src/store/diet.ts frontend/src/store/user.ts frontend/src/utils/diet-program-view.ts frontend/src/utils/diet-program-view.test.ts
git commit -m "feat: connect meal planning to daily diet tracking"
```

### Task 10: 浏览器、小程序与全量回归验收

**Files:**
- Modify: `backend/README.md`
- Modify: `frontend/README.md`
- Modify: `docs/01_产品需求文档_PRD.md`

**Interfaces:**
- Produces: 与实际功能一致的运行、接口、安全与人工验收说明。

- [ ] **Step 1: 更新文档**

记录四类方案、筛查限制、532 规则、菜单口径、mock 识别、纤维字段、迁移命令和不构成医疗建议的表述。

- [ ] **Step 2: 后端全量验证**

Run: `cd backend && pytest -q`  
Expected: 0 failed。

Run: `cd backend && alembic current`  
Expected: `20260711_1200 (head)`。

- [ ] **Step 3: 前端全量验证**

Run: `cd frontend && npm test && npm run typecheck && npm run build:h5 && npm run build:mp-weixin`  
Expected: 全部 exit 0。

- [ ] **Step 4: 使用 in-app Browser 验证 H5**

覆盖饮食首页、四种添加入口、拍照两状态、方案选择、资格阻断、偏好、532 创建、七日菜单、替换、加入记录、评估与调整确认。检查移动视口、控制台错误、加载/失败恢复和底部安全区。

- [ ] **Step 5: 微信人工验收清单**

在开发者工具和真机验证相机、相册、授权拒绝、图片上传、返回草稿、安全区、四餐保存及导航栈。真实 AI provider 不作为本轮通过条件。

- [ ] **Step 6: 最终检查与提交**

Run: `git diff --check`  
Expected: 无输出。

Run: `git status --short`  
Expected: 不包含 `.env`、构建产物、临时截图或本轮外文件。

```bash
git add backend/README.md frontend/README.md docs/01_产品需求文档_PRD.md
git commit -m "docs: document adaptive diet program workflows"
```
