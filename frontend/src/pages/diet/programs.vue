<template>
  <view class="page">
    <view class="hero"><text class="eyebrow">饮食方案</text><text class="title">选一个能长期执行的节奏</text><text class="sub">方案只提供饮食建议；不符合条件时仍可正常记录饮食。</text></view>
    <view v-if="activeProgram" class="current-card" @tap="openCurrent"><text class="current-kicker">当前使用中</text><text class="current-name">{{ activeProgram.template_name }}</text><text class="current-meta">{{ activeProgram.stage.calories_kcal }} kcal · C {{ activeProgram.stage.carbs_g }}g · P {{ activeProgram.stage.protein_g }}g · F {{ activeProgram.stage.fat_g }}g</text><text class="current-manage">查看今日执行 ›</text></view>
    <view v-if="loading" class="state">加载中…</view>
    <view v-else class="list">
      <view v-for="item in templates" :key="item.code" class="card" @tap="open(item.code)">
        <view><text class="name">{{ item.name }}</text><text class="desc">{{ item.description }}</text></view>
        <view class="tag">{{ activeProgram?.template_code === item.code ? '当前使用中' : (item.rules.strict ? '严格执行' : '可灵活调整') }}</view>
        <text class="arrow">›</text>
      </view>
    </view>
    <view class="notice">未满 18 岁、孕哺期、糖尿病或有严重肝肾胆疾病/进食障碍史，请仅使用普通饮食记录并咨询医生或营养师。</view>
  </view>
</template>
<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app';
import { ref } from 'vue';
import { dietProgramApi, type ActiveDietProgram, type DietProgramCode, type DietTemplate } from '@/api/diet-programs';
const templates = ref<DietTemplate[]>([]); const activeProgram = ref<ActiveDietProgram | null>(null); const loading = ref(true);
async function load() { loading.value = true; try { const [templateResult, active] = await Promise.all([dietProgramApi.templates(), dietProgramApi.active()]); templates.value = templateResult.items; activeProgram.value = active; } catch (e: any) { uni.showToast({ title: e?.message || '加载失败', icon: 'none' }); } finally { loading.value = false; } }
function open(code: DietProgramCode) { uni.navigateTo({ url: `/pages/diet/program-setup?code=${code}` }); }
function openCurrent() { if (activeProgram.value) uni.navigateTo({ url: `/pages/diet/meal-plan?programId=${activeProgram.value.id}&name=${encodeURIComponent(activeProgram.value.template_name)}` }); }
onShow(load);
</script>
<style scoped lang="scss">.page{min-height:100vh;padding:32rpx;background:linear-gradient(155deg,#effbf5,#fff9ee)}.hero{padding:24rpx 8rpx 28rpx;display:flex;flex-direction:column;gap:12rpx}.eyebrow{color:#35a875;font-size:24rpx;font-weight:700}.title{font-size:48rpx;font-weight:800;color:#1d3028}.sub,.desc,.notice{font-size:26rpx;color:#718078;line-height:1.6}.current-card{margin-bottom:24rpx;padding:28rpx;border-radius:26rpx;background:#163e2c;color:#fff;display:flex;flex-direction:column;gap:8rpx}.current-kicker{font-size:23rpx;color:#9be1bf}.current-name{font-size:36rpx;font-weight:800}.current-meta{font-size:24rpx;color:#c8ead9}.current-manage{margin-top:4rpx;font-size:25rpx;color:#9be1bf}.list{display:flex;flex-direction:column;gap:20rpx}.card{position:relative;padding:30rpx 92rpx 30rpx 28rpx;background:#fff;border-radius:28rpx;box-shadow:0 10rpx 32rpx rgba(36,99,72,.08);display:flex;flex-direction:column;gap:12rpx}.name{font-size:34rpx;font-weight:750;color:#21332b}.tag{font-size:22rpx;color:#269063;background:#e8f8ef;padding:6rpx 14rpx;border-radius:999rpx;align-self:flex-start}.arrow{position:absolute;right:30rpx;top:50%;font-size:48rpx;color:#59b88b}.notice{margin:36rpx 8rpx;padding:22rpx;background:rgba(255,255,255,.7);border-radius:18rpx}.state{padding:80rpx;text-align:center;color:#718078}</style>
