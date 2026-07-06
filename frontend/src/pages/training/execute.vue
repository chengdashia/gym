<template>
  <view v-if="session" class="execute-page">
    <view class="head">
      <view class="head-info">
        <view class="title">{{ session.session_name }}</view>
        <view class="meta">
          {{ formatDateTime(session.started_at) }} · {{ statusText }}
        </view>
      </view>
      <view class="head-actions">
        <view class="ghost-btn" @tap="confirmQuit">退出</view>
      </view>
    </view>

    <view class="progress-bar">
      <view class="bar-info">
        <text>{{ completedSets }} / {{ totalSets }} 组完成</text>
        <text>{{ formatDuration(session.duration_seconds) }}</text>
      </view>
      <view class="bar-track">
        <view class="bar-fill" :style="{ width: progressPct + '%' }" />
      </view>
    </view>

    <scroll-view scroll-y class="exercise-list">
      <view
        v-for="(ex, ei) in session.exercises || []"
        :key="ei"
        :class="['exercise-card', { done: isExerciseDone(ei) }]"
      >
        <view class="ex-head">
          <view class="ex-info">
            <view class="ex-name">{{ ex.exercise_name_snapshot }}</view>
            <view class="ex-meta">
              <text v-if="ex.body_part_snapshot">部位：{{ ex.body_part_snapshot }} · </text>
              <text>目标 {{ ex.planned_sets }} 组</text>
            </view>
          </view>
        </view>

        <view class="set-list">
          <view class="set-head">
            <text class="set-h">#</text>
            <text class="set-h">目标 (次/kg)</text>
            <text class="set-h">实际 (次/kg)</text>
            <text class="set-h">完成</text>
          </view>
          <view
            v-for="(s, si) in ex.sets"
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
              <view :class="['check-btn', { done: s.completed }]" @tap="toggleSet(ei, si)">
                {{ s.completed ? '✓' : '' }}
              </view>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>

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

    <view class="bottom-bar">
      <view class="bb-btn ghost" @tap="saveProgress">保存进度</view>
      <view class="bb-btn primary" @tap="finishSession">完成训练</view>
    </view>

    <ModalConfirm
      :visible="showQuit"
      title="退出训练"
      message="选择如何处理当前训练？"
      cancel-text="继续训练"
      confirm-text="保存进度"
      @confirm="saveAndQuit"
      @cancel="confirmAbandon"
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useTrainingStore } from '@/store/training';
import { trainingApi, TrainingSession } from '@/api/training';
import { createTimer } from '@/utils/timer';
import { formatDateTime, humanizeDuration } from '@/utils/date';
import RestTimer from '@/components/RestTimer.vue';
import ModalConfirm from '@/components/ModalConfirm.vue';

const id = ref(0);
const session = ref<TrainingSession | null>(null);
const trainingStore = useTrainingStore();
const showQuit = ref(false);
const showAbandon = ref(false);
const saving = ref(false);

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
  await loadSession();
});

onUnmounted(() => {
  timerInstance.stop();
});

async function loadSession() {
  if (!id.value) return;
  try {
    const s = await trainingApi.getSession(id.value);
    if (!s.exercises) s.exercises = [];
    session.value = s;
  } catch (e: any) {
    uni.showToast({ title: '加载失败', icon: 'none' });
  }
}

function isExerciseDone(ei: number) {
  const ex = session.value?.exercises?.[ei];
  if (!ex) return false;
  return ex.sets.every((s) => s.completed);
}

function toggleSet(ei: number, si: number) {
  const ex = session.value!.exercises![ei];
  const s = ex.sets[si];
  s.completed = !s.completed;
  if (s.completed) {
    ex.completed_sets = ex.sets.filter((x) => x.completed).length;
    // 自动启动倒计时
    timer.total = ex.rest_seconds;
    timer.remaining = ex.rest_seconds;
    timer.running = true;
    timer.visible = true;
    timerInstance.start(ex.rest_seconds);
  } else {
    ex.completed_sets = ex.sets.filter((x) => x.completed).length;
  }
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

async function persist(status: 'in_progress' | 'paused' | 'completed' | 'cancelled' = 'in_progress') {
  if (!session.value) return;
  saving.value = true;
  try {
    const payload = {
      status,
      exercises: (session.value.exercises || []).map((ex) => ({
        session_exercise_id: (ex as any).session_exercise_id,
        exercise_name_snapshot: ex.exercise_name_snapshot,
        body_part_snapshot: ex.body_part_snapshot,
        sort_order: ex.sort_order,
        planned_sets: ex.planned_sets,
        completed_sets: ex.completed_sets,
        rest_seconds: ex.rest_seconds,
        sets: ex.sets,
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
  const res = await persist('paused');
  if (res) {
    uni.showToast({ title: '已保存进度', icon: 'success' });
  }
}

async function finishSession() {
  const res = await persist('in_progress');
  if (!res) return;
  try {
    const finished = await trainingApi.finishSession(session.value!.id);
    session.value = finished;
    uni.showToast({ title: '训练完成 🎉', icon: 'success' });
    setTimeout(() => uni.navigateBack(), 800);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '完成失败', icon: 'none' });
  }
}

function confirmQuit() {
  showQuit.value = true;
}

async function saveAndQuit() {
  showQuit.value = false;
  await persist('paused');
  uni.navigateBack();
}

function confirmAbandon() {
  showQuit.value = false;
  showAbandon.value = true;
}

async function abandonSession() {
  showAbandon.value = false;
  try {
    await trainingApi.cancelSession(session.value!.id);
    uni.navigateBack();
  } catch {}
}
</script>

<style lang="scss" scoped>
.execute-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
  padding-bottom: 200rpx;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-3;
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
.ghost-btn {
  padding: 12rpx 24rpx;
  background: $bg-2;
  border-radius: $r-pill;
  color: $text-2;
  font-size: $fs-sm;
}

.progress-bar {
  background: $card;
  border-radius: $r-16;
  padding: $gap-2 $gap-3;
  margin-bottom: $gap-3;
  box-shadow: $shadow-sm;
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

.exercise-list {
  height: calc(100vh - 480rpx);
}
.exercise-card {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  margin-bottom: $gap-2;
  box-shadow: $shadow-sm;
  &.done {
    opacity: 0.6;
  }
}
.ex-name {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.ex-meta {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
}

.set-list {
  margin-top: $gap-2;
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

.bottom-bar {
  position: fixed;
  left: $gap-3;
  right: $gap-3;
  bottom: calc(#{$tabbar-height} + #{$gap-3});
  display: flex;
  gap: $gap-2;
  z-index: 30;
}
.bb-btn {
  flex: 1;
  text-align: center;
  padding: 22rpx;
  border-radius: $r-16;
  font-size: $fs-md;
  font-weight: 600;
  &.ghost {
    background: $card;
    color: $text-2;
    box-shadow: $shadow-md;
  }
  &.primary {
    background: $primary;
    color: #fff;
    box-shadow: 0 8rpx 24rpx rgba(95, 175, 145, 0.35);
  }
}
</style>