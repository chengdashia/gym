<template>
  <view class="home">
    <view class="hero">
      <view class="hero-top">
        <view class="greet">
          <view class="hi">{{ greetText }}，{{ nickname }}</view>
          <view class="date">{{ dateText }}</view>
        </view>
        <view class="avatar" @tap="goMine">
          <text v-if="!avatar">{{ initial }}</text>
          <image v-else :src="avatar" mode="aspectFill" class="avatar-img" />
        </view>
      </view>

      <view class="ring-card">
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

        <view class="ring-macros">
          <MacroBar label="碳水" :value="diet.carbs_g" :goal="diet.carbs_goal" color="#FFD79A" />
          <MacroBar label="蛋白质" :value="diet.protein_g" :goal="diet.protein_goal" color="#5BC89A" />
          <MacroBar label="脂肪" :value="diet.fat_g" :goal="diet.fat_goal" color="#C490E0" />
        </view>
      </view>
    </view>

    <view class="container">
      <!-- 训练卡 -->
      <view class="card-section" @tap="goTraining">
        <view class="section-head">
          <view class="left">
            <view class="bar" />
            <text class="title">今日训练</text>
            <Tag v-if="training.status === 'in_progress'" text="进行中" variant="primary" />
            <Tag v-else-if="training.is_rest_day" text="休息日" variant="soft" />
          </view>
          <text class="more">查看 ›</text>
        </view>

        <view v-if="training.status === 'no_plan'" class="empty-card">
          <view class="emoji">🏋️</view>
          <view class="empty-title">还没有训练计划</view>
          <view class="empty-desc">选择一个模板或自定义创建你的第一个计划</view>
          <view class="action-btn" @tap.stop="goCreatePlan">创建训练计划</view>
        </view>

        <view v-else class="training-info">
          <view class="training-name">{{ training.title || '今日休息' }}</view>
          <view class="training-meta">
            <text>共 {{ training.exercise_count }} 个动作</text>
          </view>
          <view class="training-actions">
            <view v-if="training.status === 'in_progress'" class="primary-btn" @tap.stop="continueSession">
              继续训练
            </view>
            <view v-else-if="!training.is_rest_day" class="primary-btn" @tap.stop="startSession">
              开始训练
            </view>
            <view v-else class="ghost-btn">好好休息 💤</view>
          </view>
        </view>
      </view>

      <!-- 体重卡 -->
      <view class="card-section">
        <view class="section-head">
          <view class="left">
            <view class="bar" />
            <text class="title">体重目标</text>
          </view>
          <text class="more" @tap.stop="goStats">趋势 ›</text>
        </view>

        <view v-if="!weight.current_weight_kg" class="empty-card mini">
          <view class="emoji">⚖️</view>
          <view class="empty-title">还没有体重记录</view>
          <view class="empty-desc">记录第一次体重，开始追踪变化</view>
          <view class="action-btn" @tap="recordWeight">记录体重</view>
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
          <view class="weight-diff" :class="{ pos: (weight.diff_kg || 0) > 0, neg: (weight.diff_kg || 0) < 0 }">
            <text v-if="weight.diff_kg && weight.diff_kg > 0">还需减 {{ weight.diff_kg }} kg</text>
            <text v-else-if="weight.diff_kg && weight.diff_kg < 0">还需增 {{ -weight.diff_kg }} kg</text>
            <text v-else>已达成目标 🎉</text>
          </view>
          <view class="weight-actions">
            <view class="ghost-btn small" @tap="recordWeight">记录体重</view>
          </view>
          <view v-if="weight.last_recorded_at" class="weight-foot">最近记录：{{ formatDateTime(weight.last_recorded_at) }}</view>
        </view>
      </view>

      <!-- 快捷入口 -->
      <view class="quick-grid">
        <view class="quick-item" @tap="goAddDiet">
          <view class="qi-icon" style="background: #EAF8F1; color: #3FA67C;">🥗</view>
          <view class="qi-label">添加饮食</view>
        </view>
        <view class="quick-item" @tap="goPhoto">
          <view class="qi-icon" style="background: #FFF3DC; color: #B86A1F;">📷</view>
          <view class="qi-label">拍照识别</view>
        </view>
        <view class="quick-item" @tap="goTraining">
          <view class="qi-icon" style="background: #E0F0FA; color: #2F6DA0;">🏋️</view>
          <view class="qi-label">训练计划</view>
        </view>
        <view class="quick-item" @tap="goStats">
          <view class="qi-icon" style="background: #F1E6F8; color: #7E45A6;">📊</view>
          <view class="qi-label">数据趋势</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { homeApi, HomeSummary } from '@/api/home';
import { useUserStore } from '@/store/user';
import { useTrainingStore } from '@/store/training';
import ProgressRing from '@/components/ProgressRing.vue';
import MacroBar from '@/components/MacroBar.vue';
import Tag from '@/components/Tag.vue';
import { today, weekdayCN, dateMD, formatDateTime } from '@/utils/date';

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
  fat_g: 0, fat_g: 0 as any, fat_goal: 0,
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
  if (!userStore.me) await userStore.fetchMe().catch(() => {});
  if (!userStore.goal?.calories_kcal) await userStore.fetchGoal().catch(() => {});
  await load();
});

onShow(() => {
  if (userStore.me) load();
});

function goMine() { uni.switchTab({ url: '/pages/mine/index' }); }
function goTraining() { uni.switchTab({ url: '/pages/training/index' }); }
function goStats() { uni.switchTab({ url: '/pages/stats/index' }); }
function goAddDiet() { uni.switchTab({ url: '/pages/diet/index' }); }
function goPhoto() { uni.navigateTo({ url: '/pages/diet/photo-recognize' }); }
function goCreatePlan() { uni.navigateTo({ url: '/pages/training/plan-edit' }); }

async function startSession() {
  const t = training.value;
  if (!t.plan_id || !t.plan_day_id) return;
  try {
    const session = await trainingStore.startSession(t.plan_id, t.plan_day_id, today());
    uni.navigateTo({ url: `/pages/training/execute?id=${session.id}` });
  } catch (e) {}
}

function continueSession() {
  if (training.value.session_id) {
    uni.navigateTo({ url: `/pages/training/execute?id=${training.value.session_id}` });
  }
}

function recordWeight() {
  uni.navigateTo({ url: '/pages/mine/account?action=weight' });
}
</script>

<style lang="scss" scoped>
.home {
  min-height: 100vh;
  background: $bg;
}

.hero {
  background: $gradient-hero;
  padding: $gap-3 $gap-3 $gap-5;
  border-radius: 0 0 $r-24 $r-24;
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-3;
}
.greet .hi {
  font-size: $fs-xl;
  font-weight: 600;
  color: #fff;
}
.greet .date {
  margin-top: 4rpx;
  font-size: $fs-sm;
  color: rgba(255, 255, 255, 0.85);
}
.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  overflow: hidden;
}
.avatar-img {
  width: 100%;
  height: 100%;
}

.ring-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: $r-24;
  padding: $gap-3;
  display: flex;
  align-items: center;
  gap: $gap-3;
  box-shadow: $shadow-lg;
}
.ring-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.ring-num {
  font-size: 56rpx;
  font-weight: 700;
  color: $text-1;
  line-height: 1;
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
  font-weight: 500;
}

.ring-macros {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}

.container {
  padding: $gap-3;
  padding-bottom: calc(#{$tabbar-height} + #{$gap-4});
}

.card-section {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  margin-bottom: $gap-3;
  box-shadow: $shadow-sm;
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
  background: $primary;
  border-radius: $r-pill;
}
.section-head .title {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
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
  font-size: 64rpx;
  margin-bottom: $gap-1;
}
.empty-card .empty-title {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;
}
.empty-card .empty-desc {
  font-size: $fs-sm;
  color: $text-3;
  margin-top: 4rpx;
}
.action-btn {
  margin-top: $gap-2;
  padding: 14rpx 36rpx;
  background: $primary;
  color: #fff;
  border-radius: $r-pill;
  font-size: $fs-sm;
  font-weight: 500;
}

.training-info {
  display: flex;
  flex-direction: column;
  gap: $gap-1;
}
.training-name {
  font-size: $fs-xl;
  font-weight: 600;
  color: $text-1;
}
.training-meta {
  font-size: $fs-sm;
  color: $text-3;
}
.training-actions {
  margin-top: $gap-2;
}
.primary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 18rpx 40rpx;
  background: $primary;
  color: #fff;
  border-radius: $r-pill;
  font-size: $fs-md;
  font-weight: 500;
}
.ghost-btn {
  display: inline-flex;
  padding: 18rpx 32rpx;
  background: $bg-2;
  color: $text-2;
  border-radius: $r-pill;
  font-size: $fs-md;
  &.small {
    padding: 12rpx 24rpx;
    font-size: $fs-sm;
  }
}

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
  font-weight: 700;
  color: $text-1;
  line-height: 1;
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
}
.weight-diff {
  text-align: center;
  font-size: $fs-md;
  font-weight: 500;
  color: $text-2;
  padding: 8rpx 0;
  background: $primary-tint;
  border-radius: $r-pill;
  &.pos { color: #B86A1F; background: #FFEED9; }
  &.neg { color: $primary-deep; }
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

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $gap-2;
  margin-top: $gap-2;
}
.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $gap-2 0;
  background: $card;
  border-radius: $r-16;
  box-shadow: $shadow-sm;
}
.qi-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: $r-20;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  margin-bottom: 8rpx;
}
.qi-label {
  font-size: $fs-xs;
  color: $text-2;
}
</style>