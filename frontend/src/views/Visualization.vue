<template>
  <div class="viz-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>📊 学习可视化大屏</h2>
        <p class="sub">薄弱点、掌握度与学习节奏一目了然</p>
      </div>
      <button class="btn-default" @click="loadAll">🔄 刷新</button>
    </div>

    <div class="stat-grid">
      <div class="stat-card primary"><div class="stat-num">{{ data.dashboard?.total_questions || 0 }}</div><div class="stat-label">总题量</div></div>
      <div class="stat-card danger"><div class="stat-num">{{ data.dashboard?.total_errors || 0 }}</div><div class="stat-label">错题数</div></div>
      <div class="stat-card success"><div class="stat-num">{{ data.dashboard?.total_mastered || 0 }}</div><div class="stat-label">已掌握</div></div>
      <div class="stat-card warning"><div class="stat-num">{{ data.dashboard?.due_today || 0 }}</div><div class="stat-label">今日待复习</div></div>
    </div>

    <div class="chart-grid">
      <div class="card">
        <div class="card-header"><h3>🎯 六大模块掌握度雷达</h3></div>
        <div class="card-body"><v-chart :option="radarOption" style="height: 360px" autoresize /></div>
      </div>
      <div class="card">
        <div class="card-header"><h3>📈 录入趋势（近30天）</h3></div>
        <div class="card-body"><v-chart :option="trendOption" style="height: 360px" autoresize /></div>
      </div>
    </div>

    <div class="chart-grid">
      <div class="card">
        <div class="card-header"><h3>⚠️ 错题分布（按模块）</h3></div>
        <div class="card-body"><v-chart :option="pieOption" style="height: 340px" autoresize /></div>
      </div>
      <div class="card">
        <div class="card-header"><h3>🔥 薄弱考点 TOP（越高越弱）</h3></div>
        <div class="card-body"><v-chart :option="weakOption" style="height: 340px" autoresize /></div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><h3>📅 学习日历热力图</h3></div>
      <div class="card-body">
        <v-chart :option="heatOption" style="height: 220px" autoresize />
        <div class="heatmap-legend">
          <span>少</span>
          <span class="legend-bar"></span>
          <span>多</span>
          <span class="legend-stat">共录入 <b>{{ heatTotal }}</b> 题 · 学习 <b>{{ heatDays }}</b> 天</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header"><h3>💡 个性化备考推荐</h3></div>
      <div class="card-body">
        <div class="recommend-list">
          <div v-for="(r, i) in (data.recommendation || [])" :key="i" class="recommend-item">
            <span class="rec-icon">{{ r.type === 'practice' ? '📝' : r.type === 'review' ? '🔄' : r.type === 'error_review' ? '⚠️' : '💡' }}</span>
            <span>{{ r.message }}</span>
          </div>
          <div v-if="!(data.recommendation || []).length" class="empty">暂无推荐，继续录入题目获取个性化建议</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, LineChart, PieChart, BarChart, HeatmapChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  CalendarComponent, VisualMapComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { statsApi } from '../api'

use([
  CanvasRenderer, RadarChart, LineChart, PieChart, BarChart, HeatmapChart,
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  CalendarComponent, VisualMapComponent,
])

const loading = ref(false)
const data = ref({})

// ECharts 画布无法解析 CSS 变量（var(--…)），必须读取为具体颜色值
function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return v || fallback
}
// 兼容后端聚合端点「数组」与「{key: [...]}」两种形状，避免图表因数据格式异常而空白
function norm(v, key) {
  if (v && !Array.isArray(v) && Array.isArray(v[key])) return v[key]
  return Array.isArray(v) ? v : []
}

const radarOption = computed(() => {
  const radar = norm(data.value.radar, 'radar')
  const indicators = radar.map(r => ({ name: r.module, max: 100 }))
  const values = radar.map(r => r.score)
  return {
    tooltip: {},
    radar: {
      indicator: indicators.length ? indicators : [{ name: '暂无', max: 100 }],
      radius: '62%',
      axisName: { color: cssVar('--text-secondary', '#64748b'), fontSize: 12 },
      splitArea: { areaStyle: { color: ['rgba(99,102,241,0.04)', 'rgba(99,102,241,0.08)'] } },
    },
    series: [{
      type: 'radar',
      data: [{ value: values, name: '掌握度', areaStyle: { color: 'rgba(99,70,229,0.25)' }, lineStyle: { color: '#4f46e5', width: 2 }, itemStyle: { color: '#4f46e5' } }],
    }],
  }
})

const trendOption = computed(() => {
  const trend = norm(data.value.trend, 'trend')
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: trend.map(t => t.date), axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: trend.map(t => t.count), itemStyle: { color: '#4f46e5', borderRadius: [4, 4, 0, 0] } }],
  }
})

const pieOption = computed(() => {
  const dist = norm(data.value.error_distribution, 'distribution')
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, type: 'scroll' },
    color: ['#ef4444', '#f59e0b', '#4f46e5', '#10b981', '#06b6d4', '#db2777'],
    series: [{
      type: 'pie', radius: ['42%', '70%'],
      data: dist.map(d => ({ name: d.name, value: d.value })),
      label: { formatter: '{b}: {c}' },
      itemStyle: { borderRadius: 6, borderColor: cssVar('--bg-elevated', '#ffffff'), borderWidth: 2 },
    }],
  }
})

const weakOption = computed(() => {
  const wp = (data.value.weak_points || []).slice().reverse()
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 10, right: 30, top: 10, bottom: 10, containLabel: true },
    xAxis: { type: 'value', max: 100 },
    yAxis: {
      type: 'category',
      data: wp.map(w => `${w.level3}/${w.level4}`),
      axisLabel: { fontSize: 11, width: 160, overflow: 'truncate' },
    },
    series: [{
      type: 'bar',
      data: wp.map(w => ({
        value: Math.round(w.weak_score),
        itemStyle: { color: w.weak_score > 60 ? '#ef4444' : w.weak_score > 35 ? '#f59e0b' : '#10b981', borderRadius: [0, 4, 4, 0] },
      })),
      label: { show: true, position: 'right', formatter: '{c}' },
    }],
  }
})

const heatDays = computed(() => (data.value.heatmap || []).filter(h => h.count > 0).length)
const heatTotal = computed(() => (data.value.heatmap || []).reduce((s, h) => s + h.count, 0))

const heatOption = computed(() => {
  const heat = data.value.heatmap || []
  const maxCount = heat.reduce((m, h) => Math.max(m, h.count), 0)
  const years = heat.map(h => h.date.slice(0, 4)).filter(Boolean)
  const year = years.length ? Math.max(...years.map(Number)) : new Date().getFullYear()
  const range = [`${year}-01-01`, `${year}-12-31`]
  return {
    tooltip: { formatter: (p) => `${p.value[0]}<br/>录入 ${p.value[1]} 题` },
    visualMap: {
      min: 0, max: Math.max(maxCount, 1), show: false,
      inRange: { color: ['#ebedf0', '#c7d2fe', '#818cf8', '#4f46e5', '#3730a3'] },
    },
    calendar: {
      top: 30, left: 30, right: 10, cellSize: ['auto', 16], range,
      itemStyle: { color: cssVar('--bg-subtle', '#f1f5f9'), borderWidth: 2, borderColor: cssVar('--bg-elevated', '#ffffff') },
      yearLabel: { show: false },
      monthLabel: { color: cssVar('--text-secondary', '#64748b') },
      dayLabel: { color: cssVar('--text-tertiary', '#94a3b8'), firstDay: 1 },
    },
    series: [{
      type: 'heatmap', coordinateSystem: 'calendar',
      data: heat.map(h => [h.date, h.count]),
    }],
  }
})

async function loadAll() {
  loading.value = true
  try {
    const res = await statsApi.all()
    data.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.viz-page { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.page-header .sub { margin: 4px 0 0; font-size: 13px; color: var(--text-tertiary); }

.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.stat-card { background: var(--bg-elevated); padding: 22px; border-radius: var(--radius-lg); text-align: center; border: 1px solid var(--border-light); }
.stat-num { font-size: 34px; font-weight: 800; }
.stat-card.primary .stat-num { color: var(--primary); }
.stat-card.danger .stat-num { color: var(--danger); }
.stat-card.success .stat-num { color: var(--success); }
.stat-card.warning .stat-num { color: var(--warning); }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

.chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card { background: var(--bg-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-light); margin-bottom: 16px; }
.card-header { padding: 16px 20px; border-bottom: 1px solid var(--border-light); }
.card-header h3 { margin: 0; font-size: 15px; font-weight: 600; }
.card-body { padding: 20px; }

.heatmap-legend { display: flex; align-items: center; gap: 8px; margin-top: 10px; font-size: 12px; color: var(--text-tertiary); }
.legend-bar { width: 120px; height: 10px; border-radius: 5px; background: linear-gradient(90deg, #ebedf0, #c7d2fe, #818cf8, #4f46e5, #3730a3); }
.legend-stat { margin-left: auto; }
.legend-stat b { color: var(--text-primary); }

.recommend-list { display: flex; flex-direction: column; gap: 8px; }
.recommend-item { display: flex; align-items: center; gap: 8px; padding: 10px 12px; background: var(--bg-subtle); border-radius: var(--radius-md); font-size: 13px; }
.rec-icon { font-size: 16px; }
.empty { text-align: center; color: var(--text-tertiary); padding: 20px; }

.btn-default { background: var(--bg-subtle); color: var(--text-secondary); border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; }
.btn-default:hover { background: var(--border-light); }
</style>
