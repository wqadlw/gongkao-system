<template>
  <div class="dashboard">
    <!-- 倒计时横幅 -->
    <div class="countdown-banner" v-if="exams.length > 0">
      <div
        v-for="(exam, i) in exams" :key="exam.id"
        class="countdown-card animate__animated animate__fadeInUp animate__faster"
        :class="exam.exam_type"
        :style="{ animationDelay: i * 80 + 'ms' }"
      >
        <div class="cd-type-chip"><el-icon><Timer /></el-icon> {{ exam.exam_type }}</div>
        <div class="cd-content">
          <div class="cd-label">{{ exam.name }}</div>
          <div class="cd-number" v-if="!exam.is_passed">{{ exam.days_left }}<span class="cd-unit">天</span></div>
          <div class="cd-number passed" v-else>已结束</div>
          <div class="cd-date"><el-icon><Calendar /></el-icon> {{ exam.exam_date }}</div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div
        v-for="(s, i) in statCards" :key="s.label"
        class="stat-card animate__animated animate__fadeInUp animate__faster"
        :class="s.type"
        :style="{ animationDelay: 100 + i * 60 + 'ms' }"
        @click="$router.push(s.to)"
      >
        <div class="stat-icon"><el-icon><component :is="s.icon" /></el-icon></div>
        <div class="stat-body">
          <div class="stat-num">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- 主体三栏：趋势(宽) + 快捷操作(侧) -->
    <div class="main-grid">
      <div class="card trend-card">
        <div class="card-header">
          <h3><el-icon><TrendCharts /></el-icon> 近 30 天录入趋势</h3>
          <span class="trend-sum" v-if="trendTotal">累计 {{ trendTotal }} 题</span>
        </div>
        <div class="card-body">
          <VChart class="trend-chart" :option="trendOption" autoresize />
        </div>
      </div>

      <div class="card quick-card">
        <div class="card-header">
          <h3><el-icon><Promotion /></el-icon> 快捷操作</h3>
        </div>
        <div class="card-body quick-list">
          <button class="quick-row primary" @click="$router.push('/question-input')">
            <span class="qb-icon"><el-icon><EditPen /></el-icon></span>
            <span class="qb-text"><b>录入新题</b><i>截图解析，结构化入库</i></span>
            <el-icon class="qb-arrow"><ArrowRight /></el-icon>
          </button>
          <button class="quick-row success" @click="$router.push('/review')">
            <span class="qb-icon"><el-icon><RefreshRight /></el-icon></span>
            <span class="qb-text"><b>开始复习</b><i>{{ stats.due_today || 0 }} 题正在等你</i></span>
            <el-icon class="qb-arrow"><ArrowRight /></el-icon>
          </button>
          <button class="quick-row warning" @click="$router.push('/errors')">
            <span class="qb-icon"><el-icon><Warning /></el-icon></span>
            <span class="qb-text"><b>错题重做</b><i>{{ stats.total_errors || 0 }} 道错题</i></span>
            <el-icon class="qb-arrow"><ArrowRight /></el-icon>
          </button>
          <button class="quick-row info" @click="$router.push('/question-bank')">
            <span class="qb-icon"><el-icon><Notebook /></el-icon></span>
            <span class="qb-text"><b>真题库</b><i>2962 份历年试卷</i></span>
            <el-icon class="qb-arrow"><ArrowRight /></el-icon>
          </button>
        </div>
      </div>
    </div>

    <!-- 模块概览 + 薄弱点 -->
    <div class="dual-row">
      <div class="card">
        <div class="card-header">
          <h3><el-icon><Histogram /></el-icon> 六大模块概览</h3>
        </div>
        <div class="card-body">
          <div v-for="(data, module) in stats.modules" :key="module" class="module-bar">
            <div class="module-info">
              <span class="module-name">{{ module }}</span>
              <span class="module-stats">
                {{ data.total }}题 · <span class="text-danger">{{ data.error }}错</span> · <span class="text-success">{{ data.mastered }}掌握</span>
              </span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: data.total > 0 ? (data.mastered / data.total * 100) + '%' : '0%' }"></div>
            </div>
          </div>
          <div v-if="!stats.modules || Object.keys(stats.modules).length === 0" class="empty">暂无数据，开始录入题目吧</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3><el-icon><Aim /></el-icon> 薄弱考点 TOP5</h3>
        </div>
        <div class="card-body">
          <div v-if="stats.weak_points && stats.weak_points.length > 0">
            <div v-for="(wp, i) in stats.weak_points" :key="i" class="weak-item">
              <div class="weak-rank">{{ i + 1 }}</div>
              <div class="weak-info">
                <div class="weak-name">{{ wp.level3 }} / {{ wp.level4 }}</div>
                <div class="weak-detail">{{ wp.total }}题 · 掌握度 {{ wp.avg_mastery }}/5 · {{ wp.error }}错</div>
              </div>
              <el-icon class="weak-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
          <div v-else class="empty">暂无数据，开始录入题目吧</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi, examApi } from '../api'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const stats = ref({})
const exams = ref([])
const trend = ref([])

const statCards = computed(() => [
  { type: 'primary', icon: 'EditPen', value: stats.value.total_questions || 0, label: '总题量', to: '/question-list' },
  { type: 'danger', icon: 'Warning', value: stats.value.total_errors || 0, label: '错题数', to: '/errors' },
  { type: 'success', icon: 'CircleCheckFilled', value: stats.value.total_mastered || 0, label: '已掌握', to: '/visualization' },
  { type: 'warning', icon: 'Timer', value: stats.value.due_today || 0, label: '今日待复习', to: '/review' },
])

const trendTotal = computed(() => trend.value.reduce((s, d) => s + (d.count || 0), 0))

const trendOption = computed(() => ({
  grid: { left: 8, right: 16, top: 24, bottom: 8, containLabel: true },
  tooltip: {
    trigger: 'axis',
    formatter: (params) => `${params[0].name}<br/><b>${params[0].value}</b> 题`,
  },
  xAxis: {
    type: 'category',
    data: trend.value.map(d => d.date),
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisTick: { show: false },
    axisLabel: { color: '#94a3b8', fontSize: 10, interval: 5 },
  },
  yAxis: {
    type: 'value',
    minInterval: 1,
    axisLabel: { color: '#94a3b8', fontSize: 10 },
    splitLine: { lineStyle: { color: '#f1f5f9' } },
  },
  series: [{
    type: 'line',
    data: trend.value.map(d => d.count),
    smooth: true,
    symbol: 'circle',
    symbolSize: 5,
    showSymbol: false,
    lineStyle: { width: 2.5, color: '#4f46e5' },
    itemStyle: { color: '#4f46e5' },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(79,70,229,0.28)' },
          { offset: 1, color: 'rgba(79,70,229,0.02)' },
        ],
      },
    },
  }],
}))

async function loadData() {
  try {
    const [statsRes, examRes, trendRes] = await Promise.all([
      statsApi.dashboard(),
      examApi.getList(),
      statsApi.trend(30),
    ])
    stats.value = statsRes.data
    exams.value = examRes.data.filter(e => !e.is_passed).slice(0, 2)
    trend.value = trendRes.data.trend || []
  } catch (e) {
    console.error(e)
  }
}

onMounted(loadData)
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ===== 倒计时横幅 ===== */
.countdown-banner {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.countdown-card {
  border-radius: var(--radius-lg);
  padding: 22px 24px;
  position: relative;
  overflow: hidden;
  color: #fff;
  box-shadow: var(--shadow-md);
}
.countdown-card.国考 {
  background: linear-gradient(130deg, #4f46e5 0%, #6d28d9 60%, #7c3aed 100%);
}
.countdown-card.省考 {
  background: linear-gradient(130deg, #0ea5e9 0%, #0891b2 60%, #06b6d4 100%);
}
.countdown-card::before {
  content: '';
  position: absolute;
  top: -60%;
  right: -12%;
  width: 240px;
  height: 240px;
  background: radial-gradient(circle, rgba(255,255,255,0.18) 0%, transparent 70%);
  border-radius: 50%;
}
.countdown-card::after {
  content: '';
  position: absolute;
  left: 0; bottom: 0;
  width: 100%; height: 56px;
  background: repeating-linear-gradient(-45deg, rgba(255,255,255,0.05) 0 2px, transparent 2px 14px);
  pointer-events: none;
}
.cd-type-chip {
  position: absolute;
  top: 16px; right: 16px;
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.18);
  backdrop-filter: blur(4px);
  z-index: 1;
}
.cd-content { position: relative; z-index: 1; }
.cd-label {
  font-size: 13px;
  opacity: 0.88;
  margin-bottom: 10px;
}
.cd-number {
  font-size: 46px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1px;
}
.cd-number.passed { font-size: 26px; opacity: 0.75; }
.cd-unit { font-size: 16px; font-weight: 400; margin-left: 4px; opacity: 0.9; }
.cd-date {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12.5px;
  opacity: 0.85;
  margin-top: 10px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.12);
}

/* ===== 统计卡片 ===== */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.stat-card {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}
.stat-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
}
.stat-icon .el-icon { font-size: 26px; }
.stat-card.primary .stat-icon { background: var(--primary-bg); color: var(--primary); }
.stat-card.danger .stat-icon { background: var(--danger-bg); color: var(--danger); }
.stat-card.success .stat-icon { background: var(--success-bg); color: var(--success); }
.stat-card.warning .stat-icon { background: var(--warning-bg); color: var(--warning); }
.stat-num { font-size: 28px; font-weight: 700; color: var(--text-primary); line-height: 1.1; }
.stat-card.primary .stat-num { color: var(--primary-dark); }
.stat-card.danger .stat-num { color: var(--danger); }
.stat-card.success .stat-num { color: var(--success); }
.stat-card.warning .stat-num { color: var(--warning); }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

/* ===== 趋势 + 快捷操作 ===== */
.main-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  align-items: stretch;
}
.card {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
  overflow: hidden;
}
.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-header h3 { margin: 0; font-size: 15px; font-weight: 600; color: var(--text-primary); }
.card-body { padding: 16px 20px; }
.trend-sum { font-size: 12px; color: var(--text-tertiary); }
.trend-chart { width: 100%; height: 220px; }

.quick-list { display: flex; flex-direction: column; gap: 10px; }
.quick-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  cursor: pointer;
  text-align: left;
  transition: all 0.18s;
  color: inherit;
  width: 100%;
}
.quick-row:hover {
  transform: translateX(3px);
  border-color: var(--border-base);
  box-shadow: var(--shadow-sm);
}
.qb-icon {
  width: 40px; height: 40px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border-radius: 10px;
}
.qb-icon .el-icon { font-size: 20px; }
.quick-row.primary .qb-icon { background: var(--primary-bg); color: var(--primary); }
.quick-row.success .qb-icon { background: var(--success-bg); color: var(--success); }
.quick-row.warning .qb-icon { background: var(--warning-bg); color: var(--warning); }
.quick-row.info .qb-icon { background: var(--info-bg); color: var(--info); }
.qb-text { flex: 1; display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.qb-text b { font-size: 13.5px; color: var(--text-primary); }
.qb-text i { font-style: normal; font-size: 12px; color: var(--text-tertiary); }
.qb-arrow { color: var(--text-tertiary); font-size: 14px; }

/* ===== 模块概览 + 薄弱点 ===== */
.dual-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.module-bar { margin-bottom: 14px; }
.module-bar:last-child { margin-bottom: 0; }
.module-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}
.module-name { font-weight: 500; color: var(--text-primary); }
.module-stats { color: var(--text-secondary); }
.text-danger { color: var(--danger); }
.text-success { color: var(--success); }
.progress-bar {
  height: 6px;
  background: var(--bg-subtle);
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 3px;
  transition: width 0.4s ease;
}

.weak-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light);
}
.weak-item:last-child { border-bottom: none; }
.weak-rank {
  width: 24px; height: 24px;
  border-radius: 50%;
  background: var(--danger-bg);
  color: var(--danger);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
  flex-shrink: 0;
}
.weak-info { flex: 1; min-width: 0; }
.weak-name { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.weak-detail { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.weak-arrow { color: var(--text-tertiary); font-size: 14px; }

.empty {
  text-align: center;
  color: var(--text-tertiary);
  padding: 20px;
  font-size: 14px;
}

@media (max-width: 900px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dual-row, .countdown-banner, .main-grid { grid-template-columns: 1fr; }
}
</style>
