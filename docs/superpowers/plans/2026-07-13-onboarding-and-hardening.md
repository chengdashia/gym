# Onboarding and Core Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver resumable minimal onboarding, consistent profile validation, atomic custom-food recording, and verified ownership/upload/config boundaries.

**Architecture:** Extend current auth/user schemas rather than creating a second onboarding store. Put trust-boundary validation and transactions in FastAPI, keep frontend helpers pure and tested, and add ownership regression tests before changing endpoints.

**Tech Stack:** Vue 3, uni-app, Pinia, FastAPI, Pydantic, SQLAlchemy, pytest, Vitest

## Global Constraints

- First login requires agreement, avatar, nickname, and one of `fat_loss`, `muscle_gain`, `maintain_health`.
- Age, gender, height, weights, and training frequency remain optional.
- No new dependency unless existing upload libraries cannot decode an image; prefer Pillow already present in backend requirements.
- Production must reject mock WeChat and default secrets.

---

### Task 1: Define minimal onboarding state

**Files:**
- Modify: `backend/app/schemas/__init__.py`
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/api/v1/users.py`
- Modify: `backend/tests/test_wechat_login.py`
- Modify: `frontend/src/api/auth.ts`
- Modify: `frontend/src/api/user.ts`
- Modify: `frontend/src/pages/login/profile-source.ts`
- Modify: `frontend/src/pages/login/profile-source.test.ts`

**Interfaces:**
- Produces user summary field: `onboarding_step: 'agreement' | 'profile' | 'goal' | 'complete'`
- Uses `profile.fitness_goal` for the core goal; no duplicate database column.

- [ ] Add backend tests for each step: missing agreement, missing avatar/nickname, missing valid goal, and complete.
- [ ] Run `cd backend && python -m pytest tests/test_wechat_login.py -q`; expect failures for the absent field.
- [ ] Implement one backend helper deriving the step from persisted user state and include it in login and `/users/me` responses.
- [ ] Add matching TypeScript unions and tests mapping step to the next onboarding view.
- [ ] Run focused backend/frontend tests; expect success.
- [ ] Commit with `feat: expose resumable onboarding state`.

### Task 2: Rebuild onboarding steps without blocking optional profile fields

**Files:**
- Modify: `frontend/src/pages/login/onboarding.vue`
- Modify: `frontend/src/store/auth.ts`
- Modify: `frontend/src/store/auth.test.ts`

**Interfaces:**
- Consumes: `onboarding_step`
- Persists: agreement via existing confirm endpoint; avatar/nickname via `updateMe`; goal via `updateMe({profile:{fitness_goal}})`.

- [ ] Add store tests proving cached authenticated users resume the server-provided step and completed users go home.
- [ ] Run the focused test; expect failure.
- [ ] Change onboarding to four explicit states: login, agreement, required profile, core goal. Require non-empty uploaded avatar URL and trimmed nickname before proceeding.
- [ ] Remove age/height/weight/training-frequency requirements from onboarding; leave them on the profile page.
- [ ] Ensure every successful step refreshes `/users/me`, so a killed app resumes from persisted server state.
- [ ] Run focused tests, all frontend tests, typecheck, and build.
- [ ] Commit with `feat: simplify first-login onboarding`.

### Task 3: Unify optional profile validation

**Files:**
- Create: `frontend/src/utils/profile-validation.ts`
- Create: `frontend/src/utils/profile-validation.test.ts`
- Modify: `frontend/src/pages/mine/profile.vue`
- Modify: `backend/app/schemas/__init__.py`
- Create: `backend/tests/test_profile_validation.py`

**Interfaces:**
- Produces: `normalizeOptionalNumber(value, min, max): number | null` and shared exported bounds.

- [ ] Write frontend tests for empty values staying null and boundary/invalid values; write backend request tests for the same numeric limits already intended by product UI.
- [ ] Run focused tests; expect failure.
- [ ] Implement the pure helper and replace conflicting clamp/save ranges with one set. Apply matching Pydantic `ge`/`le` constraints.
- [ ] Verify profile save accepts all-null optional fields and rejects out-of-range input.
- [ ] Run focused and full suites.
- [ ] Commit with `fix: unify optional profile validation`.

### Task 4: Make custom-food-and-record atomic

**Files:**
- Modify: `backend/app/schemas/__init__.py`
- Modify: `backend/app/api/v1/diet.py`
- Modify: `backend/tests/test_diet_shortcuts.py`
- Modify: `frontend/src/api/diet.ts`
- Modify: `frontend/src/pages/diet/custom-food.vue`

**Interfaces:**
- Produces: `POST /diet/custom-food-record`, accepting `{food: CustomFoodIn, record: DietRecordCreateContext}` and returning `{food, record}`.

- [ ] Write one success test and one forced record-validation failure test asserting no custom food remains after rollback.
- [ ] Run the focused backend test; expect 404 or schema failure.
- [ ] Implement both inserts before a single commit; rollback on exception through the existing request session behavior. Reuse current nutrition snapshot logic rather than copy formulas.
- [ ] Add the typed frontend API method and replace the two sequential calls.
- [ ] Run backend focused tests, frontend tests, typecheck, and build.
- [ ] Commit with `fix: create custom food records atomically`.

### Task 5: Lock ownership and idempotent training finish

**Files:**
- Modify only if tests expose gaps: `backend/app/api/v1/diet.py`, `foods.py`, `training.py`, `weight.py`, `diet_programs.py`
- Create: `backend/tests/test_resource_ownership.py`
- Modify: `backend/tests/test_training_rules.py`

**Interfaces:**
- Finishing an already completed session returns its current representation with HTTP 200; cancelled sessions remain conflict errors.

- [ ] Create two users and write cross-user GET/PUT/DELETE tests for every ID-based resource family.
- [ ] Run tests and record which endpoints fail; do not edit endpoints already protected.
- [ ] Add `user_id == current_user.id` or ownership joins only to failing queries.
- [ ] Add a repeated-finish test, then make completed finish idempotent without duplicating operation logs; preserve conflict for cancelled sessions.
- [ ] Run the ownership and training suites.
- [ ] Commit with `fix: enforce resource ownership and finish idempotency`.

### Task 6: Harden uploads and production configuration

**Files:**
- Modify: `backend/app/services/uploads.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_uploads.py`
- Modify: `backend/tests/test_security_config.py`

**Interfaces:**
- Upload validation accepts only configured image MIME/extensions, a decodable image, and the existing maximum size.
- Production startup rejects `mock_wechat=true` and default/empty JWT secrets.

- [ ] Add tests for valid JPEG/PNG, forged MIME, invalid bytes, oversize data, unsafe names, production mock, and default secret.
- [ ] Run focused tests; expect new failures.
- [ ] Extend the existing upload validator using current dependencies and server-generated UUID names. Add one startup validation function called from app initialization.
- [ ] Run focused and full backend tests.
- [ ] Commit with `fix: harden uploads and production config`.

### Task 7: Stage verification

- [ ] Run `cd backend && python -m pytest -q`; expect all backend tests to pass.
- [ ] Run `cd frontend && npm test -- --run && npx vue-tsc --noEmit && npm run build:mp-weixin`; expect success.
- [ ] Verify onboarding interruption/resume and avatar selection in WeChat DevTools.

