# Offline Android App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the existing uni-app/FastAPI product into a single-user Android APK whose profile, diet, training, weight, statistics, photos, and backups work without a server or network permission.

**Architecture:** Keep the existing Vue pages and public API module shapes, but replace HTTP calls with TypeScript services backed by a repository layer. The production repository uses Android `plus.sqlite`; tests use an in-memory adapter. User images live in the app-private document directory, and backup/restore uses a versioned ZIP selected through Android's system document picker.

**Tech Stack:** uni-app 3, Vue 3, TypeScript 5, Pinia, HTML5+ `plus.sqlite`/`plus.io`, Vitest, Android Storage Access Framework bridge, ZIP with `fflate`, SHA-256 with `@noble/hashes`.

## Global Constraints

- First release target is Android only; no iOS implementation is included.
- Runtime must not require FastAPI, MySQL, JWT, WeChat login, a remote API, or internet access.
- Do not request `android.permission.INTERNET`, `MANAGE_EXTERNAL_STORAGE`, or broad media/storage permissions.
- The application is single-user and opens directly after first-run profile setup.
- Photos are retained locally and paired with manually selected foods; no real or simulated recognition remains.
- Phase one excludes complex diet programs, stage adjustment, and automatic meal planning; all their entry points must be hidden.
- Historical diet records retain food and nutrition snapshots when food seed data changes.
- Every schema change uses a forward SQLite migration; upgrades never clear user data.
- Backup restore is transactional at the file-set level and restores the previous state after any failure.
- Preserve unrelated existing worktree changes; each task stages only its listed files.

---

## File and Boundary Map

New persistence files live under `frontend/src/local/`:

- `db/types.ts`: adapter contracts and row/value types.
- `db/plus-sqlite.ts`: production `plus.sqlite` adapter only.
- `db/memory.ts`: deterministic test adapter only.
- `db/index.ts`: connection lifecycle, transactions, and dependency injection.
- `db/migrations.ts`: ordered schema migrations.
- `db/schema.ts`: table/index SQL constants.
- `seed/*.json` and `seed/index.ts`: versioned built-in food, exercise, and training-template data.
- `repositories/*.ts`: SQL persistence grouped by domain.
- `services/*.ts`: profile, diet, weight, training, summary, files, backup, and reset business rules.
- `platform/android-documents.ts`: Android Storage Access Framework boundary.
- `platform/app-files.ts`: private file copy/delete/resolve boundary.

Existing `frontend/src/api/*.ts` remain the page-facing compatibility layer. They may import local services but must not import database adapters. Vue pages import API modules or stores only.

---

### Task 1: Android Build Target and SQLite Foundation

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/manifest.json`
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/types/html5plus.d.ts`
- Create: `frontend/src/local/db/types.ts`
- Create: `frontend/src/local/db/schema.ts`
- Create: `frontend/src/local/db/migrations.ts`
- Create: `frontend/src/local/db/plus-sqlite.ts`
- Create: `frontend/src/local/db/memory.ts`
- Create: `frontend/src/local/db/index.ts`
- Create: `frontend/src/local/db/migrations.test.ts`

**Interfaces:**
- Produces: `SqlDatabase.execute(sql, params?)`, `query<T>(sql, params?)`, `transaction(work)`, `close()`.
- Produces: `initializeLocalDatabase(): Promise<void>` and `setDatabaseForTests(db: SqlDatabase | null): void`.
- Produces: schema version `1` with all phase-one tables and foreign keys.

- [ ] **Step 1: Add the failing migration contract test**

```ts
import { beforeEach, describe, expect, it } from 'vitest';
import { createMemoryDatabase } from './memory';
import { migrateDatabase } from './migrations';

describe('local database migrations', () => {
  it('creates phase-one schema once and enables foreign keys', async () => {
    const db = createMemoryDatabase();
    await migrateDatabase(db);
    await migrateDatabase(db);
    expect(await db.query('PRAGMA user_version')).toEqual([{ user_version: 1 }]);
    expect((await db.query<{ name: string }>(
      "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
    )).map(row => row.name)).toEqual(expect.arrayContaining([
      'app_meta', 'local_profile', 'nutrition_goals', 'foods', 'custom_foods',
      'diet_records', 'exercises', 'custom_exercises', 'training_templates',
      'training_plans', 'training_plan_days', 'training_plan_exercises',
      'training_sessions', 'training_session_exercises', 'training_session_sets',
      'weight_records', 'uploaded_files',
    ]));
  });
});
```

- [ ] **Step 2: Run the test and verify the persistence boundary is missing**

Run: `cd frontend && npm test -- src/local/db/migrations.test.ts`

Expected: FAIL because `./memory` and `./migrations` do not exist.

- [ ] **Step 3: Define the database contract and schema version 1**

Use this public contract in `db/types.ts`:

```ts
export type SqlPrimitive = string | number | null;
export interface SqlDatabase {
  execute(sql: string, params?: SqlPrimitive[]): Promise<{ rowsAffected: number; insertId?: number }>;
  query<T extends Record<string, unknown>>(sql: string, params?: SqlPrimitive[]): Promise<T[]>;
  transaction<T>(work: (tx: SqlDatabase) => Promise<T>): Promise<T>;
  close(): Promise<void>;
}
```

`schema.ts` must create every table listed in the test, use `INTEGER PRIMARY KEY`, store dates as ISO-8601 text, store measured decimal values as integer hundredths, add `deleted_at TEXT`, and add indexes for diet date, weight date, training session date, plan relationships, and uploaded-file path. `migrations.ts` must run `PRAGMA foreign_keys = ON`, wrap each version in a transaction, and set `PRAGMA user_version = 1` only after all statements succeed.

- [ ] **Step 4: Implement production and test adapters**

`plus-sqlite.ts` must open `{ name: 'gym-local', path: '_doc/gym-local.db' }`, bind parameters without string concatenation, serialize transactions, and issue `ROLLBACK` on errors. `memory.ts` must implement the same contract for Vitest; use `sql.js` as a dev dependency and initialize it lazily. Add:

```json
"build:app-android": "uni build -p app-plus",
"sql.js": "^1.13.0"
```

Place `sql.js` under `devDependencies`, not runtime dependencies. Add only the camera permission needed by `uni.chooseImage` to `manifest.json`; explicitly remove network and broad storage permissions.

- [ ] **Step 5: Initialize before stores bootstrap**

Change `App.vue` launch ordering in this task to initialize persistence before the existing application bootstrap:

```ts
onLaunch(async () => {
  await initializeLocalDatabase();
  useAppStore().init();
  await useAuthStore().bootstrap();
});
```

Task 3 replaces the final line with `await useLocalProfileStore().bootstrap()` when the local profile store is introduced. This keeps Task 1 independently runnable without creating a throwaway store.

- [ ] **Step 6: Verify build and migration tests**

Run: `cd frontend && npm install && npm test -- src/local/db/migrations.test.ts && npm run typecheck && npm run build:app-android`

Expected: migration test PASS, typecheck PASS, and `dist/build/app-plus` generated without an HTTP configuration requirement.

- [ ] **Step 7: Commit the foundation**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/manifest.json frontend/src/App.vue frontend/src/types/html5plus.d.ts frontend/src/local/db
git commit -m "feat: add Android SQLite foundation"
```

---

### Task 2: Versioned Seed Data

**Files:**
- Create: `frontend/scripts/export-local-seeds.mjs`
- Create: `frontend/src/local/seed/foods.v1.json`
- Create: `frontend/src/local/seed/exercises.v1.json`
- Create: `frontend/src/local/seed/training-templates.v1.json`
- Create: `frontend/src/local/seed/index.ts`
- Create: `frontend/src/local/seed/index.test.ts`
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: `SqlDatabase` from Task 1.
- Produces: `installSeeds(db: SqlDatabase): Promise<void>` and `SEED_VERSION = 1`.

- [ ] **Step 1: Write a failing idempotency test**

```ts
it('installs seed version 1 without overwriting user rows', async () => {
  const db = await migratedMemoryDatabase();
  await installSeeds(db);
  await db.execute("INSERT INTO custom_foods(name, calories_centi, created_at) VALUES(?, ?, ?)", ['我的燕麦', 38000, NOW]);
  await installSeeds(db);
  expect((await db.query('SELECT * FROM custom_foods'))).toHaveLength(1);
  expect((await db.query<{ value: string }>("SELECT value FROM app_meta WHERE key='seed_version'"))[0].value).toBe('1');
});
```

- [ ] **Step 2: Verify it fails**

Run: `cd frontend && npm test -- src/local/seed/index.test.ts`

Expected: FAIL because `installSeeds` is missing.

- [ ] **Step 3: Export stable JSON seeds from the existing backend sources**

The script must read the existing backend seed modules, emit deterministic JSON sorted by stable code/name, and reject duplicate stable keys. Add `"seeds:build": "node scripts/export-local-seeds.mjs"`. Do not connect to MySQL and do not copy user rows from `backend/uploads` or a development database.

- [ ] **Step 4: Implement seed installation**

Use `INSERT ... ON CONFLICT(stable_key) DO UPDATE` only for built-in tables. Never update `custom_foods`, `custom_exercises`, records, plans, or sessions. Write `seed_version=1` in the same transaction after all inserts.

- [ ] **Step 5: Verify deterministic and idempotent installation**

Run: `cd frontend && npm run seeds:build && git diff --exit-code frontend/src/local/seed/*.json && npm test -- src/local/seed/index.test.ts`

Expected: generated JSON has no diff and all seed tests PASS.

- [ ] **Step 6: Commit seed support**

```bash
git add frontend/package.json frontend/scripts/export-local-seeds.mjs frontend/src/local/seed
git commit -m "feat: bundle versioned offline seed data"
```

---

### Task 3: Single-User Profile and First-Run Onboarding

**Files:**
- Create: `frontend/src/local/repositories/profile.ts`
- Create: `frontend/src/local/services/profile.ts`
- Create: `frontend/src/store/local-profile.ts`
- Create: `frontend/src/local/services/profile.test.ts`
- Modify: `frontend/src/api/user.ts`
- Modify: `frontend/src/pages/login/onboarding.vue`
- Modify: `frontend/src/pages/mine/profile.vue`
- Modify: `frontend/src/pages/mine/goals.vue`
- Modify: `frontend/src/pages/home/index.vue`
- Modify: `frontend/src/pages/mine/index.vue`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/pages.json`
- Delete: `frontend/src/utils/auth-guard.ts`
- Delete: `frontend/src/utils/auth-guard.test.ts`

**Interfaces:**
- Produces: `profileService.get()`, `saveProfile(input)`, `saveGoals(input)`, `completeOnboarding()`.
- Produces: `useLocalProfileStore()` with `ready`, `profile`, `needsOnboarding`, `bootstrap()`, and `refresh()`.
- Preserves the current `userApi.me()` and `userApi.updateMe()` response shapes for page compatibility.

- [ ] **Step 1: Write failing first-run and profile transaction tests**

```ts
it('marks a new database as requiring onboarding', async () => {
  const service = profileServiceFor(await migratedMemoryDatabase());
  expect((await service.get()).onboarding_step).toBe('profile');
});

it('saves profile, goals, and completion atomically', async () => {
  const service = profileServiceFor(await migratedMemoryDatabase());
  await service.finishOnboarding({ nickname: '东', gender: 'male', age: 30, height_cm: 175, current_weight_kg: 75, target_weight_kg: 70, fitness_goal: 'fat_loss', training_frequency: '3-4' });
  expect((await service.get()).onboarding_step).toBe('complete');
});
```

- [ ] **Step 2: Verify tests fail**

Run: `cd frontend && npm test -- src/local/services/profile.test.ts`

Expected: FAIL because the local profile service is missing.

- [ ] **Step 3: Implement profile repository and compatibility API**

Store one `local_profile` row with ID `1`. Store goal values as integer hundredths. When current weight changes, insert a same-day `weight_records` row only when its value differs from the latest same-day value. Keep the existing `UserMeOut`-compatible object at the API boundary, but remove token, phone, membership, and remote avatar semantics.

- [ ] **Step 4: Reduce onboarding to profile and goal steps**

Remove phone/password/captcha/login UI and agreement-as-auth logic from `onboarding.vue`. On launch, route to onboarding only when `needsOnboarding` is true. Remove guest/login/logout controls from Home and Mine. Local privacy text may remain accessible from Mine, but agreement acceptance must not block database use.

- [ ] **Step 5: Remove auth guards from phase-one pages**

Replace `auth.bootstrap()`/`requireAuth()` branches with local database readiness. Delete `auth-guard.ts` only after `rg "requireAuth|useAuthStore|authApi" frontend/src/pages` returns no phase-one page references.

- [ ] **Step 6: Verify local first run**

Run: `cd frontend && npm test -- src/local/services/profile.test.ts && npm run typecheck && npm test`

Expected: all tests PASS; no phase-one page redirects to login.

- [ ] **Step 7: Commit single-user flow**

```bash
git add frontend/src/App.vue frontend/src/pages.json frontend/src/api/user.ts frontend/src/store/local-profile.ts frontend/src/local/repositories/profile.ts frontend/src/local/services/profile.ts frontend/src/pages/login/onboarding.vue frontend/src/pages/mine frontend/src/pages/home/index.vue frontend/src/utils/auth-guard.ts frontend/src/utils/auth-guard.test.ts
git commit -m "feat: replace login with local onboarding"
```

---

### Task 4: Offline Foods, Diet Records, and Manual Photo Attachment

**Files:**
- Create: `frontend/src/local/repositories/foods.ts`
- Create: `frontend/src/local/repositories/diet.ts`
- Create: `frontend/src/local/repositories/uploads.ts`
- Create: `frontend/src/local/services/diet.ts`
- Create: `frontend/src/local/platform/app-files.ts`
- Create: `frontend/src/local/services/diet.test.ts`
- Modify: `frontend/src/api/diet.ts`
- Modify: `frontend/src/api/food.ts`
- Modify: `frontend/src/pages/diet/index.vue`
- Modify: `frontend/src/pages/diet/add.vue`
- Modify: `frontend/src/pages/diet/custom-food.vue`
- Modify: `frontend/src/pages/diet/record-edit.vue`
- Modify: `frontend/src/pages/diet/photo-recognize.vue`
- Delete: `frontend/src/utils/recognized-meal.ts`
- Delete: `frontend/src/utils/recognized-meal.test.ts`

**Interfaces:**
- Produces: existing `foodApi.search/createCustom` and `dietApi.list/create/update/remove/copyMeal/recent` shapes.
- Produces: `appFiles.importImage(tempPath, purpose): Promise<{ relativePath: string; uri: string }>`.
- Produces: `dietService.createRecord(input)` with a single database transaction for record and file metadata.

- [ ] **Step 1: Write failing nutrition snapshot and rollback tests**

```ts
it('keeps a historical nutrition snapshot after the food changes', async () => {
  const { service, db } = await dietFixture();
  const row = await service.createRecord({ food_source: 'system', food_id: 1, amount_g: 150, record_date: '2026-07-15', record_time: '12:00', meal_type: 'lunch' });
  await db.execute('UPDATE foods SET calories_centi=? WHERE id=?', [99900, 1]);
  expect((await service.getRecord(row.id)).calories_kcal).not.toBe(1498.5);
});

it('rolls back the diet row when file metadata insertion fails', async () => {
  const fixture = await dietFixture({ failUploadedFileInsert: true });
  await expect(fixture.service.createRecord(recordWithImage)).rejects.toThrow();
  expect(await fixture.db.query('SELECT id FROM diet_records')).toEqual([]);
});
```

- [ ] **Step 2: Verify tests fail**

Run: `cd frontend && npm test -- src/local/services/diet.test.ts`

Expected: FAIL because local diet repositories do not exist.

- [ ] **Step 3: Implement food search and diet CRUD**

Search active built-in and custom foods by escaped `LIKE`, return built-ins before custom matches, and cap results at 50. Calculate nutrition from integer hundredths and snapshot name, unit, serving weight, calories, carbs, protein, and fat into each record. Preserve all current API response field names at page boundaries.

- [ ] **Step 4: Replace recognition with manual attachment flow**

Rename the visible action to “拍照记录”. After `uni.chooseImage`, call `appFiles.importImage`, navigate to the existing food search selection mode, and save the chosen food with `image_path`. Remove recognize API calls, mock-result copy, confidence, candidate hydration, and recognition logs. If import fails, show “图片保存失败，可继续手动记录” and keep the food form usable.

- [ ] **Step 5: Verify diet and photo flows**

Run: `cd frontend && npm test -- src/local/services/diet.test.ts src/utils/diet-context.test.ts && npm run typecheck`

Expected: tests and typecheck PASS; `rg "food-recognition|模拟识别|confidence|recognized-meal" frontend/src` returns no runtime references.

- [ ] **Step 6: Commit offline diet**

```bash
git add frontend/src/api/diet.ts frontend/src/api/food.ts frontend/src/local/repositories frontend/src/local/services/diet.ts frontend/src/local/services/diet.test.ts frontend/src/local/platform/app-files.ts frontend/src/pages/diet frontend/src/utils/recognized-meal.ts frontend/src/utils/recognized-meal.test.ts
git commit -m "feat: move diet and photos offline"
```

---

### Task 5: Offline Weight Tracking

**Files:**
- Create: `frontend/src/local/repositories/weight.ts`
- Create: `frontend/src/local/services/weight.ts`
- Create: `frontend/src/local/services/weight.test.ts`
- Modify: `frontend/src/api/weight.ts`
- Modify: `frontend/src/pages/weight/index.vue`
- Modify: `frontend/src/utils/weight-record.ts`

**Interfaces:**
- Produces: existing `weightApi.list/create/update/remove` shapes.
- Produces: `weightService.series(range, endDate)` with daily rows and seven-day averages.

- [ ] **Step 1: Add failing same-day and trend tests**

```ts
it('returns the latest same-day value and a seven-day average', async () => {
  const service = await weightFixture([["2026-07-14T08:00:00", 7500], ["2026-07-14T20:00:00", 7480], ["2026-07-15T08:00:00", 7460]]);
  const result = await service.series(7, '2026-07-15');
  expect(result.items.at(-2)?.weight_kg).toBe(74.8);
  expect(result.items.at(-1)?.average_7d).toBeCloseTo(74.7);
});
```

- [ ] **Step 2: Verify it fails**

Run: `cd frontend && npm test -- src/local/services/weight.test.ts`

Expected: FAIL because local weight service is missing.

- [ ] **Step 3: Implement repository and series rules**

Validate 20–250 kg, store centi-kilograms, order records by recorded timestamp and ID, soft-delete user records, and synchronize `local_profile.current_weight_centi` to the latest non-deleted record. Port the existing daily collapse and trend rules rather than introducing new chart semantics.

- [ ] **Step 4: Verify weight pages and calculations**

Run: `cd frontend && npm test -- src/local/services/weight.test.ts src/utils/weight-record.test.ts && npm run typecheck`

Expected: PASS and the Weight page contains no HTTP/auth dependency.

- [ ] **Step 5: Commit weight migration**

```bash
git add frontend/src/local/repositories/weight.ts frontend/src/local/services/weight.ts frontend/src/local/services/weight.test.ts frontend/src/api/weight.ts frontend/src/pages/weight/index.vue frontend/src/utils/weight-record.ts
git commit -m "feat: store weight history locally"
```

---

### Task 6: Offline Training Plans and Sessions

**Files:**
- Create: `frontend/src/local/repositories/training.ts`
- Create: `frontend/src/local/services/training.ts`
- Create: `frontend/src/local/services/training.test.ts`
- Modify: `frontend/src/api/training.ts`
- Modify: `frontend/src/api/exercise.ts`
- Modify: `frontend/src/store/training.ts`
- Modify: `frontend/src/pages/training/index.vue`
- Modify: `frontend/src/pages/training/plan-edit.vue`
- Modify: `frontend/src/pages/training/execute.vue`
- Modify: `frontend/src/pages/training/history.vue`
- Modify: `frontend/src/pages/training/history-detail.vue`

**Interfaces:**
- Produces: current training/exercise API response shapes.
- Produces: `trainingService.createPlan`, `today`, `createSession`, `saveSet`, `finishSession`, `deleteSession`, and `history`.

- [ ] **Step 1: Write failing transaction and summary tests**

```ts
it('finishes a session and calculates total volume atomically', async () => {
  const service = await trainingFixture();
  const session = await service.createSession({ plan_id: 1, plan_day_id: 1, session_date: '2026-07-15' });
  await service.saveSet(session.exercises[0].id, { set_number: 1, weight_kg: 60, reps: 8, completed: true });
  const result = await service.finishSession(session.id, 1800);
  expect(result.total_volume).toBe(480);
  expect(result.status).toBe('completed');
});
```

- [ ] **Step 2: Verify it fails**

Run: `cd frontend && npm test -- src/local/services/training.test.ts`

Expected: FAIL because local training service is missing.

- [ ] **Step 3: Port plan scheduling and execution rules**

Preserve sequence and weekly schedules, rest days, makeup sessions, exercise order, completed-set semantics, duration, total reps, and `weight × reps` volume. Creating a session must snapshot plan-day exercises so later plan edits do not rewrite history. Finish, cancel, and delete operations must be transactional.

- [ ] **Step 4: Replace page-facing API internals**

Keep the existing exported `TrainingPlan`, `TrainingPlanDay`, `TrainingPlanExercise`, `TrainingSession`, `TrainingSessionExercise`, and `TrainingSessionSet` interfaces unchanged at the API boundary. Remove auth checks and network-error copy. The rest timer remains in page state and does not require a background service in phase one.

- [ ] **Step 5: Verify training flows**

Run: `cd frontend && npm test -- src/local/services/training.test.ts src/utils/training-progress.test.ts && npm run typecheck`

Expected: PASS; plan creation, execution, finish, history, and deletion compile without HTTP.

- [ ] **Step 6: Commit training migration**

```bash
git add frontend/src/local/repositories/training.ts frontend/src/local/services/training.ts frontend/src/local/services/training.test.ts frontend/src/api/training.ts frontend/src/api/exercise.ts frontend/src/store/training.ts frontend/src/pages/training
git commit -m "feat: move training plans and sessions offline"
```

---

### Task 7: Local Home Summary and Statistics

**Files:**
- Create: `frontend/src/local/services/stats.ts`
- Create: `frontend/src/local/services/home.ts`
- Create: `frontend/src/local/services/stats.test.ts`
- Modify: `frontend/src/api/home.ts`
- Modify: `frontend/src/api/stats.ts`
- Modify: `frontend/src/pages/home/index.vue`
- Modify: `frontend/src/pages/stats/index.vue`

**Interfaces:**
- Consumes: diet, weight, training, and profile repositories.
- Produces: existing `homeApi.summary` and `statsApi.weeklySummary/diet/training/weight/exercises` shapes.

- [ ] **Step 1: Add parity fixtures from backend rules**

```ts
it('matches the weekly summary fixture', async () => {
  const service = await statsFixture('mixed-week');
  expect(await service.weeklySummary('2026-07-15')).toEqual({
    diet_days: 4,
    average_calories: 1825,
    protein_goal_days: 3,
    training_sessions: 2,
    total_volume: 8240,
    weight_change: -0.6,
    nutrition_target_days: 3,
    weight_days: 5,
    streak_days: 4,
    actions: ['本周蛋白质达标 3 天，下一餐优先补充优质蛋白'],
  });
});
```

- [ ] **Step 2: Verify it fails**

Run: `cd frontend && npm test -- src/local/services/stats.test.ts`

Expected: FAIL because local stats service is missing.

- [ ] **Step 3: Port backend aggregation rules**

Port `stats_service.py`, `weekly_summary.py`, and training summary behavior into focused TypeScript functions. Generate missing calendar days, use the latest daily weight, preserve 7/30/90 ranges, calculate nutrition completion against local goals, and use one rounding helper for every public number.

- [ ] **Step 4: Replace Home and Stats API implementations**

Home summary must combine today's diet, scheduled training, latest weight, and goals in one service call. A missing table or failed query must surface a local-data error, never “网络异常”.

- [ ] **Step 5: Verify calculation parity**

Run: `cd frontend && npm test -- src/local/services/stats.test.ts src/utils/stats.test.ts && npm run typecheck`

Expected: all parity fixtures PASS.

- [ ] **Step 6: Commit local summaries**

```bash
git add frontend/src/local/services/stats.ts frontend/src/local/services/home.ts frontend/src/local/services/stats.test.ts frontend/src/api/home.ts frontend/src/api/stats.ts frontend/src/pages/home/index.vue frontend/src/pages/stats/index.vue
git commit -m "feat: calculate summaries and statistics locally"
```

---

### Task 8: ZIP Backup, Restore, Reset, and Recovery Screen

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/local/platform/android-documents.ts`
- Create: `frontend/src/local/services/backup.ts`
- Create: `frontend/src/local/services/backup.test.ts`
- Create: `frontend/src/pages/system/data-recovery.vue`
- Modify: `frontend/src/pages.json`
- Modify: `frontend/src/pages/mine/account.vue`
- Modify: `frontend/src/local/db/index.ts`
- Modify: `frontend/src/local/platform/app-files.ts`

**Interfaces:**
- Produces: `backupService.exportBackup()`, `importBackup()`, `resetAllData()`, and `recoverPendingRestore()`.
- Produces: `androidDocuments.createDocument(name, mime, bytes)` and `openDocument(mime): Promise<Uint8Array>`.

- [ ] **Step 1: Add failing archive and rollback tests**

```ts
it('round-trips the database and retained images', async () => {
  const fixture = await backupFixture();
  const bytes = await fixture.service.createArchive();
  await fixture.service.resetAllData();
  await fixture.service.restoreArchive(bytes);
  expect(await fixture.snapshot()).toEqual(fixture.originalSnapshot);
});

it('rejects traversal and checksum failures without changing current data', async () => {
  const fixture = await backupFixture();
  await expect(fixture.service.restoreArchive(maliciousArchive('../database.sqlite'))).rejects.toThrow('备份文件不安全');
  expect(await fixture.snapshot()).toEqual(fixture.originalSnapshot);
});
```

- [ ] **Step 2: Verify tests fail**

Run: `cd frontend && npm test -- src/local/services/backup.test.ts`

Expected: FAIL because backup service is missing.

- [ ] **Step 3: Add archive dependencies and manifest validation**

Add runtime dependencies `fflate` and `@noble/hashes`. Manifest type:

```ts
interface BackupManifest {
  format: 'gym-offline-backup';
  formatVersion: 1;
  appVersion: string;
  databaseVersion: number;
  exportedAt: string;
  files: Array<{ path: string; size: number; sha256: string }>;
}
```

Reject absolute paths, `..`, duplicate paths, undeclared files, unsupported format versions, newer database versions, size mismatches, and SHA-256 mismatches before replacing any live file.

- [ ] **Step 4: Implement consistent database export and atomic restore**

Before export, run a write lock and `PRAGMA wal_checkpoint(FULL)`, close the database, copy the database and retained images to a staging directory, then reopen immediately. Before restore, create `_doc/recovery/previous.zip`; extract the selected archive to staging; verify it; close the database; swap database/images using rename operations; reopen and migrate. On startup, `recoverPendingRestore()` must inspect a small restore journal and roll back an interrupted swap.

- [ ] **Step 5: Implement Android system document picker boundary**

Use `#ifdef APP-PLUS` and Android `ACTION_CREATE_DOCUMENT`/`ACTION_OPEN_DOCUMENT` intents through the platform bridge. Write/read the returned `content://` URI with Android content resolver streams. The H5/test branch throws `仅 Android App 支持备份文件选择`. Keep all Android imports inside `android-documents.ts`.

- [ ] **Step 6: Wire Account and recovery UI**

Replace current server export, account cancellation, and logout actions with “导出备份”, “从备份恢复”, and “清空全部数据”. Require explicit confirmation for restore/reset. Route database initialization failures to `/pages/system/data-recovery`, which offers retry and restore only.

- [ ] **Step 7: Verify backup security and recovery**

Run: `cd frontend && npm install && npm test -- src/local/services/backup.test.ts && npm run typecheck && npm run build:app-android`

Expected: all backup tests PASS and Android App build succeeds.

- [ ] **Step 8: Commit backup support**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/local/platform frontend/src/local/services/backup.ts frontend/src/local/services/backup.test.ts frontend/src/local/db/index.ts frontend/src/pages/system/data-recovery.vue frontend/src/pages/mine/account.vue frontend/src/pages.json
git commit -m "feat: add offline backup and recovery"
```

---

### Task 9: Remove Server Features and Prove Offline Release

**Files:**
- Delete: `frontend/src/api/auth.ts`
- Delete: `frontend/src/api/diet-programs.ts`
- Delete: `frontend/src/utils/request.ts`
- Delete: `frontend/src/utils/request.test.ts`
- Delete: `frontend/src/utils/api-base.ts`
- Delete: `frontend/src/utils/api-base.test.ts`
- Delete: `frontend/src/store/auth.ts`
- Modify: `frontend/src/utils/constants.ts`
- Modify: `frontend/src/pages.json`
- Modify: `frontend/src/manifest.json`
- Modify: `frontend/src/pages/diet/index.vue`
- Modify: `frontend/src/pages/mine/index.vue`
- Modify: `frontend/README.md`
- Create: `frontend/tests/offline-runtime.test.ts`
- Create: `docs/offline-android-release-checklist.md`

**Interfaces:**
- Produces: an APK runtime with no HTTP/auth/diet-program code path or network permission.

- [ ] **Step 1: Add a failing offline-runtime source audit**

```ts
it('contains no runtime remote request or login dependency', async () => {
  const sources = await readRuntimeSources();
  expect(sources).not.toMatch(/uni\.(request|uploadFile|downloadFile)\s*\(/);
  expect(sources).not.toMatch(/https?:\/\//);
  expect(sources).not.toMatch(/useAuthStore|requireAuth|dietProgramApi/);
});
```

The helper must scan only `frontend/src/**/*.{ts,vue,json}` and ignore comments in this test file itself.

- [ ] **Step 2: Verify the audit fails before cleanup**

Run: `cd frontend && npm test -- tests/offline-runtime.test.ts`

Expected: FAIL listing current request/auth/diet-program references.

- [ ] **Step 3: Delete obsolete runtime modules and routes**

Remove HTTP request/base URL, auth store/API, and diet program API/routes. Remove the program card and active-program query from Diet. Remove membership, login, logout, account cancellation, and remote-sync copy from Mine. Keep backend source code untouched; it is not included in the frontend build.

- [ ] **Step 4: Audit Android permissions and built output**

Ensure `manifest.json` contains only required camera capability and no network or broad storage permission. Search both source and generated App resources:

```bash
rg -n "uni\.(request|uploadFile|downloadFile)|API_BASE|useAuthStore|requireAuth|dietProgramApi|https?://" frontend/src
rg -n "android.permission.(INTERNET|MANAGE_EXTERNAL_STORAGE|READ_EXTERNAL_STORAGE|WRITE_EXTERNAL_STORAGE)" frontend/src/manifest.json frontend/dist/build/app-plus
```

Expected: both commands return no runtime matches.

- [ ] **Step 5: Run the complete automated verification**

Run: `cd frontend && npm run seeds:build && npm run typecheck && npm test && npm run build:app-android`

Expected: seed output unchanged, typecheck PASS, all tests PASS, and App build succeeds.

- [ ] **Step 6: Execute the Android flight-mode checklist**

Document and perform on a clean Android device/emulator:

1. Enable flight mode before first launch.
2. Complete profile and nutrition goals.
3. Create/edit/delete a diet entry and attach a photo.
4. Create a custom food.
5. Add/edit/delete weight records and inspect 7/30/90 trends.
6. Create a plan, execute sets, finish it, and inspect history.
7. Verify Home and Stats values against entered data.
8. Force-stop, reboot, and verify all data remains.
9. Export backup, clear data, import backup, and verify records/photos.
10. Install the next version over the current APK and verify migration preserves data.

Record device model, Android version, APK version, results, and defects in `docs/offline-android-release-checklist.md`.

- [ ] **Step 7: Generate the signed release APK**

Configure the signing certificate outside Git, build through HBuilderX or the approved local App packaging pipeline, and verify the resulting APK with Android build tools:

```bash
apksigner verify --verbose frontend/dist/release/gym-offline-release.apk
aapt dump permissions frontend/dist/release/gym-offline-release.apk
```

Expected: signature verification succeeds; permissions output contains neither INTERNET nor broad storage permissions.

- [ ] **Step 8: Commit offline release cleanup**

```bash
git add frontend docs/offline-android-release-checklist.md
git commit -m "feat: complete offline Android release"
```

---

## Final Release Gate

Do not call phase one complete until all of the following are true:

- `npm run typecheck`, `npm test`, and `npm run build:app-android` pass from a clean checkout.
- The runtime source audit finds no request, auth, or diet-program dependency.
- The APK permission audit finds no internet or broad storage permission.
- Database migration, interrupted restore, corrupted backup, and seed idempotency tests pass.
- A clean-install and an upgrade-install both pass the full flight-mode checklist.
- Exported backup restores records and retained images after a complete local reset.
