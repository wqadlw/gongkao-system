<template>
  <div class="deposit-page">
    <div class="page-header">
      <div>
        <h2>🔍 解析结果预览 · 核对并入库</h2>
        <p class="sub">核对题面与考点，勾选要沉淀的<strong>独立知识卡片</strong>，一并入库到题库、行测知识库、行测解题库</p>
      </div>
      <span class="badge">{{ mode === 'new' ? '🆕 新解析（未入库）' : (mode === 'existing' ? '已有题目' : '待处理') }} · 待处理 {{ totalPending }}</span>
    </div>

    <div class="main-grid">
      <!-- 左侧：待处理题目 -->
      <div class="left-panel">
        <div class="lp-head">
          <span>待处理题目</span>
          <router-link to="/question-input" class="lp-new">＋ 新录入</router-link>
        </div>
        <div class="q-list" v-loading="loadingList">
          <div v-if="!pendingQuestions.length" class="empty">暂无待处理</div>
          <div v-for="q in pendingQuestions" :key="q.id"
               :class="['q-item', { active: selectedQid === q.id }]"
               @click="openExisting(q)">
            <div class="q-item-main">
              <span class="q-mod" :style="{ background: modColor(q.level1), color: '#fff' }">{{ q.level1 || '未分类' }}</span>
              <span class="q-title">{{ q.card_title || stripQ(q.question_raw) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：预览 + 核对 -->
      <div class="right-panel">
        <!-- 空态 -->
        <div class="card" v-if="mode === 'empty'">
          <div class="card-body empty-state">
            <div class="es-icon">📭</div>
            <div>没有待核对的题目。请从左侧「待处理」选择，或去
              <router-link to="/question-input">题目录入</router-link>
              粘贴 AI 解析（点击「解析」即跳转到本页预览）。
            </div>
          </div>
        </div>

        <!-- 新解析草稿提示 -->
        <div class="draft-banner" v-if="mode === 'new'">
          <span class="db-ico">🆕</span>
          <span class="db-text">这是刚解析的<strong>未入库题目</strong>，请核对下方预览，勾选知识卡片后点「确认入库」。</span>
          <button class="btn-default small" @click="backToInput">返回修改</button>
          <button class="btn-default small" @click="discardDraft">放弃此题</button>
        </div>

        <div class="card" v-if="parsed">
          <div class="card-header">
            <div class="ch-head">
              <span class="ch-mod" :style="{ background: modColor(parsed.level1), color: '#fff' }">{{ parsed.level1 || '未识别模块' }}</span>
              <span class="ch-qtitle">{{ parsed.card_title || stripQ(parsed.question_raw) }}</span>
            </div>
            <div class="ch-actions">
              <label class="checkbox-label ch-err"><input type="checkbox" v-model="isError" /><span>标记为错题</span></label>
            </div>
          </div>

          <div class="card-body" v-loading="parsing">
            <!-- 题目 -->
            <div class="review-box">
              <div class="rb-label">📋 题目（核对题面）</div>
              <div class="rb-content md-body" v-html="md(parsed.question_raw || '')"></div>
            </div>

            <!-- 模块 & 考点路径 -->
            <div class="cat-path-box">
              <div class="cp-label">📂 题目将归类到</div>
              <div class="cp-path">
                <template v-for="(seg, i) in effectivePath" :key="i">
                  <span class="cp-seg">{{ seg }}</span>
                  <span v-if="i < effectivePath.length - 1" class="cp-sep">/</span>
                </template>
                <span v-if="!effectivePath.length" class="cp-empty">未识别到考点路径（AI 未给出考点定位）</span>
              </div>
              <div class="cp-source" :class="manualLevels ? 'manual' : 'auto'">
                {{ manualLevels ? '来源：手动校正' : '来源：AI 自动识别' }}
                <button class="link-btn" @click="showTreePicker = !showTreePicker">{{ showTreePicker ? '收起校正' : '▸ 校正考点（可选）' }}</button>
              </div>
              <div v-if="showTreePicker" class="tree-picker">
                <CategoryTree v-if="store.categoryTree.length" :nodes="store.categoryTree" :selectable="true" :active-id="manualNodeId" @select="onPickNode" />
                <div v-else class="tree-loading">题型树加载中…</div>
              </div>
            </div>

            <!-- 卡片缩略信息预览 -->
            <div class="card-preview" v-if="parsed.card_title || parsed.card_tags || parsed.card_summary">
              <div class="cp-label">🃏 卡片缩略信息（将展示在题库列表卡片）</div>
              <div class="cp-card">
                <div class="cpc-head">
                  <span class="cpc-mod" :style="{ background: modColor(parsed.level1), color: '#fff' }">{{ parsed.level1 }}</span>
                  <span class="cpc-type" v-if="parsed.level2">{{ parsed.level2 }}</span>
                  <span class="cpc-ans">{{ parsed.answer || '—' }}</span>
                </div>
                <div class="cpc-title">{{ parsed.card_title || '（未生成卡片标题）' }}</div>
                <div class="cpc-tags" v-if="cardPreviewTags.length">
                  <span class="cpc-tag" v-for="t in cardPreviewTags" :key="t">{{ t }}</span>
                </div>
                <div class="cpc-sum" v-if="parsed.card_summary">{{ parsed.card_summary }}</div>
              </div>
            </div>

            <!-- 结构化字段 -->
            <div class="parsed-grid">
              <div class="parsed-item"><div class="parsed-label">细分考点</div><div class="parsed-value">{{ parsed.sub_point || '-' }}</div></div>
              <div class="parsed-item"><div class="parsed-label">考察意图</div><div class="parsed-value">{{ parsed.exam_intent || '-' }}</div></div>
              <div class="parsed-item"><div class="parsed-label">难度</div><div class="parsed-value">{{ parsed.difficulty_label || '-' }}</div></div>
              <div class="parsed-item"><div class="parsed-label">考场优先级</div><div class="parsed-value">{{ parsed.exam_priority || '-' }}</div></div>
              <div class="parsed-item"><div class="parsed-label">建议用时</div><div class="parsed-value">{{ parsed.suggested_time || '-' }} 秒</div></div>
              <div class="parsed-item"><div class="parsed-label">正确答案</div><div class="parsed-value answer">{{ parsed.answer || '-' }}</div></div>
            </div>

            <div class="parsed-section" v-if="parsed.break_logic"><div class="parsed-label">破题逻辑</div><div class="parsed-content md-body" v-html="md(parsed.break_logic)"></div></div>
            <div class="parsed-section" v-if="parsed.normal_solve"><div class="parsed-label">通用解法</div><div class="parsed-content md-body" v-html="md(parsed.normal_solve)"></div></div>
            <div class="parsed-section" v-if="parsed.quick_solve"><div class="parsed-label">速算技巧</div><div class="parsed-content md-body" v-html="md(parsed.quick_solve)"></div></div>
            <div class="parsed-section" v-if="parsed.step_detail"><div class="parsed-label">解题步骤</div><div class="parsed-content md-body" v-html="md(parsed.step_detail)"></div></div>

            <!-- 出题人意图 / 两库分工 -->
            <div class="ctx-row" v-if="parsed.solve_method_judgment || parsed.kb_decision || parsed.sl_decision">
              <span class="ctx-chip method" :class="methodClass(parsed.solve_method_judgment)" v-if="parsed.solve_method_judgment">{{ parsed.solve_method_judgment }}</span>
              <span class="ctx-chip" :class="decClass(parsed.kb_decision)">知识库：{{ parsed.kb_decision || '—' }}</span>
              <span class="ctx-chip" :class="decClass(parsed.sl_decision)">解题库：{{ parsed.sl_decision || '—' }}</span>
            </div>

            <!-- 候选知识卡片 -->
            <div class="cand-area">
              <div class="cand-head">
                <h3>🧩 候选知识卡片（勾选后沉淀）</h3>
                <div class="cand-stats" v-if="hasCandidates">
                  <span>已选 知识库 <b>{{ kgSelCount }}</b> / 解题库 <b>{{ slSelCount }}</b></span>
                  <label class="sel-all"><input type="checkbox" :checked="allSelected" @change="toggleAll" /><span>全选/取消</span></label>
                </div>
              </div>

              <div v-if="!hasCandidates" class="no-cand">
                本题解析未产出可沉淀的候选知识卡片。可能原因：AI 将两库均判定为「不需要」，或产出的卡片格式未被识别。<br />
                可点「返回修改」回到录入页重新生成 / 校正提示词；或在录入页校正考点后重试。即便不选卡片，本题仍可正常入库。
              </div>

              <!-- 知识库候选 -->
              <div class="kg-group" v-if="parsed.kb_decision === '需要' && candidateKg.length">
                <div class="kg-group-head"><el-icon><Collection /></el-icon> 行测知识库候选（{{ candidateKg.length }}）</div>
                <div v-for="(k, i) in candidateKg" :key="'k' + i" :class="['kcard', { off: !isSel('k' + i) }]">
                  <div class="kc-top">
                    <input type="checkbox" :checked="isSel('k' + i)" @change="toggle('k' + i)" />
                    <span class="kc-type" :style="kgStyle(k.kg_type)">{{ k.kg_type }}</span>
                    <span class="kc-cat" v-if="catPath(k)">{{ catPath(k) }}</span>
                    <span class="kc-title">{{ k.title }}</span>
                  </div>
                  <div class="kc-cardtitle" v-if="k.card_title">🃏 {{ k.card_title }}</div>
                  <div class="kc-tags" v-if="cardTags(k.card_tags).length"><span class="kc-tag" v-for="t in cardTags(k.card_tags)" :key="t">{{ t }}</span></div>
                  <div class="kc-summary" v-if="k.card_summary">{{ k.card_summary }}</div>
                  <div class="kc-content md-body" v-html="md(k.content || '')"></div>
                </div>
              </div>

              <!-- 解题库候选 -->
              <div class="kg-group" v-if="parsed.sl_decision === '需要' && candidateSl.length">
                <div class="kg-group-head"><el-icon><Promotion /></el-icon> 行测解题库候选（{{ candidateSl.length }}）</div>
                <div v-for="(s, i) in candidateSl" :key="'s' + i" :class="['kcard', { off: !isSel('s' + i) }]">
                  <div class="kc-top">
                    <input type="checkbox" :checked="isSel('s' + i)" @change="toggle('s' + i)" />
                    <span class="kc-type" :style="solveStyle(s.solve_type)">{{ s.solve_type }}</span>
                    <span class="kc-cat" v-if="catPath(s)">{{ catPath(s) }}</span>
                    <span class="kc-title">{{ s.title }}</span>
                  </div>
                  <div class="kc-cardtitle" v-if="s.card_title">🃏 {{ s.card_title }}</div>
                  <div class="kc-tags" v-if="cardTags(s.card_tags).length"><span class="kc-tag" v-for="t in cardTags(s.card_tags)" :key="t">{{ t }}</span></div>
                  <div class="kc-summary" v-if="s.card_summary">{{ s.card_summary }}</div>
                  <div class="kc-content md-body" v-html="md(s.content || '')"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部操作栏 -->
          <div class="action-bar" v-if="parsed">
            <span class="ab-hint" v-if="!hasCandidates">未选卡片也会照常入库题目</span>
            <span class="ab-hint" v-else>将随题目一并沉淀所选知识卡片</span>
            <button class="btn-default" @click="backToInput" v-if="mode === 'new'">返回修改</button>
            <button class="btn-primary" :disabled="saving" @click="confirmDeposit">
              {{ saving ? '处理中…' : '✅ 确认入库' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { questionApi, knowledgeApi, solveLibraryApi, categoryApi } from '../api'
import { useAppStore } from '../stores/app'
import CategoryTree from '../components/CategoryTree.vue'
import { ElMessage } from 'element-plus'
import { renderMarkdown } from '../utils/md'
import { modColor, kgStyle, solveStyle } from '../utils/constants'

const md = renderMarkdown
const route = useRoute()
const router = useRouter()
const store = useAppStore()

const DRAFT_KEY = 'gk_pending_deposit'

const mode = ref('empty')            // 'new' | 'existing' | 'empty'
const draft = ref(null)              // { ai_content, parsed }
const parsed = ref(null)             // 当前用于预览 + 候选的解析结果
const currentQ = ref(null)           // 已有题目对象（existing 模式）
const pendingQuestions = ref([])
const totalPending = ref(0)
const loadingList = ref(false)
const selectedQid = ref(null)
const parsing = ref(false)
const saving = ref(false)

const selected = ref(new Set())
const isError = ref(false)
const showTreePicker = ref(false)
const manualLevels = ref(null)
const manualNodeId = ref(null)

const candidateKg = computed(() => parsed.value?.knowledge_items || [])
const candidateSl = computed(() => parsed.value?.solve_items || [])
const hasCandidates = computed(() => {
  const p = parsed.value
  if (!p) return false
  return (p.kb_decision === '需要' && candidateKg.value.length > 0) ||
         (p.sl_decision === '需要' && candidateSl.value.length > 0)
})
const kgSelCount = computed(() =>
  candidateKg.value.filter((_, i) => selected.value.has('k' + i)).length
)
const slSelCount = computed(() =>
  candidateSl.value.filter((_, i) => selected.value.has('s' + i)).length
)
const allSelected = computed(() => {
  const total = candidateKg.value.length + candidateSl.value.length
  return total > 0 && (kgSelCount.value + slSelCount.value) === total
})

const effectivePath = computed(() => {
  const src = manualLevels.value || parsed.value || {}
  return [1, 2, 3, 4, 5].map(n => src['level' + n]).filter(Boolean)
})
const cardPreviewTags = computed(() =>
  (parsed.value?.card_tags || '').split('｜').map(s => s.trim()).filter(Boolean)
)

function isSel(k) { return selected.value.has(k) }
function toggle(k) {
  const s = new Set(selected.value)
  if (s.has(k)) s.delete(k); else s.add(k)
  selected.value = s
}
function toggleAll(e) {
  const s = new Set()
  if (e.target.checked) {
    candidateKg.value.forEach((_, i) => s.add('k' + i))
    candidateSl.value.forEach((_, i) => s.add('s' + i))
  }
  selected.value = s
}
function defaultSelect() {
  const s = new Set()
  candidateKg.value.forEach((_, i) => s.add('k' + i))
  candidateSl.value.forEach((_, i) => s.add('s' + i))
  selected.value = s
}
function catPath(item) {
  return [item.level1, item.level2, item.level3].filter(Boolean).join(' - ')
}
function cardTags(s) {
  return (s || '').split('｜').map(t => t.trim()).filter(Boolean)
}
function stripQ(raw) {
  const t = (raw || '').replace(/\n/g, ' ').trim()
  return t ? t.slice(0, 42) + (t.length > 42 ? '…' : '') : '（无题干）'
}
function decClass(d) {
  if (d === '需要') return 'need'
  if (d === '不需要') return 'no-need'
  return 'unknown'
}
function methodClass(m) {
  if (m === '知识积累型') return 'memory'
  if (m === '解题运算型') return 'solve'
  if (m === '综合型') return 'both'
  return 'unknown'
}

async function loadPendingList() {
  loadingList.value = true
  try {
    const [listRes, pendingRes] = await Promise.all([
      questionApi.getList({ page: 1, page_size: 200, sort: 'new', deposited: false }),
      questionApi.getList({ page: 1, page_size: 1, deposited: false }),
    ])
    pendingQuestions.value = listRes.data.items || []
    totalPending.value = pendingRes.data.total || 0
  } catch (e) {
    ElMessage.error('待处理列表加载失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loadingList.value = false
  }
}

function loadDraft() {
  const raw = localStorage.getItem(DRAFT_KEY)
  if (!raw) return false
  try {
    const d = JSON.parse(raw)
    if (!d.ai_content) return false
    draft.value = d
    parsed.value = d.parsed || null
    mode.value = 'new'
    isError.value = false
    defaultSelect()
    return true
  } catch {
    return false
  }
}

async function openExisting(q) {
  selectedQid.value = q.id
  mode.value = 'existing'
  draft.value = null
  localStorage.removeItem(DRAFT_KEY)
  parsing.value = true
  try {
    const res = await questionApi.get(q.id)
    currentQ.value = res.data
    const pr = await questionApi.parseOnly({ ai_content: res.data.ai_raw_content })
    parsed.value = pr.data.parsed || null
    isError.value = !!res.data.is_error
    defaultSelect()
  } catch (e) {
    ElMessage.error('题目加载失败：' + (e.response?.data?.detail || e.message))
  } finally {
    parsing.value = false
  }
}

async function openExistingById(qid) {
  try {
    const res = await questionApi.get(qid)
    currentQ.value = res.data
    selectedQid.value = res.data.id
    parsed.value = null
    parsing.value = true
    const pr = await questionApi.parseOnly({ ai_content: res.data.ai_raw_content })
    parsed.value = pr.data.parsed || null
    isError.value = !!res.data.is_error
    mode.value = 'existing'
    defaultSelect()
  } catch (e) {
    ElMessage.error('题目加载失败：' + (e.response?.data?.detail || e.message))
  } finally {
    parsing.value = false
  }
}

async function onPickNode(node) {
  try {
    const res = await categoryApi.getNode(node.id)
    const d = res.data
    manualLevels.value = {
      level1: d.level1, level2: d.level2, level3: d.level3,
      level4: d.level4, level5: d.level5,
    }
    manualNodeId.value = d.id
    ElMessage.success('已校正考点：' + [d.level1, d.level2, d.level3, d.level4, d.level5].filter(Boolean).join(' / '))
  } catch (e) {
    ElMessage.error('获取节点路径失败：' + (e.response?.data?.detail || e.message))
  }
}

function buildPayloads(qid) {
  const p = parsed.value
  const kgItems = []
  const slItems = []
  candidateKg.value.forEach((k, i) => {
    if (!selected.value.has('k' + i)) return
    kgItems.push({
      module: k.level1 || p.level1 || '通用',
      kg_type: k.kg_type, title: k.title, content: k.content || '',
      level1: k.level1 || '', level2: k.level2 || '', level3: k.level3 || '',
      level4: k.level4 || '', level5: k.level5 || '',
      card_title: k.card_title || '', card_tags: k.card_tags || '', card_summary: k.card_summary || '',
      source: 'AI解析沉淀', source_question_id: qid,
    })
  })
  candidateSl.value.forEach((s, i) => {
    if (!selected.value.has('s' + i)) return
    slItems.push({
      module: s.level1 || p.level1 || '通用',
      solve_type: s.solve_type, title: s.title, content: s.content || '',
      level1: s.level1 || '', level2: s.level2 || '', level3: s.level3 || '',
      level4: s.level4 || '', level5: s.level5 || '',
      card_title: s.card_title || '', card_tags: s.card_tags || '', card_summary: s.card_summary || '',
      source: 'AI解析沉淀', source_question_id: qid,
    })
  })
  return { kgItems, slItems }
}

async function confirmDeposit() {
  if (!parsed.value) return
  saving.value = true
  try {
    let qid
    if (mode.value === 'new') {
      const lv = manualLevels.value || {}
      const res = await questionApi.quickCreate({
        ai_content: draft.value.ai_content,
        level1: lv.level1 || '', level2: lv.level2 || '', level3: lv.level3 || '',
        level4: lv.level4 || '', level5: lv.level5 || '',
        is_error: isError.value,
      })
      qid = res.data.id
    } else {
      qid = currentQ.value.id
      const lv = manualLevels.value
      if (lv) {
        await questionApi.update(qid, {
          level1: lv.level1, level2: lv.level2, level3: lv.level3,
          level4: lv.level4, level5: lv.level5, is_error: isError.value,
        })
      } else if (isError.value !== (currentQ.value.is_error || false)) {
        await questionApi.update(qid, { is_error: isError.value })
      }
    }

    const { kgItems, slItems } = buildPayloads(qid)
    let kgN = 0, slN = 0
    if (kgItems.length) { const r = await knowledgeApi.batch(kgItems); kgN = r.data?.created || kgItems.length }
    if (slItems.length) { const r = await solveLibraryApi.batch(slItems); slN = r.data?.created || slItems.length }
    await questionApi.update(qid, { deposited: true })

    localStorage.removeItem(DRAFT_KEY)
    const parts = []
    if (kgN) parts.push(`知识库 ${kgN} 条`)
    if (slN) parts.push(`解题库 ${slN} 条`)
    ElMessage.success('题目已入库' + (parts.length ? '，沉淀：' + parts.join('、') : '（未选卡片）'))

    // 重置并跳到下一题待处理
    mode.value = 'empty'
    parsed.value = null
    draft.value = null
    currentQ.value = null
    selectedQid.value = null
    selected.value = new Set()
    manualLevels.value = null
    manualNodeId.value = null
    await loadPendingList()
    if (pendingQuestions.value.length) {
      await openExisting(pendingQuestions.value[0])
    }
  } catch (e) {
    ElMessage.error('入库失败：' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

function backToInput() {
  // 草稿保留在 localStorage，录入页会恢复内容
  router.push('/question-input')
}
function discardDraft() {
  localStorage.removeItem(DRAFT_KEY)
  draft.value = null
  parsed.value = null
  mode.value = 'empty'
  router.push('/question-input')
}

onMounted(async () => {
  if (!store.categoryTree.length) await store.loadCategories()
  await loadPendingList()
  const qid = route.query.qid
  if (qid) {
    await openExistingById(qid)
    return
  }
  if (!loadDraft()) {
    mode.value = 'empty'
  }
})
</script>

<style scoped>
.deposit-page { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.page-header .sub { margin: 4px 0 0; font-size: 13px; color: var(--text-tertiary); }
.page-header .sub strong { color: var(--primary); }
.badge { background: var(--success-bg); color: var(--success); padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; white-space: nowrap; }

.main-grid { display: grid; grid-template-columns: 320px 1fr; gap: 16px; align-items: start; }
@media (max-width: 1000px) { .main-grid { grid-template-columns: 1fr; } }

.left-panel .lp-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 14px; font-weight: 600; color: var(--text-secondary); }
.lp-new { font-size: 12px; color: var(--primary); text-decoration: none; font-weight: 500; }
.q-list { display: flex; flex-direction: column; gap: 8px; max-height: 76vh; overflow-y: auto; }
.empty, .no-cand, .empty-state { color: var(--text-tertiary); font-size: 13px; padding: 16px; text-align: center; line-height: 1.7; }
.q-item { background: var(--bg-elevated); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 10px 12px; cursor: pointer; transition: all 0.15s; }
.q-item:hover { border-color: var(--primary-light); }
.q-item.active { border-color: var(--primary); box-shadow: 0 0 0 2px var(--primary-bg); }
.q-item-main { display: flex; align-items: center; gap: 8px; }
.q-mod { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 999px; flex-shrink: 0; }
.q-title { font-size: 13px; color: var(--text-primary); line-height: 1.4; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.card { background: var(--bg-elevated); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); border: 1px solid var(--border-light); overflow: hidden; margin-bottom: 16px; }
.card-header { padding: 12px 16px; border-bottom: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.ch-head { display: flex; align-items: center; gap: 8px; min-width: 0; }
.ch-mod { font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 999px; flex-shrink: 0; }
.ch-qtitle { font-size: 14px; font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ch-actions { flex-shrink: 0; }
.card-body { padding: 16px; }

.draft-banner { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding: 10px 14px; border-radius: var(--radius-md); background: var(--primary-bg); border: 1px solid var(--primary-light); margin-bottom: 16px; font-size: 13px; color: var(--text-secondary); }
.draft-banner .db-ico { font-size: 18px; }
.draft-banner .db-text { flex: 1; min-width: 200px; }
.draft-banner .db-text strong { color: var(--primary); }

.review-box { margin-bottom: 14px; border: 1px solid var(--border-light); border-radius: var(--radius-md); background: var(--bg-subtle); }
.rb-label { font-size: 12px; font-weight: 700; color: var(--text-secondary); padding: 8px 12px; border-bottom: 1px solid var(--border-light); }
.rb-content { font-size: 13px; line-height: 1.7; color: var(--text-primary); padding: 10px 14px; max-height: 260px; overflow-y: auto; }

.cat-path-box { background: linear-gradient(135deg, var(--primary-bg) 0%, var(--bg-subtle) 100%); border: 1px solid var(--primary-light); border-radius: var(--radius-md); padding: 12px 14px; margin-bottom: 14px; }
.cp-label { font-size: 12px; color: var(--text-secondary); font-weight: 600; margin-bottom: 6px; }
.cp-path { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.cp-seg { font-size: 14px; font-weight: 600; color: var(--primary); background: var(--bg-elevated); padding: 2px 10px; border-radius: 8px; }
.cp-sep { color: var(--text-tertiary); font-weight: 700; }
.cp-empty { font-size: 13px; color: var(--danger); font-weight: 500; }
.cp-source { margin-top: 8px; font-size: 11px; display: flex; align-items: center; gap: 8px; }
.cp-source.auto { color: var(--text-tertiary); }
.cp-source.manual { color: var(--primary); font-weight: 600; }
.link-btn { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 12px; padding: 0; }
.tree-picker { max-height: 280px; overflow-y: auto; border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 6px; background: var(--bg-base); margin-top: 8px; }
.tree-loading { color: var(--text-tertiary); font-size: 13px; padding: 12px; }

.card-preview .cp-card { border: 1px solid var(--border-base); border-radius: var(--radius-md); padding: 12px 14px; background: var(--bg-elevated); border-left: 3px solid var(--primary); }
.cpc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.cpc-mod { font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 999px; }
.cpc-type { font-size: 12px; color: var(--text-secondary); }
.cpc-type::before { content: '·'; margin-right: 6px; color: var(--text-tertiary); }
.cpc-ans { margin-left: auto; font-size: 12.5px; font-weight: 600; color: var(--success); background: var(--success-bg); padding: 1px 10px; border-radius: 6px; }
.cpc-title { font-size: 15px; font-weight: 600; line-height: 1.45; color: var(--text-primary); margin-bottom: 6px; }
.cpc-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.cpc-tag { font-size: 11.5px; padding: 2px 9px; border-radius: 999px; color: var(--info); background: var(--info-bg); }
.cpc-sum { font-size: 12.5px; line-height: 1.6; color: var(--text-tertiary); }

.parsed-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0; }
.parsed-item { background: var(--bg-subtle); padding: 10px 12px; border-radius: var(--radius-md); }
.parsed-label { font-size: 11px; color: var(--text-tertiary); margin-bottom: 4px; }
.parsed-value { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.parsed-value.answer { font-size: 18px; font-weight: 700; color: var(--success); }
.parsed-section { margin-bottom: 12px; }
.parsed-section .parsed-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; font-weight: 500; }
.parsed-content { font-size: 13px; color: var(--text-primary); line-height: 1.7; padding: 10px 14px; background: var(--bg-subtle); border-radius: var(--radius-md); }

.ctx-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 4px 0 14px; }
.ctx-chip { font-size: 12px; font-weight: 500; padding: 4px 12px; border-radius: 999px; border: 1px solid var(--border-base); }
.ctx-chip.need { color: #047857; background: #ecfdf5; border-color: #a7f3d0; }
.ctx-chip.no-need { color: #b45309; background: #fffbeb; border-color: #fde68a; }
.ctx-chip.unknown { color: var(--text-tertiary); background: var(--bg-subtle); }
.ctx-chip.method { color: #4338ca; background: #eef2ff; border-color: #c7d2fe; font-weight: 600; }
.ctx-chip.method.memory { color: #7c3aed; background: #f5f3ff; border-color: #ddd6fe; }
.ctx-chip.method.solve { color: #0369a1; background: #f0f9ff; border-color: #bae6fd; }
.ctx-chip.method.both { color: #b45309; background: #fffbeb; border-color: #fde68a; }

.cand-area { margin-top: 8px; border-top: 1px dashed var(--border-light); padding-top: 14px; }
.cand-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.cand-head h3 { margin: 0; font-size: 14px; font-weight: 600; color: var(--text-primary); }
.cand-stats { font-size: 12.5px; color: var(--text-secondary); display: flex; align-items: center; gap: 12px; }
.cand-stats b { color: var(--primary); }
.sel-all { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; cursor: pointer; }

.kg-group { margin-bottom: 18px; }
.kg-group-head { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 10px; }
.kg-group-head .el-icon { color: var(--primary); }

.kcard { border: 1px solid var(--border-base); border-radius: var(--radius-md); padding: 12px 14px; margin-bottom: 10px; background: var(--bg-base); transition: all 0.15s; }
.kcard.off { opacity: 0.5; }
.kcard.off .kc-title { text-decoration: line-through; }
.kc-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.kc-top input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--primary); cursor: pointer; flex-shrink: 0; }
.kc-type { font-size: 11px; font-weight: 600; padding: 1px 9px; border-radius: 999px; border: 1px solid transparent; flex-shrink: 0; }
.kc-cat { font-size: 11px; color: var(--text-secondary); background: var(--bg-subtle); padding: 1px 8px; border-radius: 6px; flex-shrink: 0; }
.kc-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.kc-cardtitle { font-size: 12px; color: var(--text-tertiary); margin-top: 6px; }
.kc-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.kc-tag { font-size: 11px; padding: 2px 9px; border-radius: 999px; color: var(--info); background: var(--info-bg); }
.kc-summary { font-size: 12.5px; line-height: 1.6; color: var(--text-secondary); margin-top: 6px; padding: 8px 10px; background: var(--primary-bg); border-radius: var(--radius-sm); border-left: 3px solid var(--primary); }
.kc-content { font-size: 13px; color: var(--text-primary); line-height: 1.7; margin-top: 8px; max-height: 320px; overflow-y: auto; padding: 10px 12px; background: var(--bg-subtle); border-radius: var(--radius-md); }

.empty-state .es-icon { font-size: 32px; margin-bottom: 10px; }

.action-bar { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-top: 1px solid var(--border-light); background: var(--bg-subtle); }
.ab-hint { font-size: 12.5px; color: var(--text-tertiary); }
.action-bar .btn-primary { margin-left: auto; }

.checkbox-label { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; cursor: pointer; }
.checkbox-label input { width: 16px; height: 16px; }

.btn-primary { background: var(--primary); color: white; border: none; padding: 8px 20px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-primary:hover { background: var(--primary-dark); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-default { background: var(--bg-subtle); color: var(--text-secondary); border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; }
.btn-default:hover { background: var(--border-light); }
.btn-default.small { padding: 4px 12px; font-size: 12px; }
</style>
