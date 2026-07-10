# Production Quality and Retention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不实现微信授权、openid 和订阅消息的前提下，修复生产安全与隐私问题，并交付 CSV 导出、快速饮食记录、训练历史值带入和规则型周总结。

**Architecture:** 保持现有 uni-app + Vue 3 + Pinia 与 FastAPI + SQLAlchemy 结构。新增逻辑优先放入现有 service/API/page 边界；批量写入由后端事务裁决，前端只负责交互状态。采用现有依赖和标准库，不增加 Redis、队列、Excel 或通用仓储层。

**Tech Stack:** Python 3、FastAPI、SQLAlchemy、Pillow、TypeScript、Vue 3、uni-app、Pinia、unittest/pytest、Vitest、vue-tsc。

## Global Constraints

- 不实现或改造微信授权登录、openid 获取和微信订阅消息发送。
- 手机号登录/注册继续作为当前可测试登录方式。
- 统计范围统一为 `7/30/90` 天。
- CSV 使用 UTF-8 BOM 和标准库 `csv`，不增加 Excel/压缩依赖。
- 饮食和识别图片私有，头像保持公开。
- 周总结只输出数据支持的规则型建议，不给出医疗判断。
- 不覆盖、删除或暂存任务范围外的现有用户改动。

---

### Task 1: 安全配置、密码比较与验证码边界

**Files:**
- Create: `backend/.env.example`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/security.py`
- Modify: `backend/app/api/v1/auth.py`
- Create: `backend/tests/test_security_config.py`
- Create: `backend/tests/test_auth_security.py`

**Interfaces:**
- Produces: `Settings.validate_for_runtime() -> None`、`_cleanup_captchas(now: float) -> None`、最多 5 次验证码错误与最多 1000 条内存记录。

- [ ] **Step 1: 写失败测试**

```python
def test_production_rejects_missing_secrets():
    settings = Settings(debug=False, db_url="", jwt_secret="")
    with pytest.raises(ValueError):
        settings.validate_for_runtime()

def test_verify_password_uses_digest_comparison(monkeypatch):
    called = []
    monkeypatch.setattr(security.hmac, "compare_digest", lambda a, b: called.append((a, b)) or True)
    assert security.verify_password("pw", security.hash_password("pw"))
    assert called

def test_captcha_is_removed_after_five_wrong_attempts():
    auth._CAPTCHA_STORE["id"] = {"answer": "1234", "expires": time.time() + 60, "attempts": 0}
    for _ in range(5):
        assert not auth._verify_captcha("id", "0000")
    assert "id" not in auth._CAPTCHA_STORE
```

- [ ] **Step 2: 运行测试确认因缺少运行时校验、恒定时间比较和 attempts 字段而失败**

Run: `cd backend && pytest -q tests/test_security_config.py tests/test_auth_security.py`  
Expected: FAIL，分别指向缺少的行为。

- [ ] **Step 3: 写最小实现**

```python
def validate_for_runtime(self) -> None:
    if not self.debug and (not self.db_url or len(self.jwt_secret) < 32):
        raise ValueError("生产环境必须配置 DB_URL 和至少 32 位 JWT_SECRET")
```

配置默认值只允许本地 SQLite/显式环境变量且不含真实密码；`verify_password` 使用 `hmac.compare_digest`。验证码每次获取和校验前清除过期项，错误次数达到 5 删除，容量达到 1000 时移除最早过期记录。

- [ ] **Step 4: 运行目标测试和后端完整测试**

Run: `cd backend && pytest -q tests/test_security_config.py tests/test_auth_security.py && pytest -q`  
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add backend/.env.example backend/app/core/config.py backend/app/core/security.py backend/app/api/v1/auth.py backend/tests/test_security_config.py backend/tests/test_auth_security.py
git commit -m "fix: harden runtime secrets and local authentication"
```

### Task 2: 统一个人数据清理与注销

**Files:**
- Create: `backend/app/services/account_data.py`
- Modify: `backend/app/api/v1/users.py`
- Create: `backend/tests/test_account_data.py`
- Modify: `frontend/src/pages/mine/account.vue`

**Interfaces:**
- Produces: `clear_personal_data(db: Session, user: User) -> list[str]`，返回提交后需要删除的文件 URL；注销复用同一函数。

- [ ] **Step 1: 写失败测试**

```python
def test_clear_personal_data_covers_all_user_owned_models():
    assert set(PERSONAL_DATA_MODELS) == {
        DietRecord, WeightRecord, UserCustomFood, UserCustomExercise,
        TrainingPlan, TrainingSession, FoodRecognitionLog, UploadedFile,
        NutritionGoal, UserReminder, UserProfile,
    }

def test_cancel_account_clears_identifiers_and_status(user):
    anonymize_account(user)
    assert user.status == "cancelled"
    assert user.phone is user.openid is user.password_hash is None
    assert user.nickname is user.avatar_url is None
```

- [ ] **Step 2: 运行测试确认 service 尚不存在**

Run: `cd backend && pytest -q tests/test_account_data.py`  
Expected: FAIL，导入失败。

- [ ] **Step 3: 实现集中清理函数并改造两个接口**

清空健身数据删除所有用户业务行和 `UserProfile`，保留账号身份字段；注销在同一事务内额外匿名化账号。操作日志只写 `{action, user_id}`，不写原始个人值。数据库提交后逐个调用 `delete_local_file`。

- [ ] **Step 4: 修改前端文案**

“删除个人数据”改为“清空健身数据”，准确列出保留账号；注销说明账号与业务数据都会清除。删除后重置 user/diet/training store，注销后额外清除 auth。

- [ ] **Step 5: 验证**

Run: `cd backend && pytest -q tests/test_account_data.py tests/test_user_weight_sync.py && pytest -q`  
Run: `cd frontend && npm run typecheck`  
Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add backend/app/services/account_data.py backend/app/api/v1/users.py backend/tests/test_account_data.py frontend/src/pages/mine/account.vue
git commit -m "fix: align personal data deletion with account promises"
```

### Task 3: 图片重编码与私有访问

**Files:**
- Modify: `backend/app/services/uploads.py`
- Modify: `backend/app/api/v1/uploads.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_uploads.py`
- Modify: `frontend/src/utils/request.ts`

**Interfaces:**
- Produces: `normalize_image(contents: bytes) -> tuple[bytes, str, str]`；`GET /api/v1/uploads/{file_id}/content`；头像继续使用 `/static`，其他用途通过鉴权接口读取。

- [ ] **Step 1: 写失败测试**

```python
def test_normalize_image_removes_exif_and_returns_real_extension():
    normalized, ext, mime = normalize_image(jpeg_with_exif())
    with Image.open(io.BytesIO(normalized)) as image:
        assert not image.getexif()
    assert (ext, mime) == (".jpg", "image/jpeg")

def test_private_content_requires_owner(client, user_a_token, user_b_token, private_upload):
    assert client.get(f"/api/v1/uploads/{private_upload.id}/content", headers=auth(user_b_token)).status_code == 404
    assert client.get(f"/api/v1/uploads/{private_upload.id}/content", headers=auth(user_a_token)).status_code == 200
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && pytest -q tests/test_uploads.py`  
Expected: FAIL，缺少重编码函数/私有读取路由。

- [ ] **Step 3: 实现最小重编码和下载路由**

使用 Pillow `ImageOps.exif_transpose`、RGB/RGBA 转换和重新保存移除 EXIF。上传文件名以后端识别格式为准。私有读取按 `UploadedFile.user_id` 查询并返回 `FileResponse`；头像继续公开。

- [ ] **Step 4: 前端增加带 token 的私有资源下载 helper**

```typescript
export function privateUploadUrl(fileId: number) {
  return `${API_BASE}/uploads/${fileId}/content`;
}
```

需要预览时使用 `uni.downloadFile` 并附带 Authorization；不创建第二套 HTTP client。

- [ ] **Step 5: 验证并提交**

Run: `cd backend && pytest -q tests/test_uploads.py && pytest -q`  
Run: `cd frontend && npm test && npm run typecheck`  
Expected: PASS。

```bash
git add backend/app/services/uploads.py backend/app/api/v1/uploads.py backend/app/main.py backend/tests/test_uploads.py frontend/src/utils/request.ts
git commit -m "fix: protect and sanitize user images"
```

### Task 4: 统计周期、占位入口和模拟识别文案

**Files:**
- Modify: `backend/app/api/v1/stats.py`
- Modify: `backend/tests/test_stats_ranges.py`
- Modify: `frontend/src/api/stats.ts`
- Modify: `frontend/src/pages/stats/index.vue`
- Modify: `frontend/src/pages/mine/index.vue`
- Modify: `frontend/src/pages/mine/account.vue`
- Modify: `frontend/src/pages/diet/photo-recognize.vue`
- Modify: `docs/01_产品需求文档_PRD.md`

**Interfaces:**
- Produces: `StatsRange = 7 | 30 | 90`，提醒入口不可见，模拟识别明确标注。

- [ ] **Step 1: 将范围测试先改为期望 90 合法、15 非法并确认失败**

```python
def test_ranges_match_prd():
    assert _normalize_range(90) == 90
    with pytest.raises(BizException):
        _normalize_range(15)
```

Run: `cd backend && pytest -q tests/test_stats_ranges.py`  
Expected: FAIL，当前仅允许 7/15/30。

- [ ] **Step 2: 最小修改前后端范围和筛选按钮**

后端 `VALID_RANGES = {7, 30, 90}`；前端 `StatsRange = 7 | 30 | 90`。隐藏“提醒设置”，移除空账号安全卡；拍照页显示“当前为模拟候选推荐，结果不来自图片分析”。

- [ ] **Step 3: 验证并提交**

Run: `cd backend && pytest -q tests/test_stats_ranges.py && pytest -q`  
Run: `cd frontend && npm test && npm run typecheck`  
Expected: PASS。

```bash
git add backend/app/api/v1/stats.py backend/tests/test_stats_ranges.py frontend/src/api/stats.ts frontend/src/pages/stats/index.vue frontend/src/pages/mine/index.vue frontend/src/pages/mine/account.vue frontend/src/pages/diet/photo-recognize.vue docs/01_产品需求文档_PRD.md
git commit -m "fix: align visible capabilities with the MVP"
```

### Task 5: CSV 个人数据导出

**Files:**
- Create: `backend/app/services/data_export.py`
- Modify: `backend/app/api/v1/users.py`
- Create: `backend/tests/test_data_export.py`
- Modify: `frontend/src/api/user.ts`
- Modify: `frontend/src/pages/mine/account.vue`

**Interfaces:**
- Produces: `build_user_export(db, user_id) -> bytes`；`GET /api/v1/users/export.csv`；`userApi.exportData()`。

- [ ] **Step 1: 写失败测试**

```python
def test_csv_has_bom_chinese_and_only_requested_user(db, user_a, user_b):
    payload = build_user_export(db, user_a.id)
    assert payload.startswith(codecs.BOM_UTF8)
    text = payload.decode("utf-8-sig")
    assert "record_type" in text and "饮食" in text
    assert str(user_b.id) not in text
```

- [ ] **Step 2: 运行确认导出 service 不存在**

Run: `cd backend && pytest -q tests/test_data_export.py`  
Expected: FAIL。

- [ ] **Step 3: 使用标准库实现导出并增加文件响应**

`csv.DictWriter` 输出 `record_type,recorded_at,name,details`；`details` 使用 `json.dumps(..., ensure_ascii=False)`。接口返回 `StreamingResponse` 和 `Content-Disposition: attachment; filename=fitness-data.csv`。

- [ ] **Step 4: 账号页增加导出按钮**

使用 `uni.downloadFile` 附带 token；成功后调用平台文件保存能力，能力缺失时提示“当前平台暂不支持保存，请在微信小程序中使用”。恢复注销前导出提示。

- [ ] **Step 5: 验证并提交**

Run: `cd backend && pytest -q tests/test_data_export.py && pytest -q`  
Run: `cd frontend && npm run typecheck`  
Expected: PASS。

```bash
git add backend/app/services/data_export.py backend/app/api/v1/users.py backend/tests/test_data_export.py frontend/src/api/user.ts frontend/src/pages/mine/account.vue
git commit -m "feat: export personal fitness data as CSV"
```

### Task 6: 最近吃过与复制上一餐

**Files:**
- Modify: `backend/app/api/v1/diet.py`
- Modify: `backend/app/schemas/__init__.py`
- Create: `backend/tests/test_diet_shortcuts.py`
- Modify: `frontend/src/api/diet.ts`
- Modify: `frontend/src/pages/diet/add.vue`
- Modify: `frontend/src/pages/diet/index.vue`

**Interfaces:**
- Produces: `GET /api/v1/diet/recent-foods?limit=10`；`POST /api/v1/diet/copy-meal`，输入 `source_date/source_meal_type/target_date/target_meal_type/record_time`。

- [ ] **Step 1: 写失败测试**

```python
def test_recent_foods_are_unique_and_newest_first(db, user):
    items = recent_foods(db, user.id, limit=10)
    assert [item["food_name_snapshot"] for item in items] == ["鸡蛋", "米饭"]

def test_copy_meal_changes_date_and_meal_but_not_images(db, user):
    copied = copy_meal(db, user.id, source_date, "breakfast", target_date, "lunch", time(12, 0))
    assert all(row.record_date.date() == target_date and row.meal_type == "lunch" for row in copied)
    assert all(row.image_url is None for row in copied)
```

- [ ] **Step 2: 运行确认 helper/路由不存在**

Run: `cd backend && pytest -q tests/test_diet_shortcuts.py`  
Expected: FAIL。

- [ ] **Step 3: 实现查询和单事务复制**

最近食物按 `(food_source, food_id, custom_food_id, food_name_snapshot)` 去重，保留最新记录数量和营养快照。复制只读取当前用户未删除记录，无来源时返回业务错误；新记录不复制图片。

- [ ] **Step 4: 实现前端入口**

添加页在搜索框下显示最近吃过；饮食页提供“复制上一餐”，弹窗选择目标餐次并用 `copying` 锁防重复提交，成功后刷新当前日期。

- [ ] **Step 5: 验证并提交**

Run: `cd backend && pytest -q tests/test_diet_shortcuts.py && pytest -q`  
Run: `cd frontend && npm test && npm run typecheck`  
Expected: PASS。

```bash
git add backend/app/api/v1/diet.py backend/app/schemas/__init__.py backend/tests/test_diet_shortcuts.py frontend/src/api/diet.ts frontend/src/pages/diet/add.vue frontend/src/pages/diet/index.vue
git commit -m "feat: speed up repeated meal logging"
```

### Task 7: 训练 session 带入上次实际表现

**Files:**
- Modify: `backend/app/api/v1/training.py`
- Create: `backend/app/services/training_history.py`
- Create: `backend/tests/test_training_history_prefill.py`
- Modify: `frontend/src/api/training.ts`
- Modify: `frontend/src/pages/training/execute.vue`

**Interfaces:**
- Produces: `last_completed_sets(db, user_id, exercise_name) -> dict[int, tuple[int | None, Decimal | None]]`；session exercise 响应增加 `prefilled_from_history: bool`。

- [ ] **Step 1: 写失败测试**

```python
def test_prefill_uses_same_user_latest_completed_actual_values(db, user):
    values = last_completed_sets(db, user.id, "卧推")
    assert values[1] == (10, Decimal("60.00"))
    assert values[2] == (8, Decimal("60.00"))
```

- [ ] **Step 2: 运行确认 service 不存在**

Run: `cd backend && pytest -q tests/test_training_history_prefill.py`  
Expected: FAIL。

- [ ] **Step 3: 实现最新已完成场次查询并接入 session 创建**

只查询当前用户、已完成、未软删除 session；按结束时间/ID 取最新同名动作。相同组序号有实际值时覆盖目标值，否则沿用计划目标。

- [ ] **Step 4: 前端显示轻量提示并验证**

执行页只在至少一个动作使用历史值时显示“已带入上次训练数据”，不增加新的交互步骤。

Run: `cd backend && pytest -q tests/test_training_history_prefill.py && pytest -q`  
Run: `cd frontend && npm run typecheck`  
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/v1/training.py backend/app/services/training_history.py backend/tests/test_training_history_prefill.py frontend/src/api/training.ts frontend/src/pages/training/execute.vue
git commit -m "feat: prefill workouts from previous performance"
```

### Task 8: 规则型周总结与首页行动提示

**Files:**
- Create: `backend/app/services/weekly_summary.py`
- Create: `backend/tests/test_weekly_summary.py`
- Modify: `backend/app/api/v1/stats.py`
- Modify: `frontend/src/api/stats.ts`
- Modify: `frontend/src/pages/stats/index.vue`
- Modify: `frontend/src/api/home.ts`
- Modify: `frontend/src/pages/home/index.vue`

**Interfaces:**
- Produces: `build_weekly_summary(db, user_id, end_date) -> dict`；`GET /api/v1/stats/weekly-summary`；返回 `diet_days,average_calories,protein_goal_days,training_sessions,total_volume,weight_change,streak_days,actions`。

- [ ] **Step 1: 写失败测试**

```python
def test_no_data_returns_single_recording_action(db, user):
    result = build_weekly_summary(db, user.id, date(2026, 7, 10))
    assert result["actions"] == ["记录更多数据后生成总结，先从今天记录一餐开始"]

def test_actions_are_limited_and_fact_based(db, populated_user):
    result = build_weekly_summary(db, populated_user.id, date(2026, 7, 10))
    assert len(result["actions"]) <= 3
    assert result["diet_days"] == 5
```

- [ ] **Step 2: 运行确认 service 不存在**

Run: `cd backend && pytest -q tests/test_weekly_summary.py`  
Expected: FAIL。

- [ ] **Step 3: 实现固定优先级规则**

优先级依次为记录不足、蛋白质目标、训练频率、体重仅作客观变化说明。目标缺失时不生成达标判断；所有查询使用用户过滤和半开日期区间。

- [ ] **Step 4: 数据页展示完整总结，首页并行请求并展示首条 action**

页面无数据时使用现有 EmptyState/Card 组件；不新建复杂图表。首页总结失败不阻断原首页三张核心卡片。

- [ ] **Step 5: 验证并提交**

Run: `cd backend && pytest -q tests/test_weekly_summary.py && pytest -q`  
Run: `cd frontend && npm test && npm run typecheck`  
Expected: PASS。

```bash
git add backend/app/services/weekly_summary.py backend/tests/test_weekly_summary.py backend/app/api/v1/stats.py frontend/src/api/stats.ts frontend/src/pages/stats/index.vue frontend/src/api/home.ts frontend/src/pages/home/index.vue
git commit -m "feat: add weekly progress guidance"
```

### Task 9: 全量验证与文档收口

**Files:**
- Modify: `backend/README.md`
- Modify: `frontend/README.md`
- Modify: `docs/01_产品需求文档_PRD.md`

**Interfaces:**
- Produces: 与实际配置、私有图片、导出、快捷记录、统计周期和微信排除项一致的运行说明。

- [ ] **Step 1: 更新文档，不写未完成能力**

记录 `.env` 必填项、数据库密码轮换提醒、CSV 格式、私有图片访问、7/30/90、模拟识别标识和微信能力排除项。

- [ ] **Step 2: 运行完整自动检查**

Run: `cd backend && pytest -q`  
Expected: 0 failed。

Run: `cd frontend && npm test && npm run typecheck && npm run build:h5 && npm run build:mp-weixin`  
Expected: 全部 exit 0。

- [ ] **Step 3: 检查改动范围和秘密**

Run: `git diff --check`  
Expected: 无输出。

Run: `rg -n "mysql\+pymysql://[^:]+:[^@]+@|jwt_secret: str = .+change-me" backend frontend -g '!*.md' -g '!.env.example'`
Expected: 无输出。

Run: `git status --short`  
Expected: 仅显示本轮改动和用户原有未跟踪文件；不包含上传测试产物、构建目录或 `.env`。

- [ ] **Step 4: 提交文档**

```bash
git add backend/README.md frontend/README.md docs/01_产品需求文档_PRD.md
git commit -m "docs: document production-quality fitness workflows"
```
