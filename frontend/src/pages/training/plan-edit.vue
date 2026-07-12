<template>
  <view class="plan-edit-page">
    <view class="header">
      <view class="title">{{ id ? '编辑训练计划' : '创建训练计划' }}</view>
      <liquid-glass-button
        variant="primary"
        size="sm"
        :block="false"
        :text="saving ? '保存中...' : '保存'"
        @tap="save"
      />
    </view>

    <liquid-glass-card variant="light" radius="20rpx" padding="24rpx">
      <view class="row">
        <text class="label">计划名称</text>
        <input v-model="plan.name" placeholder="例如：胸部+三头训练" class="input" />
      </view>
      <view class="row column">
        <text class="label">如何安排训练</text>
        <text class="schedule-hint">按顺序适合循环训练；按周可指定每个训练日的星期</text>
        <view class="seg">
          <liquid-glass-pill
            v-for="s in SCHEDULE_TYPES"
            :key="s.value"
            :text="s.label"
            :variant="plan.schedule_type === s.value ? 'primary' : 'default'"
            :active="plan.schedule_type === s.value"
            interactive
            size="md"
            @tap="plan.schedule_type = s.value as 'sequence' | 'weekly'"
          />
        </view>
      </view>
    </liquid-glass-card>

    <!-- 模板选择 -->
    <liquid-glass-card v-if="!id && templates.length" variant="light" radius="20rpx" padding="24rpx">
      <view class="template-section-head">
        <view>
          <view class="section-title">选择一个训练模板</view>
          <view class="section-desc">模板会带入训练日与动作，之后仍可自由修改。</view>
        </view>
        <text class="template-count">{{ templates.length }} 个可选</text>
      </view>
      <view class="template-list">
        <view
          v-for="t in templates"
          :key="t.id"
          :class="['template-option', { selected: selectedTplId === t.id }]"
          @tap="pickTemplate(t)"
        >
          <view class="template-option-icon"><line-icon name="dumbbell" color="#3FA67C" :size="42" /></view>
          <view class="template-option-copy">
            <view class="template-option-name">{{ t.name }}</view>
            <view class="template-option-desc">{{ t.description || '可按你的训练节奏继续调整' }}</view>
            <view class="template-option-meta">{{ t.days?.length || 0 }} 个训练日</view>
          </view>
          <text class="template-option-arrow">›</text>
        </view>
      </view>
      <view class="blank-plan-option" @tap="clearTemplate"><text>不使用模板，空白创建</text><text>›</text></view>
    </liquid-glass-card>

    <!-- 训练日列表 -->
    <liquid-glass-card variant="light" radius="20rpx" padding="24rpx">
      <view class="section-head">
        <text class="section-title">训练日</text>
        <liquid-glass-button
          variant="primary"
          size="sm"
          :block="false"
          text="+ 添加训练日"
          @tap="addDay"
        />
      </view>

      <view v-if="plan.days.length === 0" class="day-empty">
        <line-icon name="calendar" tint="mint" :size="72" class="day-empty-icon" />
        <view>还没有训练日，点击右上角添加</view>
      </view>

      <liquid-glass-card
        v-for="(day, di) in plan.days"
        :key="di"
        variant="light"
        radius="16rpx"
        padding="24rpx"
      >
        <view class="day-head">
          <view class="day-name-row">
            <input v-model="day.day_name" placeholder="训练日名称" class="day-name-input" />
            <view v-if="plan.schedule_type === 'weekly'" class="day-weekday">
              <picker
                mode="selector"
                :range="weekdayLabels"
                :value="(day.weekday || 1) - 1"
                @change="(e: any) => day.weekday = Number(e.detail.value) + 1"
              >
                <text>{{ weekdayLabels[(day.weekday || 1) - 1] }}</text>
              </picker>
            </view>
          </view>
          <view class="day-actions">
            <liquid-glass-button variant="primary" size="sm" :block="false" text="+ 动作" @tap="addExercise(di)" />
            <liquid-glass-button variant="ghost" size="sm" :block="false" text="删除日" @tap="removeDay(di)" />
          </view>
        </view>

        <view v-if="day.exercises.length === 0" class="ex-empty">
          暂无动作
        </view>

        <view v-for="(ex, ei) in day.exercises" :key="ei" class="ex-row" :class="{ 'ex-row-editing': isEditing(di, ei) }">
          <template v-if="isEditing(di, ei)">
            <view class="ex-edit-form">
              <view class="ex-edit-title">编辑动作</view>
              <view class="ex-edit-grid">
                <view class="ex-edit-field">
                  <text class="ex-edit-label">动作名</text>
                  <input v-model="exEditing.name" class="ex-edit-input" placeholder="动作名称" />
                </view>
                <view class="ex-edit-field">
                  <text class="ex-edit-label">部位</text>
                  <input v-model="exEditing.body_part" class="ex-edit-input" placeholder="部位" />
                </view>
                <view class="ex-edit-field sm">
                  <text class="ex-edit-label">组数</text>
                  <input v-model.number="exEditing.target_sets" type="number" class="ex-edit-input" />
                </view>
                <view class="ex-edit-field sm">
                  <text class="ex-edit-label">次数</text>
                  <input v-model.number="exEditing.target_reps" type="number" class="ex-edit-input" />
                </view>
                <view class="ex-edit-field sm">
                  <text class="ex-edit-label">重量</text>
                  <input v-model.number="exEditing.target_weight_kg" type="digit" class="ex-edit-input" placeholder="kg" />
                </view>
                <view class="ex-edit-field sm">
                  <text class="ex-edit-label">休息</text>
                  <input v-model.number="exEditing.rest_seconds" type="number" class="ex-edit-input" placeholder="秒" />
                </view>
              </view>
              <view class="ex-edit-actions">
                <liquid-glass-button variant="ghost" size="sm" :block="false" text="取消" @tap="cancelEx" />
                <liquid-glass-button variant="primary" size="sm" :block="false" text="保存" @tap="confirmEditEx" />
              </view>
            </view>
          </template>
          <template v-else>
            <view class="ex-info">
              <view class="ex-name">{{ ex.exercise_name_snapshot }}</view>
              <view class="ex-meta">{{ ex.target_sets }} 组 × {{ ex.target_reps }} 次 · {{ ex.target_weight_kg || '-' }} kg · 休息 {{ ex.rest_seconds }}s</view>
            </view>
            <view class="ex-actions">
              <liquid-glass-button variant="soft" size="sm" :block="false" text="编辑" @tap="editExercise(di, ei)" />
              <liquid-glass-button variant="ghost" size="sm" :block="false" text="删除" @tap="removeExercise(di, ei)" />
            </view>
          </template>
        </view>

        <!-- 新增动作：行内搜索/表单 -->
        <view v-if="isAdding(di)" class="ex-add-panel">
          <view class="ex-edit-title">添加动作</view>
          <view class="ex-search-bar">
            <input v-model="exSearchKw" placeholder="搜索动作名称" class="ex-search-input" @confirm="searchExercises" />
            <liquid-glass-button variant="primary" size="sm" :block="false" text="搜索" @tap="searchExercises" />
          </view>
          <scroll-view v-if="exEditing.exIdx === null" scroll-y class="ex-search-scroll">
            <view
              v-for="ex in exSearchList"
              :key="`${ex.source}-${ex.id}`"
              class="ex-search-item"
              @tap="selectExerciseFromSearch(ex)"
            >
              <view class="ex-search-info">
                <view class="ex-search-name">{{ ex.name }}</view>
                <view class="ex-search-meta">{{ ex.body_part }}</view>
              </view>
              <view class="add-icon">+</view>
            </view>
            <view v-if="exSearchList.length === 0 && exSearched" class="empty-tip">
              <view>没有找到动作</view>
              <liquid-glass-button variant="soft" size="sm" :block="false" text="创建自定义动作" @tap="createCustomExercise" />
            </view>
          </scroll-view>
          <view v-if="exEditing.exIdx === -1" class="ex-edit-form compact">
            <view class="ex-edit-grid">
              <view class="ex-edit-field">
                <text class="ex-edit-label">动作名</text>
                <input v-model="exEditing.name" class="ex-edit-input" placeholder="动作名称" />
              </view>
              <view class="ex-edit-field">
                <text class="ex-edit-label">部位</text>
                <input v-model="exEditing.body_part" class="ex-edit-input" placeholder="部位" />
              </view>
              <view class="ex-edit-field sm">
                <text class="ex-edit-label">组数</text>
                <input v-model.number="exEditing.target_sets" type="number" class="ex-edit-input" />
              </view>
              <view class="ex-edit-field sm">
                <text class="ex-edit-label">次数</text>
                <input v-model.number="exEditing.target_reps" type="number" class="ex-edit-input" />
              </view>
              <view class="ex-edit-field sm">
                <text class="ex-edit-label">重量</text>
                <input v-model.number="exEditing.target_weight_kg" type="digit" class="ex-edit-input" placeholder="kg" />
              </view>
              <view class="ex-edit-field sm">
                <text class="ex-edit-label">休息</text>
                <input v-model.number="exEditing.rest_seconds" type="number" class="ex-edit-input" placeholder="秒" />
              </view>
            </view>
            <view class="ex-edit-actions">
              <liquid-glass-button variant="ghost" size="sm" :block="false" text="取消" @tap="cancelEx" />
              <liquid-glass-button variant="primary" size="sm" :block="false" text="保存" @tap="confirmEditEx" />
            </view>
          </view>
        </view>
      </liquid-glass-card>
    </liquid-glass-card>

    <!-- 计划操作 -->
    <view v-if="id" class="plan-actions">
      <liquid-glass-button
        variant="soft"
        size="md"
        :block="false"
        :text="activating ? '设置中...' : '设为当前计划'"
        :disabled="activating"
        @tap="setActive"
      />
      <liquid-glass-button
        variant="danger"
        size="md"
        :block="false"
        text="删除计划"
        @tap="removePlan"
      />
    </view>

  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { trainingApi, TrainingTemplate, PlanDay, PlanExercise } from '@/api/training';
import { exerciseApi } from '@/api/exercises';
import { SCHEDULE_TYPES } from '@/utils/constants';
import { safeNavigateBack } from '@/utils/nav';
import { useAuthStore } from '@/store/auth';
import { requireAuth } from '@/utils/auth-guard';
import { validateTrainingPlan } from '@/utils/training-plan';

const id = ref(0);
const saving = ref(false);
const activating = ref(false);

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

const auth = useAuthStore();

onMounted(async () => {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    const pages = getCurrentPages();
    const opt = (pages[pages.length - 1] as any)?.options || {};
    const redirect = opt.id
      ? `/pages/training/plan-edit?id=${opt.id}`
      : '/pages/training/plan-edit';
    requireAuth({ redirect });
    return;
  }

  const pages = getCurrentPages();
  const opt = (pages[pages.length - 1] as any)?.options || {};
  id.value = Number(opt.id || 0);
  const templateId = Number(opt.templateId || 0);

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
    } catch (e) {
      uni.showToast({ title: '加载计划失败', icon: 'none' });
    }
  }

  try {
    const res = await trainingApi.getTemplates();
    templates.value = res.items || [];
    if (!id.value && templateId) {
      const template = templates.value.find((item) => item.id === templateId);
      if (!template) {
        uni.showToast({ title: '训练模板不存在', icon: 'none' });
      } else {
        pickTemplate(template);
      }
    }
  } catch (e) {
    uni.showToast({ title: '加载模板失败', icon: 'none' });
  }
});

function pickTemplate(t: TrainingTemplate) {
  selectedTplId.value = t.id;
  plan.source_template_id = t.id;
  plan.name = plan.name || t.name;
  plan.days = (t.days || []).map((d, i) => ({
    day_index: d.day_index || i + 1,
    day_name: d.day_name,
    is_rest_day: d.is_rest_day,
    weekday: d.weekday || null,
    sort_order: i,
    exercises: (d.exercises || []).map((ex, j) => ({
      exercise_source: ex.exercise_source || 'system',
      exercise_id: ex.exercise_id,
      custom_exercise_id: ex.custom_exercise_id || null,
      exercise_name_snapshot: ex.exercise_name_snapshot,
      body_part_snapshot: ex.body_part_snapshot || '',
      target_sets: ex.target_sets,
      target_reps: ex.target_reps,
      target_weight_kg: ex.target_weight_kg || null,
      rest_seconds: ex.rest_seconds,
      sort_order: j,
      note: ex.note,
    })),
  }));
}

function clearTemplate() {
  selectedTplId.value = null;
  plan.source_template_id = null;
  plan.name = '';
  plan.days = [];
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

function isEditing(di: number, ei: number) {
  return showExEditor.value && exEditing.dayIdx === di && exEditing.exIdx === ei;
}

function isAdding(di: number) {
  return showExEditor.value && exEditing.dayIdx === di && exEditing.exIdx === null;
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

function createCustomExercise() {
  const name = exSearchKw.value.trim();
  if (!name) {
    safeToast('请先输入动作名称');
    return;
  }
  uni.showModal({
    title: '创建自定义动作',
    content: '请输入训练部位',
    editable: true,
    placeholderText: '例如：胸部',
    success: async (result) => {
      if (!result.confirm) return;
      const bodyPart = (result.content || '').trim();
      if (!bodyPart) return safeToast('请输入训练部位');
      try {
        const created = await exerciseApi.createCustom({ name, body_part: bodyPart });
        selectExerciseFromSearch({ ...created, source: 'custom' });
      } catch (e: any) {
        safeToast(e?.message || '创建动作失败');
      }
    },
  });
}

function cancelEx() {
  showExEditor.value = false;
}

function confirmEditEx() {
  if (exEditing.dayIdx < 0 || exEditing.exIdx === null || exEditing.exIdx < -1) return;
  const sets = exEditing.target_sets;
  const reps = exEditing.target_reps;
  const weight = exEditing.target_weight_kg;
  const rest = exEditing.rest_seconds;
  if (
    !Number.isFinite(sets) || !Number.isInteger(sets) || sets <= 0 ||
    !Number.isFinite(reps) || !Number.isInteger(reps) || reps <= 0 ||
    !Number.isFinite(weight) || weight < 0 ||
    !Number.isFinite(rest) || !Number.isInteger(rest) || rest <= 0
  ) {
    uni.showToast({ title: '请输入有效的数值', icon: 'none' });
    return;
  }
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
  if (saving.value) return;
  const validationError = validateTrainingPlan(plan);
  if (validationError) {
    safeToast(validationError, 'none');
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
      await trainingApi.createPlan(payload);
    }
    safeToast('已保存', 'success');
    setTimeout(() => safeNavigateBack('/pages/training/index'), 600);
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

async function setActive() {
  if (!id.value || activating.value) return;
  activating.value = true;
  try {
    await trainingApi.setActive(id.value);
    safeToast('已设为当前计划', 'success');
    setTimeout(() => safeNavigateBack('/pages/training/index'), 600);
  } catch (e: any) {
    safeToast(e?.message || '设置失败', 'none');
  } finally {
    activating.value = false;
  }
}

async function removePlan() {
  if (!id.value) return;
  uni.showModal({
    title: '删除计划',
    content: '确定删除该训练计划？删除后不可恢复。',
    confirmColor: '#F26565',
    success: async (res) => {
      if (!res.confirm) return;
      try {
        await trainingApi.deletePlan(id.value);
        safeToast('已删除', 'success');
        setTimeout(() => safeNavigateBack('/pages/training/index'), 600);
      } catch (e: any) {
        safeToast(e?.message || '删除失败', 'none');
      }
    },
  });
}
</script>

<style lang="scss" scoped>
.plan-edit-page {
  background: $bg;
  padding: $gap-3;
}

.plan-actions {
  display: flex;
  gap: $gap-2;
  margin-top: $gap-3;
  justify-content: center;
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
.schedule-hint { margin: -8rpx 0 8rpx; color: $text-3; font-size: $fs-xs; line-height: 1.5; }
.input {
  flex: 1;
  min-width: 0;
  box-sizing: border-box;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 $gap-2;
  font-size: $fs-md;
  color: $text-1;
  text-align: right;
}

.seg {
  display: flex;
  gap: $gap-2;
  flex-wrap: wrap;
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

.template-section-head { display: flex; align-items: flex-start; justify-content: space-between; gap: $gap-2; }
.section-desc { margin-top: 6rpx; color: $text-3; font-size: $fs-xs; line-height: 1.5; }
.template-count { flex: none; padding: 6rpx 12rpx; border-radius: $r-pill; background: $primary-tint; color: $primary-deep; font-size: $fs-xs; }
.template-list { display: flex; flex-direction: column; gap: 16rpx; margin-top: 20rpx; }
.template-option { min-height: 156rpx; display: flex; align-items: center; gap: 20rpx; padding: 22rpx; box-sizing: border-box; border: 1rpx solid $divider; border-radius: 18rpx; background: $card; }
.template-option.selected { border-color: $primary; background: $primary-tint; box-shadow: 0 8rpx 18rpx rgba(63, 166, 124, .12); }
.template-option-icon { width: 64rpx; height: 64rpx; flex: none; display: flex; align-items: center; justify-content: center; border-radius: 18rpx; background: $primary-tint; }
.template-option.selected .template-option-icon { background: rgba(255, 255, 255, .72); }
.template-option-copy { flex: 1; min-width: 0; }
.template-option-name { color: $text-1; font-size: $fs-md; font-weight: 700; }
.template-option-desc { display: -webkit-box; margin-top: 6rpx; overflow: hidden; color: $text-3; font-size: $fs-xs; line-height: 1.45; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.template-option-meta { margin-top: 10rpx; color: $primary-deep; font-size: $fs-xs; font-weight: 650; }
.template-option-arrow { flex: none; color: $primary-deep; font-size: 40rpx; line-height: 1; }
.blank-plan-option { display: flex; align-items: center; justify-content: space-between; margin-top: 18rpx; padding: 22rpx 6rpx 0; border-top: 1rpx dashed $divider; color: $text-2; font-size: $fs-sm; }

.day-empty {
  text-align: center;
  padding: $gap-3;
  color: $text-3;
}
.day-empty-icon {
  margin: 0 auto $gap-2;
}

.day-head {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
  margin-bottom: $gap-2;
}
.day-name-row {
  display: flex;
  align-items: center;
  gap: $gap-2;
  width: 100%;
}
.day-name-input {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  font-weight: 600;
  background: $card;
  box-sizing: border-box;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 $gap-2;
  border-radius: $r-12;
  min-width: 0;
}
.day-weekday {
  padding: 8rpx 16rpx;
  background: $primary-tint;
  color: $primary-deep;
  border-radius: $r-pill;
  font-size: $fs-sm;
  flex-shrink: 0;
}
.day-actions {
  display: flex;
  gap: 8rpx;
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
  gap: $gap-2;
}
.ex-info {
  flex: 1;
  min-width: 0;
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
  flex-shrink: 0;
}

// ----- 动作行内编辑 -----
.ex-row-editing {
  flex-direction: column;
  align-items: stretch;
  background: $primary-tint;
  border-radius: $r-12;
  padding: $gap-2;
  margin: 8rpx 0;
}
.ex-edit-form {
  width: 100%;
}
.ex-edit-title {
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
  margin-bottom: $gap-2;
}
.ex-edit-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $gap-2;
}
.ex-edit-field {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  min-width: 0;
}
.ex-edit-label {
  font-size: $fs-xs;
  color: $text-2;
}
.ex-edit-input {
  background: $card;
  border-radius: $r-12;
  box-sizing: border-box;
  min-width: 0;
  width: 100%;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 $gap-2;
  font-size: $fs-md;
  color: $text-1;
}
.ex-edit-actions {
  display: flex;
  gap: $gap-2;
  margin-top: $gap-3;
  justify-content: flex-end;
}

// ----- 添加动作面板 -----
.ex-add-panel {
  background: $primary-tint;
  border-radius: $r-12;
  padding: $gap-2;
  margin-top: $gap-2;
}
.ex-search-bar {
  display: flex;
  align-items: center;
  gap: $gap-2;
  margin-bottom: $gap-2;
}
.ex-search-input {
  flex: 1;
  background: $card;
  border-radius: $r-12;
  box-sizing: border-box;
  min-width: 0;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 $gap-2;
  font-size: $fs-md;
  color: $text-1;
}
.ex-search-scroll {
  max-height: 40vh;
}
.ex-search-item {
  display: flex;
  align-items: center;
  padding: $gap-2;
  background: $card;
  border-radius: $r-12;
  margin-bottom: 8rpx;
}
.ex-search-info {
  flex: 1;
  min-width: 0;
}
.ex-search-name {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;
}
.ex-search-meta {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
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
  flex-shrink: 0;
}
.empty-tip {
  text-align: center;
  color: $text-3;
  padding: $gap-3 0;
}
</style>
