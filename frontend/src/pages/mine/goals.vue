<template>
  <view class="goals-page">
    <liquid-glass-card variant="tint" :highlight="true" custom-style="margin-bottom:0">
      <view class="head-content">
        <line-icon name="target" tint="mint" :size="96" class="head-icon" />
        <view class="head-text">每日营养目标</view>
        <view class="head-sub">系统会基于你的基础信息推荐，可手动调整</view>
      </view>
    </liquid-glass-card>

    <liquid-glass-card variant="light" :highlight="true" custom-style="margin-top:24rpx;margin-bottom:0">
      <view class="row">
        <text class="label">热量</text>
        <input v-model.number="goal.calories_kcal" type="number" class="input" />
        <text class="unit">kcal</text>
      </view>
      <view class="row">
        <text class="label">碳水</text>
        <input v-model.number="goal.carbs_g" type="digit" class="input" />
        <text class="unit">g</text>
      </view>
      <view class="row">
        <text class="label">蛋白质</text>
        <input v-model.number="goal.protein_g" type="digit" class="input" />
        <text class="unit">g</text>
      </view>
      <view class="row">
        <text class="label">脂肪</text>
        <input v-model.number="goal.fat_g" type="digit" class="input" />
        <text class="unit">g</text>
      </view>
    </liquid-glass-card>

    <view class="actions">
      <liquid-glass-button text="使用推荐值" variant="ghost" @tap="recommend" />
      <liquid-glass-button text="保存目标" variant="primary" @tap="save" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue';
import LiquidGlassCard from '@/components/LiquidGlassCard.vue';
import LiquidGlassButton from '@/components/LiquidGlassButton.vue';
import { useUserStore } from '@/store/user';
import { useAuthStore } from '@/store/auth';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';

const userStore = useUserStore();
const auth = useAuthStore();

const goal = reactive({
  calories_kcal: 0,
  carbs_g: 0,
  protein_g: 0,
  fat_g: 0,
});

onMounted(async () => {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    requireAuth({ redirect: '/pages/mine/goals' });
    return;
  }
  if (!userStore.goal?.calories_kcal) {
    await userStore.fetchGoal().catch(() => {
      uni.showToast({ title: '加载失败', icon: 'none' });
    });
  }
  Object.assign(goal, userStore.goal);
});

async function recommend() {
  uni.showLoading({ title: '生成中...' });
  try {
    const data = await userStore.recommendGoal();
    Object.assign(goal, data);
  } catch (e) {
    uni.showToast({ title: '推荐失败，请重试', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}

function validateGoal() {
  const { calories_kcal, carbs_g, protein_g, fat_g } = goal;
  if (!Number.isFinite(calories_kcal) || calories_kcal <= 0) return false;
  if (!Number.isFinite(carbs_g) || carbs_g < 0) return false;
  if (!Number.isFinite(protein_g) || protein_g < 0) return false;
  if (!Number.isFinite(fat_g) || fat_g < 0) return false;
  return true;
}

async function save() {
  if (!validateGoal()) {
    uni.showToast({ title: '请输入有效的目标值', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '保存中...' });
  try {
    await userStore.updateGoal({ ...goal });
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/mine/index'), 600);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}
</script>

<style lang="scss" scoped>
.goals-page {
  background: $bg;
  padding: $gap-3;
}
.head-content {
  text-align: center;
}
.head-icon {
  margin: 0 auto $gap-2;
}
.head-text {
  margin-top: $gap-1;
  font-size: 32rpx;
  font-weight: 700;
  color: $primary-deep;
}
.head-sub {
  margin-top: 4rpx;
  font-size: $fs-sm;
  color: $text-2;
  opacity: 0.85;
}
.row {
  display: flex;
  align-items: center;
  padding: $gap-2 0;
  border-bottom: 1rpx solid $divider;
  gap: $gap-2;
  &:last-child { border-bottom: none; }
}
.label {
  width: 180rpx;
  color: $text-2;
  font-size: $fs-md;
}
.input {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  text-align: right;
}
.unit {
  color: $text-3;
  font-size: $fs-sm;
}
.actions {
  margin-top: $gap-4;
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}
</style>
