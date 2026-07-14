# Guest Login Compliance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users browse as guests and make every login or onboarding decision explicitly cancellable.

**Architecture:** Replace the global forced `reLaunch` in `requireAuth` with a single-instance cancellable modal. Keep protected actions unchanged at their call sites. Add explicit guest exits to onboarding, remove the home auto-redirect for incomplete profiles, and expose an entry to login from the mine tab.

**Tech Stack:** Vue 3, TypeScript, uni-app, Vitest.

## Global Constraints

- Guests may browse existing tabs without automatic login navigation.
- Only confirmation in a protected-action prompt opens login.
- Cancelling must leave the current page unchanged and must not schedule a second prompt.
- Work directly on `main` and use Chinese commit messages.

---

### Task 1: Cancellable protected-action prompt

**Files:**
- Modify: `frontend/src/utils/auth-guard.ts`
- Create: `frontend/src/utils/auth-guard.test.ts`

**Interfaces:**
- Consumes: `requireAuth({ message?, redirect? })`.
- Produces: `false` for guests while opening at most one `uni.showModal`; only modal confirmation navigates to onboarding.

- [ ] **Step 1: Write failing tests**

```ts
it('keeps guests on the current page when login is cancelled', () => {
  requireAuth({ redirect: '/pages/mine/profile' });
  modalOptions.success({ confirm: false });
  expect(uni.reLaunch).not.toHaveBeenCalled();
});

it('opens onboarding only after confirmation', () => {
  requireAuth({ redirect: '/pages/mine/profile' });
  modalOptions.success({ confirm: true });
  expect(uni.navigateTo).toHaveBeenCalledWith({ url: expect.stringContaining('redirect=') });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test -- --run src/utils/auth-guard.test.ts`

Expected: FAIL because the current guard uses `showToast` and unconditional `reLaunch`.

- [ ] **Step 3: Implement the minimal modal guard**

```ts
uni.showModal({
  title: '登录后可使用此功能',
  content: options.message || '登录后可保存和同步你的数据。',
  cancelText: '暂不登录',
  confirmText: '去登录',
  success: ({ confirm }) => {
    if (confirm) uni.navigateTo({ url });
  },
});
```

Keep a module-level pending flag so duplicate callers do not stack dialogs.

- [ ] **Step 4: Run the test to verify it passes**

Run: `npm test -- --run src/utils/auth-guard.test.ts`

Expected: PASS.

### Task 2: Explicit guest exits and no forced onboarding

**Files:**
- Modify: `frontend/src/pages/login/onboarding.vue:3-145,356-358`
- Modify: `frontend/src/pages/home/index.vue:225-239`
- Modify: `frontend/src/pages/mine/index.vue:1-86,131-156`

**Interfaces:**
- Consumes: `goGuest(): void`.
- Produces: a visible guest exit on the login and incomplete onboarding steps, a guest login entry in mine, and no home redirect based on `needOnboarding`.

- [ ] **Step 1: Add guest navigation controls**

```vue
<button class="guest-action" @tap="goGuest">暂不登录，先逛逛</button>
```

Render `暂不完善，先体验` beneath every incomplete onboarding step. Implement `goGuest` with `uni.reLaunch({ url: '/pages/home/index' })`.

- [ ] **Step 2: Remove automatic incomplete-profile redirect**

Delete the home `if (auth.token && auth.user && auth.needOnboarding) { uni.reLaunch(...) }` block.

- [ ] **Step 3: Add mine login entry**

Show `登录 / 注册` for guests and navigate to `/pages/login/onboarding` only after the user taps it.

- [ ] **Step 4: Run frontend verification**

Run: `npm test -- --run && npx vue-tsc --noEmit && npm run build:mp-weixin`

Expected: all frontend tests pass, no TypeScript errors, and the mini-program build completes.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/auth-guard.ts frontend/src/utils/auth-guard.test.ts frontend/src/pages/login/onboarding.vue frontend/src/pages/home/index.vue frontend/src/pages/mine/index.vue
git commit -m "修复：支持游客浏览和取消登录"
```
