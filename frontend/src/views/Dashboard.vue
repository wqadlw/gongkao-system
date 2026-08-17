<template>
  <div class="dashboard">
    <!-- 倒计时横幅 -->
    <div class="countdown-banner" v-if="exams.length > 0">
      <div v-for="exam in exams.slice(0, 2)" :key="exam.id" class="countdown-card" :class="exam.exam_type">
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
    <div class="stat-grid">
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

    <!-- 模块概览 + 薄弱点 -->
    <div class="dual-row">
      <div class="card">
        <div class="card-header">
          <h3>📊 六大模块概览</h3>
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
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3>🎯 薄弱考点 TOP5</h3>
        </div>
        <div class="card-body">
          <div v-if="stats.weak_points && stats.weak_points.length > 0">
            <div v-for="(wp, i) in stats.weak_points" :key="i" class="weak-item">
              <div class="weak-rank">{{ i + 1 }}</div>
              <div class="weak-info">
                <div class="weak-name">{{ wp.level3 }} / {{ wp.level4 }}</div>
                <div class="weak-detail">{{ wp.total }}题 · 掌握度 {{ wp.avg_mastery }}/5 · {{ wp.error }}错</div>
              </div>
            </div>
          </div>
          <div v-else class="empty">暂无数据，开始录入题目吧</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="card">
      <div class="card-header">
        <h3>🚀 快捷操作</h3>
      </div>
      <div class="card-body">
        <div class="quick-actions">
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { statsApi, examApi } from '../api'

const stats = ref({})
const exams = ref([])

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
.countdown-card.国考 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.countdown-card.省考 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
.cd-content {
  position: relative;
  z-index: 1;
}
.cd-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}
.cd-number {
  font-size: 48px;
  font-weight: 800;
  line-height: 1;
  text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
.cd-number.passed {
  font-size: 28px;
  opacity: 0.7;
}
.cd-unit {
  font-size: 18px;
  font-weight: 400;
  margin-left: 4px;
}
.cd-date {
  font-size: 13px;
  opacity: 0.8;
  margin-top: 8px;
}

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
}
.stat-icon {
  font-size: 32px;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
}
.stat-card.primary .stat-icon { background: var(--primary-bg); }
.stat-card.danger .stat-icon { background: var(--danger-bg); }
.stat-card.success .stat-icon { background: var(--success-bg); }
.stat-card.warning .stat-icon { background: var(--warning-bg); }
.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}
.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.dual-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
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
}
.card-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.card-body {
  padding: 16px 20px;
}

.module-bar {
  margin-bottom: 12px;
}
.module-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
}
.module-name {
  font-weight: 500;
  color: var(--text-primary);
}
.module-stats {
  color: var(--text-secondary);
}
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
  transition: width 0.3s;
}

.weak-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light);
}
.weak-item:last-child {
  border-bottom: none;
}
.weak-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--danger);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.weak-info {
  flex: 1;
}
.weak-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.weak-detail {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.empty {
  text-align: center;
  color: var(--text-tertiary);
  padding: 20px;
  font-size: 14px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.quick-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  color: white;
}
.quick-btn.primary { background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); }
.quick-btn.success { background: linear-gradient(135deg, #10b981 0%, #34d399 100%); }
.quick-btn.warning { background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%); }
.quick-btn.info { background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%); }
.quick-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
.qb-icon {
  font-size: 28px;
}
</style>
