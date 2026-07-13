# Training and Weight Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an honest post-workout summary and statistically safe weight trend feedback.

**Architecture:** Build summaries from persisted session sets and weight records in focused backend services. Reuse the existing training history detail and stats page where possible instead of adding parallel navigation.

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, uni-app, ECharts, pytest, Vitest

## Global Constraints

- No automatic training-plan or nutrition-goal mutation.
- Weight trend needs at least three effective daily records; same-day latest record wins.
- Compare period averages, never infer from one-day movement.

---

### Task 1: Produce training completion summary

**Files:**
- Create: `backend/app/services/training_summary.py`
- Create: `backend/tests/test_training_summary.py`
- Modify: `backend/app/api/v1/training.py`
- Modify: `frontend/src/api/training.ts`

**Interfaces:**
- Produces `GET /training/sessions/{id}/summary` with duration, exercise/set completion, volume, previous comparable volume/change, exercise rows, and `progression_hint`.

- [ ] Test complete, partial, zero-weight, no previous session, comparable previous session, and cross-user denial.
- [ ] Run focused tests; expect endpoint/service failure.
- [ ] Implement a pure summary builder over persisted session data; comparable means the latest earlier completed session with the same plan day, falling back to session name.
- [ ] Emit a progression hint only when every planned set of an exercise is complete and effective reps meet targets.
- [ ] Add typed frontend API and run tests.
- [ ] Commit with `feat: add persisted training summaries`.

### Task 2: Present summary after finish

**Files:**
- Modify: `frontend/src/pages/training/execute.vue`
- Modify: `frontend/src/pages/training/history-detail.vue`
- Modify: `frontend/src/utils/training-progress.ts`
- Modify: `frontend/src/utils/training-progress.test.ts`

**Interfaces:**
- Consumes session summary; finished execution redirects to history detail summary state.

- [ ] Test summary formatting for partial sets, percentage/volume comparison, and hints.
- [ ] Make finish redirect only after the idempotent finish response; history detail loads summary and offers home/history actions.
- [ ] Add retry for summary load without calling finish again.
- [ ] Run frontend tests/typecheck/build and commit with `feat: show post-workout feedback`.

### Task 3: Compute daily weight series and seven-day average

**Files:**
- Create: `backend/app/services/weight_trends.py`
- Create: `backend/tests/test_weight_trends.py`
- Modify: `backend/app/api/v1/stats.py`
- Modify: `frontend/src/api/stats.ts`

**Interfaces:**
- Produces weight trend points `{date, weight_kg, average_7d}` plus `record_days`, `has_trend`, and period-average comparison.

- [ ] Test same-day latest selection, fewer than three days, rolling windows with missing days, and month/year boundaries.
- [ ] Implement daily collapse then rolling average over available effective records in the last seven natural days; return `average_7d=null` until three effective records exist.
- [ ] Compare current and previous equal-length period averages only when both contain sufficient data.
- [ ] Run focused/full backend tests and commit with `feat: add safe weight trend statistics`.

### Task 4: Render weight trend and insufficient-data states

**Files:**
- Modify: `frontend/src/pages/stats/index.vue`
- Modify: `frontend/src/utils/stats.ts`
- Modify: `frontend/src/utils/stats.test.ts`

**Interfaces:**
- Consumes raw and average points; chart shows both series when `has_trend`, otherwise shows records plus remaining-data guidance.

- [ ] Add formatter tests for null averages, comparison direction, and insufficient records.
- [ ] Render raw points and 7-day average as separate chart series; do not imply success/failure from direction alone.
- [ ] Show `还需要记录 N 天` when trend is unavailable.
- [ ] Run frontend tests/typecheck/build and commit with `feat: display seven-day weight trend`.

### Task 5: Final verification

- [ ] Run `cd backend && python -m pytest -q`.
- [ ] Run `cd frontend && npm test -- --run && npx vue-tsc --noEmit && npm run build:mp-weixin`.
- [ ] In WeChat DevTools verify completed/partial training summaries, summary retry, three-record threshold, same-day latest record, and week-boundary charts.

