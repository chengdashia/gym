<template>
  <view class="goals-page">
    <view class="head-card">
      <view class="head-emoji">🎯</view>
      <view class="head-text">每日营养目标</view>
      <view class="head-sub">系统会基于你的基础信息推荐，可手动调整</view>
    </view>

    <view class="form-card">
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
    </view>

    <view class="actions">
      <view class="btn-secondary" @tap="recommend">使用推荐值</view>
      <PrimaryButton text="保存目标" @tap="save" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue';
import PrimaryButton from '@/components/PrimaryButton.vue';
import { useUserStore } from '@/store/user';

const userStore = useUserStore();

const goal = reactive({
  calories_kcal: 0,
  carbs_g: 0,
  protein_g: 0,
  fat_g: 0,
});

onMounted(async () => {
  if (!userStore.goal?.calories_kcal) await userStore.fetchGoal().catch(() => {});
  Object.assign(goal, userStore.goal);
});

async function recommend() {
  uni.showLoading({ title: '生成中...' });
  try {
    const data = await userStore.recommendGoal();
    Object.assign(goal, data);
    uni.hideLoading();
  } catch {
    uni.hideLoading();
  }
}

async function save() {
  uni.showLoading({ title: '保存中...' });
  try {
    await userStore.updateGoal({ ...goal });
    uni.hideLoading();
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 600);
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.goals-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
}
.head-card {
  background: $gradient-primary;
  border-radius: $r-24;
  padding: $gap-4 $gap-3;
  margin-bottom: $gap-3;
  text-align: center;
  color: #fff;
}
.head-emoji {
  font-size: 64rpx;
}
.head-text {
  margin-top: $gap-1;
  font-size: 32rpx;
  font-weight: 700;
}
.head-sub {
  margin-top: 4rpx;
  font-size: $fs-sm;
  opacity: 0.85;
}
.form-card {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  box-shadow: $shadow-sm;
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
.btn-secondary {
  text-align: center;
  padding: 24rpx;
  background: $card;
  border-radius: $r-16;
  color: $primary;
  font-size: $fs-md;
  font-weight: 500;
}
</style>