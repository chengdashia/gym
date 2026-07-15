<template>
  <view class="onboarding">
    <view class="hero">
      <image src="/static/logo.png" mode="aspectFit" class="logo" />
      <view class="title">开始本地健康记录</view>
      <view class="subtitle">资料只保存在这台设备，不需要登录或联网</view>
    </view>

    <view class="card">
      <view class="field">
        <text class="label">昵称</text>
        <input v-model="form.nickname" maxlength="20" placeholder="例如：健身伙伴" class="input" />
      </view>

      <view class="field">
        <text class="label">性别</text>
        <view class="choices">
          <view v-for="item in genders" :key="item.value" :class="['choice', { active: form.gender === item.value }]" @tap="form.gender = item.value">
            {{ item.label }}
          </view>
        </view>
      </view>

      <view class="grid">
        <view class="field">
          <text class="label">年龄</text>
          <input v-model.number="form.age" type="number" placeholder="岁" class="input" />
        </view>
        <view class="field">
          <text class="label">身高</text>
          <input v-model.number="form.height_cm" type="digit" placeholder="cm" class="input" />
        </view>
        <view class="field">
          <text class="label">当前体重</text>
          <input v-model.number="form.current_weight_kg" type="digit" placeholder="kg" class="input" />
        </view>
        <view class="field">
          <text class="label">目标体重</text>
          <input v-model.number="form.target_weight_kg" type="digit" placeholder="kg" class="input" />
        </view>
      </view>

      <view class="field">
        <text class="label">核心目标</text>
        <view class="choices wrap">
          <view v-for="goal in goals" :key="goal.value" :class="['choice', { active: form.fitness_goal === goal.value }]" @tap="form.fitness_goal = goal.value">
            {{ goal.label }}
          </view>
        </view>
      </view>

      <view class="field">
        <text class="label">每周训练频率</text>
        <picker :range="frequencies" range-key="label" @change="selectFrequency">
          <view class="input picker-value">{{ selectedFrequencyLabel }}</view>
        </picker>
      </view>

      <view v-if="error" class="error">{{ error }}</view>
      <button class="submit" :disabled="saving" @tap="save">
        {{ saving ? '正在保存…' : '完成设置' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue';

import { userApi } from '@/api/user';
import { useAuthStore } from '@/store/auth';
import { FITNESS_GOALS, TRAINING_FREQUENCIES } from '@/utils/constants';

const auth = useAuthStore();
const goals = FITNESS_GOALS;
const frequencies = TRAINING_FREQUENCIES;
const genders = [
  { value: 'male', label: '男' },
  { value: 'female', label: '女' },
  { value: 'other', label: '其他' },
];
const saving = ref(false);
const error = ref('');
const form = reactive({
  nickname: '',
  gender: '' as string,
  age: null as number | null,
  height_cm: null as number | null,
  current_weight_kg: null as number | null,
  target_weight_kg: null as number | null,
  fitness_goal: '' as string,
  training_frequency: '3-4',
});

const selectedFrequencyLabel = computed(() =>
  frequencies.find((item) => item.value === form.training_frequency)?.label || '请选择',
);

function selectFrequency(event: { detail: { value: string | number } }) {
  const item = frequencies[Number(event.detail.value)];
  if (item) form.training_frequency = item.value;
}

function validate(): string {
  if (!form.nickname.trim()) return '请输入昵称';
  if (!form.fitness_goal) return '请选择核心目标';
  if (form.age != null && (form.age < 10 || form.age > 120)) return '年龄应在 10–120 岁之间';
  if (form.height_cm != null && (form.height_cm < 50 || form.height_cm > 250)) return '请输入有效身高';
  if (form.current_weight_kg != null && (form.current_weight_kg < 20 || form.current_weight_kg > 250)) return '请输入有效当前体重';
  if (form.target_weight_kg != null && (form.target_weight_kg < 20 || form.target_weight_kg > 250)) return '请输入有效目标体重';
  return '';
}

async function save() {
  error.value = validate();
  if (error.value || saving.value) return;
  saving.value = true;
  try {
    const weight = form.current_weight_kg || 70;
    const calories = Math.round(weight * 28);
    await userApi.finishOnboarding({
      ...form,
      calories_kcal: calories,
      carbs_g: Math.round(calories * 0.45 / 4),
      protein_g: Math.round(weight * 1.6),
      fat_g: Math.round(calories * 0.25 / 9),
    });
    await auth.refresh();
    uni.reLaunch({ url: '/pages/home/index' });
  } catch (cause: any) {
    error.value = cause?.message || '本地资料保存失败';
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped lang="scss">
.onboarding { min-height: 100vh; padding: 72rpx 32rpx 80rpx; box-sizing: border-box; background: $bg; }
.hero { display: flex; flex-direction: column; align-items: center; margin-bottom: 36rpx; text-align: center; }
.logo { width: 140rpx; height: 140rpx; border-radius: $r-24; }
.title { margin-top: 20rpx; color: $text-1; font-size: 42rpx; font-weight: 750; }
.subtitle { margin-top: 10rpx; color: $text-3; font-size: $fs-sm; }
.card { max-width: 720rpx; margin: auto; padding: 32rpx; border: 1rpx solid rgba(255,255,255,.7); border-radius: $r-24; background: $glass-bg-soft; box-shadow: 0 12rpx 40rpx rgba(31,42,42,.08); }
.field { margin-bottom: 26rpx; }
.label { display: block; margin-bottom: 10rpx; color: $text-2; font-size: $fs-sm; font-weight: 600; }
.input { width: 100%; min-height: 84rpx; padding: 0 22rpx; box-sizing: border-box; border: 1rpx solid rgba(63,166,124,.18); border-radius: $r-16; background: #fff; color: $text-1; }
.picker-value { display: flex; align-items: center; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 20rpx; }
.choices { display: flex; gap: 16rpx; }
.choices.wrap { flex-wrap: wrap; }
.choice { flex: 1; min-width: 110rpx; padding: 18rpx; border: 1rpx solid rgba(63,166,124,.2); border-radius: $r-12; background: #fff; text-align: center; color: $text-2; }
.choice.active { border-color: $primary; background: rgba(63,166,124,.1); color: $primary-deep; font-weight: 650; }
.error { margin-bottom: 20rpx; color: #c65353; font-size: $fs-sm; }
.submit { height: 92rpx; border: 0; border-radius: $r-16; background: $gradient-primary; color: #fff; font-size: $fs-lg; font-weight: 700; line-height: 92rpx; }
.submit::after { border: 0; }
</style>
