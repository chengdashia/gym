<template>
  <view class="onboarding">
    <view v-if="step === 0" class="step step-auth">
      <view class="auth-center">
        <view class="logo-wrap">
          <image src="/static/logo.png" mode="aspectFit" class="logo" />
          <view class="brand">健身饮食</view>
          <view class="brand-sub">让健康管理更轻盈</view>
        </view>

        <view class="auth-card">
          <!-- #ifdef MP-WEIXIN -->
          <button class="auth-submit wechat-submit" @tap="submitWechatLogin">微信授权登录</button>
          <view class="phone-login-toggle" @tap="showPhoneLogin = !showPhoneLogin">
            {{ showPhoneLogin ? '收起手机号登录' : '使用手机号登录' }}
          </view>
          <!-- #endif -->

          <view v-if="showPhoneLogin">
            <view class="auth-tabs">
              <view :class="['auth-tab', { active: authMode === 'login' }]" @tap="switchMode('login')">登录</view>
              <view :class="['auth-tab', { active: authMode === 'register' }]" @tap="switchMode('register')">注册</view>
            </view>

            <view class="auth-field">
              <text class="auth-field-label">手机号</text>
              <input v-model="authForm.phone" type="number" maxlength="11" placeholder="请输入手机号" class="auth-field-input" />
            </view>

            <view class="auth-field">
              <text class="auth-field-label">密码</text>
              <input v-model="authForm.password" password placeholder="请输入密码" class="auth-field-input" />
            </view>

            <template v-if="authMode === 'register'">
              <view class="auth-field">
                <text class="auth-field-label">确认密码</text>
                <input v-model="authForm.confirmPassword" password placeholder="请再次输入密码" class="auth-field-input" />
              </view>

              <view class="auth-field captcha-row">
                <text class="auth-field-label">验证码</text>
                <view class="captcha-wrap">
                  <input v-model="authForm.captchaCode" placeholder="请输入验证码" class="auth-field-input captcha-input" />
                  <image v-if="captcha.svg" :src="captcha.svg" mode="aspectFit" class="captcha-img" @tap="refreshCaptcha" />
                </view>
              </view>

              <view class="agree-row" @tap="agreed = !agreed">
                <view :class="['checkbox', { checked: agreed }]"><text v-if="agreed">✓</text></view>
                <text class="agree-text">
                  我已阅读并同意
                  <text class="agreement-link" @tap.stop="goAgreement('agreement')">《用户协议》</text>
                  和
                  <text class="agreement-link" @tap.stop="goAgreement('privacy')">《隐私政策》</text>
                </text>
              </view>
            </template>

            <button :class="['auth-submit', { disabled: authDisabled }]" :disabled="authDisabled" @tap="submitAuth">
              {{ authMode === 'login' ? '手机号登录' : '注册并登录' }}
            </button>
          </view>
        </view>
      </view>
    </view>

    <view v-else class="step step-profile">
      <view class="profile-shell">
        <view class="profile-topline">
          <view class="step-title">完善个人资料</view>
          <view class="step-desc">设置一个头像和昵称，让大家更容易认识你</view>
        </view>

        <view class="profile-editor">
          <!-- #ifdef MP-WEIXIN -->
          <button class="avatar-picker" open-type="chooseAvatar" @chooseavatar="handleChooseAvatar">
            <view class="profile-avatar">
              <image v-if="profileAvatarSrc" :src="profileAvatarSrc" mode="aspectFill" />
              <text v-else>{{ profileDraft.nickname.slice(0, 1) || '健' }}</text>
            </view>
            <view class="avatar-edit">更换头像</view>
          </button>
          <!-- #endif -->
          <!-- #ifndef MP-WEIXIN -->
          <view class="avatar-picker" @tap="chooseCustomAvatar">
            <view class="profile-avatar">
              <image v-if="profileAvatarSrc" :src="profileAvatarSrc" mode="aspectFill" />
              <text v-else>{{ profileDraft.nickname.slice(0, 1) || '健' }}</text>
            </view>
            <view class="avatar-edit">更换头像</view>
          </view>
          <!-- #endif -->

          <button class="album-action" @tap="chooseCustomAvatar">从相册选择或拍照</button>

          <view class="nickname-field">
            <view class="field-label">昵称</view>
          <!-- #ifdef MP-WEIXIN -->
            <input class="nickname-input" type="nickname" :value="profileDraft.nickname" maxlength="20" placeholder="点击填写昵称" @input="handleNicknameInput" @blur="handleNicknameBlur" />
          <!-- #endif -->
          <!-- #ifndef MP-WEIXIN -->
            <input v-model="profileDraft.nickname" class="nickname-input" maxlength="20" placeholder="点击填写昵称" />
          <!-- #endif -->
          </view>
          <view class="profile-state">{{ profileStatus }}</view>
        </view>

        <view v-if="profileError" class="profile-feedback">{{ profileError }}</view>

        <view class="agree-row profile-agree" @tap="agreed = !agreed">
          <view :class="['checkbox', { checked: agreed }]"><text v-if="agreed">✓</text></view>
          <text class="agree-text">
            我已阅读并同意
            <text class="agreement-link" @tap.stop="goAgreement('agreement')">《用户协议》</text>
            和
            <text class="agreement-link" @tap.stop="goAgreement('privacy')">《隐私政策》</text>
          </text>
        </view>

        <button :class="['auth-submit', { disabled: !canFinishProfile }]" :disabled="!canFinishProfile" @tap="finishProfile">
          {{ profileLoading ? '正在保存' : '完成设置' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { useUserStore } from '@/store/user';
import { authApi } from '@/api/auth';
import { uploadApi } from '@/api/uploads';
import { resolveStaticUrl } from '@/utils/request';
import { isProfileComplete, profilePayload, type ProfileSource } from './profile-source';

const step = ref(0);
const agreed = ref(false);
const authMode = ref<'login' | 'register'>('login');
const showPhoneLogin = ref(true);
const auth = useAuthStore();
const userStore = useUserStore();
const redirectUrl = ref('/pages/home/index');

// #ifdef MP-WEIXIN
showPhoneLogin.value = false;
// #endif

const authForm = reactive({ phone: '', password: '', confirmPassword: '', captchaCode: '' });
const captcha = reactive({ id: '', svg: '' });
const profileDraft = reactive({ nickname: '', avatar_url: '' });
const profileSource = ref<ProfileSource>('default');
const profileLoading = ref(false);
const profileError = ref('');
const phoneReg = /^1[3-9]\d{9}$/;

const authDisabled = computed(() => {
  if (!phoneReg.test(authForm.phone) || authForm.password.length < 6) return true;
  if (authMode.value === 'register') {
    return authForm.confirmPassword.length < 6 || authForm.captchaCode.length < 4 || !agreed.value;
  }
  return false;
});

const profileAvatarSrc = computed(() => resolveStaticUrl(profileDraft.avatar_url));
const profileStatus = computed(() => {
  if (profileLoading.value) return '正在上传头像';
  if (profileDraft.nickname.trim() && profileDraft.avatar_url) return '资料已准备好';
  if (!profileDraft.avatar_url && !profileDraft.nickname.trim()) return '还需要头像和昵称';
  return profileDraft.avatar_url ? '还需要填写昵称' : '还需要选择头像';
});
const canFinishProfile = computed(() => agreed.value && isProfileComplete(
  profileSource.value,
  profileDraft.nickname,
  profileDraft.avatar_url,
));

onLoad((options: any) => {
  if (options?.redirect) redirectUrl.value = decodeURIComponent(options.redirect);
});

onMounted(() => {
  if (showPhoneLogin.value) refreshCaptcha();
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

async function submitWechatLogin() {
  uni.showLoading({ title: '微信登录中...' });
  try {
    const data = await auth.login();
    if (data.user.agreement_confirmed) {
      goHome();
      return;
    }
    resetProfileDraft();
    step.value = 1;
  } catch (e: any) {
    uni.showToast({ title: e?.message || '微信登录失败', icon: 'none' });
  } finally {
    (uni.hideLoading as any)({ fail: () => {} });
  }
}

function resetProfileDraft() {
  profileDraft.nickname = '';
  profileDraft.avatar_url = '';
  profileSource.value = 'default';
  profileError.value = '';
}

async function handleChooseAvatar(event: { detail?: { avatarUrl?: string } }) {
  await uploadAvatar(event.detail?.avatarUrl, 'wechat');
}

function chooseCustomAvatar() {
  if (profileLoading.value) return;
  uni.showActionSheet({
    itemList: ['从相册选择', '拍照'],
    success: ({ tapIndex }) => {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: [tapIndex === 0 ? 'album' : 'camera'],
        success: (result) => uploadAvatar(result.tempFilePaths?.[0], 'custom'),
      });
    },
  });
}

async function uploadAvatar(localPath: string | undefined, source: Extract<ProfileSource, 'wechat' | 'custom'>) {
  if (!localPath) return;
  profileError.value = '';
  profileLoading.value = true;
  try {
    const uploaded = await uploadApi.avatar(localPath);
    profileDraft.avatar_url = uploaded.file_url;
    profileSource.value = source;
  } catch (error: any) {
    profileError.value = error?.message || '头像上传失败，请重新选择';
  } finally {
    profileLoading.value = false;
  }
}

function handleNicknameInput(event: any) {
  profileDraft.nickname = event.detail?.value?.trim() || '';
  if (profileSource.value === 'default') profileSource.value = 'custom';
}

function handleNicknameBlur(event: any) { handleNicknameInput(event); }

async function submitAuth() {
  if (authDisabled.value) return;
  uni.showLoading({ title: authMode.value === 'login' ? '登录中...' : '注册中...' });
  try {
    const data = authMode.value === 'login'
      ? await auth.phoneLogin(authForm.phone, authForm.password)
      : await auth.register(authForm.phone, authForm.password, authForm.confirmPassword, captcha.id, authForm.captchaCode);
    if (data.user.agreement_confirmed) {
      goHome();
      return;
    }
    resetProfileDraft();
    agreed.value = authMode.value === 'register';
    step.value = 1;
  } catch (e: any) {
    uni.showToast({ title: e?.message || '登录失败', icon: 'none' });
    if (authMode.value === 'register') refreshCaptcha();
  } finally {
    (uni.hideLoading as any)({ fail: () => {} });
  }
}

async function finishProfile() {
  if (!canFinishProfile.value) {
    profileError.value = !profileDraft.nickname.trim() || !profileDraft.avatar_url
      ? '请先设置头像和昵称'
      : '请先同意用户协议和隐私政策';
    return;
  }
  uni.showLoading({ title: '保存资料中...' });
  try {
    const payload = profilePayload(profileSource.value, profileDraft.nickname, profileDraft.avatar_url);
    await userStore.updateProfile(payload);
    await userStore.confirmAgreement();
    auth.setUser({
      nickname: payload.nickname,
      avatar_url: payload.avatar_url || null,
      agreement_confirmed: true,
    });
    uni.showToast({ title: '登录成功', icon: 'success' });
    setTimeout(goHome, 500);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败，请重试', icon: 'none' });
  } finally {
    (uni.hideLoading as any)({ fail: () => {} });
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
.onboarding { min-height: 100vh; padding: $gap-4 $gap-3 $gap-6; background: $bg; }
.step { display: flex; flex-direction: column; }
.step-auth { min-height: 100vh; justify-content: center; align-items: center; padding: $gap-4; }
.auth-center { width: 100%; max-width: 640rpx; display: flex; flex-direction: column; align-items: center; }
.logo-wrap { display: flex; flex-direction: column; align-items: center; margin-bottom: $gap-5; }
.logo { width: 180rpx; height: 180rpx; border-radius: $r-24; }
.brand { margin-top: $gap-2; font-size: 40rpx; font-weight: 700; color: $primary-deep; }
.brand-sub { margin-top: $gap-1; font-size: $fs-sm; color: $text-3; }
.auth-card, .profile-card { width: 100%; background: $glass-bg-soft; border-radius: $r-24; padding: $gap-4; box-shadow: 0 8rpx 32rpx rgba(31, 42, 42, 0.08); border: 1rpx solid rgba(255, 255, 255, 0.65); box-sizing: border-box; }
.auth-tabs { display: flex; gap: $gap-4; margin-bottom: $gap-4; }
.auth-tab { position: relative; padding: $gap-1 0; font-size: $fs-lg; font-weight: 600; color: $text-3; }
.auth-tab.active { color: $primary-deep; }
.auth-field { margin-bottom: $gap-3; }
.auth-field-label, .profile-name-label { display: block; font-size: $fs-sm; color: $text-2; margin-bottom: $gap-1; font-weight: 500; }
.auth-field-input, .profile-name-input { width: 100%; box-sizing: border-box; padding: $gap-2; border-radius: $r-12; background: rgba(255, 255, 255, 0.75); color: $text-1; }
.captcha-row { display: flex; align-items: center; gap: $gap-2; }
.captcha-wrap { flex: 1; display: flex; gap: $gap-2; align-items: center; }
.captcha-img { width: 180rpx; height: 66rpx; }
.agree-row { display: flex; align-items: flex-start; gap: $gap-2; margin: $gap-3 0; }
.checkbox { width: 34rpx; height: 34rpx; border: 2rpx solid $primary; border-radius: 8rpx; display: flex; align-items: center; justify-content: center; color: #fff; flex: none; }
.checkbox.checked { background: $primary; }
.agree-text { font-size: $fs-sm; color: $text-2; line-height: 1.5; }
.agreement-link { color: $primary-deep; }
.auth-submit { width: 100%; height: 88rpx; line-height: 88rpx; border: none; border-radius: $r-16; background: $gradient-primary; color: #fff; font-size: $fs-lg; font-weight: 600; }
.auth-submit.disabled { opacity: 0.5; }
.wechat-submit { margin-bottom: $gap-2; }
.phone-login-toggle { padding: $gap-2 0 $gap-3; text-align: center; color: $primary-deep; font-size: $fs-sm; }
.step-profile { min-height: 100vh; justify-content: center; padding: 72rpx 0 100rpx; box-sizing: border-box; }
.profile-shell { width: 100%; max-width: 680rpx; margin: auto; }
.profile-topline { margin-bottom: 56rpx; text-align: center; }
.step-title { font-size: 48rpx; line-height: 1.2; font-weight: 760; color: $text-1; letter-spacing: -1rpx; }
.step-desc { margin-top: $gap-2; color: $text-3; font-size: $fs-sm; line-height: 1.6; }
.profile-editor { display: flex; flex-direction: column; align-items: center; }
.avatar-picker { margin: 0; padding: 0; border: 0; background: transparent; line-height: 1; }
.avatar-picker::after { border: 0; }
.profile-avatar { width: 176rpx; height: 176rpx; border: 8rpx solid #fff; border-radius: 50%; overflow: hidden; background: linear-gradient(145deg, #67d2a5, #3fa67c); box-shadow: 0 16rpx 40rpx rgba(51, 130, 94, 0.2); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 64rpx; box-sizing: border-box; }
.profile-avatar image { width: 100%; height: 100%; }
.avatar-edit { margin-top: $gap-2; color: $primary-deep; font-size: $fs-sm; line-height: 1.4; }
.album-action { margin: 10rpx 0 52rpx; padding: 0; border: 0; background: transparent; color: $text-3; font-size: $fs-xs; line-height: 48rpx; }
.album-action::after { border: 0; }
.nickname-field { width: 100%; }
.field-label { margin-bottom: $gap-1; color: $text-2; font-size: $fs-sm; font-weight: 600; }
.nickname-input { width: 100%; height: 96rpx; padding: 0 $gap-3; border: 1rpx solid rgba(63, 166, 124, .2); border-radius: $r-16; background: #fff; color: $text-1; font-size: $fs-md; box-sizing: border-box; text-align: center; box-shadow: 0 8rpx 24rpx rgba(31, 42, 42, .04); }
.profile-state { margin-top: $gap-2; color: $text-3; font-size: $fs-xs; }
.profile-feedback { margin-top: $gap-2; padding: $gap-2 $gap-3; border-radius: $r-12; background: #fff5e8; color: #a86828; font-size: $fs-xs; line-height: 1.5; }
.profile-agree { margin: 48rpx 0 $gap-3; }
</style>
