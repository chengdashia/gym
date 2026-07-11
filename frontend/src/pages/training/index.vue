<template>
  <view class="training-page">
    <view class="training-hero">
      <view class="hero-copy">
        <text class="eyebrow">{{ dateLabel }}</text>
        <text class="hero-title">{{ title }}</text>
        <text class="hero-sub">{{ subtitle }}</text>
      </view>
      <line-icon name="dumbbell" color="#3FA67C" :stroke-width="1.8" :size="72" />
    </view>

    <view class="quick-row">
      <view class="quick-action" @tap="goHistory"><line-icon name="history" color="#8FA3A1" :size="38" /><text>训练历史</text></view>
      <view class="quick-action" @tap="managePlans"><line-icon name="settings" color="#8FA3A1" :size="38" /><text>管理计划</text></view>
    </view>

    <view v-if="loading" class="state-copy">正在准备今天的训练...</view>

    <template v-else-if="todayInfo?.has_plan">
      <liquid-glass-card class="today-card" :highlight="true" custom-style="margin-bottom:0">
        <view class="today-head">
          <view>
            <view class="today-name">{{ todayInfo.title || '今日训练' }}</view>
            <view class="today-meta">{{ todayExercises.length }} 个动作 · {{ totalSets }} 组</view>
          </view>
          <liquid-glass-pill :text="statusText" :variant="statusVariant" size="xs" />
        </view>

        <view v-if="todayInfo.is_rest_day" class="rest-state">
          <line-icon name="moon" color="#8FA3A1" :size="68" />
          <text>今天是休息日，恢复也是训练的一部分</text>
        </view>

        <view v-else class="exercise-list">
          <view v-for="(exercise, index) in todayExercises" :key="`${exercise.exercise_name_snapshot}-${index}`" :class="['exercise-row', progressFor(index)]">
            <view class="exercise-index">{{ progressIcon(index) }}</view>
            <view class="exercise-main">
              <view class="exercise-name">{{ exercise.exercise_name_snapshot }}</view>
              <view class="exercise-part">{{ exercise.body_part_snapshot || '未分类' }}</view>
            </view>
            <view class="exercise-target">
              <view>{{ exercise.target_sets }} 组 × {{ exercise.target_reps }} 次</view>
              <view class="exercise-detail">{{ progressLabel(index) }} · {{ targetDetail(exercise) }}</view>
            </view>
          </view>
        </view>

        <view v-if="!todayInfo.is_rest_day" class="primary-action">
          <liquid-glass-button
            :text="sessionHasProgress ? '继续训练' : (todayInfo.today_completed ? '再练一次' : '开始今日训练')"
            :variant="todayInfo.today_completed ? 'soft' : 'primary'"
            size="lg"
            @tap="sessionHasProgress ? continueSession() : startSession()"
          />
        </view>
        <view v-if="todayInfo.previous_session" class="carryover" @tap="goHistory">
          昨天的「{{ todayInfo.previous_session.session_name }}」{{ todayInfo.previous_session.status === 'partial' ? '未完成，可从历史补练' : '未训练，可从历史补练' }} ›
        </view>
      </liquid-glass-card>
    </template>

    <template v-else>
      <view class="empty-intro">
        <view class="empty-title">先选一个适合你的训练模板</view>
        <view class="empty-sub">选择后会自动生成计划，下一步即可开始训练</view>
      </view>
      <view class="template-list">
        <liquid-glass-card
          v-for="tpl in templates.slice(0, 3)"
          :key="tpl.id"
          hoverable
          class="template-card"
          @tap="useTemplate(tpl)"
        >
          <view class="template-main">
            <view class="template-name">{{ tpl.name }}</view>
            <view class="template-desc">{{ tpl.description || `${tpl.days.length} 个训练日` }}</view>
            <view class="template-tags"><text>{{ tpl.difficulty || '通用' }}</text><text>{{ tpl.days.length }} 日计划</text></view>
          </view>
          <view class="template-use">使用 ›</view>
        </liquid-glass-card>
      </view>
      <view class="custom-plan tap-spring" @tap="goCreatePlan">自定义训练计划</view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useTrainingStore } from '@/store/training';
import { useAuthStore } from '@/store/auth';
import { trainingApi, type PlanExercise, type TrainingTemplate } from '@/api/training';
import { dateMD, today, weekdayCN } from '@/utils/date';
import { requireAuth } from '@/utils/auth-guard';
import { exerciseProgress } from '@/utils/training-progress';

const trainingStore = useTrainingStore();
const auth = useAuthStore();
const loading = ref(false);
const templates = ref<TrainingTemplate[]>([]);

const todayInfo = computed(() => trainingStore.today);
const activePlan = computed(() => trainingStore.activePlan);
const todayExercises = computed(() => todayInfo.value?.today_day?.exercises || []);
const totalSets = computed(() => todayExercises.value.reduce((sum, item) => sum + Number(item.target_sets || 0), 0));
const sessionHasProgress = computed(() => Boolean(todayInfo.value?.session_id && todayInfo.value.incomplete_session?.exercises?.some(exercise => exercise.completed_sets > 0 || exercise.sets.some(set => set.completed))));
const dateLabel = `${dateMD(today())} ${weekdayCN(today())}`;
const title = computed(() => {
  if (!todayInfo.value?.has_plan) return '今天练什么？';
  if (todayInfo.value.is_rest_day) return '今天好好恢复';
  if (sessionHasProgress.value) return '继续完成今天的训练';
  if (todayInfo.value.today_completed) return '今天已经完成';
  return todayInfo.value.title || '今日训练';
});
const subtitle = computed(() => {
  if (!todayInfo.value?.has_plan) return '选择模板，马上建立你的训练节奏';
  if (todayInfo.value.is_rest_day) return '休息、拉伸，准备下一次训练';
  if (todayInfo.value?.previous_session) return `昨天有未完成记录，今天仍按计划训练`;
  return `${todayExercises.value.length} 个动作已经为你准备好`;
});
const statusText = computed(() => sessionHasProgress.value ? '进行中' : todayInfo.value?.today_completed ? '已完成' : todayInfo.value?.is_rest_day ? '休息日' : '待开始');
const statusVariant = computed<'primary' | 'soft' | 'default'>(() => sessionHasProgress.value ? 'primary' : 'soft');

function syncTabBar() {
  const pages = getCurrentPages();
  const tabBar = (pages[pages.length - 1] as any)?.getTabBar?.();
  if (tabBar) tabBar.setData({ activeIdx: 2 });
}

async function load() {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  loading.value = true;
  try {
    await Promise.all([trainingStore.fetchPlans(), trainingStore.fetchToday(today())]);
    if (!trainingStore.today?.has_plan) {
      const result = await trainingApi.getTemplates();
      templates.value = result.items || [];
    }
  } catch (e: any) {
    uni.showToast({ title: e?.message || '训练内容加载失败', icon: 'none' });
  } finally {
    loading.value = false;
  }
}

function targetDetail(exercise: PlanExercise) {
  const weight = Number(exercise.target_weight_kg || 0);
  return `${weight > 0 ? `${weight} kg` : '自重'} · 休息 ${exercise.rest_seconds}s`;
}

function sessionExercise(index: number) {
  return todayInfo.value?.incomplete_session?.exercises?.[index];
}
function progressFor(index: number) { return exerciseProgress(sessionExercise(index)); }
function progressIcon(index: number) {
  const progress = progressFor(index);
  return progress === 'completed' ? '✓' : progress === 'in_progress' ? '◐' : index + 1;
}
function progressLabel(index: number) {
  const exercise = sessionExercise(index);
  const progress = exerciseProgress(exercise);
  if (progress === 'completed') return '已完成';
  if (progress === 'in_progress') return `${exercise?.completed_sets || 0}/${exercise?.planned_sets || 0} 组完成`;
  return '未开始';
}

async function startSession() {
  if (!requireAuth({ redirect: '/pages/training/index' })) return;
  const info = todayInfo.value;
  if (!info?.plan_id || !info.plan_day_id) return;
  try {
    const session = await trainingStore.startSession(info.plan_id, info.plan_day_id, today());
    uni.navigateTo({ url: `/pages/training/execute?id=${session.id}` });
  } catch (e: any) {
    uni.showToast({ title: e?.message || '开始训练失败', icon: 'none' });
  }
}

function continueSession() {
  if (todayInfo.value?.session_id) uni.navigateTo({ url: `/pages/training/execute?id=${todayInfo.value.session_id}` });
}

async function useTemplate(tpl: TrainingTemplate) {
  if (!requireAuth({ redirect: '/pages/training/index' })) return;
  uni.showLoading({ title: '正在创建计划' });
  try {
    const plan = await trainingApi.createPlan({
      name: tpl.name,
      schedule_type: 'sequence',
      source_template_id: tpl.id,
      days: tpl.days.map((day, dayIndex) => ({
        day_index: day.day_index,
        day_name: day.day_name,
        is_rest_day: day.is_rest_day,
        weekday: day.weekday,
        sort_order: dayIndex,
        exercises: day.exercises.map((exercise, index) => ({ ...exercise, sort_order: index })),
      })),
    });
    await trainingApi.setActive(plan.id);
    await load();
    uni.showToast({ title: '计划已启用', icon: 'success' });
  } catch (e: any) {
    uni.showToast({ title: e?.message || '创建失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}

function goHistory() { uni.navigateTo({ url: '/pages/training/history' }); }
function goCreatePlan() { uni.navigateTo({ url: '/pages/training/plan-edit' }); }
function managePlans() {
  const items = activePlan.value ? ['编辑当前计划', '创建新计划'] : ['创建训练计划'];
  uni.showActionSheet({ itemList: items, success: ({ tapIndex }) => {
    if (activePlan.value && tapIndex === 0) uni.navigateTo({ url: `/pages/training/plan-edit?id=${activePlan.value.id}` });
    else goCreatePlan();
  }});
}

onMounted(load);
onShow(() => { syncTabBar(); if (auth.isLogged) load(); });
</script>

<style lang="scss" scoped>
.training-page { padding: $gap-3; padding-bottom: calc(#{$tabbar-height} + #{$gap-5}); }
.training-hero { display: flex; align-items: center; justify-content: space-between; padding: $gap-3 4rpx $gap-4; }
.hero-copy { display: flex; flex-direction: column; }
.eyebrow { color: $text-3; font-size: $fs-sm; }
.hero-title { margin-top: 8rpx; color: $text-1; font-size: 48rpx; line-height: 1.2; font-weight: 800; }
.hero-sub { margin-top: 8rpx; color: $text-2; font-size: $fs-sm; }
.quick-row { display: flex; gap: $gap-2; margin-bottom: $gap-3; }
.quick-action { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8rpx; height: 72rpx; border-radius: $r-pill; background: rgba(255,255,255,.72); color: $text-2; font-size: $fs-sm; box-shadow: $shadow-glass-sm; }
.state-copy { text-align: center; padding: $gap-5; color: $text-3; }
.today-card { padding: $gap-3; }
.today-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: $gap-2; }
.today-name { color: $text-1; font-size: $fs-xl; font-weight: 750; }
.today-meta { margin-top: 4rpx; color: $text-3; font-size: $fs-sm; }
.exercise-row { display: flex; align-items: center; gap: $gap-2; padding: 22rpx 0; border-top: 1rpx solid $divider; }
.exercise-row.in_progress { margin: 4rpx -12rpx; padding: 20rpx 12rpx; border-radius: $r-12; background: rgba(91,200,154,.12); }
.carryover{margin-top:20rpx;padding:18rpx 20rpx;border-radius:16rpx;background:rgba(255,183,77,.14);color:#8a5a00;font-size:25rpx;}
.exercise-row.completed { margin: 4rpx -12rpx; padding: 20rpx 12rpx; border-radius: $r-12; background: rgba(91,200,154,.2); }
.exercise-row.completed .exercise-name, .exercise-row.completed .exercise-detail { color: $primary-deep; }
.exercise-index { width: 44rpx; height: 44rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: $primary-tint; color: $primary-deep; font-weight: 700; }
.exercise-row.completed .exercise-index { background: $primary; color: #fff; }
.exercise-row.in_progress .exercise-index { background: rgba(91, 200, 154, .22); color: $primary-deep; }
.exercise-main { flex: 1; min-width: 0; }
.exercise-name { color: $text-1; font-size: $fs-md; font-weight: 650; }
.exercise-part, .exercise-detail { color: $text-3; font-size: $fs-xs; }
.exercise-target { text-align: right; color: $text-1; font-size: $fs-sm; }
.primary-action { margin-top: $gap-3; }
.rest-state { display: flex; flex-direction: column; align-items: center; gap: $gap-2; padding: $gap-5 0; color: $text-2; }
.empty-intro { margin: $gap-2 0 $gap-3; }
.empty-title { font-size: $fs-xl; color: $text-1; font-weight: 750; }
.empty-sub { margin-top: 6rpx; color: $text-3; font-size: $fs-sm; }
.template-card { display: flex; align-items: center; margin-bottom: $gap-2; }
.template-main { flex: 1; min-width: 0; }
.template-name { color: $text-1; font-size: $fs-lg; font-weight: 700; }
.template-desc { margin-top: 4rpx; color: $text-3; font-size: $fs-sm; }
.template-tags { display: flex; gap: 8rpx; margin-top: 12rpx; }
.template-tags text { padding: 4rpx 12rpx; border-radius: $r-pill; color: $primary-deep; background: $primary-tint; font-size: $fs-xs; }
.template-use { color: $primary-deep; font-size: $fs-sm; font-weight: 650; }
.custom-plan { text-align: center; padding: $gap-3; color: $primary-deep; font-weight: 650; }
</style>
