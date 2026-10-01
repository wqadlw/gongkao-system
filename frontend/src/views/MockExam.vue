<template>
  <div class="mock-page">
    <div class="page-header">
      <div>
        <h2><el-icon><Stopwatch /></el-icon> 模考模式</h2>
        <p class="sub">限时整卷模拟 · 按模块计分 · 错题复盘</p>
      </div>
      <el-button v-if="view !== 'paper'" type="primary" @click="view = 'setup'">
        <el-icon><Plus /></el-icon> 新建模考
      </el-button>
    </div>

    <!-- 历史列表 -->
    <div v-if="view === 'history'" class="history-wrap">
      <div class="card">
        <div class="card-header"><h3>历史模考</h3></div>
        <div class="card-body">
          <table class="mock-table">
            <thead><tr><th>名称</th><th>日期</th><th>题数</th><th>得分</th><th>状态</th><th width="160">操作</th></tr></thead>
            <tbody>
              <tr v-for="m in history" :key="m.id">
                <td>{{ m.name }}</td>
                <td>{{ m.mock_date }}</td>
                <td>{{ m.question_total }}</td>
                <td><b>{{ m.graded ? m.total_score : '—' }}</b><span v-if="m.graded" class="dim"> / {{ m.question_total }}</span></td>
                <td>
                  <span class="badge" :class="m.graded ? 'ok' : 'doing'">{{ m.graded ? '已交卷' : '进行中' }}</span>
                </td>
                <td>
                  <button class="btn-default small" @click="m.graded ? openResult(m.id) : resumeMock(m.id)">
                    {{ m.graded ? '复盘' : '继续作答' }}
                  </button>
                  <button class="btn-icon danger" @click="removeMock(m.id)"><el-icon><Delete /></el-icon></button>
                </td>
              </tr>
              <tr v-if="history.length === 0"><td colspan="6" class="empty">还没有模考记录，点击右上角「新建模考」开始</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 组卷表单 -->
    <div v-if="view === 'setup'" class="setup-wrap">
      <div class="card">
        <div class="card-header"><h3>组卷设置</h3></div>
        <div class="card-body setup-body">
          <div class="form-row">
            <label>模考名称</label>
            <el-input v-model="setup.name" placeholder="留空自动命名" style="width: 260px" />
          </div>
          <div class="form-row">
            <label>组卷方式</label>
            <el-radio-group v-model="setup.mode">
              <el-radio value="modules">按模块随机抽题</el-radio>
              <el-radio value="source">按真题卷</el-radio>
            </el-radio-group>
          </div>
          <div v-if="setup.mode === 'modules'" class="form-row">
            <label>选择模块</label>
            <el-checkbox-group v-model="setup.modules">
              <el-checkbox v-for="m in MODULES" :key="m" :value="m">{{ m }}</el-checkbox>
            </el-checkbox-group>
          </div>
          <div v-if="setup.mode === 'source'" class="form-row">
            <label>真题卷来源</label>
            <el-input v-model="setup.source" placeholder="输入试卷名称（与题库 source 一致），如：2024年广东…" style="width: 420px" />
          </div>
          <div class="form-row">
            <label>题数</label>
            <el-input-number v-model="setup.count" :min="5" :max="135" :step="5" />
            <label class="gap">时长（分钟，0=自动）</label>
            <el-input-number v-model="setup.minutes" :min="0" :max="180" />
          </div>
          <div class="form-row actions">
            <el-button @click="view = 'history'">返回</el-button>
            <el-button type="primary" :loading="starting" @click="startMock">
              <el-icon><Stopwatch /></el-icon> 开始模考
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 答题界面 -->
    <div v-if="view === 'paper' && paper" class="paper-wrap">
      <div class="paper-top card">
        <div class="pt-left">
          <span class="paper-name">{{ paper.name }}</span>
          <span class="paper-count">{{ answeredCount }} / {{ paper.questions.length }} 已答</span>
        </div>
        <div class="pt-timer" :class="{ warn: remainSeconds < 300 }">
          <el-icon><Timer /></el-icon> {{ timerText }}
        </div>
        <el-button type="danger" @click="submitMock">交卷</el-button>
      </div>

      <div class="paper-body">
        <div class="card paper-question">
          <div class="pq-meta">
            <span class="res-type">{{ currentQuestion.module }}</span>
            <span class="pq-no">第 {{ currentQuestion.order_no }} 题</span>
          </div>
          <div class="pq-stem md-body" v-html="md(currentQuestion.question_raw)"></div>
          <div class="pq-nav">
            <el-button :disabled="currentIndex === 0" @click="currentIndex--">上一题</el-button>
            <el-button :disabled="currentIndex >= paper.questions.length - 1" @click="currentIndex++">下一题</el-button>
          </div>
        </div>

        <div class="card answer-sheet">
          <div class="as-title">答题卡</div>
          <div class="as-grid">
            <button
              v-for="(q, i) in paper.questions" :key="q.question_id"
              class="as-cell" :class="{ done: answers[q.question_id], current: i === currentIndex }"
              @click="currentIndex = i"
            >{{ q.order_no }}</button>
          </div>
          <div class="as-legend">
            <span class="dot done"></span>已作答
            <span class="dot"></span>未作答
          </div>
        </div>
      </div>
    </div>

    <!-- 成绩单 -->
    <div v-if="view === 'result' && result" class="result-wrap">
      <div class="card result-card">
        <div class="score-hero" :class="scoreLevel">
          <div class="sh-num">{{ result.correct }}<i> / {{ result.total }}</i></div>
          <div class="sh-label">正确率 {{ result.accuracy }}% · 用时 {{ result.duration_minutes }} 分钟</div>
        </div>
        <div class="module-table">
          <div v-for="m in result.modules" :key="m.module" class="module-row">
            <span class="module-name">{{ m.module }}</span>
            <span class="module-num">{{ m.correct }} / {{ m.total }}</span>
            <div class="progress-bar"><div class="progress-fill" :style="{ width: (m.correct / m.total * 100) + '%' }"></div></div>
          </div>
        </div>
        <div class="result-actions">
          <el-button @click="view = 'history'">返回列表</el-button>
          <el-button type="primary" @click="view = 'setup'">再来一次</el-button>
        </div>
      </div>

      <div class="card wrong-card">
        <div class="card-header"><h3>逐题复盘（{{ result.questions.length }} 题）</h3></div>
        <div class="card-body">
          <div v-for="q in result.questions" :key="q.question_id" class="wrong-item" :class="{ wrong: !q.is_correct }">
            <div class="wi-head">
              <span class="res-type" :class="q.is_correct ? 'ok' : 'bad'">{{ q.is_correct ? '✓' : '✗' }}</span>
              <span class="wi-no">第 {{ q.order_no }} 题 · {{ q.module }}</span>
              <span class="wi-answer">你的答案 <b :class="q.is_correct ? 'ok' : 'bad'">{{ q.selected || '未答' }}</b> · 正确答案 <b class="ok">{{ q.answer }}</b></span>
              <router-link :to="'/question/' + q.question_id" class="link">详情 →</router-link>
            </div>
            <div class="wi-stem md-body" v-html="md(q.question_raw)"></div>
            <div v-if="q.break_logic || q.normal_solve" class="wi-solve">
              <div v-if="q.break_logic" class="a-section logic"><div class="a-label">破题逻辑</div><div class="md-body" v-html="md(q.break_logic)"></div></div>
              <div v-else class="a-section"><div class="a-label">解析</div><div class="md-body" v-html="md(q.normal_solve)"></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mockApi } from '../api'
import { renderMarkdown } from '../utils/md'

const md = renderMarkdown
const MODULES = ['政治理论', '常识判断', '言语理解与表达', '数量关系', '判断推理', '资料分析']

const view = ref('history')
const history = ref([])
const setup = ref({ name: '', mode: 'modules', modules: ['判断推理', '资料分析'], source: '', count: 20, minutes: 0 })
const starting = ref(false)

const paper = ref(null)
const answers = ref({})
const currentIndex = ref(0)
const remainSeconds = ref(0)
const timerId = ref(null)

const result = ref(null)
const currentResultId = ref(0)

const currentQuestion = computed(() => paper.value ? paper.value.questions[currentIndex.value] : null)
const answeredCount = computed(() => Object.keys(answers.value).length)
const timerText = computed(() => {
  const s = Math.max(0, remainSeconds.value)
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
})
const scoreLevel = computed(() => {
  if (!result.value) return ''
  const acc = result.value.accuracy
  return acc >= 80 ? 'good' : acc >= 60 ? 'mid' : 'bad'
})

async function loadHistory() {
  try {
    const res = await mockApi.list()
    history.value = res.data.items
  } catch { ElMessage.error('模考列表加载失败') }
}

async function startMock() {
  starting.value = true
  try {
    const res = await mockApi.start({
      name: setup.value.name,
      modules: setup.value.mode === 'modules' ? setup.value.modules : [],
      source: setup.value.mode === 'source' ? setup.value.source : '',
      count: setup.value.count,
      minutes: setup.value.minutes,
    })
    paper.value = { mock_id: res.data.mock_id, name: res.data.name, questions: res.data.questions }
    answers.value = {}
    currentIndex.value = 0
    remainSeconds.value = res.data.duration_seconds
    view.value = 'paper'
    startTimer()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '组卷失败')
  } finally { starting.value = false }
}

function startTimer() {
  clearInterval(timerId.value)
  timerId.value = setInterval(() => {
    remainSeconds.value--
    if (remainSeconds.value <= 0) {
      clearInterval(timerId.value)
      ElMessage.warning('时间到，自动交卷')
      submitMock()
    }
  }, 1000)
}

async function resumeMock(id) {
  try {
    const res = await mockApi.paper(id)
    paper.value = { mock_id: id, name: res.data.name, questions: res.data.questions }
    answers.value = {}
    paper.value.questions.forEach(q => { if (q.selected) answers.value[q.question_id] = q.selected })
    currentIndex.value = 0
    remainSeconds.value = 15 * 60
    view.value = 'paper'
    startTimer()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '无法继续该模考')
    loadHistory()
  }
}

async function submitMock() {
  const payload = { answers: Object.entries(answers.value).map(([qid, selected]) => ({ question_id: Number(qid), selected })), duration_seconds: 0 }
  if (view.value === 'paper') {
    const ok = await ElMessageBox.confirm(`确认交卷？已答 ${answeredCount.value} / ${paper.value.questions.length} 题`, '交卷确认', { type: 'warning' }).catch(() => false)
    if (!ok) return
  }
  clearInterval(timerId.value)
  try {
    const res = await mockApi.submit(currentPaperId(), payload)
    await loadHistory()
    openResult(currentPaperId(), res.data.duration_seconds || 0)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '交卷失败')
  }
}

let durationSeconds = 0
function currentPaperId() { return paper.value?.mock_id }

function openResult(id, duration = 0) {
  currentResultId.value = id
  loadResult(id)
}

async function loadResult(id) {
  try {
    const res = await mockApi.result(id)
    result.value = { ...res.data }
    view.value = 'result'
  } catch { ElMessage.error('成绩加载失败') }
}

async function removeMock(id) {
  const ok = await ElMessageBox.confirm('删除该次模考记录？', '确认', { type: 'warning' }).catch(() => false)
  if (!ok) return
  await mockApi.remove(id)
  loadHistory()
}

onMounted(loadHistory)
onUnmounted(() => clearInterval(timerId.value))
</script>

<style scoped>
.mock-page { max-width: 1080px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; display: flex; align-items: center; gap: 8px; }
.page-header .sub { margin: 4px 0 0; font-size: 12.5px; color: var(--text-tertiary); }

.mock-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.mock-table th, .mock-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border-light); }
.mock-table th { color: var(--text-tertiary); font-weight: 600; }
.mock-table .dim { color: var(--text-tertiary); font-size: 12px; }
.badge { font-size: 11px; padding: 2px 10px; border-radius: 999px; }
.badge.ok { background: var(--success-bg); color: var(--success); }
.badge.doing { background: var(--warning-bg); color: var(--warning); }
.empty { text-align: center; color: var(--text-tertiary); padding: 24px 0; }

.setup-body { display: flex; flex-direction: column; gap: 16px; }
.form-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.form-row label { font-size: 13px; color: var(--text-secondary); min-width: 90px; }
.form-row label.gap { margin-left: 20px; }
.form-row.actions { justify-content: flex-end; }

.paper-top { display: flex; align-items: center; gap: 16px; padding: 12px 18px; margin-bottom: 14px; }
.pt-left { flex: 1; display: flex; align-items: center; gap: 12px; min-width: 0; }
.paper-name { font-weight: 700; }
.paper-count { font-size: 12.5px; color: var(--text-tertiary); }
.pt-timer {
  display: flex; align-items: center; gap: 6px; font-size: 20px; font-weight: 800;
  color: var(--primary); font-variant-numeric: tabular-nums;
}
.pt-timer.warn { color: var(--danger); animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0.55; } }

.paper-body { display: flex; gap: 14px; align-items: flex-start; }
.paper-question { flex: 1; min-width: 0; padding: 20px; }
.pq-meta { display: flex; gap: 10px; margin-bottom: 12px; }
.pq-no { font-weight: 700; font-size: 14px; color: var(--primary); }
.pq-stem { font-size: 14.5px; line-height: 1.8; }
.pq-nav { margin-top: 18px; display: flex; gap: 10px; }

.answer-sheet { width: 240px; flex-shrink: 0; padding: 14px; position: sticky; top: 16px; }
.as-title { font-size: 13px; font-weight: 700; margin-bottom: 10px; color: var(--text-primary); }
.as-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; }
.as-cell {
  padding: 7px 0; border: 1px solid var(--border-base); border-radius: var(--radius-sm);
  background: var(--bg-elevated); font-size: 12.5px; cursor: pointer; color: var(--text-secondary);
}
.as-cell.done { background: var(--primary); border-color: var(--primary); color: #fff; }
.as-cell.current { outline: 2px solid var(--primary); outline-offset: 1px; }
.as-legend { margin-top: 10px; font-size: 11.5px; color: var(--text-tertiary); display: flex; align-items: center; gap: 6px; }
.as-legend .dot { width: 10px; height: 10px; border-radius: 3px; background: var(--bg-elevated); border: 1px solid var(--border-base); display: inline-block; margin-left: 8px; }
.as-legend .dot.done { background: var(--primary); border-color: var(--primary); }

.score-hero { text-align: center; padding: 26px; border-radius: var(--radius-lg); color: #fff; margin-bottom: 18px; }
.score-hero.good { background: linear-gradient(135deg, #059669, #10b981); }
.score-hero.mid { background: linear-gradient(135deg, #2563eb, #0891b2); }
.score-hero.bad { background: linear-gradient(135deg, #dc2626, #f97316); }
.sh-num { font-size: 44px; font-weight: 800; line-height: 1; }
.sh-num i { font-size: 18px; font-style: normal; opacity: 0.85; }
.sh-label { margin-top: 8px; font-size: 13px; opacity: 0.9; }
.module-table { display: flex; flex-direction: column; gap: 10px; padding: 0 8px; }
.module-row { display: grid; grid-template-columns: 140px 70px 1fr; align-items: center; gap: 12px; }
.module-name { font-size: 13px; color: var(--text-primary); }
.module-num { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.progress-bar { height: 8px; background: var(--bg-subtle); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--primary), var(--primary-light)); }
.result-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }

.wrong-card { margin-top: 16px; }
.wrong-item { padding: 14px 0; border-bottom: 1px solid var(--border-light); }
.wrong-item.wrong { background: rgba(239, 68, 68, 0.03); }
.wi-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.res-type { font-size: 12px; font-weight: 700; padding: 2px 10px; border-radius: 999px; }
.res-type.ok { background: var(--success-bg); color: var(--success); }
.res-type.bad { background: var(--danger-bg); color: var(--danger); }
.wi-no { font-size: 12.5px; color: var(--text-tertiary); }
.wi-answer { font-size: 12.5px; color: var(--text-secondary); }
.wi-answer b.ok { color: var(--success); }
.wi-answer b.bad { color: var(--danger); }
.wi-stem { font-size: 13px; }
.wi-solve { margin-top: 8px; }
.a-section { padding-left: 12px; border-left: 3px solid var(--primary); margin-bottom: 8px; }
.a-label { font-size: 12px; color: var(--text-tertiary); font-weight: 700; margin-bottom: 4px; }
.link { font-size: 12.5px; color: var(--primary); text-decoration: none; margin-left: auto; }
</style>
