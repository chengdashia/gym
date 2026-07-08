<template>
  <view class="home">
    <!-- Hero 玻璃面板：卡路里环 + 三大营养 -->
    <view class="hero-section">
      <view class="hero-top">
        <view class="greet">
          <view class="hi">{{ greetText }}，{{ nickname }}</view>
          <view class="date">{{ dateText }}</view>
        </view>
        <view class="avatar-wrap" @tap="goMine">
          <view class="avatar">
            <text v-if="!avatar">{{ initial }}</text>
            <image v-else :src="avatar" mode="aspectFill" class="avatar-img" />
          </view>
        </view>
      </view>

      <liquid-glass-panel variant="light" :highlight="true" :ambient="true" class="ring-panel">
        <view class="ring-row">
          <view class="ring-wrap">
            <ProgressRing
              :value="diet.calories_kcal"
              :goal="diet.calories_goal || 1"
              :size="220"
              :thickness="18"
              color="#5BC89A"
            >
              <view class="ring-content">
                <view class="ring-num">{{ Math.round(diet.calories_kcal) }}</view>
                <view class="ring-label">已摄入 kcal</view>
                <view class="ring-goal">目标 {{ Math.round(diet.calories_goal) }}</view>
              </view>
            </ProgressRing>
          </view>

          <view class="ring-macros">
            <MacroBar label="碳水" :value="diet.carbs_g" :goal="diet.carbs_goal" color="#FFD79A" />
            <MacroBar label="蛋白质" :value="diet.protein_g" :goal="diet.protein_goal" color="#5BC89A" />
            <MacroBar label="脂肪" :value="diet.fat_g" :goal="diet.fat_goal" color="#C490E0" />
          </view>
        </view>
      </liquid-glass-panel>
    </view>

    <view class="container">
      <!-- 训练卡 -->
      <liquid-glass-card :highlight="true" hoverable @tap="goTraining" class="card-section">
        <view class="section-head">
          <view class="left">
            <view class="bar" />
            <text class="title">今日训练</text>
            <liquid-glass-pill v-if="training.status === 'in_progress'" text="进行中" variant="primary" size="xs" />
            <liquid-glass-pill v-else-if="training.is_rest_day" text="休息日" variant="soft" size="xs" />
          </view>
          <text class="more">查看 ›</text>
        </view>

        <view v-if="training.status === 'no_plan'" class="empty-card">
          <line-icon name="dumbbell" tint="mint" :size="80" class="emoji" />
          <view class="empty-title">还没有训练计划</view>
          <view class="empty-desc">选择一个模板或自定义创建你的第一个计划</view>
          <liquid-glass-button text="创建训练计划" variant="primary" size="sm" :block="false" @tap.stop="goCreatePlan" />
        </view>

        <view v-else class="training-info">
          <view class="training-name">{{ training.title || '今日休息' }}</view>
          <view class="training-meta">
            <text>共 {{ training.exercise_count }} 个动作</text>
          </view>
          <view class="training-actions">
            <liquid-glass-button
              v-if="training.status === 'in_progress'"
              text="继续训练"
              variant="primary"
              size="sm"
              :block="false"
              @tap.stop="continueSession"
            />
            <liquid-glass-button
              v-else-if="!training.is_rest_day"
              text="开始训练"
              variant="primary"
              size="sm"
              :block="false"
              @tap.stop="startSession"
            />
            <liquid-glass-pill v-else text="好好休息" variant="soft" size="sm" />
          </view>
        </view>
      </liquid-glass-card>

      <!-- 体重卡 -->
      <liquid-glass-card :highlight="true" class="card-section">
        <view class="section-head">
          <view class="left">
            <view class="bar" />
            <text class="title">体重目标</text>
          </view>
          <text class="more" @tap.stop="goStats">趋势 ›</text>
        </view>

        <view v-if="!weight.current_weight_kg" class="empty-card mini">
          <line-icon name="scale" tint="warm" :size="80" class="emoji" />
          <view class="empty-title">还没有体重记录</view>
          <view class="empty-desc">记录第一次体重，开始追踪变化</view>
          <liquid-glass-button text="记录体重" variant="soft" size="sm" :block="false" @tap="recordWeight" />
        </view>

        <view v-else class="weight-info">
          <view class="weight-numbers">
            <view class="weight-current">
              <view class="num">{{ weight.current_weight_kg }}</view>
              <view class="unit">kg 当前</view>
            </view>
            <view class="weight-arrow">→</view>
            <view class="weight-target">
              <view class="num">{{ weight.target_weight_kg || '-' }}</view>
              <view class="unit">kg 目标</view>
            </view>
          </view>
          <view :class="['weight-diff', { pos: (weight.diff_kg || 0) > 0, neg: (weight.diff_kg || 0) < 0 }]">
            <text v-if="weight.diff_kg && weight.diff_kg > 0">还需减 {{ weight.diff_kg }} kg</text>
            <text v-else-if="weight.diff_kg && weight.diff_kg < 0">还需增 {{ -weight.diff_kg }} kg</text>
            <text v-else>已达成目标</text>
          </view>
          <view class="weight-actions">
            <liquid-glass-button text="记录体重" variant="soft" size="sm" :block="false" @tap="recordWeight" />
          </view>
          <view v-if="weight.last_recorded_at" class="weight-foot">最近记录：{{ formatDateTime(weight.last_recorded_at) }}</view>
        </view>
      </liquid-glass-card>
    </view>

    <!-- 自定义液态玻璃 TabBar 由 pages.json tabBar.custom 渲染 -->
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { homeApi, HomeSummary } from '@/api/home';
import { useUserStore } from '@/store/user';
import { useAuthStore } from '@/store/auth';
import { useTrainingStore } from '@/store/training';
import ProgressRing from '@/components/ProgressRing.vue';
import MacroBar from '@/components/MacroBar.vue';
import { today, weekdayCN, dateMD, formatDateTime } from '@/utils/date';
import { requireAuth } from '@/utils/auth-guard';

// 同步自定义 tabBar 高亮
function syncTabBar() {
  const pages = getCurrentPages();
  const page = pages[pages.length - 1];
  const tabBar = (page as any)?.getTabBar?.();
  if (tabBar) tabBar.setData({ activeIdx: 0 });
}

const userStore = useUserStore();
const trainingStore = useTrainingStore();

const summary = ref<HomeSummary | null>(null);
const nickname = computed(() => userStore.nickname);
const avatar = computed(() => userStore.avatar);
const initial = computed(() => nickname.value?.[0] || '健');

const diet = computed(() => summary.value?.diet || {
  calories_kcal: 0, calories_goal: 0,
  carbs_g: 0, carbs_goal: 0,
  protein_g: 0, protein_goal: 0,
  fat_g: 0, fat_goal: 0,
  record_count: 0,
});

const training = computed(() => summary.value?.training || {
  status: 'no_plan', plan_id: null, plan_day_id: null,
  session_id: null, title: null, exercise_count: 0, is_rest_day: false,
} as HomeSummary['training']);

const weight = computed(() => summary.value?.weight || {
  current_weight_kg: null, target_weight_kg: null, diff_kg: null, last_recorded_at: null,
} as HomeSummary['weight']);

const greetText = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return '凌晨好';
  if (h < 11) return '早上好';
  if (h < 14) return '中午好';
  if (h < 18) return '下午好';
  return '晚上好';
});

const dateText = computed(() => `${dateMD(today())} ${weekdayCN(today())}`);

async function load() {
  try {
    summary.value = await homeApi.summary(today());
  } catch (e) {
    console.error('[home] load failed', e);
  }
}

onMounted(async () => {
  const auth = useAuthStore();
  if (!auth.ready) await auth.bootstrap();
  // 登录态但未确认协议 → 跳到 onboarding 完善资料
  // 放在首页 onMounted 中执行（页面 webview 已 ready），避免 onLaunch 过早 reLaunch
  // 触发「routeDone with a webviewId X is not found」错误
  if (auth.token && auth.user && !auth.user.agreement_confirmed) {
    uni.reLaunch({ url: '/pages/login/onboarding' });
    return;
  }
  if (auth.isLogged) {
    if (!userStore.me) await userStore.fetchMe().catch(() => {});
    if (!userStore.goal?.calories_kcal) await userStore.fetchGoal().catch(() => {});
    await load();
  }
});

onShow(async () => {
  syncTabBar();
  const auth = useAuthStore();
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  if (!userStore.me) await userStore.fetchMe().catch(() => {});
  load();
});

function goMine() { uni.switchTab({ url: '/pages/mine/index' }); }
function goTraining() { uni.switchTab({ url: '/pages/training/index' }); }
function goStats() { uni.switchTab({ url: '/pages/stats/index' }); }

async function startSession() {
  if (!requireAuth({ redirect: '/pages/home/index' })) return;
  const t = training.value;
  if (!t.plan_id || !t.plan_day_id) return;
  try {
    const session = await trainingStore.startSession(t.plan_id, t.plan_day_id, today());
    uni.navigateTo({ url: `/pages/training/execute?id=${session.id}` });
  } catch (e) {
    uni.showToast({ title: '开始训练失败', icon: 'none' });
  }
}

function continueSession() {
  if (!requireAuth({ redirect: '/pages/home/index' })) return;
  if (training.value.session_id) {
    uni.navigateTo({ url: `/pages/training/execute?id=${training.value.session_id}` });
  }
}

function goCreatePlan() {
  if (!requireAuth({ redirect: '/pages/home/index' })) return;
  uni.navigateTo({ url: '/pages/training/plan-edit' });
}

function recordWeight() {
  if (!requireAuth({ redirect: '/pages/home/index' })) return;
  uni.navigateTo({ url: '/pages/mine/account?action=weight' });
}
</script>

<style lang="scss" scoped>
.home {
  padding-bottom: calc(#{$tabbar-height} + #{$gap-4} + #{$gap-2});
  animation: lg-fade-up 0.4s $ease-spring both;
}

// ----- Hero -----
.hero-section {
  position: relative;
  padding: $gap-3 $gap-3 $gap-4;
  background: linear-gradient(160deg, rgba(166, 227, 197, 0.5) 0%, rgba(91, 200, 154, 0.2) 100%);
  border-radius: 0 0 40rpx 40rpx;
  margin-bottom: $gap-3;
  overflow: hidden;
}

// 环境光斑（hero 左上 + 右下）
.hero-section::before {
  content: '';
  position: absolute;
  top: -100rpx;
  left: -60rpx;
  width: 320rpx;
  height: 320rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.45) 0%, transparent 70%);
  pointer-events: none;
}

.hero-section::after {
  content: '';
  position: absolute;
  bottom: -80rpx;
  right: -60rpx;
  width: 280rpx;
  height: 280rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 215, 154, 0.35) 0%, transparent 70%);
  pointer-events: none;
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-3;
  position: relative;
  z-index: 1;
}

.greet .hi {
  font-size: $fs-xl;
  font-weight: 700;
  color: $primary-deep;
  letter-spacing: 0.5rpx;
}

.greet .date {
  margin-top: 4rpx;
  font-size: $fs-sm;
  color: $text-2;
  opacity: 0.85;
}

.avatar-wrap {
  padding: 6rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  box-shadow:
    inset 0 1rpx 0 rgba(255, 255, 255, 0.7),
    0 4rpx 12rpx rgba(95, 175, 145, 0.15);
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32rpx;
  font-weight: 700;
  overflow: hidden;
  transition: transform 0.3s $ease-spring;
}

.avatar:active {
  transform: scale(0.94);
}

.avatar-img {
  width: 100%;
  height: 100%;
}

// ----- Ring Panel -----
.ring-panel {
  padding: $gap-3;
  position: relative;
  z-index: 1;
}

.ring-row {
  display: flex;
  align-items: center;
  gap: $gap-3;
}

.ring-wrap {
  flex-shrink: 0;
}

.ring-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ring-num {
  font-size: 56rpx;
  font-weight: 800;
  color: $text-1;
  line-height: 1;
  letter-spacing: -1rpx;
}

.ring-label {
  margin-top: 8rpx;
  font-size: $fs-xs;
  color: $text-3;
}

.ring-goal {
  margin-top: 2rpx;
  font-size: $fs-xs;
  color: $primary;
  font-weight: 600;
}

.ring-macros {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}

// ----- Container -----
.container {
  padding: 0 $gap-3;
}

// ----- Cards (复用 lg-card 外壳，仅控制内部细节) -----
.card-section {
  padding: $gap-3;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-2;
}

.section-head .left {
  display: flex;
  align-items: center;
  gap: $gap-1;
}

.section-head .bar {
  width: 6rpx;
  height: 28rpx;
  background: $gradient-primary;
  border-radius: $r-pill;
  box-shadow: 0 2rpx 6rpx rgba(95, 175, 145, 0.3);
}

.section-head .title {
  font-size: $fs-lg;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.3rpx;
}

.section-head .more {
  font-size: $fs-sm;
  color: $text-3;
}

.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $gap-3 0;
  text-align: center;
  &.mini { padding: $gap-2 0; }
}

.empty-card .emoji {
  margin: 0 auto $gap-1;
}

.empty-card .empty-title {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 600;
}

.empty-card .empty-desc {
  font-size: $fs-sm;
  color: $text-3;
  margin-top: 4rpx;
  margin-bottom: $gap-2;
}

.training-info {
  display: flex;
  flex-direction: column;
  gap: $gap-1;
}

.training-name {
  font-size: $fs-xl;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.3rpx;
}

.training-meta {
  font-size: $fs-sm;
  color: $text-3;
}

.training-actions {
  margin-top: $gap-2;
}

// ----- Weight -----
.weight-info {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}

.weight-numbers {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: $gap-2 0;
}

.weight-current, .weight-target {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.weight-current .num, .weight-target .num {
  font-size: 60rpx;
  font-weight: 800;
  color: $text-1;
  line-height: 1;
  letter-spacing: -1rpx;
}

.weight-target .num { color: $primary; }

.weight-current .unit, .weight-target .unit {
  margin-top: 4rpx;
  font-size: $fs-xs;
  color: $text-3;
}

.weight-arrow {
  font-size: 36rpx;
  color: $text-3;
  font-weight: 300;
}

.weight-diff {
  text-align: center;
  font-size: $fs-md;
  font-weight: 600;
  color: $text-2;
  padding: 12rpx 0;
  background: rgba(234, 248, 241, 0.6);
  border-radius: $r-pill;
  backdrop-filter: blur(8rpx);
  &.pos { color: #B86A1F; background: rgba(255, 238, 217, 0.7); }
  &.neg { color: $primary-deep; background: rgba(234, 248, 241, 0.7); }
}

.weight-actions {
  display: flex;
  justify-content: center;
}

.weight-foot {
  font-size: $fs-xs;
  color: $text-3;
  text-align: center;
}
</style>