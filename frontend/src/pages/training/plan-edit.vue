<template>
  <view class="plan-edit-page">
    <view class="header">
      <view class="title">{{ id ? '编辑训练计划' : '创建训练计划' }}</view>
      <view class="save-btn" @tap="save">{{ saving ? '保存中...' : '保存' }}</view>
    </view>

    <view class="form-card">
      <view class="row">
        <text class="label">计划名称</text>
        <input v-model="plan.name" placeholder="例如：胸部+三头训练" class="input" />
      </view>
      <view class="row column">
        <text class="label">排期方式</text>
        <view class="seg">
          <view
            v-for="s in SCHEDULE_TYPES"
            :key="s.value"
            :class="['seg-item', { active: plan.schedule_type === s.value }]"
            @tap="plan.schedule_type = s.value as 'sequence' | 'weekly'"
          >
            <view class="seg-name">{{ s.label }}</view>
            <view class="seg-desc">{{ s.desc }}</view>
          </view>
        </view>
      </view>
    </view>

    <!-- 模板选择 -->
    <view v-if="!id && templates.length" class="section">
      <view class="section-title">从模板开始</view>
      <view class="tpl-grid">
        <view
          v-for="t in templates"
          :key="t.id"
          :class="['tpl-card', { active: selectedTplId === t.id }]"
          @tap="pickTemplate(t)"
        >
          <view class="tpl-name">{{ t.name }}</view>
          <view class="tpl-desc">{{ t.description }}</view>
          <view class="tpl-meta">{{ t.days?.length || 0 }} 个训练日</view>
        </view>
      </view>
    </view>

    <!-- 训练日列表 -->
    <view class="section">
      <view class="section-head">
        <text class="section-title">训练日</text>
        <view class="add-day-btn" @tap="addDay">+ 添加训练日</view>
      </view>

      <view v-if="plan.days.length === 0" class="day-empty">
        <view class="emoji">📅</view>
        <view>还没有训练日，点击右上角添加</view>
      </view>

      <view v-for="(day, di) in plan.days" :key="di" class="day-card">
        <view class="day-head">
          <input v-model="day.day_name" placeholder="训练日名称" class="day-name-input" />
          <view class="day-weekday" v-if="plan.schedule_type === 'weekly'">
            <picker
              mode="selector"
              :range="weekdayLabels"
              :value="(day.weekday || 1) - 1"
              @change="(e: any) => day.weekday = Number(e.detail.value) + 1"
            >
              <text>{{ weekdayLabels[(day.weekday || 1) - 1] }}</text>
            </picker>
          </view>
          <view class="day-actions">
            <view class="da-btn" @tap="addExercise(di)">+ 动作</view>
            <view class="da-btn danger" @tap="removeDay(di)">删除</view>
          </view>
        </view>

        <view v-if="day.exercises.length === 0" class="ex-empty">
          暂无动作
        </view>

        <view v-for="(ex, ei) in day.exercises" :key="ei" class="ex-row">
          <view class="ex-info">
            <view class="ex-name">{{ ex.exercise_name_snapshot }}</view>
            <view class="ex-meta">{{ ex.target_sets }} 组 × {{ ex.target_reps }} 次 · {{ ex.target_weight_kg || '-' }} kg · 休息 {{ ex.rest_seconds }}s</view>
          </view>
          <view class="ex-actions">
            <view class="ea-btn" @tap="editExercise(di, ei)">编辑</view>
            <view class="ea-btn danger" @tap="removeExercise(di, ei)">删除</view>
          </view>
        </view>
      </view>
    </view>

    <!-- 动作编辑弹窗 -->
    <view v-if="showExEditor" class="ex-mask" @tap="cancelEx">
      <view class="ex-picker" @tap.stop>
        <view class="ex-title">{{ exIdx === null ? '选择动作' : '编辑动作' }}</view>

        <view v-if="exIdx === null" class="ex-search">
          <input v-model="exSearchKw" placeholder="搜索动作" class="input" @confirm="searchExercises" />
          <view class="search-btn" @tap="searchExercises">搜索</view>
        </view>

        <view v-if="exIdx === null" class="ex-search-list">
          <view
            v-for="ex in exSearchList"
            :key="`${ex.source}-${ex.id}`"
            class="ex-search-item"
            @tap="selectExerciseFromSearch(ex)"
          >
            <view class="ex-info">
              <view class="ex-name">{{ ex.name }}</view>
              <view class="ex-meta">{{ ex.body_part }}</view>
            </view>
            <view class="add-icon">+</view>
          </view>
          <view v-if="exSearchList.length === 0 && exSearched" class="empty-tip">
            没有找到动作，试试其它关键词
          </view>
        </view>

        <view v-else class="ex-form">
          <view class="row">
            <text class="label">动作名</text>
            <text class="value">{{ exEditing.name }}</text>
          </view>
          <view class="row">
            <text class="label">部位</text>
            <text class="value">{{ exEditing.body_part }}</text>
          </view>
          <view class="row">
            <text class="label">组数</text>
            <input v-model.number="exEditing.target_sets" type="number" class="input" />
          </view>
          <view class="row">
            <text class="label">次数</text>
            <input v-model.number="exEditing.target_reps" type="number" class="input" />
          </view>
          <view class="row">
            <text class="label">重量 (kg)</text>
            <input v-model.number="exEditing.target_weight_kg" type="digit" class="input" placeholder="可选" />
          </view>
          <view class="row">
            <text class="label">组间休息</text>
            <input v-model.number="exEditing.rest_seconds" type="number" class="input" />
            <text class="unit">秒</text>
          </view>
        </view>

        <view class="ex-picker-actions">
          <view class="ghost" @tap="cancelEx">取消</view>
          <view v-if="exEditing.exIdx !== null && exEditing.exIdx >= 0" class="primary" @tap="confirmEditEx">确定</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { trainingApi, TrainingTemplate, PlanDay, PlanExercise } from '@/api/training';
import { exerciseApi } from '@/api/exercises';
import { SCHEDULE_TYPES, WEEKDAY_CN } from '@/utils/constants';

const id = ref(0);
const saving = ref(false);

const weekdayLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

const plan = reactive({
  name: '',
  schedule_type: 'weekly' as 'sequence' | 'weekly',
  source_template_id: null as number | null,
  days: [] as PlanDay[],
});

const templates = ref<TrainingTemplate[]>([]);
const selectedTplId = ref<number | null>(null);

const showExEditor = ref(false);
const exEditing = reactive({
  dayIdx: -1,
  exIdx: null as number | null,
  exercise_source: 'system' as 'system' | 'custom',
  exercise_id: null as number | null,
  custom_exercise_id: null as number | null,
  name: '',
  body_part: '',
  target_sets: 4,
  target_reps: 10,
  target_weight_kg: 0 as number,
  rest_seconds: 90,
  sort_order: 0,
});

const exSearchKw = ref('');
const exSearchList = ref<{ id: number; name: string; body_part: string; source: 'system' | 'custom' }[]>([]);
const exSearched = ref(false);

onMounted(async () => {
  const pages = getCurrentPages();
  const opt = (pages[pages.length - 1] as any)?.options || {};
  id.value = Number(opt.id || 0);

  if (id.value) {
    try {
      const p = await trainingApi.getPlan(id.value);
      plan.name = p.name;
      plan.schedule_type = p.schedule_type;
      plan.source_template_id = p.source_template_id || null;
      plan.days = (p.days || []).map((d) => ({
        day_index: d.day_index,
        day_name: d.day_name,
        is_rest_day: d.is_rest_day,
        weekday: d.weekday || null,
        sort_order: d.sort_order || 0,
        exercises: d.exercises || [],
      }));
    } catch {}
  }

  try {
    const res = await trainingApi.getTemplates();
    templates.value = res.items || [];
  } catch {}
});

function pickTemplate(t: TrainingTemplate) {
  selectedTplId.value = t.id;
  plan.source_template_id = t.id;
  plan.name = plan.name || t.name;
  plan.schedule_type = 'weekly';
  plan.days = (t.days || []).map((d, i) => ({
    day_index: d.day_index || i + 1,
    day_name: d.day_name,
    is_rest_day: d.is_rest_day,
    weekday: d.weekday || null,
    sort_order: i,
    exercises: (d.exercises || []).map((ex, j) => ({
      exercise_source: ex.exercise_source,
      exercise_id: ex.exercise_id,
      custom_exercise_id: ex.custom_exercise_id,
      exercise_name_snapshot: ex.exercise_name_snapshot,
      body_part_snapshot: ex.body_part_snapshot,
      target_sets: ex.target_sets,
      target_reps: ex.target_reps,
      target_weight_kg: ex.target_weight_kg,
      rest_seconds: ex.rest_seconds,
      sort_order: j,
    })),
  }));
}

function addDay() {
  const dayIdx = plan.days.length + 1;
  plan.days.push({
    day_index: dayIdx,
    day_name: plan.schedule_type === 'sequence' ? `Day${dayIdx}` : '',
    is_rest_day: false,
    weekday: plan.schedule_type === 'weekly' ? Math.min(dayIdx, 7) : null,
    sort_order: plan.days.length,
    exercises: [],
  });
}

function removeDay(i: number) {
  uni.showModal({
    title: '提示',
    content: '确定删除该训练日？',
    success: (r) => {
      if (r.confirm) plan.days.splice(i, 1);
    },
  });
}

function addExercise(dayIdx: number) {
  exEditing.dayIdx = dayIdx;
  exEditing.exIdx = null;
  exSearchKw.value = '';
  exSearchList.value = [];
  exSearched.value = false;
  showExEditor.value = true;
  searchExercises();
}

function editExercise(di: number, ei: number) {
  const ex = plan.days[di].exercises[ei];
  exEditing.dayIdx = di;
  exEditing.exIdx = ei;
  exEditing.exercise_source = ex.exercise_source;
  exEditing.exercise_id = ex.exercise_id;
  exEditing.custom_exercise_id = ex.custom_exercise_id;
  exEditing.name = ex.exercise_name_snapshot;
  exEditing.body_part = ex.body_part_snapshot || '';
  exEditing.target_sets = ex.target_sets;
  exEditing.target_reps = ex.target_reps;
  exEditing.target_weight_kg = ex.target_weight_kg || 0;
  exEditing.rest_seconds = ex.rest_seconds;
  exEditing.sort_order = ex.sort_order || ei;
  showExEditor.value = true;
}

function removeExercise(di: number, ei: number) {
  plan.days[di].exercises.splice(ei, 1);
}

async function searchExercises() {
  try {
    const res = await exerciseApi.search({ keyword: exSearchKw.value, page_size: 30 });
    exSearchList.value = (res.items || []).map((it: any) => ({
      id: it.id,
      name: it.name,
      body_part: it.body_part,
      source: it.source || 'system',
    }));
    exSearched.value = true;
  } catch {
    exSearchList.value = [];
  }
}

function selectExerciseFromSearch(ex: any) {
  exEditing.exercise_source = ex.source;
  exEditing.exercise_id = ex.source === 'system' ? ex.id : null;
  exEditing.custom_exercise_id = ex.source === 'custom' ? ex.id : null;
  exEditing.name = ex.name;
  exEditing.body_part = ex.body_part;
  exEditing.exIdx = -1; // 表示新增
  exEditing.sort_order = plan.days[exEditing.dayIdx].exercises.length;
}

function cancelEx() {
  showExEditor.value = false;
}

function confirmEditEx() {
  if (exEditing.dayIdx < 0 || exEditing.exIdx === null || exEditing.exIdx < -1) return;
  const payload: PlanExercise = {
    exercise_source: exEditing.exercise_source,
    exercise_id: exEditing.exercise_id,
    custom_exercise_id: exEditing.custom_exercise_id,
    exercise_name_snapshot: exEditing.name,
    body_part_snapshot: exEditing.body_part,
    target_sets: exEditing.target_sets,
    target_reps: exEditing.target_reps,
    target_weight_kg: exEditing.target_weight_kg || null,
    rest_seconds: exEditing.rest_seconds,
    sort_order: exEditing.sort_order,
  };
  if (exEditing.exIdx === -1) {
    plan.days[exEditing.dayIdx].exercises.push(payload);
  } else if (exEditing.exIdx >= 0) {
    plan.days[exEditing.dayIdx].exercises[exEditing.exIdx] = payload;
  }
  showExEditor.value = false;
}

async function save() {
  if (!plan.name.trim()) {
    safeToast('请填写计划名称', 'none');
    return;
  }
  if (plan.days.length === 0) {
    safeToast('请至少添加一个训练日', 'none');
    return;
  }
  saving.value = true;
  try {
    const payload = {
      name: plan.name,
      schedule_type: plan.schedule_type,
      source_template_id: plan.source_template_id,
      days: plan.days.map((d, i) => ({
        day_index: i + 1,
        day_name: d.day_name || `Day${i + 1}`,
        is_rest_day: d.is_rest_day,
        weekday: plan.schedule_type === 'weekly' ? d.weekday || null : null,
        sort_order: i,
        exercises: d.exercises.map((ex, j) => ({
          exercise_source: ex.exercise_source,
          exercise_id: ex.exercise_id,
          custom_exercise_id: ex.custom_exercise_id,
          exercise_name_snapshot: ex.exercise_name_snapshot,
          body_part_snapshot: ex.body_part_snapshot,
          target_sets: ex.target_sets,
          target_reps: ex.target_reps,
          target_weight_kg: ex.target_weight_kg,
          rest_seconds: ex.rest_seconds,
          sort_order: j,
        })),
      })),
    };
    if (id.value) {
      await trainingApi.updatePlan(id.value, payload);
    } else {
      const created = await trainingApi.createPlan(payload);
      if (created && (created as any).id) {
        // 后端 /activate 可能在某些版本不存在；静默兜底，避免阻塞保存
        try { await trainingApi.setActive((created as any).id); } catch { /* noop */ }
      }
    }
    safeToast('已保存', 'success');
    setTimeout(() => {
      if (typeof uni !== 'undefined' && uni.navigateBack) uni.navigateBack();
    }, 600);
  } catch (e: any) {
    safeToast(e?.message || '保存失败', 'none');
  } finally {
    saving.value = false;
  }
}

function safeToast(title: string, icon: 'success' | 'none' | 'error' = 'none') {
  try {
    if (typeof uni !== 'undefined' && uni.showToast) {
      uni.showToast({ title, icon });
    }
  } catch {
    /* 页面已销毁，忽略 */
  }
}
</script>

<style lang="scss" scoped>
.plan-edit-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $gap-2 0;
  margin-bottom: $gap-2;
}
.title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-1;
}
.save-btn {
  padding: 12rpx 28rpx;
  background: $primary;
  color: #fff;
  border-radius: $r-pill;
  font-size: $fs-sm;
  font-weight: 500;
}

.form-card, .section {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  margin-bottom: $gap-3;
  box-shadow: $shadow-sm;
}
.row {
  display: flex;
  align-items: center;
  padding: $gap-2 0;
  border-bottom: 1rpx solid $divider;
  gap: $gap-2;
  &.column {
    flex-direction: column;
    align-items: stretch;
  }
  &:last-child { border-bottom: none; }
}
.label {
  width: 160rpx;
  color: $text-2;
  font-size: $fs-sm;
}
.input {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  text-align: right;
}
.unit {
  color: $text-3;
  font-size: $fs-sm;
}
.value {
  flex: 1;
  text-align: right;
  font-size: $fs-md;
  color: $text-1;
}

.seg {
  display: flex;
  gap: $gap-2;
}
.seg-item {
  flex: 1;
  padding: $gap-2;
  background: $bg-2;
  border-radius: $r-12;
  text-align: center;
  &.active {
    background: $primary-tint;
    border: 2rpx solid $primary;
  }
}
.seg-name {
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
}
.seg-desc {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $gap-2;
}
.section-title {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.add-day-btn {
  padding: 8rpx 20rpx;
  background: $primary-tint;
  color: $primary-deep;
  border-radius: $r-pill;
  font-size: $fs-sm;
}

.tpl-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $gap-2;
}
.tpl-card {
  padding: $gap-2;
  background: $bg;
  border-radius: $r-12;
  border: 2rpx solid transparent;
  &.active {
    background: $primary-tint;
    border-color: $primary;
  }
}
.tpl-name {
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
}
.tpl-desc {
  font-size: $fs-xs;
  color: $text-3;
  margin: 4rpx 0;
}
.tpl-meta {
  font-size: $fs-xs;
  color: $primary;
  font-weight: 500;
}

.day-empty {
  text-align: center;
  padding: $gap-3;
  color: $text-3;
}
.day-empty .emoji {
  font-size: 56rpx;
  margin-bottom: $gap-1;
}

.day-card {
  background: $bg;
  border-radius: $r-16;
  padding: $gap-3;
  margin-bottom: $gap-2;
}
.day-head {
  display: flex;
  align-items: center;
  gap: $gap-2;
  margin-bottom: $gap-2;
  flex-wrap: wrap;
}
.day-name-input {
  flex: 1;
  min-width: 200rpx;
  font-size: $fs-md;
  color: $text-1;
  font-weight: 600;
  background: $card;
  padding: 12rpx $gap-2;
  border-radius: $r-12;
}
.day-weekday {
  padding: 8rpx 16rpx;
  background: $primary-tint;
  color: $primary-deep;
  border-radius: $r-pill;
  font-size: $fs-sm;
}
.day-actions {
  display: flex;
  gap: 8rpx;
}
.da-btn {
  padding: 6rpx 16rpx;
  background: $card;
  border-radius: $r-pill;
  font-size: $fs-xs;
  color: $text-2;
  &.danger {
    background: #FFE2E2;
    color: $danger;
  }
}

.ex-empty {
  text-align: center;
  color: $text-3;
  font-size: $fs-sm;
  padding: $gap-2 0;
}
.ex-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $gap-2 0;
  border-top: 1rpx solid $divider;
}
.ex-info {
  flex: 1;
}
.ex-name {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;
}
.ex-meta {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
}
.ex-actions {
  display: flex;
  gap: 8rpx;
}
.ea-btn {
  padding: 6rpx 16rpx;
  background: $bg-2;
  border-radius: $r-pill;
  font-size: $fs-xs;
  color: $text-2;
  &.danger {
    background: #FFE2E2;
    color: $danger;
  }
}

.ex-mask {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}
.ex-picker {
  width: 100%;
  max-height: 80vh;
  background: $card;
  border-radius: $r-24 $r-24 0 0;
  padding: $gap-3;
  overflow-y: auto;
  padding-bottom: calc(#{$gap-3} + env(safe-area-inset-bottom));
}
.ex-title {
  font-size: $fs-xl;
  font-weight: 600;
  color: $text-1;
  margin-bottom: $gap-2;
}
.ex-search {
  display: flex;
  align-items: center;
  background: $bg-2;
  border-radius: $r-12;
  padding: 4rpx 4rpx 4rpx $gap-2;
  margin-bottom: $gap-2;
}
.ex-search .input {
  flex: 1;
  text-align: left;
  background: transparent;
}
.search-btn {
  padding: 14rpx 24rpx;
  background: $primary;
  color: #fff;
  border-radius: $r-pill;
  font-size: $fs-sm;
}
.ex-search-list {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.ex-search-item {
  display: flex;
  align-items: center;
  padding: $gap-2;
  background: $bg-2;
  border-radius: $r-12;
}
.add-icon {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: $primary;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $fs-lg;
  font-weight: 600;
}
.empty-tip {
  text-align: center;
  color: $text-3;
  padding: $gap-3 0;
}
.ex-picker-actions {
  display: flex;
  gap: $gap-2;
  margin-top: $gap-3;
}
.ghost, .primary {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  border-radius: $r-16;
  font-size: $fs-md;
}
.ghost {
  background: $bg-2;
  color: $text-2;
}
.primary {
  background: $primary;
  color: #fff;
  font-weight: 500;
}
</style>