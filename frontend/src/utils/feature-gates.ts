import type { NutritionGoal } from '@/api/user';

export const FEATURE_GATES = {
  photoRecognition: false,
  membership: false,
} as const;

export function hasNutritionGoal(goal: Partial<NutritionGoal> | null | undefined): boolean {
  return Number(goal?.calories_kcal || 0) > 0;
}

export function requireNutritionGoal(goal: Partial<NutritionGoal> | null | undefined, redirect: string): boolean {
  if (hasNutritionGoal(goal)) return true;
  uni.showModal({
    title: '先设置每日营养目标',
    content: '设置后才能开始记录和分析饮食，其他内容仍可继续浏览。',
    confirmText: '去设置',
    cancelText: '暂不设置',
    success: (res) => {
      if (res.confirm) uni.navigateTo({ url: `/pages/mine/goals?redirect=${encodeURIComponent(redirect)}` });
    },
  });
  return false;
}
