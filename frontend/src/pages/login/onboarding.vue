<template>
  <view class="onboarding">
    <!-- 步骤1：协议 -->
    <view v-if="step === 0" class="step">
      <liquid-glass-panel variant="light" :highlight="true" :ambient="true" class="hero-panel">
        <view class="logo-wrap">
          <view class="logo">🌿</view>
          <view class="brand">健身饮食</view>
          <view class="brand-sub">让健康管理更轻盈</view>
        </view>
      </liquid-glass-panel>

      <liquid-glass-card :highlight="true" class="protocol-card">
        <view class="protocol-title">欢迎使用</view>
        <view class="protocol-desc">请仔细阅读以下协议条款，开始你的健康之旅。</view>

        <view class="protocol-item">
          <view class="protocol-name">📄 用户协议</view>
          <view class="protocol-content">
            欢迎使用健身饮食小程序（以下简称"本服务"）。在使用本服务前，请仔细阅读本协议。你使用本服务即视为同意本协议全部条款，包括个人信息处理规则、健康数据存储方式及第三方服务（微信登录、对象存储、模拟 AI 识别）的接入范围。
          </view>
        </view>

        <view class="protocol-item">
          <view class="protocol-name">🔒 隐私政策</view>
          <view class="protocol-content">
            我们非常重视你的隐私。本服务仅在为你提供饮食与训练记录功能所必需的范围内，收集你的头像、昵称、身体数据、饮食记录、训练记录和体重记录。你可以随时在「我的-账号与数据」中删除个人数据或注销账号。
          </view>
        </view>

        <view class="agree-row" @tap="agreed = !agreed">
          <view :class="['checkbox', { checked: agreed }]">
            <text v-if="agreed">✓</text>
          </view>
          <text class="agree-text">我已阅读并同意《用户协议》和《隐私政策》</text>
        </view>
      </liquid-glass-card>

      <liquid-glass-button
        text="同意并继续"
        variant="primary"
        size="lg"
        :disabled="!agreed"
        @tap="next"
      />
    </view>

    <!-- 步骤2：基础资料 -->
    <view v-else-if="step === 1" class="step">
      <view class="step-head">
        <liquid-glass-pill text="第 2 步" variant="soft" size="md" />
        <view class="step-title">基础信息</view>
        <view class="step-desc">用于计算你的每日营养目标</view>
      </view>

      <liquid-glass-card :highlight="true" class="form-card">
        <view class="form-row">
          <text class="form-label">性别</text>
          <view class="seg">
            <liquid-glass-pill
              :text="'男'"
              :variant="form.gender === 'male' ? 'primary' : 'default'"
              size="sm"
              interactive
              :active="form.gender === 'male'"
              @tap="form.gender = 'male'"
            />
            <liquid-glass-pill
              :text="'女'"
              :variant="form.gender === 'female' ? 'primary' : 'default'"
              size="sm"
              interactive
              :active="form.gender === 'female'"
              @tap="form.gender = 'female'"
            />
          </view>
        </view>

        <view class="form-row">
          <text class="form-label">年龄</text>
          <input v-model.number="form.age" type="number" placeholder="请输入年龄" class="form-input" />
          <text class="form-unit">岁</text>
        </view>

        <view class="form-row">
          <text class="form-label">身高</text>
          <input v-model.number="form.height_cm" type="digit" placeholder="请输入身高" class="form-input" />
          <text class="form-unit">cm</text>
        </view>

        <view class="form-row">
          <text class="form-label">当前体重</text>
          <input v-model.number="form.current_weight_kg" type="digit" placeholder="请输入当前体重" class="form-input" />
          <text class="form-unit">kg</text>
        </view>

        <view class="form-row">
          <text class="form-label">目标体重</text>
          <input v-model.number="form.target_weight_kg" type="digit" placeholder="请输入目标体重" class="form-input" />
          <text class="form-unit">kg</text>
        </view>

        <view class="form-row column">
          <text class="form-label">健身目标</text>
          <view class="chips">
            <liquid-glass-pill
              v-for="g in goals"
              :key="g.value"
              :text="g.label"
              :variant="form.fitness_goal === g.value ? 'primary' : 'soft'"
              size="md"
              interactive
              :active="form.fitness_goal === g.value"
              @tap="form.fitness_goal = g.value"
            />
          </view>
        </view>

        <view class="form-row column">
          <text class="form-label">每周训练频率</text>
          <view class="chips">
            <liquid-glass-pill
              v-for="f in frequencies"
              :key="f.value"
              :text="f.label"
              :variant="form.training_frequency === f.value ? 'primary' : 'soft'"
              size="md"
              interactive
              :active="form.training_frequency === f.value"
              @tap="form.training_frequency = f.value"
            />
          </view>
        </view>
      </liquid-glass-card>

      <view class="actions">
        <liquid-glass-button text="上一步" variant="ghost" size="md" :block="false" @tap="step = 0" customStyle="padding-left:36rpx;padding-right:36rpx;" />
        <liquid-glass-button text="下一步：生成目标" variant="primary" size="md" :block="false" @tap="submitProfile" customStyle="flex:1;margin-left:16rpx;" />
      </view>
    </view>

    <!-- 步骤3：推荐目标 -->
    <view v-else-if="step === 2" class="step">
      <view class="step-head">
        <liquid-glass-pill text="第 3 步" variant="soft" size="md" />
        <view class="step-title">你的每日营养目标</view>
        <view class="step-desc">系统已根据你的基础信息自动估算，可手动调整</view>
      </view>

      <liquid-glass-panel variant="mint" :highlight="true" :ambient="true" class="goal-panel">
        <view class="goal-big">
          <view class="goal-num">{{ goal.calories_kcal }}</view>
          <view class="goal-unit">kcal / 天</view>
        </view>
        <view class="goal-divider" />
        <view class="goal-macros">
          <view class="macro-cell">
            <view class="macro-name">碳水</view>
            <view class="macro-val">{{ goal.carbs_g }} g</view>
          </view>
          <view class="macro-cell">
            <view class="macro-name">蛋白质</view>
            <view class="macro-val">{{ goal.protein_g }} g</view>
          </view>
          <view class="macro-cell">
            <view class="macro-name">脂肪</view>
            <view class="macro-val">{{ goal.fat_g }} g</view>
          </view>
        </view>
      </liquid-glass-panel>

      <liquid-glass-card :highlight="true" class="form-card">
        <view class="form-row">
          <text class="form-label">热量 (kcal)</text>
          <input v-model.number="goal.calories_kcal" type="number" class="form-input" />
        </view>
        <view class="form-row">
          <text class="form-label">碳水 (g)</text>
          <input v-model.number="goal.carbs_g" type="digit" class="form-input" />
        </view>
        <view class="form-row">
          <text class="form-label">蛋白质 (g)</text>
          <input v-model.number="goal.protein_g" type="digit" class="form-input" />
        </view>
        <view class="form-row">
          <text class="form-label">脂肪 (g)</text>
          <input v-model.number="goal.fat_g" type="digit" class="form-input" />
        </view>
      </liquid-glass-card>

      <view class="actions">
        <liquid-glass-button text="上一步" variant="ghost" size="md" :block="false" @tap="step = 1" customStyle="padding-left:36rpx;padding-right:36rpx;" />
        <liquid-glass-button text="完成，开始记录" variant="primary" size="md" :block="false" @tap="finish" customStyle="flex:1;margin-left:16rpx;" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useAuthStore } from '@/store/auth';
import { useUserStore } from '@/store/user';
import { FITNESS_GOALS, TRAINING_FREQUENCIES, FitnessGoal } from '@/utils/constants';

const step = ref(0);
const agreed = ref(false);

const form = reactive({
  gender: 'male' as 'male' | 'female',
  age: 25,
  height_cm: 170,
  current_weight_kg: 65,
  target_weight_kg: 62,
  fitness_goal: 'fat_loss' as FitnessGoal,
  training_frequency: '3-4',
});

const goal = reactive({
  calories_kcal: 1800,
  carbs_g: 200,
  protein_g: 120,
  fat_g: 55,
});

const goals = FITNESS_GOALS;
const frequencies = TRAINING_FREQUENCIES;

const auth = useAuthStore();
const userStore = useUserStore();

async function next() {
  if (!agreed.value) return;
  uni.showLoading({ title: '登录中...' });
  try {
    if (!auth.token) {
      await auth.login();
    }
    await userStore.fetchMe();
    if (userStore.me?.agreement_confirmed) {
      uni.hideLoading();
      goHome();
      return;
    }
    step.value = 1;
  } catch (e: any) {
    uni.showToast({ title: e?.message || '登录失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}

async function submitProfile() {
  if (!form.age || !form.height_cm || !form.current_weight_kg || !form.target_weight_kg) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '保存中...' });
  try {
    await userStore.updateProfile({ profile: { ...form } });
    const recommended = await userStore.recommendGoal();
    Object.assign(goal, recommended);
    await userStore.confirmAgreement();
    step.value = 2;
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}

async function finish() {
  uni.showLoading({ title: '保存中...' });
  try {
    await userStore.updateGoal({ ...goal });
    uni.hideLoading();
    goHome();
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  }
}

function goHome() {
  uni.reLaunch({ url: '/pages/home/index' });
}
</script>

<style lang="scss" scoped>
.onboarding {
  min-height: 100vh;
  padding: $gap-4 $gap-3 $gap-6;
  animation: lg-fade-up 0.4s $ease-spring both;
}

.step {
  display: flex;
  flex-direction: column;
}

// ----- Step 1: 协议 -----
.hero-panel {
  margin-bottom: $gap-4;
  padding: $gap-5 $gap-3;
}

.logo-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo {
  width: 160rpx;
  height: 160rpx;
  border-radius: 40rpx;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 80rpx;
  box-shadow:
    0 16rpx 40rpx rgba(95, 175, 145, 0.35),
    inset 0 1rpx 0 rgba(255, 255, 255, 0.5);
}

.brand {
  margin-top: $gap-3;
  font-size: 48rpx;
  font-weight: 700;
  color: $primary-deep;
  letter-spacing: 1rpx;
}

.brand-sub {
  margin-top: $gap-1;
  font-size: $fs-md;
  color: $text-3;
}

.protocol-card {
  margin-bottom: $gap-4;
}

.protocol-title {
  font-size: $fs-xl;
  font-weight: 700;
  color: $text-1;
  text-align: center;
}

.protocol-desc {
  margin-top: $gap-1;
  text-align: center;
  color: $text-3;
  font-size: $fs-sm;
  margin-bottom: $gap-3;
}

.protocol-item {
  margin-bottom: $gap-2;
  padding: $gap-2;
  background: rgba(234, 248, 241, 0.5);
  border-radius: $r-16;
}

.protocol-name {
  font-size: $fs-md;
  font-weight: 600;
  color: $primary-deep;
  margin-bottom: 8rpx;
}

.protocol-content {
  font-size: $fs-sm;
  color: $text-2;
  line-height: 1.6;
}

.agree-row {
  display: flex;
  align-items: center;
  margin-top: $gap-3;
  gap: $gap-2;
}

.checkbox {
  width: 40rpx;
  height: 40rpx;
  border-radius: $r-12;
  background: rgba(255, 255, 255, 0.7);
  border: 2rpx solid rgba(95, 175, 145, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: $fs-md;
  font-weight: 700;
  transition: all 0.3s $ease-spring;
}

.checkbox.checked {
  background: $gradient-primary;
  border-color: transparent;
  box-shadow: 0 4rpx 12rpx rgba(95, 175, 145, 0.35);
}

.agree-text {
  font-size: $fs-sm;
  color: $text-2;
  flex: 1;
  line-height: 1.5;
}

// ----- Step 2/3 通用 -----
.step-head {
  margin: $gap-3 0 $gap-3;
}

.step-title {
  margin-top: $gap-2;
  font-size: 48rpx;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.5rpx;
}

.step-desc {
  margin-top: $gap-1;
  font-size: $fs-md;
  color: $text-3;
}

.form-card {
  padding: $gap-3;
}

.form-row {
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

.form-label {
  flex: 1;
  color: $text-2;
  font-size: $fs-md;
  font-weight: 500;
}

.form-input {
  flex: 2;
  text-align: right;
  font-size: $fs-md;
  color: $text-1;
  font-weight: 600;
}

.form-unit {
  color: $text-3;
  font-size: $fs-sm;
}

.seg {
  display: flex;
  gap: 12rpx;
  align-items: center;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: $gap-1;
}

.actions {
  display: flex;
  gap: $gap-2;
  align-items: center;
  margin-top: $gap-4;
}

// ----- Step 3: 推荐目标 -----
.goal-panel {
  padding: $gap-5 $gap-3;
  margin-bottom: $gap-3;
}

.goal-big {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8rpx;
  padding: $gap-2 0;
}

.goal-num {
  font-size: 96rpx;
  font-weight: 800;
  color: $primary-deep;
  line-height: 1;
  letter-spacing: -2rpx;
  text-shadow: 0 2rpx 8rpx rgba(95, 175, 145, 0.15);
}

.goal-unit {
  font-size: $fs-md;
  color: $primary-deep;
  opacity: 0.7;
}

.goal-divider {
  height: 1rpx;
  background: rgba(255, 255, 255, 0.5);
  margin: $gap-3 0;
}

.goal-macros {
  display: flex;
  justify-content: space-around;
}

.macro-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.macro-name {
  font-size: $fs-sm;
  color: $primary-deep;
  opacity: 0.75;
}

.macro-val {
  font-size: $fs-xl;
  font-weight: 700;
  color: $primary-deep;
}
</style>