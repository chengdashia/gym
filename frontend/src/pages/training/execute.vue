<template>
  <view v-if="loading" class="loading">加载中...</view>
  <view v-else-if="session" class="execute-page">
    <view class="topbar">
      <view>
        <view class="session-name">{{ session.session_name }}</view>
        <view class="session-progress">{{ completedSets }}/{{ totalSets }} 组 · {{ Math.round(liveVolume) }} kg</view>
      </view>
      <view class="exit-action tap-spring" @tap="saveProgress">保存并退出</view>
    </view>
    <view class="progress-track"><view class="progress-fill" :style="{ width: progressPct + '%' }" /></view>

    <liquid-glass-card v-if="currentEx && currentSet" class="focus-card" custom-style="margin-bottom:0">
      <view class="focus-kicker">动作 {{ currentExIdx + 1 }}/{{ session.exercises?.length || 0 }} · 第 {{ currentSetIdx + 1 }}/{{ currentEx.sets.length }} 组</view>
      <view class="focus-name">{{ currentEx.exercise_name_snapshot }}</view>
      <view class="focus-meta">{{ currentEx.body_part_snapshot || '未分类' }} · 休息 {{ currentEx.rest_seconds }}s</view>

      <view class="target-tip">目标：{{ currentSet.target_reps || '-' }} 次<text v-if="!isBodyweight"> · {{ currentSet.target_weight_kg || '-' }} kg</text></view>

      <view :class="['input-grid', { single: isBodyweight }]">
        <view class="metric-input">
          <view class="metric-head"><text class="metric-label">实际次数</text><text class="dial-link" @tap="openDial('reps')">滚轮调整</text></view>
          <view class="metric-value"><input v-model.number="currentSet.actual_reps" type="number" :placeholder="String(currentSet.target_reps || 0)" /><text>次</text></view>
        </view>
        <view v-if="!isBodyweight" class="metric-input">
          <view class="metric-head"><text class="metric-label">实际重量</text><text class="dial-link" @tap="openDial('weight')">滚轮调整</text></view>
          <view class="metric-value"><input v-model.number="currentSet.actual_weight_kg" type="digit" :placeholder="String(currentSet.target_weight_kg || 0)" /><text>kg</text></view>
        </view>
      </view>

      <liquid-glass-button
        :text="saving ? '正在保存...' : (currentSet.completed ? '保存本组修改' : '完成本组并休息')"
        size="lg"
        :disabled="saving"
        @tap="completeCurrentSet"
      />

      <view class="set-strip">
        <view
          v-for="(set, index) in currentEx.sets"
          :key="set.set_id || set.id || index"
          :class="['set-dot', { active: index === currentSetIdx, done: set.completed }]"
          @tap="selectSet(index)"
        >{{ set.completed ? '✓' : index + 1 }}</view>
      </view>
    </liquid-glass-card>

    <liquid-glass-card class="overview-card" custom-style="margin-bottom:0">
      <view class="overview-title">全部动作</view>
      <view
        v-for="(exercise, index) in session.exercises || []"
        :key="exercise.session_exercise_id || index"
        :class="['exercise-item', exerciseProgress(exercise), { active: index === currentExIdx }]"
        @tap="selectExercise(index)"
      >
        <view class="exercise-state">{{ exerciseStateIcon(exercise) }}</view>
        <view class="exercise-info"><view class="exercise-name">{{ exercise.exercise_name_snapshot }}</view><view class="exercise-meta">{{ exercise.completed_sets }}/{{ exercise.planned_sets }} 组完成</view></view>
        <view class="exercise-label">{{ exerciseStateLabel(exercise) }}</view>
      </view>
    </liquid-glass-card>

    <view class="finish-area">
      <liquid-glass-button text="结束本次训练" :variant="allDone ? 'primary' : 'ghost'" :disabled="finishing" @tap="requestFinish" />
    </view>

    <view v-if="dialVisible" class="dial-mask" @tap="dialVisible = false">
      <view class="dial-sheet" @tap.stop>
        <view class="dial-title">调整{{ dialType === 'reps' ? '次数' : '重量' }}</view>
        <picker-view class="dial-picker" :value="dialSelection" indicator-style="height: 88rpx" @change="onDialChange">
          <picker-view-column>
            <view v-for="value in dialValues" :key="value" class="dial-row">{{ value }} {{ dialType === 'reps' ? '次' : 'kg' }}</view>
          </picker-view-column>
        </picker-view>
        <view class="dial-actions"><view class="dial-cancel tap-spring" @tap="dialVisible = false">取消</view><view class="dial-confirm tap-spring" @tap="confirmDial">使用此数值</view></view>
      </view>
    </view>

    <RestTimer :visible="timer.visible" :remaining="timer.remaining" :total="timer.total" :running="timer.running" @toggle="timerToggle" @skip="timerSkip" @adjust="timerAdjust" @close="timerClose" />
    <ModalConfirm :visible="showAbandon" title="放弃训练" message="放弃后本次记录将被标记为已放弃。" cancel-text="返回" confirm-text="放弃" danger @confirm="abandonSession" @cancel="showAbandon = false" />
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { onBackPress } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { trainingApi, type SessionExercise, type TrainingSession } from '@/api/training';
import { createTimer } from '@/utils/timer';
import { safeNavigateBack } from '@/utils/nav';
import { requireAuth } from '@/utils/auth-guard';
import { exerciseProgress, sessionVolume } from '@/utils/training-progress';
import RestTimer from '@/components/RestTimer.vue';
import ModalConfirm from '@/components/ModalConfirm.vue';

const id = ref(0);
const session = ref<TrainingSession | null>(null);
const loading = ref(true);
const saving = ref(false);
const finishing = ref(false);
const showAbandon = ref(false);
const currentExIdx = ref(0);
const currentSetIdx = ref(0);
const dialVisible = ref(false);
const dialType = ref<'reps' | 'weight'>('reps');
const dialSelection = ref([0]);
const auth = useAuthStore();
const timer = reactive({ visible: false, remaining: 0, total: 0, running: true });
const timerInstance = createTimer((remaining, total) => { timer.remaining = remaining; timer.total = total; if (!remaining) timer.visible = false; }, () => { timer.visible = false; uni.vibrateShort({ type: 'medium' }); });
let allowBack = false;

const currentEx = computed(() => session.value?.exercises?.[currentExIdx.value] || null);
const currentSet = computed(() => currentEx.value?.sets?.[currentSetIdx.value] || null);
const completedSets = computed(() => (session.value?.exercises || []).reduce((sum, exercise) => sum + exercise.sets.filter((set) => set.completed).length, 0));
const totalSets = computed(() => (session.value?.exercises || []).reduce((sum, exercise) => sum + exercise.sets.length, 0));
const progressPct = computed(() => totalSets.value ? Math.round(completedSets.value / totalSets.value * 100) : 0);
const allDone = computed(() => totalSets.value > 0 && completedSets.value === totalSets.value);
const liveVolume = computed(() => sessionVolume(session.value?.exercises || []));
const isBodyweight = computed(() => Number(currentSet.value?.target_weight_kg || 0) <= 0);
const repValues = Array.from({ length: 100 }, (_, index) => index + 1);
const weightValues = Array.from({ length: 401 }, (_, index) => index * .5);
const dialValues = computed(() => dialType.value === 'reps' ? repValues : weightValues);

onMounted(async () => {
  const pages = getCurrentPages();
  id.value = Number((pages[pages.length - 1] as any)?.options?.id || 0);
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) { requireAuth({ redirect: id.value ? `/pages/training/execute?id=${id.value}` : '/pages/training/execute' }); return; }
  await loadSession();
  jumpToFirstIncomplete();
});
onUnmounted(() => timerInstance.stop());
onBackPress(() => {
  if (allowBack) return false;
  void saveProgress();
  return true;
});

async function loadSession() {
  if (!id.value) { loading.value = false; return; }
  loading.value = true;
  try { session.value = await trainingApi.getSession(id.value); }
  catch (e: any) { uni.showToast({ title: e?.message || '加载失败', icon: 'none' }); }
  finally { loading.value = false; }
}

function jumpToFirstIncomplete() {
  const exercises = session.value?.exercises || [];
  const exIndex = exercises.findIndex((exercise) => exercise.sets.some((set) => !set.completed));
  currentExIdx.value = exIndex >= 0 ? exIndex : 0;
  const setIndex = exercises[currentExIdx.value]?.sets.findIndex((set) => !set.completed) ?? 0;
  currentSetIdx.value = setIndex >= 0 ? setIndex : 0;
  prepareCurrentSet();
}

function prepareCurrentSet() {
  const set = currentSet.value;
  if (!set) return;
  if (set.actual_reps == null || set.actual_reps === 0) set.actual_reps = set.target_reps ?? null;
  if (!isBodyweight.value && (set.actual_weight_kg == null || set.actual_weight_kg === 0)) set.actual_weight_kg = set.target_weight_kg ?? null;
}
function selectExercise(index: number) { currentExIdx.value = index; const first = currentEx.value?.sets.findIndex((set) => !set.completed) ?? 0; currentSetIdx.value = first >= 0 ? first : 0; prepareCurrentSet(); }
function selectSet(index: number) { currentSetIdx.value = index; prepareCurrentSet(); }
function openDial(type: 'reps' | 'weight') {
  dialType.value = type;
  const current = type === 'reps' ? Number(currentSet.value?.actual_reps || 1) : Number(currentSet.value?.actual_weight_kg || 0);
  const index = dialValues.value.reduce((best, value, candidate) => Math.abs(value - current) < Math.abs(dialValues.value[best] - current) ? candidate : best, 0);
  dialSelection.value = [index];
  dialVisible.value = true;
}
function onDialChange(event: any) { dialSelection.value = event.detail.value; }
function confirmDial() {
  const set = currentSet.value;
  if (!set) return;
  const value = dialValues.value[dialSelection.value[0]];
  if (dialType.value === 'reps') set.actual_reps = value;
  else set.actual_weight_kg = value;
  dialVisible.value = false;
}

function sanitize(value: any) { const number = Number(value); return Number.isFinite(number) && number >= 0 ? number : null; }
function payload(status: 'in_progress' | 'paused' = 'in_progress') {
  return { status, exercises: (session.value?.exercises || []).map((exercise) => ({
    session_exercise_id: (exercise as any).id ?? exercise.session_exercise_id,
    sets: exercise.sets.map((set) => ({ set_id: (set as any).id ?? set.set_id, set_index: set.set_index, actual_reps: sanitize(set.actual_reps), actual_weight_kg: sanitize(set.actual_weight_kg), completed: !!set.completed })),
  })) };
}
async function persist(status: 'in_progress' | 'paused' = 'in_progress') {
  if (!session.value) return false;
  saving.value = true;
  try {
    const updated = await trainingApi.updateSession(session.value.id, payload(status));
    session.value.total_volume = updated.total_volume;
    session.value.status = updated.status;
    return true;
  }
  catch (e: any) { uni.showToast({ title: e?.message || '保存失败', icon: 'none' }); return false; }
  finally { saving.value = false; }
}

async function completeCurrentSet() {
  const set = currentSet.value;
  const exercise = currentEx.value;
  if (!set || !exercise) return;
  prepareCurrentSet();
  if (!Number(set.actual_reps)) { uni.showToast({ title: '请输入实际次数', icon: 'none' }); return; }
  set.completed = true;
  exercise.completed_sets = exercise.sets.filter((item) => item.completed).length;
  const restSeconds = exercise.rest_seconds;
  if (!await persist()) { set.completed = false; exercise.completed_sets = exercise.sets.filter((item) => item.completed).length; return; }
  timer.visible = true; timer.running = true; timer.total = restSeconds; timer.remaining = restSeconds; timerInstance.start(restSeconds);
  uni.vibrateShort({ type: 'light' });
  advanceToNextIncomplete();
}
function advanceToNextIncomplete() {
  const exercises = session.value?.exercises || [];
  for (let exIndex = currentExIdx.value; exIndex < exercises.length; exIndex += 1) {
    const start = exIndex === currentExIdx.value ? currentSetIdx.value + 1 : 0;
    const relative = exercises[exIndex].sets.slice(start).findIndex((set) => !set.completed);
    if (relative >= 0) { currentExIdx.value = exIndex; currentSetIdx.value = start + relative; prepareCurrentSet(); return; }
  }
}

function exerciseStateIcon(exercise: SessionExercise) { const state = exerciseProgress(exercise); return state === 'completed' ? '✓' : state === 'in_progress' ? '◐' : '○'; }
function exerciseStateLabel(exercise: SessionExercise) { const state = exerciseProgress(exercise); return state === 'completed' ? '已完成' : state === 'in_progress' ? '进行中' : '未开始'; }
async function saveProgress() {
  if (saving.value) return;
  if (await persist('paused')) {
    uni.showToast({ title: '进度已保存', icon: 'success' });
    allowBack = true;
    setTimeout(() => safeNavigateBack('/pages/training/index'), 300);
  }
}
function requestFinish() {
  if (allDone.value) { void finishSession(); return; }
  uni.showModal({ title: '还有未完成组', content: `已完成 ${completedSets.value}/${totalSets.value} 组，仍要结束训练吗？`, success: ({ confirm }) => { if (confirm) void finishSession(); } });
}
async function finishSession() {
  if (!session.value || finishing.value) return;
  finishing.value = true;
  try {
    if (!await persist()) return;
    const finished = await trainingApi.finishSession(session.value.id);
    session.value.total_volume = finished.total_volume;
    session.value.status = finished.status;
    uni.showToast({ title: `训练完成 · ${Math.round(finished.total_volume)} kg`, icon: 'success' });
    allowBack = true;
    setTimeout(() => safeNavigateBack('/pages/training/index'), 700);
  } catch (e: any) { uni.showToast({ title: e?.message || '完成失败', icon: 'none' }); }
  finally { finishing.value = false; }
}
async function abandonSession() { if (!session.value) return; try { await trainingApi.cancelSession(session.value.id); safeNavigateBack('/pages/training/index'); } catch { uni.showToast({ title: '操作失败', icon: 'none' }); } }
function timerToggle() { if (timer.running) timerInstance.pause(); else timerInstance.resume(); timer.running = !timer.running; }
function timerSkip() { timerInstance.skip(); }
function timerAdjust(delta: number) { timerInstance.adjust(delta); }
function timerClose() { timerInstance.stop(); timer.visible = false; }
</script>

<style lang="scss" scoped>
.execute-page { min-height: 100vh; padding: $gap-3; padding-bottom: calc(#{$gap-4} + env(safe-area-inset-bottom)); }
.loading { min-height: 100vh; display: flex; align-items: center; justify-content: center; color: $text-3; }
.topbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: $gap-2; }
.session-name { font-size: $fs-xl; color: $text-1; font-weight: 800; }
.session-progress { margin-top: 4rpx; color: $text-3; font-size: $fs-sm; }
.exit-action { padding: 12rpx 22rpx; border-radius: $r-pill; color: $text-2; background: rgba(255,255,255,.72); box-shadow: $shadow-glass-sm; }
.progress-track { height: 10rpx; background: $bg-2; border-radius: $r-pill; overflow: hidden; margin-bottom: $gap-3; }
.progress-fill { height: 100%; background: $gradient-primary; transition: width .35s $ease-spring; }
.focus-card { padding: $gap-3; }
.focus-kicker { color: $primary-deep; font-size: $fs-sm; font-weight: 650; }
.focus-name { margin-top: 8rpx; color: $text-1; font-size: 44rpx; font-weight: 800; }
.focus-meta { color: $text-3; font-size: $fs-sm; }
.target-tip { margin-top: $gap-3; padding: 12rpx 16rpx; border-radius: $r-12; background: $primary-tint; color: $primary-deep; font-size: $fs-sm; }
.input-grid { display: grid; grid-template-columns: 1fr 1fr; gap: $gap-2; margin: $gap-3 0; }
.input-grid.single { grid-template-columns: 1fr; }
.metric-input { padding: $gap-2; border-radius: $r-16; background: rgba(255,255,255,.78); box-shadow: inset 0 0 0 1rpx $divider; }
.metric-head { display: flex; align-items: center; justify-content: space-between; }
.metric-label { color: $text-3; font-size: $fs-xs; }
.dial-link { color: $primary-deep; font-size: 20rpx; }
.metric-value { display: flex; align-items: baseline; gap: 6rpx; margin-top: 4rpx; color: $text-2; }
.metric-value input { flex: 1; min-width: 0; height: 88rpx; color: $text-1; font-size: 52rpx; font-weight: 800; }
.metric-value text { flex-shrink: 0; white-space: nowrap; }
.set-strip { display: flex; justify-content: center; gap: 12rpx; margin-top: $gap-3; }
.set-dot { width: 52rpx; height: 52rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: $text-3; background: $bg-2; }
.set-dot.done { color: #fff; background: $primary; }
.set-dot.active { box-shadow: 0 0 0 4rpx rgba(91,200,154,.24); }
.overview-card { margin-top: $gap-3; padding: $gap-2; }
.overview-title { padding: $gap-1 $gap-1 $gap-2; color: $text-1; font-size: $fs-lg; font-weight: 700; }
.exercise-item { display: flex; align-items: center; gap: $gap-2; padding: $gap-2; border-top: 1rpx solid $divider; border-radius: $r-12; }
.exercise-item.active { background: $primary-tint; }
.exercise-state { width: 44rpx; height: 44rpx; display: flex; align-items: center; justify-content: center; border-radius: 50%; color: $text-3; background: $bg-2; }
.exercise-item.completed .exercise-state { color: #fff; background: $primary; }
.exercise-item.in_progress .exercise-state { color: $primary-deep; background: rgba(91,200,154,.22); }
.exercise-info { flex: 1; min-width: 0; }
.exercise-name { color: $text-1; font-size: $fs-md; font-weight: 650; }
.exercise-meta { color: $text-3; font-size: $fs-xs; }
.exercise-label { color: $text-3; font-size: $fs-xs; }
.exercise-item.in_progress .exercise-label, .exercise-item.completed .exercise-label { color: $primary-deep; }
.finish-area { margin-top: $gap-3; }
.dial-mask { position: fixed; inset: 0; z-index: 220; display: flex; align-items: flex-end; background: rgba(31,42,42,.35); }
.dial-sheet { width: 100%; padding: $gap-3; padding-bottom: calc(#{$gap-3} + env(safe-area-inset-bottom)); border-radius: 36rpx 36rpx 0 0; background: rgba(247,250,248,.98); }
.dial-title { text-align: center; color: $text-1; font-size: $fs-lg; font-weight: 700; }
.dial-picker { height: 420rpx; margin: $gap-2 0; }
.dial-row { height: 88rpx; display: flex; align-items: center; justify-content: center; color: $text-1; font-size: 40rpx; font-weight: 650; }
.dial-actions { display: flex; gap: $gap-2; }
.dial-cancel, .dial-confirm { flex: 1; text-align: center; padding: 20rpx; border-radius: $r-pill; font-weight: 650; }
.dial-cancel { color: $text-2; background: $bg-2; }
.dial-confirm { color: #fff; background: $gradient-primary; }
</style>
