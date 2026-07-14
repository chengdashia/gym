# Guest Login Compliance Design

## Goal

Meet the mini-program review requirement that users can cancel or refuse login and can experience the app without being repeatedly prompted or forced to authenticate.

## Confirmed behavior

- The app opens on the home tab for guests and never automatically redirects a guest to login.
- The login page has a visible `暂不登录，先逛逛` action that returns to the home tab.
- A user who has logged in but has not completed agreement, avatar, nickname, or goal setup can choose `暂不完善，先体验` on every incomplete onboarding step.
- The home page no longer forces incomplete users back into onboarding.
- A protected action requests login through one cancellable dialog with `暂不登录` and `去登录` buttons. Cancel keeps the current page unchanged; only confirmation navigates to login.
- The mine tab provides an explicit login entry for guests.

## Scope

Frontend-only. Guest users can browse the existing home, diet, training, and mine tabs; data-changing or private-data actions remain protected. No backend authentication policy changes are required.
