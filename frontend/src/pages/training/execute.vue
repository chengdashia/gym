<template>
  <view v-if="loading" class="loading">加载中...</view>
  <view v-else-if="session" class="execute-page">
    <!-- 顶部：进度 + 退出 -->
    <liquid-glass-panel variant="light" :highlight="true" :ambient="true" class="hero-panel">
      <view class="head">
        <view class="head-info">
          <view class="title">{{ session.session_name }}</view>
          <view class="meta">
            {{ formatDateTime(session.started_at) }} · {{ statusText }}
          </view>
        </view>
        <view class="head-actions">
          <liquid-glass-button text="退出" variant="ghost" size="sm" :block="false" @tap="confirmQuit" />
        </view>
      </view>

      <!-- 进度条 -->
      <view class="progress-bar">
        <view class="bar-info">
          <text>{{ completedSets }} / {{ totalSets }} 组完成</text>
          <text>动作 {{ currentExIdx + 1 }} / {{ session.exercises?.length || 0 }}</text>
        </view>
        <view class="bar-track">
          <view class="bar-fill" :style="{ width: progressPct + '%' }" />
        </view>
      </view>
    </liquid-glass-panel>

    <!-- 引导式训练：当前动作 -->
    <view v-if="currentEx" class="current-area">
      <liquid-glass-card variant="light" :highlight="true" class="current-card">
        <view class="current-head">
          <view class="current-idx">动作 {{ currentExIdx + 1 }}</view>
          <view v-if="isCurrentDone" class="done-tag">已完成 ✓</view>
        </view>
        <view class="current-name">{{ currentEx.exercise_name_snapshot }}</view>
        <view v-if="currentEx.body_part_snapshot" class="current-meta">部位：{{ currentEx.body_part_snapshot }}</view>
        <view class="current-meta">目标 {{ currentEx.planned_sets }} 组 · 组间休息 {{ currentEx.rest_seconds }}s</view>

        <!-- 组列表 -->
        <view class="set-list">
          <view class="set-head">
            <text class="set-h">#</text>
            <text class="set-h">目标 (次/kg)</text>
            <text class="set-h">实际 (次/kg)</text>
            <text class="set-h">完成</text>
          </view>
          <view
            v-for="(s, si) in currentEx.sets"
            :key="si"
            :class="['set-row', { done: s.completed }]"
          >
            <text class="set-idx">{{ si + 1 }}</text>
            <view class="target-cell">
              <text>{{ s.target_reps || '-' }} × {{ s.target_weight_kg || '-' }}</text>
            </view>
            <view class="actual-cell">
              <input
                v-model.number="s.actual_reps"
                type="number"
                class="set-input"
                placeholder="次"
              />
              <text class="set-x">×</text>
              <input
                v-model.number="s.actual_weight_kg"
                type="digit"
                class="set-input"
                placeholder="kg"
              />
            </view>
            <view class="done-cell">
              <view :class="['check-btn', { done: s.completed }]" @tap="toggleSet(si)">
                {{ s.completed ? '✓' : '' }}
              </view>
            </view>
          </view>
        </view>
      </liquid-glass-card>

      <!-- 当前动作操作 -->
      <view class="current-actions">
        <view v-if="!isCurrentDone" class="hint">可按任意顺序勾选组数</view>
        <liquid-glass-button v-if="hasNextEx" text="下一个动作 →" variant="ghost" size="sm" :block="false" @tap="nextExercise" />
        <liquid-glass-button v-if="allDone" :text="finishing ? '提交中...' : '完成训练'" variant="primary" :disabled="finishing" @tap="finishSession" />
      </view>
    </view>

    <!-- 全部动作概览（可折叠） -->
    <liquid-glass-card variant="light" :highlight="true" class="overview-card">
      <view class="overview-head" @tap="showOverview = !showOverview">
        <text>全部动作（{{ session.exercises?.length || 0 }}）</text>
        <text class="overview-toggle">{{ showOverview ? '收起 ▲' : '展开 ▼' }}</text>
      </view>
      <view v-if="showOverview" class="overview-list">
        <view
          v-for="(ex, ei) in session.exercises || []"
          :key="ei"
          :class="['overview-item', { current: ei === currentExIdx, done: isExerciseDone(ei) }]"
          @tap="jumpTo(ei)"
        >
          <view class="ov-idx">{{ ei + 1 }}</view>
          <view class="ov-info">
            <view class="ov-name">{{ ex.exercise_name_snapshot }}</view>
            <view class="ov-meta">{{ ex.completed_sets }}/{{ ex.planned_sets }} 组</view>
          </view>
          <view v-if="ei === currentExIdx" class="ov-tag">当前</view>
          <view v-else-if="isExerciseDone(ei)" class="ov-tag done">✓</view>
        </view>
      </view>
    </liquid-glass-card>

    <!-- 组间歇倒计时 -->
    <RestTimer
      :visible="timer.visible"
      :remaining="timer.remaining"
      :total="timer.total"
      :running="timer.running"
      @toggle="timerToggle"
      @skip="timerSkip"
      @adjust="timerAdjust"
      @close="timerClose"
    />

    <!-- 退出确认 -->
    <ModalConfirm
      :visible="showQuit"
      title="退出训练"
      message="选择如何处理当前训练？"
      cancel-text="继续训练"
      confirm-text="保存进度"
      @confirm="saveProgress"
      @cancel="closeExitModal"
    />

    <ModalConfirm
      :visible="showAbandon"
      title="放弃训练"
      message="放弃后本次记录将被标记为已放弃，是否确认？"
      cancel-text="返回"
      confirm-text="放弃"
      danger
      @confirm="abandonSession"
      @cancel="showAbandon = false"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue';
import { useTrainingStore } from '@/store/training';
import { useAuthStore } from '@/store/auth';
import { trainingApi, TrainingSession } from '@/api/training';
import { createTimer } from '@/utils/timer';
import { formatDateTime } from '@/utils/date';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';
import RestTimer from '@/components/RestTimer.vue';
import ModalConfirm from '@/components/ModalConfirm.vue';

const id = ref(0);
const session = ref<TrainingSession | null>(null);
const loading = ref(true);
const trainingStore = useTrainingStore();
const auth = useAuthStore();
const showQuit = ref(false);
const showAbandon = ref(false);
const saving = ref(false);
const finishing = ref(false);
const currentExIdx = ref(0);
const showOverview = ref(false);

const timer = reactive({
  visible: false,
  remaining: 0,
  total: 0,
  running: true,
});

let timerInstance = createTimer(
  (remaining, total) => {
    timer.remaining = remaining;
    timer.total = total;
    if (remaining === 0) {
      timer.visible = false;
    }
  },
  () => {
    timer.visible = false;
    uni.vibrateShort({ type: 'medium' });
  },
);

let persistTimer: ReturnType<typeof setTimeout> | null = null;

const currentEx = computed(() => session.value?.exercises?.[currentExIdx.value] || null);

const isCurrentDone = computed(() => {
  const ex = currentEx.value;
  if (!ex || !ex.sets?.length) return false;
  return ex.sets.every((s) => s.completed);
});

const hasNextEx = computed(() => {
  const total = session.value?.exercises?.length || 0;
  return currentExIdx.value < total - 1;
});

// 所有动作的所有组是否全部完成，作为允许结束训练的条件
const allDone = computed(() => {
  const exs = session.value?.exercises;
  if (!exs || !exs.length) return false;
  return exs.every((e) => e.sets.length > 0 && e.sets.every((s) => s.completed));
});

const completedSets = computed(() => {
  if (!session.value?.exercises) return 0;
  return session.value.exercises.reduce((s, e) => s + e.sets.filter((x) => x.completed).length, 0);
});

const totalSets = computed(() => {
  if (!session.value?.exercises) return 0;
  return session.value.exercises.reduce((s, e) => s + e.sets.length, 0);
});

const progressPct = computed(() => {
  if (!totalSets.value) return 0;
  return Math.round((completedSets.value / totalSets.value) * 100);
});

const statusText = computed(() => {
  switch (session.value?.status) {
    case 'completed': return '已完成';
    case 'paused': return '已暂停';
    case 'cancelled': return '已放弃';
    default: return '进行中';
  }
});

onMounted(async () => {
  const pages = getCurrentPages();
  const opt = (pages[pages.length - 1] as any)?.options || {};
  id.value = Number(opt.id || 0);

  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    const redirect = id.value
      ? `/pages/training/execute?id=${id.value}`
      : '/pages/training/execute';
    requireAuth({ redirect });
    return;
  }

  await loadSession();
  // 跳到第一个未完成的动作
  jumpToFirstUndone();
});

onUnmounted(() => {
  timerInstance.stop();
  if (persistTimer) {
    clearTimeout(persistTimer);
    persistTimer = null;
  }
});

async function loadSession() {
  if (!id.value) {
    loading.value = false;
    return;
  }
  loading.value = true;
  try {
    const s = await trainingApi.getSession(id.value);
    if (!s.exercises) s.exercises = [];
    session.value = s;
  } catch (e: any) {
    uni.showToast({ title: '加载失败', icon: 'none' });
  } finally {
    loading.value = false;
  }
}

function jumpToFirstUndone() {
  const exs = session.value?.exercises;
  if (!exs || !exs.length) return;
  const idx = exs.findIndex((e) => !e.sets.every((s) => s.completed));
  currentExIdx.value = idx >= 0 ? idx : 0;
}

function isExerciseDone(ei: number) {
  const ex = session.value?.exercises?.[ei];
  if (!ex) return false;
  return ex.sets.every((s) => s.completed);
}

function sanitizeNum(v: any): number | null {
  if (v === null || v === undefined || v === '') return null;
  const n = typeof v === 'number' ? v : Number(v);
  if (!Number.isFinite(n) || n < 0) return null;
  return n;
}

function toggleSet(si: number) {
  const ex = currentEx.value;
  if (!ex) return;
  const s = ex.sets[si];
  s.completed = !s.completed;
  ex.completed_sets = ex.sets.filter((x) => x.completed).length;
  if (s.completed) {
    // 勾选完成时，若未填写实际值，自动用目标值预填，避免详情里实际数据全为空
    if (s.actual_reps == null || s.actual_reps === undefined) {
      s.actual_reps = s.target_reps ?? null;
    }
    if (s.actual_weight_kg == null || s.actual_weight_kg === undefined) {
      s.actual_weight_kg = s.target_weight_kg ?? null;
    }
    // 自动启动组间歇倒计时
    timer.total = ex.rest_seconds;
    timer.remaining = ex.rest_seconds;
    timer.running = true;
    timer.visible = true;
    timerInstance.start(ex.rest_seconds);
    // 保存进度
  }
  schedulePersist();
}

function nextExercise() {
  if (hasNextEx.value) {
    currentExIdx.value += 1;
    uni.vibrateShort({ type: 'light' });
  }
}

function jumpTo(ei: number) {
  currentExIdx.value = ei;
  showOverview.value = false;
}

function timerToggle() {
  if (timer.running) {
    timerInstance.pause();
    timer.running = false;
  } else {
    timerInstance.resume();
    timer.running = true;
  }
}

function timerSkip() {
  timerInstance.skip();
}

function timerAdjust(delta: number) {
  timerInstance.adjust(delta);
}

function timerClose() {
  timerInstance.stop();
  timer.visible = false;
}

function schedulePersist() {
  if (persistTimer) {
    clearTimeout(persistTimer);
    persistTimer = null;
  }
  persistTimer = setTimeout(() => {
    persistTimer = null;
    void persist('in_progress');
  }, 600);
}

async function persist(status: 'in_progress' | 'paused' | 'completed' | 'cancelled' = 'in_progress') {
  if (!session.value) return null;
  saving.value = true;
  try {
    const payload = {
      status,
      exercises: (session.value.exercises || []).map((ex) => ({
        session_exercise_id: (ex as any).id ?? (ex as any).session_exercise_id,
        exercise_name_snapshot: ex.exercise_name_snapshot,
        body_part_snapshot: ex.body_part_snapshot,
        sort_order: ex.sort_order,
        planned_sets: ex.planned_sets,
        completed_sets: ex.completed_sets,
        rest_seconds: ex.rest_seconds,
        sets: (ex.sets || []).map((s) => ({
          set_id: (s as any).id ?? s.set_id,
          set_index: s.set_index,
          actual_reps: sanitizeNum(s.actual_reps),
          actual_weight_kg: sanitizeNum(s.actual_weight_kg),
          completed: !!s.completed,
        })),
      })),
    };
    const updated = await trainingApi.updateSession(session.value.id, payload);
    session.value = updated;
    return updated;
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
    return null;
  } finally {
    saving.value = false;
  }
}

async function saveProgress() {
  if (!session.value) return;
  if (persistTimer) {
    clearTimeout(persistTimer);
    persistTimer = null;
  }
  try {
    const payload = (session.value.exercises || []).map((ex) => ({
      session_exercise_id: (ex as any).id ?? (ex as any).session_exercise_id,
      exercise_name_snapshot: ex.exercise_name_snapshot,
      body_part_snapshot: ex.body_part_snapshot,
      sort_order: ex.sort_order,
      planned_sets: ex.planned_sets,
      completed_sets: ex.completed_sets,
      rest_seconds: ex.rest_seconds,
      sets: (ex.sets || []).map((s) => ({
        set_id: (s as any).id ?? s.set_id,
        set_index: s.set_index,
        actual_reps: sanitizeNum(s.actual_reps),
        actual_weight_kg: sanitizeNum(s.actual_weight_kg),
        completed: !!s.completed,
      })),
    }));
    await trainingApi.updateSession(session.value.id, { status: 'paused', exercises: payload });
    uni.showToast({ title: '已保存进度', icon: 'success' });
    showQuit.value = false;
    setTimeout(() => safeNavigateBack('/pages/training/index'), 800);
  } catch (e) {
    uni.showToast({ title: '保存失败', icon: 'none' });
  }
}

async function finishSession() {
  if (!session.value) return;
  if (finishing.value) return;
  finishing.value = true;
  if (persistTimer) {
    clearTimeout(persistTimer);
    persistTimer = null;
  }
  const res = await persist('in_progress');
  if (!res) {
    finishing.value = false;
    return;
  }
  try {
    const finished = await trainingApi.finishSession(session.value!.id);
    session.value = finished;
    uni.showToast({ title: '训练完成', icon: 'success' });
    setTimeout(() => safeNavigateBack('/pages/training/index'), 800);
  } catch (e: any) {
    // 训练已结束（重复点击等场景）时，直接返回，避免报错
    if (e?.code === 40901 || (e?.message || '').includes('已结束')) {
      uni.showToast({ title: '训练已完成', icon: 'success' });
      setTimeout(() => safeNavigateBack('/pages/training/index'), 600);
    } else {
      uni.showToast({ title: e?.message || '完成失败', icon: 'none' });
    }
  } finally {
    finishing.value = false;
  }
}

function confirmQuit() {
  uni.showActionSheet({
    itemList: ['保存进度并退出', '将本次标记为完成', '放弃本次训练'],
    success: ({ tapIndex }) => {
      if (tapIndex === 0) saveProgress();
      if (tapIndex === 1) finishSession();
      if (tapIndex === 2) showAbandon.value = true;
    },
  });
}

function closeExitModal() {
  showQuit.value = false;
}

async function abandonSession() {
  if (!session.value) return;
  showAbandon.value = false;
  try {
    await trainingApi.cancelSession(session.value!.id);
    safeNavigateBack('/pages/training/index');
  } catch (e) {
    uni.showToast({ title: '操作失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.execute-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
  padding-bottom: calc(#{$gap-3} + env(safe-area-inset-bottom));
}

.loading {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg;
  color: $text-3;
  font-size: $fs-md;
}

// ----- 顶部 Hero Panel -----
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-3;
}
.head-info {
  flex: 1;
  min-width: 0;
}
.title {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-1;
}
.meta {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
}

.bar-info {
  display: flex;
  justify-content: space-between;
  font-size: $fs-sm;
  color: $text-2;
  margin-bottom: $gap-1;
}
.bar-track {
  height: 12rpx;
  background: $bg-2;
  border-radius: $r-pill;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: $gradient-primary;
  border-radius: $r-pill;
  transition: width 0.4s ease;
}

// ----- 当前动作卡片 -----
.current-area {
  margin-bottom: $gap-3;
}
.current-card {
  margin-bottom: 0;
}
.current-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-1;
}
.current-idx {
  font-size: $fs-xs;
  color: $primary;
  font-weight: 600;
  background: $primary-tint;
  padding: 4rpx 16rpx;
  border-radius: $r-pill;
}
.done-tag {
  font-size: $fs-xs;
  color: #fff;
  background: $primary;
  padding: 4rpx 16rpx;
  border-radius: $r-pill;
}
.current-name {
  font-size: $fs-xl;
  font-weight: 700;
  color: $text-1;
  margin-bottom: 4rpx;
}
.current-meta {
  font-size: $fs-sm;
  color: $text-3;
  margin-top: 2rpx;
}

.set-list {
  margin-top: $gap-3;
}
.set-head, .set-row {
  display: grid;
  grid-template-columns: 60rpx 1.2fr 1.4fr 80rpx;
  align-items: center;
  gap: $gap-1;
  padding: $gap-1 0;
}
.set-head {
  border-bottom: 1rpx solid $divider;
  margin-bottom: 4rpx;
}
.set-h {
  font-size: $fs-xs;
  color: $text-3;
  text-align: center;
}
.set-row {
  &.done {
    background: $primary-tint;
    border-radius: $r-12;
    padding: $gap-1;
    margin: 4rpx 0;
  }
}
.set-idx {
  text-align: center;
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
}
.target-cell {
  font-size: $fs-sm;
  color: $text-2;
  text-align: center;
}
.actual-cell {
  display: flex;
  align-items: center;
  gap: 4rpx;
}
.set-input {
  width: 80rpx;
  height: 56rpx;
  background: $bg;
  border-radius: $r-8;
  text-align: center;
  font-size: $fs-sm;
  color: $text-1;
}
.set-x {
  font-size: $fs-xs;
  color: $text-3;
}
.done-cell {
  display: flex;
  justify-content: center;
}
.check-btn {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  border: 2rpx solid $divider;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: #fff;
  &.done {
    background: $primary;
    border-color: $primary;
    font-weight: 600;
  }
}

.current-actions {
  margin-top: $gap-3;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $gap-2;
}
.hint {
  font-size: $fs-sm;
  color: $text-3;
}

// ----- 全部动作概览 -----
.overview-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: $fs-sm;
  color: $text-2;
  font-weight: 600;
}
.overview-toggle {
  font-size: $fs-xs;
  color: $primary;
}
.overview-list {
  margin-top: $gap-2;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.overview-item {
  display: flex;
  align-items: center;
  padding: $gap-2;
  background: $bg-2;
  border-radius: $r-12;
  &.current {
    background: $primary-tint;
    border: 2rpx solid $primary;
  }
  &.done {
    opacity: 0.6;
  }
}
.ov-idx {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: $card;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $fs-sm;
  font-weight: 600;
  color: $text-2;
  margin-right: $gap-2;
  flex-shrink: 0;
}
.ov-info {
  flex: 1;
  min-width: 0;
}
.ov-name {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;
}
.ov-meta {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 2rpx;
}
.ov-tag {
  font-size: $fs-xs;
  color: $primary;
  font-weight: 600;
  &.done {
    color: $primary;
    background: $card;
    width: 40rpx;
    height: 40rpx;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
