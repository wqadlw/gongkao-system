<template>
  <div class="dashboard">
    <PageHeader
      title="首页看板"
      subtitle="你的公考备考驾驶舱：考试倒计时 · 数据概览 · 薄弱考点洞察"
      icon="DataLine"
    />

    <!-- 倒计时横幅 -->
    <div class="countdown-banner" v-if="exams.length > 0">
      <div
        v-for="exam in exams.slice(0, 2)"
        :key="exam.id"
        class="countdown-card"
        :class="examGrad(exam.exam_type)"
      >
        <div class="cd-content">
          <div class="cd-label">{{ exam.name }}</div>
          <div class="cd-number" v-if="!exam.is_passed">
            {{ exam.days_left }}<span class="cd-unit">天</span>
          </div>
          <div class="cd-number passed" v-else>已结束</div>
          <div class="cd-date">{{ exam.exam_date }}</div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="gk-grid gk-grid-4">
      <div class="stat-card primary">
        <div class="stat-icon">📝</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.total_questions || 0 }}</div>
          <div class="stat-label">总题量</div>
        </div>
      </div>
      <div class="stat-card danger">
        <div class="stat-icon">⚠️</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.total_errors || 0 }}</div>
          <div class="stat-label">错题数</div>
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.total_mastered || 0 }}</div>
          <div class="stat-label">已掌握</div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">⏰</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.due_today || 0 }}</div>
          <div class="stat-label">今日待复习</div>
        </div>
      </div>
    </div>

    <!-- 今日复习进度 + 掌握度趋势 -->
    <div class="gk-row">
      <GkCard title="🔄 今日复习进度">
        <div class="review-progress">
          <el-progress
            type="circle"
            :percentage="reviewPct"
            :width="118"
            :stroke-width="10"
            :color="reviewPct >= 100 ? 'var(--success)' : 'var(--primary)'"
          />
          <div class="rp-meta">
            <div class="rp-line">今日已复习 <b>{{ (stats.review_progress && stats.review_progress.done_today) || 0 }}</b> 题</div>
            <div class="rp-line rp-sub">待复习 {{ stats.due_today }} 题 · 可复习 {{ (stats.review_progress && stats.review_progress.reviewable) || 0 }} 题</div>
            <el-button v-if="stats.due_today > 0" type="primary" size="small" @click="$router.push('/review')">去复习</el-button>
            <div v-else class="rp-done">🎉 今日无待复习</div>
          </div>
        </div>
      </GkCard>

      <GkCard title="📈 掌握度趋势（近 7 天）">
        <div v-if="hasTrendData" class="trend-spark">
          <svg viewBox="0 0 280 80" class="spark" preserveAspectRatio="none">
            <polyline :points="sparkPoints" fill="none" stroke="var(--primary)" stroke-width="2.5" stroke-linejoin="round" />
            <circle v-for="(p, i) in sparkDots" :key="i" :cx="p.x" :cy="p.y" r="3.5" fill="var(--primary)" />
          </svg>
          <div class="spark-labels">
            <span v-for="(t, i) in (stats.mastery_trend || [])" :key="i">{{ t.date }}</span>
          </div>
        </div>
        <EmptyState v-else icon="📊" title="暂无复习记录" desc="开始复习后，这里会显示掌握度随时间的提升曲线。" />
      </GkCard>
    </div>

    <!-- 最近录入 -->
    <GkCard title="🆕 最近录入">
      <div v-if="stats.recent_questions && stats.recent_questions.length" class="recent-list">
        <a
          v-for="r in stats.recent_questions"
          :key="r.id"
          class="recent-item"
          :href="'/question/' + r.id"
          @click.prevent="$router.push('/question/' + r.id)"
        >
          <span class="recent-dot" :style="modStyle(r.module)"></span>
          <span class="recent-main">
            <span class="recent-title">{{ r.title }}</span>
            <span class="recent-sub">{{ r.create_time }} · {{ r.sub_point || '—' }}</span>
          </span>
          <span class="recent-lv" :class="r.master_level >= 4 ? 'ok' : (r.is_error ? 'err' : '')">L{{ r.master_level }}</span>
        </a>
      </div>
      <EmptyState v-else icon="📥" title="还没有题目" desc="去「题目录入」粘贴 AI 解析，开始构建你的题库。" />
    </GkCard>

    <!-- 模块概览 + 薄弱点 -->
    <div class="gk-row">
      <GkCard title="六大模块概览">
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
      </GkCard>

      <GkCard title="🎯 薄弱考点 TOP5">
        <div v-if="stats.weak_points && stats.weak_points.length > 0">
          <div v-for="(wp, i) in stats.weak_points" :key="i" class="weak-item">
            <div class="weak-rank">{{ i + 1 }}</div>
            <div class="weak-info">
              <div class="weak-name">{{ wp.level3 }} / {{ wp.level4 }}</div>
              <div class="weak-detail">{{ wp.total }}题 · 掌握度 {{ wp.avg_mastery }}/5 · {{ wp.error }}错</div>
            </div>
          </div>
        </div>
        <EmptyState v-else icon="🌱" title="暂无薄弱点" desc="开始录入题目并标记掌握度后，这里会显示最值得攻克的考点。" />
      </GkCard>
    </div>

    <!-- 快捷操作 -->
    <GkCard title="🚀 快捷操作">
      <div class="gk-grid gk-grid-4 quick-actions">
        <button class="quick-btn primary" @click="$router.push('/question-input')">
          <span class="qb-icon">✏️</span>
          <span>录入新题</span>
        </button>
        <button class="quick-btn success" @click="$router.push('/review')">
          <span class="qb-icon">🔄</span>
          <span>开始复习</span>
        </button>
        <button class="quick-btn warning" @click="$router.push('/errors')">
          <span class="qb-icon">⚠️</span>
          <span>错题重做</span>
        </button>
        <button class="quick-btn info" @click="$router.push('/visualization')">
          <span class="qb-icon">📈</span>
          <span>查看大屏</span>
        </button>
      </div>
    </GkCard>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { statsApi, examApi } from '../api'
import { modStyle } from '../utils/constants'

const stats = ref({})
const exams = ref([])

// 考试类型 → 装饰渐变（集中管理，避免组件内硬编码 hex）
const EXAM_GRAD = {
  '国考': 'gk-grad-indigo',
  '省考': 'gk-grad-rose',
  '事业单位': 'gk-grad-teal',
  '选调生': 'gk-grad-primary',
  '遴选': 'gk-grad-primary',
}
function examGrad(t) {
  return EXAM_GRAD[t] || 'gk-grad-primary'
}

// 今日复习进度百分比
const reviewPct = computed(() => {
  const rp = stats.value.review_progress || {}
  const due = rp.due || 0
  const done = rp.done_today || 0
  if (due === 0) return done > 0 ? 100 : 0
  return Math.min(100, Math.round(done / due * 100))
})

// 掌握度趋势迷你图（SVG sparkline，跳过无数据的天）
const sparkPoints = computed(() => {
  const arr = (stats.value.mastery_trend || []).map(t => t.mastery)
  const pts = arr.map((m, i) => {
    const x = 20 + i * 40
    return m == null ? null : `${x},${70 - (m / 5) * 60}`
  }).filter(Boolean)
  return pts.join(' ')
})
const sparkDots = computed(() => {
  const arr = (stats.value.mastery_trend || [])
  return arr.map((t, i) => ({ x: 20 + i * 40, y: t.mastery == null ? null : 70 - (t.mastery / 5) * 60 })).filter(d => d.y != null)
})
const hasTrendData = computed(() => (stats.value.mastery_trend || []).some(t => t.mastery != null))

async function loadData() {
  try {
    const [statsRes, examRes] = await Promise.all([
      statsApi.dashboard(),
      examApi.getList()
    ])
    stats.value = statsRes.data
    exams.value = examRes.data.filter(e => !e.is_passed).slice(0, 2)
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

.countdown-banner {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.countdown-card {
  border-radius: var(--radius-lg);
  padding: 24px;
  position: relative;
  overflow: hidden;
  color: white;
}
.countdown-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
  border-radius: 50%;
}
.cd-content { position: relative; z-index: 1; }
.cd-label { font-size: 14px; opacity: 0.9; margin-bottom: 8px; }
.cd-number {
  font-size: 48px; font-weight: 800; line-height: 1;
  text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
.cd-number.passed { font-size: 28px; opacity: 0.7; }
.cd-unit { font-size: 18px; font-weight: 400; margin-left: 4px; }
.cd-date { font-size: 13px; opacity: 0.8; margin-top: 8px; }

.stat-card {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-light);
}
.stat-icon {
  font-size: 32px;
  width: 56px; height: 56px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md);
}
.stat-card.primary .stat-icon { background: var(--primary-bg); }
.stat-card.danger .stat-icon { background: var(--danger-bg); }
.stat-card.success .stat-icon { background: var(--success-bg); }
.stat-card.warning .stat-icon { background: var(--warning-bg); }
.stat-num { font-size: 28px; font-weight: 700; color: var(--text-primary); }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

.module-bar { margin-bottom: 12px; }
.module-info {
  display: flex; justify-content: space-between;
  margin-bottom: 6px; font-size: 13px;
}
.module-name { font-weight: 500; color: var(--text-primary); }
.module-stats { color: var(--text-secondary); }
.text-danger { color: var(--danger); }
.text-success { color: var(--success); }
.progress-bar { height: 6px; background: var(--bg-subtle); border-radius: 3px; overflow: hidden; }
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 3px; transition: width 0.3s;
}

.weak-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid var(--border-light);
}
.weak-item:last-child { border-bottom: none; }
.weak-rank {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--danger); color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.weak-info { flex: 1; }
.weak-name { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.weak-detail { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

.quick-btn {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 20px; border: none; border-radius: var(--radius-md);
  cursor: pointer; font-size: 14px; font-weight: 500;
  transition: all 0.2s; color: white;
}
.quick-btn.primary { background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); }
.quick-btn.success { background: linear-gradient(135deg, #10b981 0%, #34d399 100%); }
.quick-btn.warning { background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%); }
.quick-btn.info { background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%); }
.quick-btn:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.qb-icon { font-size: 28px; }

/* 今日复习进度 */
.review-progress { display: flex; align-items: center; gap: 20px; }
.rp-meta { flex: 1; min-width: 0; }
.rp-line { font-size: 14px; color: var(--text-primary); }
.rp-line b { font-size: 22px; color: var(--primary); margin-right: 2px; }
.rp-sub { font-size: 12px; color: var(--text-secondary); margin: 4px 0 10px; }
.rp-done { font-size: 14px; color: var(--success); font-weight: 600; padding: 8px 0; }

/* 掌握度趋势 sparkline */
.trend-spark { padding: 6px 0; }
.spark { width: 100%; height: 80px; display: block; }
.spark-labels {
  display: flex; justify-content: space-between;
  font-size: 10px; color: var(--text-tertiary); margin-top: 2px; padding: 0 10px;
}

/* 最近录入 */
.recent-list { display: flex; flex-direction: column; gap: 8px; }
.recent-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: var(--radius-md);
  background: var(--bg-subtle); text-decoration: none; color: inherit;
  transition: all 0.15s; border: 1px solid transparent;
}
.recent-item:hover { border-color: var(--primary); background: var(--primary-bg); transform: translateX(2px); }
.recent-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.recent-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.recent-title { font-size: 13.5px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recent-sub { font-size: 12px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recent-lv {
  flex-shrink: 0; font-size: 12px; font-weight: 700;
  padding: 3px 9px; border-radius: 999px;
  background: var(--bg-elevated); color: var(--text-secondary); border: 1px solid var(--border-base);
}
.recent-lv.ok { color: var(--success); border-color: var(--success-bg); background: var(--success-bg); }
.recent-lv.err { color: var(--danger); border-color: var(--danger-bg); background: var(--danger-bg); }

@media (max-width: 720px) {
  .countdown-banner { grid-template-columns: 1fr; }
}
</style>
