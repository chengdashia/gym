<template>
  <view class="account-page">
    <!-- 记录体重专用模式 -->
    <view v-if="isWeightAction" class="weight-only-page">
      <!-- Hero：当前体重 + 变化 + BMI + 目标 -->
      <liquid-glass-card variant="light" :highlight="true" class="hero-card">
        <view class="hero-top">
          <view>
            <view class="hero-label">最新体重</view>
            <view class="hero-weight">
              {{ latestWeight ? formatNumber(latestWeight.weight_kg) : '--' }}
              <text class="hero-unit">kg</text>
            </view>
            <view class="hero-date">{{ latestWeight ? latestWeight.record_date : '暂无记录' }}</view>
          </view>
          <view v-if="latestWeight && weightChange !== null" :class="['change-pill', changePillClass]">
            {{ changePillText }}
          </view>
        </view>

        <view class="hero-meta">
          <view class="meta-item">
            <text class="meta-label">BMI</text>
            <text class="meta-value">{{ bmi || '--' }}</text>
          </view>
          <view class="meta-divider" />
          <view class="meta-item">
            <text class="meta-label">目标体重</text>
            <text class="meta-value">{{ targetWeightKg ? formatNumber(targetWeightKg) + ' kg' : '未设置' }}</text>
          </view>
        </view>
      </liquid-glass-card>

      <!-- 趋势图 -->
      <liquid-glass-card variant="light" :highlight="true" class="chart-card">
        <view class="chart-head">
          <text class="chart-title">近 7 次趋势</text>
          <view class="chart-toggle">
            <liquid-glass-pill
              text="柱状"
              size="sm"
              :variant="chartType === 'bar' ? 'primary' : 'default'"
              :active="chartType === 'bar'"
              interactive
              @tap="chartType = 'bar'"
            />
            <liquid-glass-pill
              text="折线"
              size="sm"
              :variant="chartType === 'line' ? 'primary' : 'default'"
              :active="chartType === 'line'"
              interactive
              @tap="chartType = 'line'"
            />
          </view>
        </view>

        <view v-if="weightHistory.length < 2" class="chart-empty">
          <line-icon name="scale" tint="mint" :size="64" />
          <text>多记录几次，趋势会更清晰</text>
        </view>
        <view v-else class="chart-body">
          <canvas
            type="2d"
            id="weight-trend-canvas"
            canvas-id="weight-trend-canvas"
            class="chart-canvas"
          />
        </view>
      </liquid-glass-card>

      <!-- 今日输入 -->
      <liquid-glass-card variant="light" :highlight="true" class="input-card">
        <view class="input-label">今日体重</view>
        <view class="input-row">
          <input
            v-model="newWeight"
            type="digit"
            placeholder="0.0"
            class="weight-input"
            :focus="isWeightAction"
          />
          <text class="input-unit">kg</text>
        </view>
        <view class="form-row">
          <text class="label">日期</text>
          <picker mode="date" :value="weightDate" @change="weightDate = $event.detail.value"><text>{{ weightDate }}</text></picker>
        </view>
        <view class="form-row">
          <text class="label">时间</text>
          <picker mode="time" :value="weightTime" @change="weightTime = $event.detail.value"><text>{{ weightTime }}</text></picker>
        </view>
        <view class="form-row">
          <text class="label">备注</text>
          <input v-model="weightNote" placeholder="可选" class="input" />
        </view>
        <view v-if="projectedChangeText" class="projected-change">
          {{ projectedChangeText }}
        </view>
        <view class="save-actions">
          <liquid-glass-button :text="editingWeightId ? '保存修改' : '保存体重'" variant="primary" :disabled="saving" @tap="saveWeight" />
          <liquid-glass-button v-if="editingWeightId" text="取消编辑" variant="ghost" @tap="resetWeightForm" />
        </view>
      </liquid-glass-card>
      <liquid-glass-card v-if="weightRecords.length" variant="light" class="history-card">
        <view class="history-head" @tap="recordsExpanded = !recordsExpanded">
          <view class="chart-title">最近记录 <text class="record-count">{{ weightRecords.length }} 条</text></view>
          <text class="expand-action">{{ recordsExpanded ? '收起' : '展开' }} {{ recordsExpanded ? '⌃' : '⌄' }}</text>
        </view>
        <view v-if="recordsExpanded" v-for="item in weightRecords" :key="item.id" class="row">
          <view><view>{{ item.weight_kg }} kg</view><view class="hero-date">{{ item.record_date }} {{ item.record_time }} {{ item.note || '' }}</view></view>
          <view class="weight-actions"><text class="edit-action" @tap.stop="editWeight(item)">编辑</text><text class="danger-text" @tap.stop="removeWeight(item)">删除</text></view>
        </view>
      </liquid-glass-card>
    </view>

    <view v-else class="section">
      <view class="section-title">账号安全</view>
      <liquid-glass-card variant="light" :highlight="true" padding="0" custom-style="margin-bottom:0">
      </liquid-glass-card>
      <view class="section-title grouped-title">数据与存储</view>
      <liquid-glass-card variant="light" :highlight="true" padding="0" custom-style="margin-bottom:0">
        <view class="menu-item disabled">
          <line-icon name="phone" tint="sky" :size="48" class="mi-icon" />
          <text class="mi-label">手机号授权</text>
          <text class="mi-value">功能开发中</text>
        </view>
        <view class="menu-item disabled">
          <line-icon name="export" tint="mint" :size="48" class="mi-icon" />
          <text class="mi-label">数据导出</text>
          <text class="mi-value">功能开发中</text>
        </view>
        <view class="menu-item" @tap="clearCache">
          <line-icon name="broom" tint="warm" :size="48" class="mi-icon" />
          <text class="mi-label">清除缓存</text>
          <text class="mi-value">{{ cacheSize }}</text>
        </view>
      </liquid-glass-card>
      <view class="section-title grouped-title">隐私与协议</view>
      <liquid-glass-card variant="light" :highlight="true" padding="0" custom-style="margin-bottom:0">
        <view class="menu-item" @tap="goAgreement('agreement')"><line-icon name="document" tint="neutral" :size="48" class="mi-icon" /><text class="mi-label">用户协议</text><text class="mi-arrow">›</text></view>
        <view class="menu-item" @tap="goAgreement('privacy')"><line-icon name="shield" tint="sky" :size="48" class="mi-icon" /><text class="mi-label">隐私政策</text><text class="mi-arrow">›</text></view>
      </liquid-glass-card>
    </view>

    <view v-if="!isWeightAction" class="section danger-section">
      <view class="section-title">危险操作</view>
      <liquid-glass-card variant="light" :highlight="true" padding="0" custom-style="margin-bottom:0">
        <view class="menu-item" @tap="confirmDeleteData">
          <line-icon name="trash" tint="rose" :size="48" class="mi-icon" />
          <text class="mi-label danger">删除个人数据</text>
          <text class="mi-arrow">›</text>
        </view>
        <view class="menu-item" @tap="confirmCancel">
          <line-icon name="close" tint="rose" :size="48" class="mi-icon" />
          <text class="mi-label danger">注销账号</text>
          <text class="mi-arrow">›</text>
        </view>
      </liquid-glass-card>
    </view>

    <ModalConfirm
      :visible="showDeleteData"
      title="删除个人数据"
      message="将删除你的饮食、训练、体重、自定义食物等所有个人数据，此操作不可恢复。系统数据不受影响。"
      confirm-text="确认删除"
      danger
      @confirm="deleteData"
      @cancel="showDeleteData = false"
    />

    <ModalConfirm
      :visible="showCancel"
      title="注销账号"
      message="注销后账号将不可恢复，请提前导出重要数据。"
      confirm-text="确认注销"
      danger
      @confirm="cancelAccount"
      @cancel="showCancel = false"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { onShow, onLoad } from '@dcloudio/uni-app';
import LiquidGlassCard from '@/components/LiquidGlassCard.vue';
import LiquidGlassButton from '@/components/LiquidGlassButton.vue';
import LiquidGlassPill from '@/components/LiquidGlassPill.vue';
import ModalConfirm from '@/components/ModalConfirm.vue';
import LineIcon from '@/components/LineIcon.vue';
import { useUserStore } from '@/store/user';
import { useAuthStore } from '@/store/auth';
import { useDietStore } from '@/store/diet';
import { useTrainingStore } from '@/store/training';
import { weightApi, WeightRecord } from '@/api/weight';
import { clearAllCache } from '@/utils/cache';
import { formatTime, today } from '@/utils/date';
import { requireAuth } from '@/utils/auth-guard';
import { weightRecordToForm } from '@/utils/weight-record';

const userStore = useUserStore();
const auth = useAuthStore();
const dietStore = useDietStore();
const trainingStore = useTrainingStore();
const newWeight = ref<string>('');
const weightDate = ref(today());
const weightTime = ref(formatTime(new Date()));
const weightNote = ref('');
const editingWeightId = ref<number | null>(null);
const latestWeight = ref<WeightRecord | null>(null);
const weightHistory = ref<WeightRecord[]>([]);
const weightRecords = ref<WeightRecord[]>([]);
const showDeleteData = ref(false);
const showCancel = ref(false);
const cacheSize = ref('0 KB');
const loading = ref(false);
const saving = ref(false);
const highlightWeight = ref(false);
const isWeightAction = ref(false);
const chartType = ref<'bar' | 'line'>('bar');
const recordsExpanded = ref(false);

onLoad((options: any) => {
  if (options?.action === 'weight') {
    isWeightAction.value = true;
    uni.setNavigationBarTitle({ title: '记录体重' });
  }
});

onMounted(async () => {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    requireAuth({ redirect: '/pages/mine/account' });
    return;
  }
  if (!userStore.me) await userStore.fetchMe().catch(() => {
    uni.showToast({ title: '加载失败', icon: 'none' });
  });
  if (isWeightAction.value) await loadWeight();
  computeCache();
});

onShow(async () => {
  if (!auth.isLogged) return;
  if (!userStore.me) await userStore.fetchMe().catch(() => {
    uni.showToast({ title: '加载失败', icon: 'none' });
  });
  if (isWeightAction.value) await loadWeight();
});

async function loadWeight() {
  loading.value = true;
  try {
    const res = await weightApi.list(30);
    // API 返回降序（最新在前）
    const items = res.items || [];
    weightRecords.value = items;
    latestWeight.value = items[0] || null;
    // 最近 7 条，反转为正序（旧→新）给图表
    weightHistory.value = items.slice(0, 7).reverse();
    // 数据更新后重绘图表
    nextTick(() => drawChart());
  } catch (e) {
    uni.showToast({ title: '加载体重记录失败', icon: 'none' });
  } finally {
    loading.value = false;
  }
}

function formatNumber(n: number | null | undefined): string {
  if (n === null || n === undefined || !Number.isFinite(n)) return '--';
  return Number(n).toFixed(1);
}

const bmi = computed(() => {
  const h = userStore.me?.profile?.height_cm;
  const w = latestWeight.value?.weight_kg;
  if (!h || !w) return '';
  const b = w / Math.pow(h / 100, 2);
  return b.toFixed(1);
});

const targetWeightKg = computed(() => userStore.me?.profile?.target_weight_kg || null);

const weightChange = computed(() => {
  const list = weightHistory.value;
  if (list.length < 2) return null;
  const latest = list[list.length - 1]?.weight_kg;
  const prev = list[list.length - 2]?.weight_kg;
  if (latest == null || prev == null) return null;
  return Number((latest - prev).toFixed(1));
});

const changePillText = computed(() => {
  const c = weightChange.value;
  if (c === null) return '';
  if (c === 0) return '持平';
  return `${c > 0 ? '▲' : '▼'} ${Math.abs(c)} kg`;
});

const changePillClass = computed(() => {
  const c = weightChange.value;
  if (c === null) return '';
  if (c < 0) return 'down';
  if (c > 0) return 'up';
  return 'flat';
});

const projectedChange = computed(() => {
  const input = parseFloat(newWeight.value);
  const last = latestWeight.value?.weight_kg;
  if (!Number.isFinite(input) || last == null) return null;
  return Number((input - last).toFixed(1));
});

const projectedChangeText = computed(() => {
  const c = projectedChange.value;
  if (c === null) return '';
  if (c === 0) return '预计与上次持平';
  return `预计较上次 ${c > 0 ? '+' : ''}${c} kg`;
});

// 用 canvas 2D 原生 API 绘制趋势图（兼容微信小程序）
const PRIMARY_COLOR = '#5BC89A';
const WARM_COLOR = '#FF8A65';
const TEXT_COLOR = '#8FA3A1';
const GRID_COLOR = '#E6ECEA';

function drawChart() {
  const data = weightHistory.value;
  if (data.length < 2) return;

  const query = uni.createSelectorQuery();
  query.select('#weight-trend-canvas')
    .fields({ node: true, size: true }, () => {})
    .exec((res: any) => {
      if (!res || !res[0] || !res[0].node) return;
      const canvas = res[0].node;
      const width = res[0].width;
      const height = res[0].height;
      const dpr = (uni.getWindowInfo().pixelRatio || 1) as number;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      const ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);

      // 清空
      ctx.clearRect(0, 0, width, height);

      const padTop = 28;
      const padBottom = 28;
      const padLeft = 22;
      const padRight = 22;
      const chartW = width - padLeft - padRight;
      const chartH = height - padTop - padBottom;

      const weights = data.map((d) => d.weight_kg);
      const target = targetWeightKg.value;
      const allVals = target != null ? [...weights, target] : [...weights];
      const dataMin = Math.min(...allVals);
      const dataMax = Math.max(...allVals);
      const pad = (dataMax - dataMin) * 0.2 || 1;
      const yMin = Math.max(0, dataMin - pad);
      const yMax = dataMax + pad;

      function yToPx(v: number): number {
        if (yMax <= yMin) return padTop + chartH / 2;
        return padTop + chartH - ((v - yMin) / (yMax - yMin)) * chartH;
      }

      const n = data.length;
      function xToPx(i: number): number {
        if (n <= 1) return padLeft + chartW / 2;
        return padLeft + (i / (n - 1)) * chartW;
      }

      // 目标线
      if (target != null) {
        const ty = yToPx(target);
        ctx.strokeStyle = WARM_COLOR;
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(padLeft, ty);
        ctx.lineTo(width - padRight, ty);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = WARM_COLOR;
        ctx.font = '9px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('目标', width - padRight - 2, ty - 4);
      }

      if (chartType.value === 'bar') {
        // 柱状图
        const barW = Math.min(24, chartW / n * 0.6);
        weights.forEach((w, i) => {
          const cx = xToPx(i);
          const by = yToPx(w);
          // 渐变
          const grad = ctx.createLinearGradient(0, by, 0, padTop + chartH);
          grad.addColorStop(0, PRIMARY_COLOR);
          grad.addColorStop(1, 'rgba(91, 200, 154, 0.4)');
          ctx.fillStyle = grad;
          // 圆角矩形
          const r = 4;
          const x = cx - barW / 2;
          ctx.beginPath();
          ctx.moveTo(x + r, by);
          ctx.lineTo(x + barW - r, by);
          ctx.arcTo(x + barW, by, x + barW, by + r, r);
          ctx.lineTo(x + barW, padTop + chartH);
          ctx.lineTo(x, padTop + chartH);
          ctx.lineTo(x, by + r);
          ctx.arcTo(x, by, x + r, by, r);
          ctx.closePath();
          ctx.fill();
        });
      } else {
        // 折线图
        // 填充区域
        ctx.beginPath();
        weights.forEach((w, i) => {
          const px = xToPx(i);
          const py = yToPx(w);
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.lineTo(xToPx(n - 1), padTop + chartH);
        ctx.lineTo(xToPx(0), padTop + chartH);
        ctx.closePath();
        const areaGrad = ctx.createLinearGradient(0, padTop, 0, padTop + chartH);
        areaGrad.addColorStop(0, 'rgba(91, 200, 154, 0.3)');
        areaGrad.addColorStop(1, 'rgba(91, 200, 154, 0)');
        ctx.fillStyle = areaGrad;
        ctx.fill();

        // 线
        ctx.strokeStyle = PRIMARY_COLOR;
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.beginPath();
        weights.forEach((w, i) => {
          const px = xToPx(i);
          const py = yToPx(w);
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.stroke();

        // 数据点
        weights.forEach((w, i) => {
          const px = xToPx(i);
          const py = yToPx(w);
          ctx.fillStyle = '#fff';
          ctx.beginPath();
          ctx.arc(px, py, 4, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = PRIMARY_COLOR;
          ctx.beginPath();
          ctx.arc(px, py, 3, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      // 每个数据点的数值标签
      ctx.fillStyle = '#1F2A2A';
      ctx.font = 'bold 10px sans-serif';
      ctx.textAlign = 'center';
      weights.forEach((w, i) => {
        const px = xToPx(i);
        const py = yToPx(w);
        ctx.fillText(formatNumber(w), px, py - 8);
      });

      // X 轴日期标签
      ctx.fillStyle = TEXT_COLOR;
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      data.forEach((d, i) => {
        const label = d.record_date.slice(5);
        const px = xToPx(i);
        ctx.fillText(label, px, height - 8);
      });
    });
}

// 切换图表类型时重绘
watch(chartType, () => {
  nextTick(() => drawChart());
});

function computeCache() {
  try {
    const info = uni.getStorageInfoSync();
    const kb = info.currentSize || 0;
    cacheSize.value = kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;
  } catch {
    cacheSize.value = '-';
  }
}

async function saveWeight() {
  const weightNum = parseFloat(newWeight.value);
  if (!Number.isFinite(weightNum) || weightNum <= 0) {
    uni.showToast({ title: '请输入有效体重', icon: 'none' });
    return;
  }
  saving.value = true;
  uni.showLoading({ title: '保存中...' });
  try {
    const payload = {
      record_date: weightDate.value,
      record_time: weightTime.value,
      weight_kg: weightNum,
      note: weightNote.value.trim(),
    };
    if (editingWeightId.value) await weightApi.update(editingWeightId.value, payload);
    else await weightApi.create(payload);
    resetWeightForm();
    await loadWeight();
    await userStore.fetchMe().catch(() => {});
    uni.showToast({ title: '已记录', icon: 'success' });
    if (isWeightAction.value) {
      setTimeout(() => {
        const pages = getCurrentPages();
        if (pages.length > 1) {
          uni.navigateBack();
        } else {
          uni.reLaunch({ url: '/pages/home/index' });
        }
      }, 600);
    }
  } catch (e: any) {
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  } finally {
    uni.hideLoading();
    saving.value = false;
  }
}

function resetWeightForm() {
  editingWeightId.value = null;
  newWeight.value = '';
  weightDate.value = today();
  weightTime.value = formatTime(new Date());
  weightNote.value = '';
}

function editWeight(item: WeightRecord) {
  const form = weightRecordToForm(item);
  editingWeightId.value = item.id;
  newWeight.value = form.weight;
  weightDate.value = form.date;
  weightTime.value = form.time;
  weightNote.value = form.note;
  uni.pageScrollTo({ selector: '.input-card', duration: 250 });
}

function removeWeight(item: WeightRecord) {
  uni.showModal({ title: '删除体重记录', content: `确定删除 ${item.record_date} 的 ${item.weight_kg} kg 记录？`, success: async ({ confirm }) => {
    if (!confirm) return;
    await weightApi.remove(item.id);
    if (editingWeightId.value === item.id) resetWeightForm();
    await loadWeight();
    await userStore.fetchMe().catch(() => {});
  }});
}

function goAgreement(type: 'agreement' | 'privacy') {
  uni.navigateTo({ url: `/pages/mine/agreement?type=${type}` });
}

function clearCache() {
  uni.showModal({
    title: '清除缓存',
    content: '将清除所有本地缓存（token 除外），确定吗？',
    success: async (r) => {
      if (r.confirm) {
        clearAllCache();
        uni.showToast({ title: '已清除', icon: 'success' });
        computeCache();
      }
    },
  });
}

function confirmDeleteData() {
  showDeleteData.value = true;
}

async function deleteData() {
  showDeleteData.value = false;
  uni.showLoading({ title: '处理中...' });
  try {
    await userStore.deleteData();
    userStore.reset();
    dietStore.$reset();
    trainingStore.$reset();
    newWeight.value = '';
    latestWeight.value = null;
    weightHistory.value = [];
    uni.showToast({ title: '已删除', icon: 'success' });
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}

function confirmCancel() {
  showCancel.value = true;
}

async function cancelAccount() {
  showCancel.value = false;
  uni.showLoading({ title: '处理中...' });
  try {
    await userStore.cancelAccount();
    userStore.reset();
    dietStore.$reset();
    trainingStore.$reset();
    auth.logout();
    uni.showToast({ title: '已注销', icon: 'success' });
    setTimeout(() => uni.reLaunch({ url: '/pages/login/onboarding' }), 800);
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  } finally {
    uni.hideLoading();
  }
}
</script>

<style lang="scss" scoped>
.account-page {
  background: $bg;
  padding: $gap-3;
  min-height: 100vh;
}
.section {
  margin-bottom: $gap-3;
}
.section-title {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
  margin-bottom: $gap-2;
  padding-left: $gap-1;
}

.weight-only-page {
  display: flex;
  flex-direction: column;
  gap: $gap-3;
}

.hero-card {
  padding: $gap-4 $gap-3;
}
.hero-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $gap-4;
}
.hero-label {
  font-size: $fs-sm;
  color: $text-3;
  margin-bottom: 6rpx;
}
.hero-weight {
  font-size: 72rpx;
  font-weight: 800;
  color: $text-1;
  line-height: 1.1;
  letter-spacing: -2rpx;
}
.hero-unit {
  font-size: $fs-lg;
  font-weight: 500;
  color: $text-3;
  margin-left: 8rpx;
}
.hero-date {
  font-size: $fs-sm;
  color: $text-3;
  margin-top: 8rpx;
}
.change-pill {
  font-size: $fs-sm;
  font-weight: 600;
  padding: 8rpx 16rpx;
  border-radius: $r-pill;
  &.down {
    color: $primary;
    background: $primary-tint;
  }
  &.up {
    color: $warn;
    background: rgba(255, 200, 120, 0.2);
  }
  &.flat {
    color: $text-3;
    background: $bg-2;
  }
}
.hero-meta {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding-top: $gap-3;
  border-top: 1rpx solid $divider;
}
.meta-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
}
.meta-label {
  font-size: $fs-xs;
  color: $text-3;
}
.meta-value {
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
}
.meta-divider {
  width: 1rpx;
  height: 48rpx;
  background: $divider;
}

.chart-card {
  padding: $gap-3;
}
.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $gap-2;
}
.chart-title {
  font-size: $fs-md;
  font-weight: 600;
  color: $text-1;
}
.chart-toggle {
  display: flex;
  gap: 8rpx;
}
.chart-body {
  position: relative;
  height: 300rpx;
  width: 100%;
}
.chart-canvas {
  width: 100%;
  height: 300rpx;
}
.chart-empty {
  height: 300rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $gap-2;
  color: $text-3;
  font-size: $fs-sm;
}

.input-card {
  padding: $gap-4 $gap-3;
  text-align: center;
}
.input-label {
  font-size: $fs-sm;
  color: $text-3;
  margin-bottom: $gap-2;
}
.input-row {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 12rpx;
}
.weight-input {
  font-size: 72rpx;
  font-weight: 700;
  color: $text-1;
  text-align: center;
  width: 260rpx;
  min-height: 90rpx;
}
.input-unit {
  font-size: $fs-xl;
  color: $text-3;
  font-weight: 500;
}
.projected-change {
  margin-top: $gap-2;
  font-size: $fs-sm;
  color: $text-2;
}
.save-actions {
  margin-top: $gap-4;
}

.weight-section {
  border-radius: $r-24;
  &.highlight {
    animation: weight-highlight 600ms ease-out;
  }
}

@keyframes weight-highlight {
  0% { background-color: rgba(91, 200, 154, 0); }
  50% { background-color: rgba(91, 200, 154, 0.3); }
  100% { background-color: rgba(91, 200, 154, 0); }
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $gap-1 0;
  border-bottom: 1rpx solid $divider;
  &:last-of-type { border-bottom: none; }
}
.label {
  color: $text-2;
  font-size: $fs-sm;
}
.value {
  color: $text-1;
  font-size: $fs-md;
}
.form-row {
  display: flex;
  align-items: center;
  padding: $gap-2 0;
  border-top: 1rpx solid $divider;
  margin-top: $gap-2;
  gap: $gap-2;
}
.input {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  text-align: right;
}
.weight-actions {
  margin-top: $gap-2;
}
.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: $gap-2;
}
.record-count { margin-left: 8rpx; color: $text-3; font-size: $fs-xs; font-weight: 500; }
.expand-action { color: $primary-deep; font-size: $fs-sm; font-weight: 600; }
.edit-action, .danger-text {
  padding: 10rpx 16rpx;
  border-radius: $r-pill;
  font-size: $fs-sm;
  font-weight: 600;
}
.edit-action { color: $primary-deep; background: $primary-tint; }
.danger-text { color: $danger; background: rgba(242, 101, 101, .08); }
.grouped-title { margin-top: $gap-4; }

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
  &.disabled {
    opacity: 0.5;
    pointer-events: none;
  }
}
.mi-icon {
  margin-right: $gap-2;
  flex-shrink: 0;
}
.mi-label {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  &.danger { color: $danger; font-weight: 600; }
}
.mi-value {
  color: $text-3;
  font-size: $fs-sm;
}
.mi-arrow {
  color: $text-3;
  font-size: $fs-lg;
}

.danger-section {
  margin-top: $gap-4;
}
</style>
