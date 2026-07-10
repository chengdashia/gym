<template>
  <view class="onboarding">
    <!-- 步骤1：登录 / 注册 -->
    <view v-if="step === 0" class="step step-auth">
      <view class="auth-center">
        <view class="logo-wrap">
          <line-icon name="leaf" tint="mint" :size="120" class="logo" />
          <view class="brand">健身饮食</view>
          <view class="brand-sub">让健康管理更轻盈</view>
        </view>

        <view class="auth-card">
          <view class="auth-tabs">
            <view
              :class="['auth-tab', { active: authMode === 'login' }]"
              @tap="switchMode('login')"
            >登录</view>
            <view
              :class="['auth-tab', { active: authMode === 'register' }]"
              @tap="switchMode('register')"
            >注册</view>
          </view>

          <view class="auth-field">
            <text class="auth-field-label">手机号</text>
            <input
              v-model="authForm.phone"
              type="number"
              maxlength="11"
              placeholder="请输入手机号"
              class="auth-field-input"
            />
          </view>

          <view class="auth-field">
            <text class="auth-field-label">密码</text>
            <input
              v-model="authForm.password"
              password
              placeholder="请输入密码"
              class="auth-field-input"
            />
          </view>

          <template v-if="authMode === 'register'">
            <view class="auth-field">
              <text class="auth-field-label">确认密码</text>
              <input
                v-model="authForm.confirmPassword"
                password
                placeholder="请再次输入密码"
                class="auth-field-input"
              />
            </view>

            <view class="auth-field captcha-row">
              <text class="auth-field-label">验证码</text>
              <view class="captcha-wrap">
                <input
                  v-model="authForm.captchaCode"
                  placeholder="请输入验证码"
                  class="auth-field-input captcha-input"
                />
                <image
                  v-if="captcha.svg"
                  :src="captcha.svg"
                  mode="aspectFit"
                  class="captcha-img"
                  @tap="refreshCaptcha"
                />
              </view>
            </view>

            <view class="agree-row" @tap="agreed = !agreed">
              <view :class="['checkbox', { checked: agreed }]">
                <text v-if="agreed">✓</text>
              </view>
              <text class="agree-text">
                我已阅读并同意
                <text class="agreement-link" @tap.stop="goAgreement('agreement')">《用户协议》</text>
                和
                <text class="agreement-link" @tap.stop="goAgreement('privacy')">《隐私政策》</text>
              </text>
            </view>
          </template>
        </view>

        <button
          :class="['auth-submit', { disabled: authDisabled }]"
          :disabled="authDisabled"
          @tap="submitAuth"
        >
          {{ authMode === 'login' ? '登录' : '注册并登录' }}
        </button>
      </view>
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

        <view class="form-row column">
          <view class="form-row-line">
            <text class="form-label">年龄</text>
            <input v-model.number="form.age" type="number" placeholder="请输入年龄" class="form-input" />
            <text class="form-unit">岁</text>
          </view>
          <slider :min="10" :max="100" :step="1" :value="form.age" activeColor="#3FA67C" blockColor="#3FA67C" block-size="20" @changing="e => form.age = e.detail.value" @change="e => form.age = e.detail.value" class="form-slider" />
        </view>

        <view class="form-row column">
          <view class="form-row-line">
            <text class="form-label">身高</text>
            <input v-model.number="form.height_cm" type="digit" placeholder="请输入身高" class="form-input" />
            <text class="form-unit">cm</text>
          </view>
          <slider :min="120" :max="220" :step="1" :value="form.height_cm" activeColor="#3FA67C" blockColor="#3FA67C" block-size="20" @changing="e => form.height_cm = e.detail.value" @change="e => form.height_cm = e.detail.value" class="form-slider" />
        </view>

        <view class="form-row column">
          <view class="form-row-line">
            <text class="form-label">当前体重</text>
            <input v-model.number="form.current_weight_kg" type="digit" placeholder="请输入当前体重" class="form-input" />
            <text class="form-unit">kg</text>
          </view>
          <slider :min="30" :max="200" :step="0.5" :value="form.current_weight_kg" activeColor="#3FA67C" blockColor="#3FA67C" block-size="20" @changing="e => form.current_weight_kg = e.detail.value" @change="e => form.current_weight_kg = e.detail.value" class="form-slider" />
        </view>

        <view class="form-row column">
          <view class="form-row-line">
            <text class="form-label">目标体重</text>
            <input v-model.number="form.target_weight_kg" type="digit" placeholder="请输入目标体重" class="form-input" />
            <text class="form-unit">kg</text>
          </view>
          <slider :min="30" :max="200" :step="0.5" :value="form.target_weight_kg" activeColor="#3FA67C" blockColor="#3FA67C" block-size="20" @changing="e => form.target_weight_kg = e.detail.value" @change="e => form.target_weight_kg = e.detail.value" class="form-slider" />
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
import { reactive, ref, computed, onMounted } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { useUserStore } from '@/store/user';
import { authApi } from '@/api/auth';
import { FITNESS_GOALS, TRAINING_FREQUENCIES, FitnessGoal } from '@/utils/constants';

const step = ref(0);
const agreed = ref(false);
const authMode = ref<'login' | 'register'>('login');

const authForm = reactive({
  phone: '',
  password: '',
  confirmPassword: '',
  captchaCode: '',
});

const captcha = reactive({ id: '', svg: '' });

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
const redirectUrl = ref('/pages/home/index');

onLoad((options: any) => {
  if (options?.redirect) {
    redirectUrl.value = decodeURIComponent(options.redirect);
  }
});

const phoneReg = /^1[3-9]\d{9}$/;

const authDisabled = computed(() => {
  if (!phoneReg.test(authForm.phone) || authForm.password.length < 6) return true;
  if (authMode.value === 'register') {
    if (authForm.confirmPassword.length < 6 || authForm.captchaCode.length < 4 || !agreed.value) return true;
  }
  return false;
});

onMounted(() => {
  refreshCaptcha();
});

function switchMode(mode: 'login' | 'register') {
  authMode.value = mode;
  agreed.value = false;
}

async function refreshCaptcha() {
  try {
    const res = await authApi.getCaptcha();
    captcha.id = res.captcha_id;
    captcha.svg = res.svg;
  } catch {
    captcha.id = '';
    captcha.svg = '';
  }
}

async function submitAuth() {
  if (authDisabled.value) return;
  uni.showLoading({ title: authMode.value === 'login' ? '登录中...' : '注册中...' });
  try {
    let data;
    if (authMode.value === 'login') {
      data = await auth.phoneLogin(authForm.phone, authForm.password);
    } else {
      data = await auth.register(
        authForm.phone,
        authForm.password,
        authForm.confirmPassword,
        captcha.id,
        authForm.captchaCode,
      );
    }
    if (data.user.agreement_confirmed) {
      goHome();
      return;
    }
    step.value = 1;
  } catch (e: any) {
    uni.showToast({ title: e?.message || (authMode.value === 'login' ? '登录失败' : '注册失败'), icon: 'none' });
    refreshCaptcha();
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
    goHome();
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}

function goHome() {
  uni.reLaunch({ url: redirectUrl.value });
}

function goAgreement(type: 'agreement' | 'privacy') {
  uni.navigateTo({ url: `/pages/mine/agreement?type=${type}` });
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

// ----- Step 1: 登录 / 注册 -----
.step-auth {
  min-height: 100vh;
  justify-content: center;
  align-items: center;
  padding: $gap-4 $gap-4 $gap-6;

  .auth-center {
    width: 100%;
    max-width: 640rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .logo-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: $gap-5;
  }

  .logo {
    width: 120rpx;
    height: 120rpx;
  }

  .brand {
    margin-top: $gap-2;
    font-size: 40rpx;
    font-weight: 700;
    color: $primary-deep;
    letter-spacing: 1rpx;
  }

  .brand-sub {
    margin-top: $gap-1;
    font-size: $fs-sm;
    color: $text-3;
  }

  .auth-card {
    width: 100%;
    background: $glass-bg-soft;
    border-radius: $r-24;
    padding: $gap-4;
    box-shadow: 0 8rpx 32rpx rgba(31, 42, 42, 0.08);
    border: 1rpx solid rgba(255, 255, 255, 0.65);
    margin-bottom: $gap-4;
  }

  .auth-tabs {
    display: flex;
    gap: $gap-4;
    margin-bottom: $gap-4;
  }

  .auth-tab {
    position: relative;
    padding: $gap-1 0;
    font-size: $fs-lg;
    font-weight: 600;
    color: $text-3;
    transition: color 0.25s $ease-glass;

    &.active {
      color: $primary-deep;

      &::after {
        content: '';
        position: absolute;
        left: 0;
        right: 0;
        bottom: -4rpx;
        height: 4rpx;
        background: $gradient-primary;
        border-radius: $r-pill;
      }
    }
  }

  .auth-field {
    margin-bottom: $gap-3;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .auth-field-label {
    display: block;
    font-size: $fs-sm;
    color: $text-2;
    margin-bottom: $gap-1;
    font-weight: 500;
  }

  .auth-field-input {
    width: 100%;
    height: 76rpx;
    padding: 0 $gap-3;
    background: $primary-tint;
    border-radius: $r-12;
    font-size: $fs-md;
    color: $text-1;
    box-sizing: border-box;

    &::placeholder {
      color: $text-3;
    }
  }

  .captcha-wrap {
    display: flex;
    align-items: center;
    gap: $gap-2;
  }

  .captcha-input {
    flex: 1;
    min-width: 0;
  }

  .captcha-img {
    width: 180rpx;
    height: 76rpx;
    border-radius: $r-12;
    background: $card;
    flex-shrink: 0;
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

    &.checked {
      background: $gradient-primary;
      border-color: transparent;
      box-shadow: 0 4rpx 12rpx rgba(95, 175, 145, 0.35);
    }
  }

  .agree-text {
    font-size: $fs-sm;
    color: $text-2;
    flex: 1;
    line-height: 1.5;
  }

  .agreement-link {
    color: $primary-deep;
  }

  .auth-submit {
    width: 100%;
    height: 88rpx;
    line-height: 88rpx;
    border-radius: $r-16;
    border: none;
    background: $gradient-primary;
    color: #fff;
    font-size: $fs-lg;
    font-weight: 600;
    box-shadow: 0 8rpx 24rpx rgba(95, 175, 145, 0.32);
    transition: opacity 0.25s $ease-glass, transform 0.15s $ease-glass;

    &.disabled {
      opacity: 0.5;
      box-shadow: none;
    }

    &:active:not(.disabled) {
      transform: scale(0.92);
    }

    &::after {
      border: none;
    }
  }
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

.form-row-line {
  display: flex;
  align-items: center;
  gap: $gap-2;
  width: 100%;
}

.form-slider {
  width: 100%;
  margin: 0;
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
