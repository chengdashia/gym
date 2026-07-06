// ECharts 主题与基础工具
export const chartTheme = {
  primary: '#5BC89A',
  primarySoft: '#C5ECDB',
  primaryDeep: '#3FA67C',
  accent: '#FFD79A',
  warm: '#FF8A65',
  info: '#6BA8D6',
  purple: '#C490E0',
  text1: '#1F2A2A',
  text2: '#5C6B6A',
  text3: '#8FA3A1',
  divider: '#E6ECEA',
  grid: '#EEF4F1',
};

export function baseLineOption() {
  return {
    color: [chartTheme.primary, chartTheme.accent, chartTheme.info, chartTheme.purple],
    textStyle: { color: chartTheme.text2, fontSize: 11 },
    legend: {
      icon: 'circle',
      bottom: 0,
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: chartTheme.text2, fontSize: 11 },
    },
    grid: { left: 36, right: 16, top: 24, bottom: 36 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: chartTheme.divider,
      borderWidth: 1,
      textStyle: { color: chartTheme.text1, fontSize: 11 },
    },
    xAxis: {
      type: 'category',
      axisLine: { lineStyle: { color: chartTheme.divider } },
      axisLabel: { color: chartTheme.text3, fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: chartTheme.text3, fontSize: 10 },
      splitLine: { lineStyle: { color: chartTheme.grid, type: 'dashed' } },
    },
  };
}