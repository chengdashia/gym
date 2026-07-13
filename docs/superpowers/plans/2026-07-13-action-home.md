# Action-oriented Home Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the home page into a single prioritized next action plus honest daily and weekly feedback.

**Architecture:** Extend the existing `/home/summary` aggregation and keep all date/statistics decisions in backend services. The Vue page renders typed sections and degrades each section independently.

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, uni-app, pytest, Vitest

## Global Constraints

- Use `Asia/Shanghai`; do not add user timezones.
- One aggregate request per home load.
- One highlighted primary action; no medical or automatic goal-adjustment claims.

---

### Task 1: Define summary contract and action priority

**Files:**
- Modify: `backend/app/schemas/__init__.py`
- Modify: `backend/app/api/v1/home.py`
- Modify: `backend/tests/test_business_rules.py`
- Modify: `frontend/src/api/home.ts`
- Create: `frontend/src/utils/home-action.test.ts`
- Create: `frontend/src/utils/home-action.ts`

**Interfaces:**
- Produces `primary_action: {type, title, description, url} | null`.
- Action order: required profile, nutrition goal, current meal, resume training, start training, weight, complete.

- [ ] Write backend scenario tests for every priority collision and frontend exhaustive mapping tests for action types.
- [ ] Run focused suites; expect failure.
- [ ] Implement one backend priority function from already-loaded summary state and typed frontend mapping with no duplicate priority logic.
- [ ] Run focused suites and commit with `feat: add prioritized home action`.

### Task 2: Add honest nutrition and training states

**Files:**
- Modify: `backend/app/api/v1/home.py`
- Modify: `backend/tests/test_business_rules.py`
- Modify: `frontend/src/api/home.ts`
- Modify: `frontend/src/pages/home/index.vue`

**Interfaces:**
- Diet adds `calories_remaining`, `calories_over`, `protein_remaining`.
- Training status union adds `partial`; existing statuses remain compatible.

- [ ] Test zero goal, below goal, exact goal, over goal, paused/in-progress, partial, rest, and complete.
- [ ] Implement non-negative remaining/over fields and map current training session status.
- [ ] Render actionable copy and correct buttons without negative remaining values.
- [ ] Run tests/typecheck/build and commit with `feat: clarify daily nutrition and training state`.

### Task 3: Add behavior streak and weekly snapshot

**Files:**
- Modify: `backend/app/services/weekly_summary.py`
- Modify: `backend/app/api/v1/home.py`
- Modify: `backend/tests/test_weekly_summary.py`
- Modify: `frontend/src/api/home.ts`
- Modify: `frontend/src/pages/home/index.vue`

**Interfaces:**
- Produces `weekly: {diet_days, nutrition_target_days, training_completed, training_planned, weight_days, behavior_streak, comparison}`.
- An active day has at least one diet record, completed training, or weight record; nutrition target is 85%–115% when goal > 0.

- [ ] Test duplicate same-day behaviors, streak breaks, week/year boundaries, 85%/115% inclusivity, and missing goals.
- [ ] Extend the existing weekly service with set-based day aggregation and include it in home summary.
- [ ] Add a compact weekly card; render unavailable fields as data-insufficient, not zero-performance claims.
- [ ] Run focused/full suites and commit with `feat: add weekly behavior feedback`.

### Task 4: Independent loading/error states

**Files:**
- Modify: `frontend/src/pages/home/index.vue`
- Create: `frontend/src/utils/home-summary.ts`
- Create: `frontend/src/utils/home-summary.test.ts`

**Interfaces:**
- Produces safe normalizer defaults for missing `diet`, `training`, `weight`, or `weekly` sections.

- [ ] Test partial and legacy summary payloads.
- [ ] Implement pure normalization and render retry only for whole-request failure; partial missing sections show local unavailable states.
- [ ] Run frontend tests/typecheck/build and commit with `fix: degrade home summary safely`.

### Task 5: Stage verification

- [ ] Run all backend and frontend test/build commands.
- [ ] Verify every primary-action state with seeded accounts in WeChat DevTools and confirm only one primary CTA is highlighted.

