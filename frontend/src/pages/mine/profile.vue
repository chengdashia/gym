<template>
  <view class="profile-page">
    <view v-if="ready" class="form-wrap">
      <liquid-glass-card variant="light" :highlight="true" custom-style="margin-bottom:0">
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
        <view class="row column">
          <view class="row-line">
            <text class="label">年龄</text>
            <input v-model.number="form.profile.age" type="number" placeholder="请输入" class="input" @blur="clampAge" />
            <text class="unit">岁</text>
          </view>
          <slider :min="10" :max="100" :step="1" :value="num(form.profile.age)" active-color="#3FA67C" block-color="#3FA67C" background-color="#E8F5EE" block-size="28" @changing="onAgeChange" @change="onAgeChange" class="form-slider" />
        </view>
        <view class="row column">
          <view class="row-line">
            <text class="label">身高</text>
            <input v-model.number="form.profile.height_cm" type="number" placeholder="请输入" class="input" @blur="clampHeight" />
            <text class="unit">cm</text>
          </view>
          <slider :min="120" :max="220" :step="1" :value="num(form.profile.height_cm)" active-color="#3FA67C" block-color="#3FA67C" background-color="#E8F5EE" block-size="28" @changing="onHeightChange" @change="onHeightChange" class="form-slider" />
        </view>
        <view class="row column">
          <view class="row-line">
            <text class="label">当前体重</text>
            <input v-model.number="form.profile.current_weight_kg" type="digit" placeholder="请输入" class="input" @blur="clampWeight" />
            <text class="unit">kg</text>
          </view>
          <slider :min="30" :max="200" :step="0.5" :value="num(form.profile.current_weight_kg)" active-color="#3FA67C" block-color="#3FA67C" background-color="#E8F5EE" block-size="28" @changing="onCurrentWeightChange" @change="onCurrentWeightChange" class="form-slider" />
        </view>
        <view class="row column">
          <view class="row-line">
            <text class="label">目标体重</text>
            <input v-model.number="form.profile.target_weight_kg" type="digit" placeholder="请输入" class="input" @blur="clampTargetWeight" />
            <text class="unit">kg</text>
          </view>
          <slider :min="30" :max="200" :step="0.5" :value="num(form.profile.target_weight_kg)" active-color="#3FA67C" block-color="#3FA67C" background-color="#E8F5EE" block-size="28" @changing="onTargetWeightChange" @change="onTargetWeightChange" class="form-slider" />
        </view>
        <view class="row column">
          <text class="label">健身目标</text>
          <view class="chips">
            <view
              v-for="g in goals"
              :key="g.value"
              :class="['chip', { active: form.profile.fitness_goal === g.value }]"
              :style="chipStyle(g.value, g.color)"
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
      </liquid-glass-card>

      <view class="actions">
        <liquid-glass-button text="保存资料" variant="primary" @tap="save" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue';
import LiquidGlassCard from '@/components/LiquidGlassCard.vue';
import LiquidGlassButton from '@/components/LiquidGlassButton.vue';
import { useUserStore } from '@/store/user';
import { useAuthStore } from '@/store/auth';
import { FITNESS_GOALS, TRAINING_FREQUENCIES } from '@/utils/constants';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';

const userStore = useUserStore();
const auth = useAuthStore();
const goals = FITNESS_GOALS;
const frequencies = TRAINING_FREQUENCIES;
const ready = ref(false);

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

function num(v: any) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function syncFromStore() {
  const me = userStore.me;
  if (!me) return;
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

onMounted(async () => {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    requireAuth({ redirect: '/pages/mine/profile' });
    return;
  }
  if (!userStore.me) {
    await userStore.fetchMe().catch(() => {
      uni.showToast({ title: '加载失败', icon: 'none' });
    });
  }
  syncFromStore();
  ready.value = true;
});

function clampAge() { form.profile.age = Math.max(10, Math.min(100, Math.round(num(form.profile.age)))); }
function clampHeight() { form.profile.height_cm = Math.max(120, Math.min(220, Math.round(num(form.profile.height_cm)))); }
function clampWeight() { form.profile.current_weight_kg = Math.max(30, Math.min(200, Math.round(num(form.profile.current_weight_kg) * 2) / 2)); }
function clampTargetWeight() { form.profile.target_weight_kg = Math.max(30, Math.min(200, Math.round(num(form.profile.target_weight_kg) * 2) / 2)); }

function onAgeChange(e: any) { form.profile.age = e.detail.value; }
function onHeightChange(e: any) { form.profile.height_cm = e.detail.value; }
function onCurrentWeightChange(e: any) { form.profile.current_weight_kg = e.detail.value; }
function onTargetWeightChange(e: any) { form.profile.target_weight_kg = e.detail.value; }

function chipStyle(value: string, color?: string) {
  return form.profile.fitness_goal === value && color ? `background:${color};color:#fff` : undefined;
}

function validateProfile() {
  const { age, height_cm, current_weight_kg, target_weight_kg } = form.profile;
  if (!Number.isFinite(age) || !Number.isInteger(age) || age < 5 || age > 120) return false;
  if (!Number.isFinite(height_cm) || height_cm < 50 || height_cm > 300) return false;
  if (!Number.isFinite(current_weight_kg) || current_weight_kg < 20 || current_weight_kg > 500) return false;
  if (!Number.isFinite(target_weight_kg) || target_weight_kg < 20 || target_weight_kg > 500) return false;
  return true;
}

async function save() {
  if (!validateProfile()) {
    uni.showToast({ title: '请输入有效的数值', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '保存中...' });
  try {
    await userStore.updateProfile({
      nickname: form.nickname,
      avatar_url: form.avatar_url,
      profile: form.profile,
    });
    uni.hideLoading();
    uni.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/mine/index'), 600);
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.profile-page {
  padding: $gap-3;
}
.form-wrap {
  width: 100%;
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
.row-line {
  display: flex;
  align-items: center;
  gap: $gap-2;
  width: 100%;
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
.form-slider {
  width: 100%;
  margin: 0;
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
