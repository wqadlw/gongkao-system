<template>
  <div class="review-page">
    <div class="page-header">
      <div>
        <h2>🔄 智能复习中心</h2>
        <p class="sub">按记忆曲线复习，掌握一类题目的思路与技巧</p>
      </div>
      <div class="mode-tabs">
        <button :class="['tab', { active: mode === 'due' }]" @click="switchMode('due')">今日待复习</button>
        <button :class="['tab', { active: mode === 'overdue' }]" @click="switchMode('overdue')">逾期题目</button>
        <button :class="['tab', { active: mode === 'all' }]" @click="switchMode('all')">全部题目</button>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-card primary"><div class="stat-num">{{ dueList.length }}</div><div class="stat-label">队列题目</div></div>
      <div class="stat-card warning"><div class="stat-num">{{ reviewStats.due_today || 0 }}</div><div class="stat-label">今日到期</div></div>
      <div class="stat-card success"><div class="stat-num">{{ reviewStats.mastered || 0 }}</div><div class="stat-label">已掌握</div></div>
      <div class="stat-card danger"><div class="stat-num">{{ reviewStats.overdue || 0 }}</div><div class="stat-label">逾期</div></div>
    </div>

    <div v-if="currentQuestion" class="review-card" :key="currentQuestion.id">
      <div class="review-header">
        <div class="rh-left">
          <span class="mod-tag" :style="modStyle(currentQuestion.level1)">{{ currentQuestion.level1 }}</span>
          <span class="review-cat">{{ catPath(currentQuestion) }}</span>
        </div>
        <div class="review-progress">{{ currentIndex + 1 }} / {{ dueList.length }}</div>
      </div>

      <div class="progress-track"><div class="progress-fill" :style="{ width: ((currentIndex) / Math.max(dueList.length, 1) * 100) + '%' }"></div></div>

      <div class="review-question">
        <div class="q-label">📝 题目</div>
        <div class="q-text md-body" v-html="md(currentQuestion.question_raw || '（无题干）')"></div>
      </div>

      <div class="review-answer" :class="{ opened: showAnswer }">
        <button class="answer-toggle" @click="showAnswer = !showAnswer">
          {{ showAnswer ? '🙈 收起答案与解析' : '👁️ 点击查看答案与解析' }}
        </button>
        <div v-if="showAnswer" class="answer-section">
          <div class="answer-line">
            <span class="al-label">正确答案</span>
            <span class="answer-badge">{{ currentQuestion.answer }}</span>
          </div>
          <div v-if="currentQuestion.sub_point" class="a-section"><div class="a-label">细分考点</div><div class="md-body" v-html="md(currentQuestion.sub_point)"></div></div>
          <div v-if="currentQuestion.break_logic" class="a-section"><div class="a-label">破题逻辑</div><div class="md-body" v-html="md(currentQuestion.break_logic)"></div></div>
          <div v-if="currentQuestion.normal_solve" class="a-section"><div class="a-label">通用解法</div><div class="md-body" v-html="md(currentQuestion.normal_solve)"></div></div>
          <div v-if="currentQuestion.quick_solve" class="a-section success"><div class="a-label">速算技巧</div><div class="md-body" v-html="md(currentQuestion.quick_solve)"></div></div>
          <div v-if="currentQuestion.step_detail" class="a-section"><div class="a-label">详细步骤</div><div class="md-body" v-html="md(currentQuestion.step_detail)"></div></div>
          <div class="a-actions">
            <button class="link-btn" @click="goDetail(currentQuestion.id)">查看完整解析与笔记 →</button>
          </div>
        </div>
      </div>

      <div class="review-actions">
        <button class="review-btn again" @click="submitReview('again')">😵 完全忘记</button>
        <button class="review-btn hard" @click="submitReview('hard')">😣 困难</button>
        <button class="review-btn good" @click="submitReview('good')">😊 良好</button>
        <button class="review-btn easy" @click="submitReview('easy')">😎 简单</button>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">🎉</div>
      <div class="empty-text">复习队列已清空</div>
      <div class="empty-sub">保持节奏，继续录入与复习！</div>
      <button class="btn-primary" @click="$router.push('/question-input')">录入新题</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { reviewApi } from '../api'
import { renderMarkdown } from '../utils/md'
import { ElMessage } from 'element-plus'
import { modStyle } from '../utils/constants'

const md = renderMarkdown
const route = useRoute()
const router = useRouter()
function catPath(q) {
  return [q.level2, q.level3, q.level4, q.level5].filter(Boolean).join(' / ')
}

const mode = ref('due')
const dueList = ref([])
const currentIndex = ref(0)
const currentQuestion = ref(null)
const reviewStats = ref({})
const showAnswer = ref(false)

const current = () => dueList.value[currentIndex.value]

async function loadDue() {
  let res
  if (mode.value === 'overdue') res = await reviewApi.getOverdue()
  else if (mode.value === 'all') res = await reviewApi.getDue(300)
  else res = await reviewApi.getDue(100)
  dueList.value = res.data
  currentIndex.value = 0
  currentQuestion.value = dueList.value[0] || null
  showAnswer.value = false
  const statsRes = await reviewApi.getStats()
  reviewStats.value = statsRes.data
}

function switchMode(m) {
  mode.value = m
  loadDue()
}

async function submitReview(result) {
  if (!currentQuestion.value) return
  try {
    await reviewApi.submit({
      question_id: currentQuestion.value.id,
      review_result: result,
      cost_time: 0,
    })
    ElMessage.success(`已记录：${{ again: '完全忘记', hard: '困难', good: '良好', easy: '简单' }[result]}`)
    currentIndex.value++
    if (currentIndex.value < dueList.value.length) {
      currentQuestion.value = dueList.value[currentIndex.value]
      showAnswer.value = false
    } else {
      currentQuestion.value = null
      ElMessage.success('🎉 本轮复习完成！')
    }
    const statsRes = await reviewApi.getStats()
    reviewStats.value = statsRes.data
  } catch {
    ElMessage.error('提交失败')
  }
}

function goDetail(id) {
  router.push('/question/' + id)
}

onMounted(() => {
  if (route.query.mode === 'error') mode.value = 'all'
  loadDue()
})
</script>

<style scoped>
.review-page { max-width: 920px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.page-header .sub { margin: 4px 0 0; font-size: 13px; color: var(--text-tertiary); }
.mode-tabs { display: flex; gap: 4px; background: var(--bg-subtle); padding: 4px; border-radius: var(--radius-md); }
.tab { padding: 6px 16px; border: none; background: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; color: var(--text-secondary); }
.tab.active { background: var(--primary); color: white; }

.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: var(--bg-elevated); padding: 18px; border-radius: var(--radius-lg); text-align: center; border: 1px solid var(--border-light); }
.stat-num { font-size: 30px; font-weight: 800; }
.stat-card.primary .stat-num { color: var(--primary); }
.stat-card.warning .stat-num { color: var(--warning); }
.stat-card.success .stat-num { color: var(--success); }
.stat-card.danger .stat-num { color: var(--danger); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }

.review-card { background: var(--bg-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-light); padding: 24px; box-shadow: var(--shadow-sm); animation: pop 0.25s ease; }
@keyframes pop { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }

.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.rh-left { display: flex; align-items: center; gap: 10px; }
.mod-tag { font-size: 12px; font-weight: 700; padding: 3px 12px; border-radius: 999px; border: 1px solid transparent; }
.review-cat { font-size: 13px; color: var(--text-secondary); }
.review-progress { font-weight: 700; font-size: 15px; color: var(--primary); }

.progress-track { height: 4px; background: var(--bg-subtle); border-radius: 2px; overflow: hidden; margin-bottom: 16px; }
.progress-fill { height: 100%; background: var(--primary); transition: width 0.3s; }

.review-question { margin-bottom: 16px; }
.q-label { font-size: 12px; color: var(--text-tertiary); font-weight: 700; margin-bottom: 8px; }
.q-text { font-size: 15px; line-height: 1.8; padding: 16px; background: var(--bg-subtle); border-radius: var(--radius-md); }

.review-answer { margin-bottom: 20px; }
.answer-toggle {
  width: 100%; padding: 12px; border: 1px dashed var(--border-base); border-radius: var(--radius-md);
  background: var(--bg-base); color: var(--primary); font-weight: 600; cursor: pointer; font-size: 14px;
  transition: all 0.15s;
}
.answer-toggle:hover { border-color: var(--primary); background: var(--primary-bg); }
.answer-section { margin-top: 14px; padding: 16px; background: var(--bg-subtle); border-radius: var(--radius-md); animation: pop 0.2s ease; }
.answer-line { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.al-label { font-size: 13px; color: var(--text-secondary); }
.answer-badge { background: var(--success); color: #fff; font-weight: 700; padding: 3px 14px; border-radius: 4px; font-size: 18px; }
.a-section { margin-bottom: 12px; }
.a-label { font-size: 12px; color: var(--text-tertiary); font-weight: 700; margin-bottom: 5px; }
.a-section.success .a-label { color: var(--success); }
.a-actions { margin-top: 8px; }
.link-btn { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 13px; padding: 4px 0; }

.review-actions { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }
.review-btn { padding: 12px 22px; border: none; border-radius: var(--radius-md); cursor: pointer; font-size: 14px; font-weight: 500; color: white; transition: transform 0.12s, opacity 0.12s; }
.review-btn:hover { transform: translateY(-2px); opacity: 0.92; }
.review-btn.again { background: var(--danger); }
.review-btn.hard { background: var(--warning); }
.review-btn.good { background: var(--primary); }
.review-btn.easy { background: var(--success); }

.empty-state { text-align: center; padding: 60px 20px; background: var(--bg-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-light); }
.empty-icon { font-size: 60px; }
.empty-text { font-size: 18px; font-weight: 600; margin-top: 12px; }
.empty-sub { font-size: 14px; color: var(--text-tertiary); margin-top: 4px; margin-bottom: 16px; }
.btn-primary { background: var(--primary); color: #fff; border: none; padding: 10px 22px; border-radius: var(--radius-md); cursor: pointer; font-size: 14px; font-weight: 500; }
.btn-primary:hover { background: var(--primary-dark); }
</style>
