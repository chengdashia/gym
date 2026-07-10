<template>
  <view class="mine-page">
    <!-- Profile 玻璃面板（带环境光斑） -->
    <liquid-glass-panel variant="mint" :highlight="true" :ambient="true" class="profile-panel">
      <view class="profile-row">
        <view class="avatar" @tap="goProfile">
          <text v-if="!avatar">{{ initial }}</text>
          <image v-else :src="avatar" class="avatar-img" mode="aspectFill" />
        </view>
        <view class="info">
          <view class="name">{{ nickname }}</view>
          <view class="meta">
            <liquid-glass-pill
              :text="isMember ? '会员' : '普通用户'"
              :variant="isMember ? 'warn' : 'default'"
              size="xs"
            />
            <text v-if="profile?.fitness_goal" class="goal-text">· {{ goalLabel }}</text>
          </view>
        </view>
        <view class="edit-btn" @tap="goProfile">
          <text>编辑</text>
          <text class="edit-arrow">›</text>
        </view>
      </view>
    </liquid-glass-panel>

    <!-- 4 格入口 -->
    <view class="grid">
      <liquid-glass-card :highlight="true" hoverable radius="20rpx" padding="20rpx 0" @tap="goGoals" class="grid-item">
        <line-icon name="target" color="#8FA3A1" :stroke-width="1.7" :size="52" class="gi-icon" />
        <view class="gi-label">目标</view>
        <view class="gi-value">{{ goal.calories_kcal }} kcal</view>
      </liquid-glass-card>
      <liquid-glass-card :highlight="true" hoverable radius="20rpx" padding="20rpx 0" @tap="goWeight" class="grid-item">
        <line-icon name="scale" color="#8FA3A1" :stroke-width="1.7" :size="52" class="gi-icon" />
        <view class="gi-label">体重</view>
        <view class="gi-value">{{ profile?.current_weight_kg || '-' }} kg</view>
      </liquid-glass-card>
      <liquid-glass-card :highlight="true" hoverable radius="20rpx" padding="20rpx 0" @tap="goAccount" class="grid-item">
        <line-icon name="lock" color="#8FA3A1" :stroke-width="1.7" :size="52" class="gi-icon" />
        <view class="gi-label">账号</view>
        <view class="gi-value">数据管理</view>
      </liquid-glass-card>
    </view>

    <!-- 菜单 1 -->
    <liquid-glass-card :highlight="true" class="menu-card">
      <view class="menu-item" @tap="goProfile">
        <line-icon name="user" color="#8FA3A1" :stroke-width="1.7" :size="44" class="mi-icon" />
        <text class="mi-label">基础资料</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goGoals">
        <line-icon name="target" color="#8FA3A1" :stroke-width="1.7" :size="44" class="mi-icon" />
        <text class="mi-label">目标设置</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goAccount">
        <line-icon name="lock" color="#8FA3A1" :stroke-width="1.7" :size="44" class="mi-icon" />
        <text class="mi-label">账号与数据</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goTrainingHistory">
        <line-icon name="history" color="#8FA3A1" :stroke-width="1.7" :size="44" class="mi-icon" />
        <text class="mi-label">训练历史</text>
        <text class="mi-arrow">›</text>
      </view>
    </liquid-glass-card>

    <!-- 菜单 2 -->
    <liquid-glass-card :highlight="true" class="menu-card">
      <view class="menu-item" @tap="goAgreement('agreement')">
        <line-icon name="document" color="#8FA3A1" :stroke-width="1.7" :size="44" class="mi-icon" />
        <text class="mi-label">用户协议</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goAgreement('privacy')">
        <line-icon name="shield" color="#8FA3A1" :stroke-width="1.7" :size="44" class="mi-icon" />
        <text class="mi-label">隐私政策</text>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="logout">
        <line-icon name="logout" color="#D96B7D" :stroke-width="1.7" :size="44" class="mi-icon" />
        <text class="mi-label danger">退出登录</text>
        <text class="mi-arrow">›</text>
      </view>
    </liquid-glass-card>

    <view class="version">v1.0.0 · 健身与饮食记录</view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useUserStore } from '@/store/user';
import { useAuthStore } from '@/store/auth';
import { FITNESS_GOALS } from '@/utils/constants';
import { clearAll } from '@/utils/cache';
import { requireAuth } from '@/utils/auth-guard';

// 同步自定义 tabBar 高亮
function syncTabBar() {
  const pages = getCurrentPages();
  const page = pages[pages.length - 1];
  const tabBar = (page as any)?.getTabBar?.();
  if (tabBar) tabBar.setData({ activeIdx: 4 });
}

const userStore = useUserStore();
const auth = useAuthStore();

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

async function load() {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  if (!userStore.me) await userStore.fetchMe().catch(() => {});
  if (!userStore.goal?.calories_kcal) await userStore.fetchGoal().catch(() => {});
}

onMounted(load);
onShow(() => {
  syncTabBar();
  if (auth.isLogged) load();
});

function goProfile() {
  const url = '/pages/mine/profile';
  if (!requireAuth({ redirect: url })) return;
  uni.navigateTo({ url });
}
function goGoals() {
  const url = '/pages/mine/goals';
  if (!requireAuth({ redirect: url })) return;
  uni.navigateTo({ url });
}
function goAccount() {
  const url = '/pages/mine/account';
  if (!requireAuth({ redirect: url })) return;
  uni.navigateTo({ url });
}
function goWeight() {
  const url = '/pages/mine/account?action=weight';
  if (!requireAuth({ redirect: url })) return;
  uni.navigateTo({ url });
}
function goTrainingHistory() {
  const url = '/pages/training/history';
  if (!requireAuth({ redirect: url })) return;
  uni.navigateTo({ url });
}
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
  padding: $gap-3;
  padding-bottom: calc(#{$tabbar-height} + #{$gap-4});
}

// ----- Profile Panel -----
.profile-panel {
  padding: $gap-3;
  position: relative;
  overflow: hidden;
}

.profile-row {
  display: flex;
  align-items: center;
  gap: $gap-2;
  position: relative;
  z-index: 1;
}

.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #FFFFFF 0%, #C5ECDB 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: $primary-deep;
  font-size: 48rpx;
  font-weight: 800;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow:
    inset 0 2rpx 0 rgba(255, 255, 255, 0.8),
    0 6rpx 16rpx rgba(95, 175, 145, 0.2);
  transition: transform 0.3s $ease-spring;
}

.avatar:active {
  transform: scale(0.92);
}

.avatar-img {
  width: 100%;
  height: 100%;
}

.info {
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 36rpx;
  font-weight: 800;
  color: $primary-deep;
  letter-spacing: 0.3rpx;
}

.meta {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.goal-text {
  font-size: $fs-sm;
  color: $text-2;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: 12rpx 20rpx;
  background: rgba(255, 255, 255, 0.65);
  border-radius: $r-pill;
  font-size: $fs-sm;
  color: $primary-deep;
  font-weight: 600;
  box-shadow:
    inset 0 1rpx 0 rgba(255, 255, 255, 0.7),
    0 2rpx 6rpx rgba(95, 175, 145, 0.1);
  transition: background 0.3s $ease-glass, transform 0.3s $ease-spring;

  &:active {
    background: rgba(255, 255, 255, 0.9);
    transform: scale(0.92);
  }
}

.edit-arrow {
  font-size: $fs-md;
  line-height: 1;
}

// ----- Grid -----
.grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $gap-2;
  margin-bottom: $gap-3;
}

.grid-item {
  text-align: center;
}

.gi-icon {
  margin: 0 auto 8rpx;
}

.gi-label {
  font-size: $fs-xs;
  color: $text-3;
  font-weight: 500;
}

.gi-value {
  font-size: $fs-xs;
  color: $text-1;
  font-weight: 700;
  margin-top: 2rpx;
}

// ----- Menu Card -----
.menu-card {
  padding: 0;
  margin-bottom: $gap-3;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: $gap-3;
  border-bottom: 1rpx solid $divider;
  transition: background 0.3s $ease-glass;

  &:active {
    background: rgba(255, 255, 255, 0.5);
  }

  &:last-child { border-bottom: none; }
}

.mi-icon {
  margin-right: $gap-2;
}

.mi-label {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;

  &.danger { color: $danger; font-weight: 600; }
}

.mi-arrow {
  color: $text-3;
  font-size: $fs-lg;
  line-height: 1;
}

.version {
  text-align: center;
  color: $text-3;
  font-size: $fs-xs;
  padding: $gap-3 0;
  opacity: 0.7;
}
</style>
