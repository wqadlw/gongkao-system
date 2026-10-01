<template>
  <div class="review-page">
    <div class="page-header">
      <div>
        <h2><el-icon><Refresh /></el-icon> 智能复习中心</h2>
        <p class="sub">
          FSRS 记忆调度
          <span class="engine-badge" :class="{ on: engine === 'FSRS' }">{{ engineBadge }}</span>
          · 空格翻面 · 1/2/3/4 评分
          <el-link type="primary" :underline="false" class="opt-link" @click="openOptimize">
            <el-icon><MagicStick /></el-icon> 优化参数
          </el-link>
        </p>
      </div>
      <div class="mode-tabs">
        <button :class="['tab', { active: mode === 'due' }]" @click="switchMode('due')">今日待复习</button>
        <button :class="['tab', { active: mode === 'overdue' }]" @click="switchMode('overdue')">逾期题目</button>
        <button :class="['tab', { active: mode === 'all' }]" @click="switchMode('all')">全部题目</button>
      </div>
    </div>

    <!-- 状态条 -->
    <div class="stat-strip">
      <div class="chip"><b>{{ dueList.length }}</b><i>队列</i></div>
      <div class="chip warn"><b>{{ reviewStats.due_today || 0 }}</b><i>今日到期</i></div>
      <div class="chip ok"><b>{{ reviewStats.mastered || 0 }}</b><i>已掌握</i></div>
      <div class="chip bad"><b>{{ reviewStats.overdue || 0 }}</b><i>逾期</i></div>
      <div class="chip done" v-if="sessionDone"><b>{{ sessionDone }}</b><i>本轮已复习</i></div>
    </div>

    <!-- 刷卡区 -->
    <div v-if="currentQuestion" class="review-card" :key="currentQuestion.id">
      <div class="review-header">
        <div class="rh-left">
          <span class="mod-tag" :style="modStyle(currentQuestion.level1)">{{ currentQuestion.level1 }}</span>
          <span class="review-cat">{{ catPath(currentQuestion) }}</span>
        </div>
        <div class="review-progress">{{ currentIndex + 1 }} <i>/ {{ dueList.length }}</i></div>
      </div>

      <div class="progress-track"><div class="progress-fill" :style="{ width: (currentIndex / Math.max(dueList.length, 1) * 100) + '%' }"></div></div>

      <div class="review-question md-body" v-html="md(currentQuestion.question_raw || '（无题干）')"></div>

      <div class="review-answer" :class="{ opened: showAnswer }">
        <button class="answer-toggle" @click="showAnswer = true" v-if="!showAnswer">
          <el-icon><View /></el-icon> 显示答案与解析 <kbd>Space</kbd>
        </button>
        <div v-else class="answer-section">
          <div class="answer-line">
            <span class="al-label">正确答案</span>
            <span class="answer-badge">{{ currentQuestion.answer || '—' }}</span>
            <span v-if="currentQuestion.sub_point" class="sub-point">{{ currentQuestion.sub_point }}</span>
          </div>
          <div v-if="currentQuestion.break_logic" class="a-section logic"><div class="a-label">破题逻辑</div><div class="md-body" v-html="md(currentQuestion.break_logic)"></div></div>
          <div v-if="currentQuestion.normal_solve" class="a-section"><div class="a-label">通用解法</div><div class="md-body" v-html="md(currentQuestion.normal_solve)"></div></div>
          <div v-if="currentQuestion.quick_solve" class="a-section quick"><div class="a-label">速算技巧</div><div class="md-body" v-html="md(currentQuestion.quick_solve)"></div></div>
          <div v-if="currentQuestion.step_detail" class="a-section"><div class="a-label">详细步骤</div><div class="md-body" v-html="md(currentQuestion.step_detail)"></div></div>
          <button class="link-btn" @click="goDetail(currentQuestion.id)">查看完整解析与笔记 →</button>
        </div>
      </div>

      <div class="review-actions">
        <button class="review-btn again" :disabled="!showAnswer" @click="submitReview('again')">
          完全忘记 <kbd>1</kbd>
        </button>
        <button class="review-btn hard" :disabled="!showAnswer" @click="submitReview('hard')">
          困难 <kbd>2</kbd>
        </button>
        <button class="review-btn good" :disabled="!showAnswer" @click="submitReview('good')">
          良好 <kbd>3</kbd>
        </button>
        <button class="review-btn easy" :disabled="!showAnswer" @click="submitReview('easy')">
          简单 <kbd>4</kbd>
        </button>
      </div>
      <p class="rate-hint" v-if="!showAnswer">先自己作答，再翻面对照；评分会由 FSRS 计算下次复习时间</p>
    </div>

    <!-- 完成 / 空态 -->
    <div v-else class="empty-state">
      <template v-if="sessionDone">
        <div class="empty-icon ok"><el-icon><CircleCheckFilled /></el-icon></div>
        <div class="empty-text">本轮复习完成！共 {{ sessionDone }} 题</div>
        <div class="empty-sub">FSRS 已按你的作答更新每题的下次复习时间</div>
      </template>
      <template v-else>
        <div class="empty-icon"><el-icon><CircleCheckFilled /></el-icon></div>
        <div class="empty-text">复习队列已清空</div>
        <div class="empty-sub">保持节奏，继续录入与复习！</div>
      </template>
      <div class="empty-btns">
        <button class="btn-primary" @click="switchMode('all')">复习全部题目</button>
        <button class="btn-default" @click="$router.push('/question-input')">录入新题</button>
      </div>
    </div>

    <!-- FSRS 参数优化对话框 -->
    <el-dialog v-model="optVisible" title="FSRS 参数个性化优化" width="620px">
      <p class="opt-desc">
        基于你的复习日志训练专属 FSRS 权重（官方 Rust 实现，本地训练不上传任何数据）。
        复习记录越多，参数越贴合你的记忆规律。
      </p>
      <el-alert
        v-if="optResult && !optResult.ok"
        type="warning" :title="optResult.message" :closable="false" show-icon
      />
      <template v-if="optResult && optResult.ok">
        <el-result icon="success" :title="optResult.message" />
        <div class="opt-params">
          <div class="opt-col">
            <div class="opt-col-title">默认参数</div>
            <code>{{ fmtParams(optResult.old_parameters) }}</code>
          </div>
          <div class="opt-col">
            <div class="opt-col-title">你的专属参数</div>
            <code class="opt-new">{{ fmtParams(optResult.new_parameters) }}</code>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="optVisible = false">关闭</el-button>
        <el-button type="primary" :loading="optimizing" @click="runOptimize">开始优化</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
const engine = ref('legacy')
const sessionDone = ref(0)
const optVisible = ref(false)
const optimizing = ref(false)
const optResult = ref(null)
const customParams = ref(false)

const engineBadge = computed(() => {
  if (engine.value !== 'FSRS') return '未启用'
  return customParams.value ? '已启用 · 个性化参数' : '已启用 · 默认参数'
})

function fmtParams(params) {
  if (!Array.isArray(params)) return '—'
  return params.map(p => Number(p).toFixed(2)).join(', ')
}

function openOptimize() {
  optResult.value = null
  optVisible.value = true
}

async function runOptimize() {
  optimizing.value = true
  try {
    const res = await reviewApi.optimize()
    optResult.value = res.data
    if (res.data.ok) {
      customParams.value = true
      ElMessage.success('参数已生效，后续复习将使用个性化权重')
    }
  } catch {
    ElMessage.error('优化失败，请检查后端日志')
  } finally {
    optimizing.value = false
  }
}

async function loadDue() {
  let res
  if (mode.value === 'overdue') res = await reviewApi.getOverdue()
  else if (mode.value === 'all') res = await reviewApi.getDue(300)
  else res = await reviewApi.getDue(100)
  dueList.value = res.data
  currentIndex.value = 0
  currentQuestion.value = dueList.value[0] || null
  showAnswer.value = false
  sessionDone.value = 0
  const [statsRes, engineRes] = await Promise.all([reviewApi.getStats(), reviewApi.engine()])
  reviewStats.value = statsRes.data
  engine.value = engineRes.data.engine
  customParams.value = !!engineRes.data.custom_parameters
}

function switchMode(m) {
  mode.value = m
  loadDue()
}

async function submitReview(result) {
  if (!currentQuestion.value) return
  try {
    const res = await reviewApi.submit({
      question_id: currentQuestion.value.id,
      review_result: result,
      cost_time: 0,
    })
    sessionDone.value++
    const label = { again: '完全忘记', hard: '困难', good: '良好', easy: '简单' }[result]
    const days = res.data.days_until_next
    const nextText = days >= 1 ? `${Math.round(days)} 天后` : days > 0 ? `${Math.round(days * 24 * 60)} 分钟后` : '稍后'
    ElMessage.success(`${label} · 下次复习：${nextText}${res.data.engine === 'FSRS' ? '（FSRS）' : ''}`)
    currentIndex.value++
    if (currentIndex.value < dueList.value.length) {
      currentQuestion.value = dueList.value[currentIndex.value]
      showAnswer.value = false
    } else {
      currentQuestion.value = null
    }
    const statsRes = await reviewApi.getStats()
    reviewStats.value = statsRes.data
  } catch {
    ElMessage.error('提交失败')
  }
}

function onKeydown(e) {
  if (!currentQuestion.value) return
  const tag = (e.target && e.target.tagName) || ''
  if (tag === 'INPUT' || tag === 'TEXTAREA') return
  if (e.code === 'Space') {
    e.preventDefault()
    if (!showAnswer.value) showAnswer.value = true
    return
  }
  if (!showAnswer.value) return
  const map = { Digit1: 'again', Digit2: 'hard', Digit3: 'good', Digit4: 'easy' }
  if (map[e.code]) {
    e.preventDefault()
    submitReview(map[e.code])
  }
}

function goDetail(id) {
  router.push('/question/' + id)
}

onMounted(() => {
  if (route.query.mode === 'error') mode.value = 'all'
  loadDue()
  window.addEventListener('keydown', onKeydown)
})
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.review-page { max-width: 860px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.page-header .sub { margin: 4px 0 0; font-size: 12.5px; color: var(--text-tertiary); display: flex; align-items: center; gap: 6px; }
.engine-badge { font-size: 11px; padding: 1px 8px; border-radius: 999px; background: var(--bg-subtle); color: var(--text-tertiary); }
.engine-badge.on { background: var(--success-bg); color: var(--success); }
.opt-link { font-size: 12px; margin-left: 4px; vertical-align: baseline; }
.opt-link .el-icon { font-size: 12px; vertical-align: -0.15em; }
.opt-desc { font-size: 13px; color: var(--text-secondary); margin: 0 0 12px; line-height: 1.7; }
.opt-params { display: flex; gap: 12px; }
.opt-col { flex: 1; background: var(--bg-subtle); border-radius: var(--radius-md); padding: 10px 12px; }
.opt-col-title { font-size: 12px; color: var(--text-tertiary); font-weight: 700; margin-bottom: 6px; }
.opt-col code { font-size: 11.5px; line-height: 1.8; word-break: break-all; display: block; color: var(--text-secondary); }
.opt-col code.opt-new { color: var(--primary); font-weight: 600; }
.mode-tabs { display: flex; gap: 4px; background: var(--bg-subtle); padding: 4px; border-radius: var(--radius-md); }
.tab { padding: 6px 16px; border: none; background: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; color: var(--text-secondary); }
.tab.active { background: var(--primary); color: white; }

/* 状态条 */
.stat-strip { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.chip {
  display: flex; align-items: baseline; gap: 5px;
  background: var(--bg-elevated); border: 1px solid var(--border-light);
  border-radius: 999px; padding: 5px 14px;
}
.chip b { font-size: 17px; font-weight: 700; color: var(--primary); }
.chip i { font-style: normal; font-size: 12px; color: var(--text-secondary); }
.chip.warn b { color: var(--warning); }
.chip.ok b { color: var(--success); }
.chip.bad b { color: var(--danger); }
.chip.done { background: var(--primary-bg); border-color: transparent; }
.chip.done b { color: var(--primary-dark); }

/* 卡片 */
.review-card {
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  padding: 26px;
  box-shadow: var(--shadow-md);
  animation: pop 0.25s ease;
}
@keyframes pop { from { opacity: 0; transform: translateY(8px) scale(0.99); } to { opacity: 1; transform: none; } }

.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.rh-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.mod-tag { font-size: 12px; font-weight: 700; padding: 3px 12px; border-radius: 999px; border: 1px solid transparent; flex-shrink: 0; }
.review-cat { font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.review-progress { font-weight: 700; font-size: 16px; color: var(--primary); flex-shrink: 0; }
.review-progress i { font-style: normal; font-size: 12px; color: var(--text-tertiary); font-weight: 400; }

.progress-track { height: 4px; background: var(--bg-subtle); border-radius: 2px; overflow: hidden; margin-bottom: 18px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--primary), var(--primary-light)); transition: width 0.3s; }

.review-question {
  font-size: 15px; line-height: 1.85;
  padding: 18px;
  background: var(--bg-subtle);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}

.review-answer { margin-bottom: 20px; }
.answer-toggle {
  width: 100%; padding: 13px; border: 1px dashed var(--border-base); border-radius: var(--radius-md);
  background: var(--bg-base); color: var(--primary); font-weight: 600; cursor: pointer; font-size: 14px;
  transition: all 0.15s;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.answer-toggle:hover { border-color: var(--primary); background: var(--primary-bg); }
.answer-toggle kbd, .review-btn kbd {
  font-family: inherit; font-size: 11px; padding: 1px 7px; border-radius: 4px;
  background: rgba(79,70,229,0.1); color: var(--primary); border: 1px solid rgba(79,70,229,0.2);
}
.answer-section { padding: 16px; background: var(--bg-subtle); border-radius: var(--radius-md); animation: pop 0.2s ease; }
.answer-line { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.al-label { font-size: 13px; color: var(--text-secondary); }
.answer-badge { background: var(--success); color: #fff; font-weight: 700; padding: 3px 14px; border-radius: 4px; font-size: 18px; }
.sub-point { font-size: 12px; color: var(--text-secondary); background: var(--bg-elevated); padding: 3px 10px; border-radius: 999px; border: 1px solid var(--border-light); }
.a-section { margin-bottom: 12px; padding-left: 12px; border-left: 3px solid var(--border-base); }
.a-section.logic { border-left-color: var(--primary); }
.a-section.quick { border-left-color: var(--success); }
.a-label { font-size: 12px; color: var(--text-tertiary); font-weight: 700; margin-bottom: 5px; }
.link-btn { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 13px; padding: 4px 0; }

/* 评分区 */
.review-actions { display: flex; justify-content: center; gap: 12px; flex-wrap: wrap; }
.review-btn {
  padding: 12px 22px; border: none; border-radius: var(--radius-md); cursor: pointer;
  font-size: 14px; font-weight: 500; color: white;
  display: flex; align-items: center; gap: 8px;
  transition: transform 0.12s, opacity 0.12s;
}
.review-btn:hover:not(:disabled) { transform: translateY(-2px); opacity: 0.92; }
.review-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.review-btn.again { background: var(--danger); }
.review-btn.hard { background: var(--warning); }
.review-btn.good { background: var(--primary); }
.review-btn.easy { background: var(--success); }
.review-btn kbd { background: rgba(255,255,255,0.22); color: #fff; border-color: rgba(255,255,255,0.3); }
.rate-hint { text-align: center; font-size: 12px; color: var(--text-tertiary); margin: 12px 0 0; }

/* 空态 */
.empty-state {
  text-align: center; padding: 60px 20px;
  background: var(--bg-elevated); border-radius: var(--radius-lg); border: 1px solid var(--border-light);
}
.empty-icon { font-size: 60px; color: var(--text-tertiary); }
.empty-icon.ok { color: var(--success); }
.empty-text { font-size: 18px; font-weight: 600; margin-top: 12px; }
.empty-sub { font-size: 14px; color: var(--text-tertiary); margin-top: 4px; }
.empty-btns { display: flex; gap: 10px; justify-content: center; margin-top: 18px; }
.btn-primary { background: var(--primary); color: #fff; border: none; padding: 10px 22px; border-radius: var(--radius-md); cursor: pointer; font-size: 14px; font-weight: 500; }
.btn-primary:hover { background: var(--primary-dark); }
.btn-default { background: var(--bg-elevated); color: var(--text-primary); border: 1px solid var(--border-base); padding: 10px 22px; border-radius: var(--radius-md); cursor: pointer; font-size: 14px; }
</style>
