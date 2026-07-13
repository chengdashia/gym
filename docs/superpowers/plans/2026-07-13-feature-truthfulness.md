# Feature Truthfulness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hide unfinished photo-recognition and membership experiences while making saved-only reminders honest and valid.

**Architecture:** Reuse the existing feature-gate module for visibility and keep dormant backend capabilities intact. Reminder behavior remains local form validation plus the existing persistence API.

**Tech Stack:** Vue 3, uni-app, Pinia, Vitest, TypeScript

## Global Constraints

- Do not delete photo-recognition pages, APIs, mock provider, data, or backend membership fields.
- Do not add payment, AI provider, subscription-message, scheduler, or notification code.
- Add no dependency.

---

### Task 1: Centralize dormant feature visibility

**Files:**
- Modify: `frontend/src/utils/feature-gates.ts`
- Modify: `frontend/src/utils/feature-gates.test.ts`
- Modify: `frontend/src/pages/diet/index.vue`
- Modify: `frontend/src/pages/diet/add.vue`
- Modify: `frontend/src/pages/mine/index.vue`

**Interfaces:**
- Produces: `FEATURE_GATES.photoRecognition === false`, `FEATURE_GATES.membership === false`

- [ ] Write failing tests asserting both gates are `false` and that exported gate keys are readonly booleans.
- [ ] Run `cd frontend && npm test -- --run src/utils/feature-gates.test.ts`; expect the new assertions to fail.
- [ ] Add the two false gates and replace photo/member visibility conditions in the three pages with these gates. Remove visible member labels and expiry copy; do not change API response types.
- [ ] Search with `rg -n "会员|普通用户|拍照识别|photo-recognize" frontend/src/pages` and verify remaining matches are dormant page implementation or non-user-facing code, not reachable buttons.
- [ ] Run the focused test and `npm run build:mp-weixin`; expect success.
- [ ] Commit only these files with `fix: hide unfinished photo and membership features`.

### Task 2: Make reminders saved-only and valid

**Files:**
- Modify: `frontend/src/pages/mine/reminders.vue`
- Create: `frontend/src/utils/reminders.ts`
- Create: `frontend/src/utils/reminders.test.ts`

**Interfaces:**
- Produces: `validateReminderItems(items: ReminderItem[]): string | null`

- [ ] Write tests proving disabled reminders may have no weekdays, enabled reminders with empty weekdays return `请至少选择一天`, and enabled reminders with one weekday pass.
- [ ] Run `cd frontend && npm test -- --run src/utils/reminders.test.ts`; expect module-not-found failure.
- [ ] Implement the single validation function without dependencies.
- [ ] Update weekday toggling so removing the final day leaves `weekdays === ''`; validate before API submission.
- [ ] Replace the header with `当前仅保存提醒计划，不会发送系统通知` and success copy with `提醒计划已保存`.
- [ ] Run focused tests, all frontend tests, and the mini-program build; expect success.
- [ ] Commit with `fix: clarify saved-only reminder behavior`.

### Task 3: Stage verification

**Files:** No production edits expected.

- [ ] Run `cd frontend && npm test -- --run`; expect all tests to pass.
- [ ] Run `cd frontend && npx vue-tsc --noEmit`; expect exit 0.
- [ ] Run `cd frontend && npm run build:mp-weixin`; expect a completed build.
- [ ] In WeChat DevTools verify diet and mine pages have no photo/member entry, reminders can clear all weekdays, and enabled empty weekdays cannot save.

