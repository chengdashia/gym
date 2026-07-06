<template>
  <view class="mine-page">
    <view class="profile-card">
      <view class="avatar" @tap="goProfile">
        <text v-if="!avatar">{{ initial }}</text>
        <image v-else :src="avatar" class="avatar-img" mode="aspectFill" />
      </view>
      <view class="info">
        <view class="name">{{ nickname }}</view>
        <view class="meta">
          <Tag v-if="isMember" text="会员" variant="warn" />
          <Tag v-else text="普通用户" variant="neutral" />
          <text v-if="profile?.fitness_goal" class="goal-text">· {{ goalLabel }}</text>
        </view>
      </view>
      <view class="edit-btn" @tap="goProfile">编辑 ›</view>
    </view>

    <view class="grid">
      <view class="grid-item" @tap="goGoals">
        <view class="gi-icon" style="background: #EAF8F1; color: #3FA67C;">🎯</view>
        <view class="gi-label">目标</view>
        <view class="gi-value">{{ goal.calories_kcal }} kcal</view>
      </view>
      <view class="grid-item" @tap="goWeight">
        <view class="gi-icon" style="background: #FFF3DC; color: #B86A1F;">⚖️</view>
        <view class="gi-label">体重</view>
        <view class="gi-value">{{ profile?.current_weight_kg || '-' }} kg</view>
      </view>
      <view class="grid-item" @tap="goReminders">
        <view class="gi-icon" style="background: #E0F0FA; color: #2F6DA0;">🔔</view>
        <view class="gi-label">提醒</view>
        <view class="gi-value">{{ enabledReminderCount }} 项开启</view>
      </view>
      <view class="grid-item" @tap="goAccount">
        <view class="gi-icon" style="background: #F1E6F8; color: #7E45A6;">🔒</view>
        <view class="gi-label">账号</view>
        <view class="gi-value">数据管理</view>
      </view>
    </view>

    <view class="menu-card">
      <view class="menu-item" @tap="goProfile">
        <view class="mi-emoji">👤</view>
        <text class="mi-label">基础资料</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goGoals">
        <view class="mi-emoji">🎯</view>
        <text class="mi-label">目标设置</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goReminders">
        <view class="mi-emoji">🔔</view>
        <text class="mi-label">提醒设置</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goAccount">
        <view class="mi-emoji">🔒</view>
        <text class="mi-label">账号与数据</text>
        <text class="mi-arrow">›</text>
      </view>
    </view>

    <view class="menu-card">
      <view class="menu-item" @tap="goAgreement('agreement')">
        <view class="mi-emoji">📄</view>
        <text class="mi-label">用户协议</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goAgreement('privacy')">
        <view class="mi-emoji">🛡️</view>
        <text class="mi-label">隐私政策</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="logout">
        <view class="mi-emoji">🚪</view>
        <text class="mi-label" style="color: $danger;">退出登录</text>
        <text class="mi-arrow">›</text>
      </view>
    </view>

    <view class="version">v1.0.0 · 健身与饮食记录</view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useUserStore } from '@/store/user';
import { useAuthStore } from '@/store/auth';
import { useAppStore } from '@/store/app';
import Tag from '@/components/Tag.vue';
import { FITNESS_GOALS } from '@/utils/constants';
import { clearAll } from '@/utils/cache';

const userStore = useUserStore();
const auth = useAuthStore();
const appStore = useAppStore();

const nickname = computed(() => userStore.nickname);
const avatar = computed(() => userStore.avatar);
const initial = computed(() => nickname.value?.[0] || '健');
const profile = computed(() => userStore.me?.profile);
const goal = computed(() => userStore.goal);
const isMember = computed(() => !!userStore.me?.is_member);

const goalLabel = computed(() => {
  const v = profile.value?.fitness_goal;
  return FITNESS_GOALS.find((g) => g.value === v)?.label || '';
});

const enabledReminderCount = computed(() => userStore.reminders.filter((r) => r.enabled).length);

async function load() {
  if (!userStore.me) await userStore.fetchMe().catch(() => {});
  if (!userStore.goal?.calories_kcal) await userStore.fetchGoal().catch(() => {});
  await userStore.fetchReminders().catch(() => {});
}

onMounted(load);
onShow(load);

function goProfile() { uni.navigateTo({ url: '/pages/mine/profile' }); }
function goGoals() { uni.navigateTo({ url: '/pages/mine/goals' }); }
function goReminders() { uni.navigateTo({ url: '/pages/mine/reminders' }); }
function goAccount() { uni.navigateTo({ url: '/pages/mine/account' }); }
function goWeight() { uni.navigateTo({ url: '/pages/mine/account?action=weight' }); }
function goAgreement(t: 'agreement' | 'privacy') { uni.navigateTo({ url: `/pages/mine/agreement?type=${t}` }); }

function logout() {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出登录吗？',
    success: (r) => {
      if (r.confirm) {
        clearAll();
        auth.logout();
        uni.reLaunch({ url: '/pages/login/onboarding' });
      }
    },
  });
}
</script>

<style lang="scss" scoped>
.mine-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
  padding-bottom: calc(#{$tabbar-height} + #{$gap-4});
}

.profile-card {
  background: $gradient-card;
  border-radius: $r-24;
  padding: $gap-3;
  display: flex;
  align-items: center;
  gap: $gap-2;
  margin-bottom: $gap-3;
  box-shadow: $shadow-md;
}
.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 48rpx;
  font-weight: 600;
  flex-shrink: 0;
  overflow: hidden;
}
.avatar-img {
  width: 100%;
  height: 100%;
}
.info {
  flex: 1;
}
.name {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-1;
}
.meta {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.goal-text {
  font-size: $fs-sm;
  color: $text-3;
}
.edit-btn {
  padding: 12rpx 20rpx;
  background: $card;
  border-radius: $r-pill;
  font-size: $fs-sm;
  color: $primary;
  font-weight: 500;
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $gap-2;
  margin-bottom: $gap-3;
}
.grid-item {
  background: $card;
  border-radius: $r-16;
  padding: $gap-2;
  text-align: center;
  box-shadow: $shadow-sm;
}
.gi-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: $r-20;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  margin: 0 auto $gap-1;
}
.gi-label {
  font-size: $fs-xs;
  color: $text-3;
}
.gi-value {
  font-size: $fs-xs;
  color: $text-1;
  font-weight: 500;
  margin-top: 2rpx;
}

.menu-card {
  background: $card;
  border-radius: $r-20;
  margin-bottom: $gap-3;
  overflow: hidden;
  box-shadow: $shadow-sm;
}
.menu-item {
  display: flex;
  align-items: center;
  padding: $gap-3;
  border-bottom: 1rpx solid $divider;
  &:last-child { border-bottom: none; }
}
.mi-emoji {
  width: 64rpx;
  height: 64rpx;
  border-radius: $r-16;
  background: $bg-2;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  margin-right: $gap-2;
}
.mi-label {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
}
.mi-arrow {
  color: $text-3;
  font-size: $fs-lg;
}

.version {
  text-align: center;
  color: $text-3;
  font-size: $fs-xs;
  padding: $gap-3 0;
}
</style>