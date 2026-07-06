<template>
  <view class="profile-page">
    <view class="form-card">
      <view class="row">
        <text class="label">昵称</text>
        <input v-model="form.nickname" placeholder="请输入昵称" class="input" />
      </view>
      <view class="row">
        <text class="label">头像URL</text>
        <input v-model="form.avatar_url" placeholder="可选" class="input" />
      </view>
      <view class="row">
        <text class="label">性别</text>
        <view class="seg">
          <view :class="['seg-item', { active: form.profile.gender === 'male' }]" @tap="form.profile.gender = 'male'">男</view>
          <view :class="['seg-item', { active: form.profile.gender === 'female' }]" @tap="form.profile.gender = 'female'">女</view>
        </view>
      </view>
      <view class="row">
        <text class="label">年龄</text>
        <input v-model.number="form.profile.age" type="number" placeholder="请输入" class="input" />
        <text class="unit">岁</text>
      </view>
      <view class="row">
        <text class="label">身高</text>
        <input v-model.number="form.profile.height_cm" type="digit" placeholder="请输入" class="input" />
        <text class="unit">cm</text>
      </view>
      <view class="row">
        <text class="label">当前体重</text>
        <input v-model.number="form.profile.current_weight_kg" type="digit" placeholder="请输入" class="input" />
        <text class="unit">kg</text>
      </view>
      <view class="row">
        <text class="label">目标体重</text>
        <input v-model.number="form.profile.target_weight_kg" type="digit" placeholder="请输入" class="input" />
        <text class="unit">kg</text>
      </view>
      <view class="row column">
        <text class="label">健身目标</text>
        <view class="chips">
          <view
            v-for="g in goals"
            :key="g.value"
            :class="['chip', { active: form.profile.fitness_goal === g.value }]"
            :style="form.profile.fitness_goal === g.value ? { background: g.color, color: '#fff' } : {}"
            @tap="form.profile.fitness_goal = g.value"
          >{{ g.label }}</view>
        </view>
      </view>
      <view class="row column">
        <text class="label">训练频率</text>
        <view class="chips">
          <view
            v-for="f in frequencies"
            :key="f.value"
            :class="['chip', { active: form.profile.training_frequency === f.value }]"
            @tap="form.profile.training_frequency = f.value"
          >{{ f.label }}</view>
        </view>
      </view>
    </view>

    <view class="actions">
      <PrimaryButton text="保存资料" @tap="save" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue';
import PrimaryButton from '@/components/PrimaryButton.vue';
import { useUserStore } from '@/store/user';
import { FITNESS_GOALS, TRAINING_FREQUENCIES } from '@/utils/constants';

const userStore = useUserStore();
const goals = FITNESS_GOALS;
const frequencies = TRAINING_FREQUENCIES;

const form = reactive({
  nickname: '',
  avatar_url: '',
  profile: {
    gender: 'male' as 'male' | 'female',
    age: 25,
    height_cm: 170,
    current_weight_kg: 65,
    target_weight_kg: 62,
    fitness_goal: 'fat_loss' as any,
    training_frequency: '3-4',
  },
});

onMounted(async () => {
  if (!userStore.me) await userStore.fetchMe().catch(() => {});
  const me = userStore.me;
  if (me) {
    form.nickname = me.nickname || '';
    form.avatar_url = me.avatar_url || '';
    if (me.profile) {
      form.profile.gender = (me.profile.gender as any) || 'male';
      form.profile.age = me.profile.age || 25;
      form.profile.height_cm = me.profile.height_cm || 170;
      form.profile.current_weight_kg = me.profile.current_weight_kg || 65;
      form.profile.target_weight_kg = me.profile.target_weight_kg || 62;
      form.profile.fitness_goal = (me.profile.fitness_goal as any) || 'fat_loss';
      form.profile.training_frequency = me.profile.training_frequency || '3-4';
    }
  }
});

async function save() {
  uni.showLoading({ title: '保存中...' });
  try {
    await userStore.updateProfile({
      nickname: form.nickname,
      avatar_url: form.avatar_url,
      profile: form.profile,
    });
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
.profile-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
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
  &.column {
    flex-direction: column;
    align-items: stretch;
    gap: $gap-1;
  }
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
.seg {
  flex: 1;
  display: flex;
  background: $bg-2;
  border-radius: $r-pill;
  padding: 4rpx;
}
.seg-item {
  flex: 1;
  text-align: center;
  padding: 12rpx;
  border-radius: $r-pill;
  font-size: $fs-sm;
  color: $text-2;
  &.active {
    background: $primary;
    color: #fff;
    font-weight: 500;
  }
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: $gap-1;
}
.chip {
  padding: 14rpx 28rpx;
  border-radius: $r-pill;
  background: $bg-2;
  color: $text-2;
  font-size: $fs-sm;
  &.active {
    background: $primary;
    color: #fff;
    font-weight: 500;
  }
}
.actions {
  margin-top: $gap-4;
}
</style>