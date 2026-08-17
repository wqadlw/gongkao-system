<template>
  <div class="qd-page" v-loading="loading">
    <div class="qd-grid" :class="{ embedded }">
      <!-- 左：题型树（高亮本题型；点击跳到该题型列表） -->
      <aside class="qd-tree" v-if="!embedded">
        <div class="qd-tree-head">
          <span class="qth-title"><el-icon><Files /></el-icon> 题型导航</span>
        </div>
        <div class="qd-tree-scroll">
          <CategoryTree v-if="store.categoryTree.length" :nodes="store.categoryTree" :active-path="crumb" />
          <div v-else class="qd-tree-loading">题型树加载中…</div>
        </div>
      </aside>

      <!-- 中：题目详情 -->
      <div class="qd-main">
        <template v-if="q">
          <!-- Hero -->
          <div class="hero">
            <div class="hero-top">
              <button class="btn-ghost" @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回题库</button>
              <div class="hero-actions">
                <button class="btn-default" @click="toggleFav" :class="{ pinned: isFav }"><el-icon><Star /></el-icon> {{ isFav ? '已收藏' : '收藏' }}</button>
                <button class="btn-default" @click="openReclass"><el-icon><Edit /></el-icon> 重新归类</button>
                <button class="btn-default" @click="openNoteDialog"><el-icon><Notebook /></el-icon> 粘贴 AI 笔记</button>
                <button class="btn-primary" @click="generateNote" :disabled="genLoading"><el-icon><MagicStick /></el-icon> 一键生成笔记</button>
                <button class="btn-default" @click="startReview"><el-icon><Refresh /></el-icon> 立即复习</button>
              </div>
            </div>

            <div class="hero-meta">
              <span class="mod-tag" :style="modStyle(q.level1)">{{ q.level1 }}</span>
              <span v-if="q.is_error" class="err-badge">错题</span>

              <!-- 掌握度（行内，可改） -->
              <span class="meta-mastery" title="掌握度">
                <el-rate :model-value="q.master_level || 1" :max="5" size="small"
                  @change="setMaster" />
              </span>

              <!-- 错题开关 + 错因 -->
              <span class="meta-error">
                <button class="err-toggle" :class="{ on: q.is_error }" @click="toggleError">
                  <el-icon><WarnTriangleFilled /></el-icon> {{ q.is_error ? '已标记错题' : '标记错题' }}
                </button>
                <div v-if="reasonOpen" class="reason-pop">
                  <div class="reason-catch" @click="reasonOpen = false"></div>
                  <div class="reason-menu">
                    <div class="reason-title">选择错因</div>
                    <button v-for="r in ERROR_REASONS" :key="r" class="reason-item" @click="pickReason(r)">{{ r }}</button>
                  </div>
                </div>
              </span>
            </div>

            <div class="hero-crumb">
              <template v-for="(seg, i) in crumb" :key="i">
                <span class="crumb-seg">{{ seg }}</span>
                <span v-if="i < crumb.length - 1" class="crumb-sep">/</span>
              </template>
            </div>

            <div class="hero-chips">
              <span class="chip"><i>难度</i><b class="stars">{{ '★'.repeat(q.difficulty || 3) }}{{ '☆'.repeat(5 - (q.difficulty || 3)) }}</b></span>
              <span class="chip"><i>建议用时</i><b>{{ q.suggested_time }} 秒</b></span>
              <span class="chip"><i>考场优先级</i><b>{{ q.exam_priority || '-' }}</b></span>
              <span class="chip answer"><i>正确答案</i><b>{{ q.answer }}</b></span>
              <span v-if="q.error_reason" class="chip err"><i>错因</i><b>{{ q.error_reason }}</b></span>
            </div>
          </div>

          <!-- 题目（始终可见） -->
          <div class="card" id="sec-question" v-if="q.question_raw">
            <div class="card-head"><el-icon class="ico"><Document /></el-icon><h3>题目</h3></div>
            <div class="card-body"><div class="question-text md-body" v-html="md(q.question_raw)"></div></div>
          </div>

          <!-- 答题模式：先隐藏解析，点“显示答案”揭示 -->
          <div v-if="mode === 'practice' && !revealed" class="reveal-banner" @click="reveal">
            <el-icon class="rb-ico"><View /></el-icon>
            <div class="rb-text">本题已隐藏答案与解析</div>
            <div class="rb-sub">作答后点击显示 · 已用 <b>{{ fmtTime(elapsed) }}</b></div>
            <button class="rb-btn">显示答案与解析</button>
          </div>

          <!-- 解析区（学习模式始终显示；答题模式揭示后显示） -->
          <template v-if="showSolutions">
            <div class="card" id="sec-func" v-if="modFuncs.length">
              <div class="card-head func"><el-icon class="ico"><MagicStick /></el-icon><h3>题型专属功能 · {{ q.level1 }}</h3></div>
              <div class="card-body">
                <div class="func-btns">
                  <button v-for="fn in modFuncs" :key="fn.key" class="func-btn"
                    :class="{ on: activeFunc && activeFunc.key === fn.key }" @click="runFunc(fn)">
                    <el-icon><component :is="fn.icon" /></el-icon>{{ fn.label }}
                  </button>
                </div>
                <div v-if="activeFunc" class="func-card">
                  <div class="fc-head">
                    <b>{{ activeFunc.label }}</b>
                    <span class="fc-desc">{{ activeFunc.desc }}</span>
                    <button class="fc-close" @click="activeFunc = null"><el-icon><Close /></el-icon></button>
                  </div>
                  <div v-for="f in funcCard" :key="f.label" class="fc-row">
                    <div class="fc-label">{{ f.label }}</div>
                    <div class="fc-val md-body" v-html="md(f.value)"></div>
                  </div>
                  <div v-if="!funcCard.length" class="fc-empty">本题暂无该功能对应的解析字段，录入时可让 AI 补全。</div>
                </div>
              </div>
            </div>

            <div class="card" id="sec-intent" v-if="q.exam_intent || q.option_feature">
              <div class="card-head collapsible" @click="toggleSec('sec-intent')"><el-icon class="ico"><Aim /></el-icon><h3>出题人意图与选项特征</h3><span class="card-caret" :class="{ open: !isCollapsed('sec-intent') }">▾</span></div>
              <div class="card-body" v-show="!isCollapsed('sec-intent')">
                <div v-if="q.exam_intent" class="section"><div class="section-label">出题人意图</div><div class="section-content md-body" v-html="md(q.exam_intent)"></div></div>
                <div v-if="q.option_feature" class="section"><div class="section-label">选项特征</div><div class="section-content md-body" v-html="md(q.option_feature)"></div></div>
              </div>
            </div>

            <div class="card" id="sec-trap" v-if="q.break_logic || q.trap_read || q.trap_calc || q.trap_thought || q.error_path">
              <div class="card-head warn collapsible" @click="toggleSec('sec-trap')"><el-icon class="ico"><WarningFilled /></el-icon><h3>解题思路与避坑提醒</h3><span class="card-caret" :class="{ open: !isCollapsed('sec-trap') }">▾</span></div>
              <div class="card-body" v-show="!isCollapsed('sec-trap')">
                <div v-if="q.break_logic" class="section"><div class="section-label">破题逻辑</div><div class="section-content md-body" v-html="md(q.break_logic)"></div></div>
                <div v-if="q.trap_read" class="trap-item warning"><span class="trap-tag">读题陷阱</span><span class="md-body md-inline" v-html="mdi(q.trap_read)"></span></div>
                <div v-if="q.trap_calc" class="trap-item danger"><span class="trap-tag">计算陷阱</span><span class="md-body md-inline" v-html="mdi(q.trap_calc)"></span></div>
                <div v-if="q.trap_thought" class="trap-item info"><span class="trap-tag">思维误区</span><span class="md-body md-inline" v-html="mdi(q.trap_thought)"></span></div>
                <div v-if="q.error_path" class="section"><div class="section-label">常见错误路径</div><div class="section-content md-body" v-html="md(q.error_path)"></div></div>
              </div>
            </div>

            <div class="card" id="sec-tip" v-if="q.normal_solve || q.quick_solve || q.identify_signal">
              <div class="card-head tip collapsible" @click="toggleSec('sec-tip')"><el-icon class="ico"><Lightbulb /></el-icon><h3>通用技巧与考场速算方法</h3><span class="card-caret" :class="{ open: !isCollapsed('sec-tip') }">▾</span></div>
              <div class="card-body" v-show="!isCollapsed('sec-tip')">
                <div v-if="q.normal_solve" class="section"><div class="section-label">常规通用解法</div><div class="section-content md-body" v-html="md(q.normal_solve)"></div></div>
                <div v-if="q.quick_solve" class="section success"><div class="section-label">速算/秒杀技巧</div><div class="section-content md-body" v-html="md(q.quick_solve)"></div></div>
                <div v-if="q.identify_signal" class="section info"><div class="section-label">题型识别信号</div><div class="section-content md-body" v-html="md(q.identify_signal)"></div></div>
              </div>
            </div>

            <div class="card" id="sec-step" v-if="q.step_detail">
              <div class="card-head step collapsible" @click="toggleSec('sec-step')"><el-icon class="ico"><Promotion /></el-icon><h3>详细解题步骤</h3><span class="card-caret" :class="{ open: !isCollapsed('sec-step') }">▾</span></div>
              <div class="card-body" v-show="!isCollapsed('sec-step')"><div class="step-content md-body" v-html="md(q.step_detail)"></div></div>
            </div>

            <div class="card" id="sec-background" v-if="q.background_knowledge">
              <div class="card-head bg collapsible" @click="toggleSec('sec-background')"><el-icon class="ico"><Collection /></el-icon><h3>思维模型和知识背景</h3><span class="card-caret" :class="{ open: !isCollapsed('sec-background') }">▾</span></div>
              <div class="card-body" v-show="!isCollapsed('sec-background')"><div class="md-body" v-html="md(q.background_knowledge)"></div></div>
            </div>

            <div class="card" id="sec-practice" v-if="q.practice_question">
              <div class="card-head practice collapsible" @click="toggleSec('sec-practice')"><el-icon class="ico"><Medal /></el-icon><h3>同考点巩固练习</h3><span class="card-caret" :class="{ open: !isCollapsed('sec-practice') }">▾</span></div>
              <div class="card-body" v-show="!isCollapsed('sec-practice')">
                <div class="practice-q md-body" v-html="md(q.practice_question)"></div>
                <details class="practice-answer" v-if="q.practice_answer">
                  <summary>查看答案解析</summary>
                  <div class="md-body" v-html="md(q.practice_answer)"></div>
                </details>
              </div>
            </div>

            <div class="card" id="sec-raw">
              <div class="card-head collapsible" @click="toggleSec('sec-raw')"><el-icon class="ico"><Memo /></el-icon><h3>AI 原始内容</h3>
                <button class="btn-default small" @click.stop="copyRaw"><el-icon><CopyDocument /></el-icon> 复制</button>
                <span class="card-caret" :class="{ open: !isCollapsed('sec-raw') }">▾</span>
              </div>
              <div class="card-body" v-show="!isCollapsed('sec-raw')"><pre class="raw-content">{{ q.ai_raw_content }}</pre></div>
            </div>
          </template>
        </template>
      </div>

      <!-- 右：控制 + 悬浮跟随卡（仅独立页） -->
      <aside class="qd-rail" v-if="!embedded">
        <!-- 练习模式（置顶吸住） -->
        <div class="rail-card mode-card">
          <div class="rc-title">练习模式</div>
          <div class="seg">
            <button class="seg-btn" :class="{ on: mode === 'study' }" @click="setMode('study')">学习模式</button>
            <button class="seg-btn" :class="{ on: mode === 'practice' }" @click="setMode('practice')">答题模式</button>
          </div>
          <div class="mode-hint" v-if="mode === 'practice'">
            <span class="timer"><el-icon><Timer /></el-icon> {{ fmtTime(elapsed) }}</span>
            隐藏解析，作答后显示
          </div>
          <div class="mode-hint" v-else>完整展示，适合研读</div>
        </div>

        <!-- 本考点进度 + 上下题 -->
        <div class="rail-card nav-card" v-if="related.length">
          <div class="rc-title">本考点进度</div>
          <div class="pos">第 <b>{{ posIndex + 1 }}</b> / {{ related.length }} 题
            <span class="pos-sub">（{{ q && q.level2 || q.level1 }}）</span>
          </div>
          <div class="nav-btns">
            <button class="nav-btn" :disabled="!prev" @click="goTo(prev)"><el-icon><ArrowLeft /></el-icon> 上一题</button>
            <button class="nav-btn" :disabled="!next" @click="goTo(next)">下一题 <el-icon><ArrowRight /></el-icon></button>
          </div>
          <div class="kb-hint"><kbd>J</kbd>/<kbd>K</kbd> 切换 · <kbd>空格</kbd> 显示答案</div>
        </div>

        <!-- 本考点其他题目 -->
        <div class="rail-card sibling-card" v-if="related.length">
          <div class="rc-title">本考点其他题目</div>
          <div class="sib-list">
            <button v-for="s in related" :key="s.id" class="sib-item"
              :class="{ on: s.id === effectiveId, err: s.is_error }" @click="goTo(s)">
              <span class="sib-diff">{{ '★'.repeat(s.difficulty || 3) }}</span>
              <span class="sib-text md-body" v-html="mdInline(s.question_raw || '（无题干）')"></span>
            </button>
          </div>
        </div>

        <!-- 随机一题 -->
        <button class="rail-random" @click="randomQuestion"><el-icon><RefreshRight /></el-icon> 随机一题</button>
      </aside>
    </div>

    <!-- 本题速览 + 相关知识点：右下角悬浮跟随卡（固定视口，可折叠，支持 Markdown） -->
    <div class="qf-float" v-if="q && !embedded" :class="{ collapsed: qfCollapsed }">
      <div class="qf-head" @click="qfCollapsed && (qfCollapsed = false)">
        <span class="qf-title">
          <span class="qf-dot" :style="{ background: modColor(q.level1) }"></span>
          <template v-if="qfCollapsed">{{ typeShort }} · 速览</template>
          <template v-else><el-icon><Document /></el-icon> 本题速览</template>
        </span>
        <div class="qf-head-right">
          <button v-if="!qfCollapsed" class="qf-ibtn" :class="{ on: isFav }" @click.stop="toggleFav" :title="isFav ? '取消收藏' : '收藏'"><el-icon><Star /></el-icon></button>
          <button class="qf-ibtn" @click.stop="qfCollapsed = !qfCollapsed" :title="qfCollapsed ? '展开' : '收起'">
            <el-icon><component :is="qfCollapsed ? 'CaretTop' : 'CaretBottom'" /></el-icon>
          </button>
        </div>
      </div>
      <div v-show="!qfCollapsed" class="qf-body">
        <div class="qf-q md-body" :class="{ clamp: !qfExpanded }" v-html="md(q.question_raw || '（无题干）')"></div>
        <button class="qf-expand" v-if="!qfExpanded" @click="qfExpanded = true">展开题面 ▾</button>
        <button class="qf-expand" v-else @click="qfExpanded = false">收起题面 ▴</button>
        <div class="qf-answer">
          <span class="qf-a-label">正确答案</span>
          <b>{{ qfReveal ? (q.answer || '—') : '• • •' }}</b>
          <button class="qf-reveal" @click="qfReveal = !qfReveal">{{ qfReveal ? '隐藏' : '显示' }}</button>
        </div>

        <div class="qf-kg" v-if="relatedKb.length">
          <div class="qf-kg-title"><el-icon><Reading /></el-icon> 相关知识点</div>
          <div class="qf-kg-list">
            <button v-for="k in relatedKb.slice(0, 6)" :key="k.id" class="qf-kg-item" @click="goKnowledge(k)">
              <span class="qf-kg-dot" :style="{ background: kgTypeColor(k.kg_type) }"></span>
              <span class="qf-kg-name">{{ k.title }}</span>
            </button>
          </div>
          <button class="qf-kg-more" @click="goKnowledge()">查看知识库全部 ›</button>
        </div>
      </div>
    </div>

    <!-- 重新归类 -->
    <el-dialog v-model="reclassVisible" title="重新归类" width="440px" align-center>
      <p class="rc-tip">选择该题应归属的考点节点（按题型树精确归类，修正 AI 误判）：</p>
      <div class="rc-tree">
        <CategoryTree v-if="store.categoryTree.length" :nodes="store.categoryTree" :selectable="true" @select="onTreeSelect" />
      </div>
      <div v-if="selectedNode" class="rc-path">
        目标：<b>{{ pathText(selectedNode) }}</b>
      </div>
      <template #footer>
        <button class="btn-default" @click="reclassVisible = false">取消</button>
        <button class="btn-primary" :disabled="!selectedNode" @click="confirmReclassify">确认归类</button>
      </template>
    </el-dialog>

    <!-- 生成备考笔记 -->
    <div v-if="noteVisible" class="modal-overlay" @click="noteVisible = false">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3><el-icon><Notebook /></el-icon> 生成备考笔记</h3>
          <button class="btn-icon" @click="noteVisible = false"><el-icon><Close /></el-icon></button>
        </div>
        <div class="modal-body">
          <div class="note-tip">
            <b>方式一（推荐）</b>：直接点上方「一键生成笔记」，系统会从本题已解析的题型/知识点/思路/技巧自动拼装备考笔记，无需再往返 AI。<br/>
            <b>方式二</b>：回到 AI 对话回复「需要」，把返回内容整段粘贴到下方即可。
          </div>
          <textarea v-model="noteInput" class="note-input" rows="12" placeholder="粘贴 AI 返回的备考笔记 Markdown 内容…"></textarea>
          <div v-if="notePreview" class="note-preview">
            <div class="np-title">预览</div>
            <pre v-if="notePreview.question_display" class="np-code">{{ notePreview.question_display }}</pre>
            <div v-if="notePreview.type_judgment" class="np-row"><b>题型判定：</b><span class="md-body md-inline" v-html="mdi(notePreview.type_judgment)"></span></div>
            <div v-if="notePreview.knowledge_points" class="np-row"><b>知识点：</b><span class="md-body md-inline" v-html="mdi(notePreview.knowledge_points)"></span></div>
            <div v-if="notePreview.solve_steps" class="np-block"><b>解题步骤</b><div class="md-body" v-html="md(notePreview.solve_steps)"></div></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-default" @click="previewNote" :disabled="!noteInput"><el-icon><View /></el-icon> 预览</button>
          <button class="btn-primary" @click="saveNote" :disabled="!noteInput || noteLoading">
            {{ noteLoading ? '入库中…' : '入库' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { questionApi, noteApi, reviewApi, knowledgeApi } from '../api'
import { useAppStore } from '../stores/app'
import { ElMessage } from 'element-plus'
import { renderMarkdown, renderInline } from '../utils/md'
import CategoryTree from '../components/CategoryTree.vue'
import { MOD_FUNCTIONS, modStyle, modColor, FUNCTION_FIELD_LABELS, kgStyle, KG_TYPES } from '../utils/constants'

const props = defineProps({
  questionId: { type: Number, default: null },
  embedded: { type: Boolean, default: false },
})
const emit = defineEmits(['reclassified'])

const md = renderMarkdown
const mdi = renderInline
const mdInline = renderInline

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const q = ref(null)
const loading = ref(true)
const noteLoading = ref(false)
const noteVisible = ref(false)
const noteInput = ref('')
const notePreview = ref(null)
const genLoading = ref(false)
const reclassVisible = ref(false)
const selectedNode = ref(null)

// 练习模式：study（展示全部）/ practice（先隐藏解析）
const mode = ref(localStorage.getItem('gk_detailMode') || 'study')
const revealed = ref(true)
const elapsed = ref(0)
let timerId = null

const ERROR_REASONS = ['计算错误', '概念模糊', '粗心大意', '方法不当', '审题偏差', '其他']
const reasonOpen = ref(false)

const effectiveId = computed(() =>
  props.questionId ?? (route.params.id ? Number(route.params.id) : null)
)
const isFav = computed(() => !!(q.value && q.value.is_favorite))
const qfReveal = ref(false)
const qfExpanded = ref(false)
const qfCollapsed = ref(false)
const relatedKb = ref([])
const kgTypeColor = (t) => (KG_TYPES.find(x => x.key === t) || {}).color || '#64748b'
const typeShort = computed(() => {
  if (!q.value) return ''
  const t = (q.value.level2 && q.value.level2 !== '全部') ? q.value.level2 : (q.value.level1 || '')
  return t.length > 6 ? t.slice(0, 6) : t
})

// 详情页各板块可折叠：详细解题步骤（sec-step）默认展开，其余默认收起
const collapsed = reactive({})
function isCollapsed(id) {
  if (collapsed[id] === undefined) return id !== 'sec-step'
  return collapsed[id]
}
function toggleSec(id) {
  collapsed[id] = !isCollapsed(id)
}

// 题型专属功能（单一事实源：模块 → 功能）
const modFuncs = computed(() => (q.value && MOD_FUNCTIONS[q.value.level1]) || [])
const activeFunc = ref(null)
const funcCard = computed(() => {
  if (!activeFunc.value || !q.value) return []
  return activeFunc.value.fields
    .map(f => ({ label: FUNCTION_FIELD_LABELS[f] || f, value: q.value[f] || '' }))
    .filter(x => (x.value || '').trim())
})
function runFunc(fn) { activeFunc.value = fn }

const crumb = computed(() => {
  if (!q.value) return []
  return [q.value.level1, q.value.level2, q.value.level3, q.value.level4, q.value.level5].filter(Boolean)
})

const showSolutions = computed(() => mode.value === 'study' || revealed.value)

// 本考点（同 level2，缺省回退 level1）题目列表 → 上下题 + 进度
const related = ref([])
const posIndex = computed(() => related.value.findIndex(x => x.id === effectiveId.value))
const prev = computed(() => (posIndex.value > 0 ? related.value[posIndex.value - 1] : null))
const next = computed(() => (posIndex.value >= 0 && posIndex.value < related.value.length - 1 ? related.value[posIndex.value + 1] : null))

async function loadRelated() {
  if (!q.value) return
  // “全部”是题型树容器名，非真实子型；空或容器名时按模块（level1）聚合兄弟题
  const l2 = (q.value.level2 && q.value.level2 !== '全部') ? q.value.level2 : ''
  const l1 = q.value.level1
  try {
    const res = await questionApi.getList({ page: 1, page_size: 5000, sort: 'old', ...(l2 ? { level2: l2 } : { level1: l1 }) })
    related.value = (res.data.items || []).slice()
  } catch { related.value = [] }
}

function loadQuestion() {
  if (!effectiveId.value) return
  loading.value = true
  activeFunc.value = null
  reasonOpen.value = false
  // 切换题目时重置答题模式状态
  revealed.value = mode.value === 'study'
  stopTimer(); elapsed.value = 0
  return questionApi.get(effectiveId.value)
    .then(res => { q.value = res.data })
    .catch(() => ElMessage.error('加载失败'))
    .finally(() => { loading.value = false })
}

// 本地回写，避免整页重载
function applyQpatch(patch) {
  if (!q.value) return
  q.value = { ...q.value, ...patch }
}

async function setMaster(v) {
  if (!q.value) return
  try {
    await questionApi.update(q.value.id, { master_level: v })
    applyQpatch({ master_level: v })
    ElMessage.success('掌握度已更新')
  } catch (e) { ElMessage.error('更新失败：' + (e.response?.data?.detail || e.message)) }
}

function toggleError() {
  if (!q.value) return
  if (q.value.is_error) {
    updateError(false, '')
  } else {
    reasonOpen.value = true
  }
}
async function pickReason(r) {
  reasonOpen.value = false
  await updateError(true, r)
}
async function updateError(isError, reason) {
  if (!q.value) return
  try {
    await questionApi.update(q.value.id, { is_error: isError, error_reason: reason })
    applyQpatch({ is_error: isError, error_reason: reason })
    await store.loadCategories()  // 同步题型树错题计数
    ElMessage.success(isError ? '已标记为错题' : '已取消错题标记')
  } catch (e) { ElMessage.error('更新失败：' + (e.response?.data?.detail || e.message)) }
}

function setMode(m) {
  mode.value = m
  localStorage.setItem('gk_detailMode', m)
  if (m === 'practice') {
    revealed.value = false
    startTimer()
  } else {
    revealed.value = true
    stopTimer()
  }
}
function reveal() {
  revealed.value = true
  stopTimer()
  if (q.value) questionApi.update(q.value.id, { cost_time: elapsed.value }).catch(() => {})
}
function startTimer() {
  stopTimer()
  timerId = setInterval(() => { elapsed.value++ }, 1000)
}
function stopTimer() {
  if (timerId) { clearInterval(timerId); timerId = null }
}
function fmtTime(s) {
  const m = Math.floor(s / 60), ss = s % 60
  return `${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
}

function goTo(item) {
  if (!item || item.id === effectiveId.value) return
  // 离开前若处于答题模式，记录用时
  if (mode.value === 'practice' && timerId) {
    stopTimer()
    if (q.value) questionApi.update(q.value.id, { cost_time: elapsed.value }).catch(() => {})
  }
  router.push(`/question/${item.id}`)
}
function goBack() {
  const cat = currentCatId()
  router.push(cat ? `/question-list?cat=${cat}` : '/question-list')
}
function currentCatId() {
  if (!q.value) return null
  const lv = [q.value.level1, q.value.level2, q.value.level3, q.value.level4, q.value.level5].filter(Boolean)
  const hit = store.categoryFlat.find(c => {
    const cl = [c.level1, c.level2, c.level3, c.level4, c.level5].filter(Boolean)
    if (cl.length !== lv.length) return false
    return cl.every((v, i) => v === lv[i])
  })
  return hit ? hit.id : null
}

// 键盘快捷键
function onKey(e) {
  const tg = e.target
  if (tg && (tg.tagName === 'INPUT' || tg.tagName === 'TEXTAREA' || tg.isContentEditable)) return
  if (e.key === 'j' || e.key === 'J' || e.key === 'ArrowRight') { e.preventDefault(); goTo(next.value) }
  else if (e.key === 'k' || e.key === 'K' || e.key === 'ArrowLeft') { e.preventDefault(); goTo(prev.value) }
  else if (e.key === ' ') {
    if (mode.value === 'practice' && !revealed.value) { e.preventDefault(); reveal() }
  }
  else if (e.key === 'e' || e.key === 'E') { toggleError() }
  else if (e.key === 'f' || e.key === 'F') { toggleFav() }
}

async function toggleFav() {
  if (!q.value) return
  try {
    await questionApi.update(q.value.id, { is_favorite: !q.value.is_favorite })
    applyQpatch({ is_favorite: !q.value.is_favorite })
    ElMessage.success(q.value.is_favorite ? '已收藏' : '已取消收藏')
  } catch (e) { ElMessage.error('操作失败：' + (e.response?.data?.detail || e.message)) }
}

async function loadRelatedKb() {
  if (!q.value) return
  try {
    const res = await knowledgeApi.byModule(q.value.level1)
    relatedKb.value = res.data.items || []
  } catch { relatedKb.value = [] }
}

function goKnowledge(k) {
  router.push(k ? `/knowledge?module=${encodeURIComponent(k.module)}#k${k.id}` : '/knowledge')
}

async function randomQuestion() {
  try {
    const res = await questionApi.getList({ page: 1, page_size: 5000 })
    const items = res.data.items || []
    if (!items.length) { ElMessage.warning('题库还没有题目'); return }
    const pick = items[Math.floor(Math.random() * items.length)]
    router.push(`/question/${pick.id}`)
  } catch { ElMessage.warning('获取题目失败') }
}

function openReclass() { reclassVisible.value = true; selectedNode.value = null }
function onTreeSelect(node) { selectedNode.value = node }
function pathText(n) {
  return [n.level1, n.level2, n.level3, n.level4, n.level5].filter(Boolean).join(' / ')
}
async function confirmReclassify() {
  if (!selectedNode.value || !q.value) return
  const n = selectedNode.value
  try {
    await questionApi.update(q.value.id, {
      level1: n.level1, level2: n.level2, level3: n.level3, level4: n.level4, level5: n.level5,
    })
    await store.loadCategories()
    reclassVisible.value = false
    ElMessage.success('已重新归类，题型树已更新')
    emit('reclassified', n)
    loadQuestion()
  } catch (e) {
    ElMessage.error('归类失败：' + (e.response?.data?.detail || e.message))
  }
}

function openNoteDialog() {
  noteInput.value = ''
  notePreview.value = null
  noteVisible.value = true
}
async function previewNote() {
  if (!noteInput.value) return
  try {
    const res = await noteApi.parseOnly({ ai_note_content: noteInput.value })
    notePreview.value = res.data.parsed
  } catch { ElMessage.warning('预览失败，可直接入库') }
}
async function saveNote() {
  if (!noteInput.value) return
  noteLoading.value = true
  try {
    await noteApi.fromAi({
      ai_note_content: noteInput.value,
      question_id: effectiveId.value,
      level5: q.value?.level5 || '',
    })
    ElMessage.success('备考笔记已入库，可在「笔记管理」查看')
    noteVisible.value = false
  } catch (e) {
    ElMessage.error('入库失败：' + (e.response?.data?.detail || e.message))
  } finally {
    noteLoading.value = false
  }
}
async function generateNote() {
  if (!q.value) return
  genLoading.value = true
  try {
    const res = await noteApi.generateFromQuestion({ question_id: effectiveId.value })
    ElMessage.success(res.data.message + '，已可在「笔记管理」查看')
  } catch (e) {
    ElMessage.error('生成失败：' + (e.response?.data?.detail || e.message))
  } finally {
    genLoading.value = false
  }
}
async function startReview() {
  await reviewApi.submit({ question_id: effectiveId.value, review_result: 'good', cost_time: elapsed.value })
  ElMessage.success('复习记录已提交')
  loadQuestion()
}
async function copyRaw() {
  try {
    await navigator.clipboard.writeText(q.value.ai_raw_content)
    ElMessage.success('已复制')
  } catch { ElMessage.warning('复制失败') }
}

watch(effectiveId, async () => {
  await loadQuestion()
  await loadRelated()
  await loadRelatedKb()
})
onMounted(async () => {
  if (!store.categoryTree.length) await store.loadCategories()
  await loadQuestion()
  await loadRelated()
  await loadRelatedKb()
  if (mode.value === 'practice') startTimer()
  window.addEventListener('keydown', onKey)
})
onUnmounted(() => {
  stopTimer()
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.qd-page { height: 100%; }
.qd-grid {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr) 280px;
  gap: 16px;
  height: 100%;
  align-items: start;
}
.qd-grid.embedded { grid-template-columns: minmax(0, 1fr); }

/* 左：题型树 */
.qd-tree {
  position: sticky; top: 0; align-self: start;
  max-height: 100%; display: flex; flex-direction: column;
  background: var(--bg-elevated); border: 1px solid var(--border-base);
  border-radius: 12px; overflow: hidden;
}
.qd-tree-head { padding: 14px 14px 10px; border-bottom: 1px solid var(--border-light); flex-shrink: 0; }
.qth-title { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: var(--text-primary); }
.qd-tree-scroll { flex: 1; overflow-y: auto; padding: 6px 8px; }
.qd-tree-loading { padding: 20px; color: var(--text-tertiary); font-size: 13px; }

/* 中：详情 */
.qd-main { min-width: 0; }

/* Hero（扁平） */
.hero {
  background: var(--bg-elevated);
  border: 1px solid var(--border-base); border-radius: 12px;
  padding: 16px 18px; margin-bottom: 12px;
}
.hero-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.hero-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.hero-meta { display: flex; align-items: center; gap: 10px; margin-top: 14px; flex-wrap: wrap; }
.mod-tag { font-size: 12.5px; font-weight: 500; padding: 3px 12px; border-radius: 999px; border: 1px solid transparent; }
.err-badge { font-size: 11px; font-weight: 700; color: #fff; background: var(--danger); padding: 2px 10px; border-radius: 999px; }
.meta-mastery { display: inline-flex; align-items: center; }
.meta-error { position: relative; display: inline-flex; align-items: center; }
.err-toggle {
  display: inline-flex; align-items: center; gap: 4px; font-size: 12px; cursor: pointer;
  padding: 4px 12px; border-radius: 999px; border: 1px solid var(--border-base);
  background: var(--bg-base); color: var(--text-secondary);
}
.err-toggle.on { color: #fff; background: var(--danger); border-color: var(--danger); }
.err-toggle:hover { border-color: var(--danger); color: var(--danger); }
.err-toggle.on:hover { color: #fff; }
.reason-pop { position: absolute; top: 34px; left: 0; z-index: 50; }
.reason-catch { position: fixed; inset: 0; }
.reason-menu {
  position: relative; background: var(--bg-elevated); border: 1px solid var(--border-light);
  border-radius: var(--radius-md); box-shadow: var(--shadow-md); padding: 6px; min-width: 150px;
}
.reason-title { font-size: 11px; color: var(--text-tertiary); padding: 4px 8px; }
.reason-item { display: block; width: 100%; text-align: left; background: none; border: none; padding: 7px 10px; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; color: var(--text-primary); }
.reason-item:hover { background: var(--bg-subtle); color: var(--primary); }

.hero-crumb { margin-top: 12px; font-size: 14px; color: var(--text-secondary); font-weight: 500; }
.crumb-seg { color: var(--primary); }
.crumb-sep { color: var(--text-tertiary); margin: 0 6px; }
.hero-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--bg-base); border: 1px solid var(--border-light);
  padding: 5px 12px; border-radius: 999px; font-size: 12px; color: var(--text-tertiary);
}
.chip i { font-style: normal; }
.chip b { color: var(--text-primary); font-weight: 600; }
.chip .stars { color: var(--warning); letter-spacing: 1px; }
.chip.answer { background: var(--success-bg); border-color: var(--success); }
.chip.answer b { color: var(--success); font-size: 15px; font-weight: 800; }
.chip.err { background: var(--danger-bg); border-color: var(--danger); }
.chip.err b { color: var(--danger); }

/* 卡片（扁平） */
.card {
  background: var(--bg-elevated); border-radius: 12px;
  border: 1px solid var(--border-base);
  margin-bottom: 12px; overflow: hidden; scroll-margin-top: 16px;
}
.card-head {
  padding: 12px 16px; border-bottom: 1px solid var(--border-light);
  border-left: 3px solid var(--primary); display: flex; align-items: center; gap: 8px;
}
.card-head.warn { border-left-color: var(--warning); }
.card-head.tip { border-left-color: var(--success); }
.card-head.step { border-left-color: var(--info); }
.card-head.practice { border-left-color: #db2777; }
.card-head .ico { font-size: 16px; color: var(--primary); }
.card-head.warn .ico { color: var(--warning); }
.card-head.tip .ico { color: var(--success); }
.card-head.step .ico { color: var(--info); }
.card-head.practice .ico { color: #db2777; }
.card-head.bg { border-left-color: #84cc16; }
.card-head.bg .ico { color: #84cc16; }
.card-head h3 { margin: 0; font-size: 14px; font-weight: 500; flex: 1; }
.card-body { padding: 16px; }

.question-text { font-size: 14px; line-height: 1.8; padding: 12px 14px; background: var(--bg-subtle); border-radius: var(--radius-md); color: var(--text-primary); }

.section { margin-bottom: 12px; }
.section:last-child { margin-bottom: 0; }
.section-label { font-size: 12px; color: var(--text-secondary); font-weight: 600; margin-bottom: 4px; }
.section-content { font-size: 13px; line-height: 1.7; color: var(--text-primary); padding: 10px 14px; background: var(--bg-subtle); border-radius: var(--radius-md); }
.section.success .section-content { background: var(--success-bg); }
.section.info .section-content { background: var(--info-bg); }

.trap-item { padding: 10px 14px; border-radius: var(--radius-md); margin-bottom: 8px; font-size: 13px; display: flex; align-items: flex-start; gap: 8px; line-height: 1.7; }
.trap-item.warning { background: var(--warning-bg); }
.trap-item.danger { background: var(--danger-bg); }
.trap-item.info { background: var(--info-bg); }
.trap-tag { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.6); flex-shrink: 0; color: var(--text-secondary); }

.step-content { font-size: 13px; line-height: 1.8; padding: 12px 14px; background: var(--bg-subtle); border-radius: var(--radius-md); color: var(--text-primary); }

.practice-q { font-size: 14px; line-height: 1.7; padding: 12px 14px; background: var(--bg-subtle); border-radius: var(--radius-md); margin-bottom: 12px; color: var(--text-primary); }
.practice-answer { font-size: 13px; color: var(--text-secondary); }
.practice-answer summary { cursor: pointer; color: var(--primary); font-weight: 500; margin-bottom: 8px; }

.raw-content { font-size: 12px; line-height: 1.6; max-height: 400px; overflow-y: auto; white-space: pre-wrap; word-break: break-word; padding: 12px; background: var(--bg-subtle); border-radius: var(--radius-md); font-family: 'Consolas', 'Monaco', monospace; }

/* 答题模式揭示横幅 */
.reveal-banner {
  text-align: center; padding: 40px 20px; margin-bottom: 16px; cursor: pointer;
  background: var(--bg-elevated); border: 1px dashed var(--border-base); border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm); transition: all 0.15s;
}
.reveal-banner:hover { border-color: var(--primary); background: var(--primary-bg); }
.rb-ico { font-size: 34px; color: var(--text-tertiary); }
.rb-text { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 10px 0 4px; }
.rb-sub { font-size: 12.5px; color: var(--text-tertiary); margin-bottom: 16px; }
.rb-sub b { color: var(--primary); }
.rb-btn { background: var(--primary); color: #fff; border: none; padding: 9px 22px; border-radius: var(--radius-md); cursor: pointer; font-size: 14px; font-weight: 500; }
.rb-btn:hover { background: var(--primary-dark); }

/* 题型专属功能 */
.card-head.func { border-left-color: #8b5cf6; }
.card-head.func .ico { color: #8b5cf6; }
.func-btns { display: flex; flex-wrap: wrap; gap: 8px; }
.func-btn {
  display: inline-flex; align-items: center; gap: 5px; font-size: 13px;
  padding: 7px 14px; border-radius: var(--radius-md); cursor: pointer;
  background: var(--bg-subtle); border: 1px solid var(--border-base); color: var(--text-secondary);
  transition: all 0.15s;
}
.func-btn:hover { color: #8b5cf6; border-color: #8b5cf6; }
.func-btn.on { color: #fff; background: #8b5cf6; border-color: #8b5cf6; }
.func-btn .el-icon { font-size: 15px; }
.func-card { margin-top: 14px; padding: 14px; border-radius: var(--radius-md); background: var(--bg-subtle); border: 1px solid var(--border-light); }
.fc-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.fc-head b { color: #8b5cf6; font-size: 14px; }
.fc-desc { font-size: 12px; color: var(--text-tertiary); flex: 1; }
.fc-close { margin-left: auto; background: none; border: none; cursor: pointer; color: var(--text-tertiary); display: flex; }
.fc-close:hover { color: var(--danger); }
.fc-row { margin-bottom: 10px; }
.fc-row:last-child { margin-bottom: 0; }
.fc-label { font-size: 12px; color: var(--text-secondary); font-weight: 600; margin-bottom: 4px; }
.fc-val { font-size: 13px; line-height: 1.7; color: var(--text-primary); padding: 10px 14px; background: var(--bg-elevated); border-radius: var(--radius-md); }
.fc-empty { font-size: 12.5px; color: var(--text-tertiary); }

/* 右：控制 + 悬浮跟随卡 */
.qd-rail { display: flex; flex-direction: column; gap: 12px; align-self: start; padding-bottom: 96px; }
.rail-card { background: var(--bg-elevated); border: 1px solid var(--border-base); border-radius: 12px; padding: 14px; }
.rail-card.mode-card { position: sticky; top: 0; z-index: 21; }
.rc-title { font-size: 12px; font-weight: 500; color: var(--text-tertiary); margin-bottom: 10px; letter-spacing: 0.3px; }

.seg { display: flex; background: var(--bg-subtle); border-radius: var(--radius-md); padding: 3px; gap: 3px; }
.seg-btn { flex: 1; border: none; background: none; padding: 7px 0; border-radius: var(--radius-sm); cursor: pointer; font-size: 13px; color: var(--text-secondary); transition: all 0.15s; }
.seg-btn.on { background: var(--bg-elevated); color: var(--primary); font-weight: 700; box-shadow: var(--shadow-sm); }
.mode-hint { font-size: 12px; color: var(--text-tertiary); margin-top: 10px; line-height: 1.6; }
.mode-hint .timer { display: inline-flex; align-items: center; gap: 4px; color: var(--primary); font-weight: 600; margin-right: 6px; }

.pos { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; }
.pos b { color: var(--primary); font-size: 16px; font-weight: 800; }
.pos-sub { font-size: 11px; color: var(--text-tertiary); }
.nav-btns { display: flex; gap: 6px; }
.nav-btn { flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 4px; background: var(--bg-subtle); border: 1px solid var(--border-base); color: var(--text-secondary); padding: 8px 6px; border-radius: var(--radius-md); cursor: pointer; font-size: 12.5px; transition: all 0.15s; }
.nav-btn:hover:not(:disabled) { color: var(--primary); border-color: var(--primary); }
.nav-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.kb-hint { margin-top: 10px; font-size: 11px; color: var(--text-tertiary); }
.kb-hint kbd { background: var(--bg-subtle); border: 1px solid var(--border-base); border-radius: 4px; padding: 1px 5px; font-size: 11px; font-family: monospace; }

.sib-list { display: flex; flex-direction: column; gap: 6px; max-height: 360px; overflow-y: auto; }
.sib-item { display: flex; align-items: center; gap: 8px; padding: 9px 11px; border-radius: var(--radius-md); cursor: pointer; text-align: left; background: var(--bg-subtle); border: 1px solid transparent; transition: all 0.12s; }
.sib-item:hover { background: var(--bg-elevated); border-color: var(--border-base); }
.sib-item.on { background: var(--primary-bg); border-color: var(--primary); }
.sib-item.err { border-left: 3px solid var(--danger); }
.sib-diff { font-size: 9px; color: var(--warning); letter-spacing: -1px; flex-shrink: 0; width: 30px; overflow: hidden; white-space: nowrap; }
.sib-text { flex: 1; min-width: 0; font-size: 12.5px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.5; }
.sib-text :deep(p) { margin: 0; display: inline; }

/* 右下角悬浮跟随卡：固定视口，可折叠，扁平 */
.qf-float {
  position: fixed; right: 20px; bottom: 20px; z-index: 60; width: 320px;
  background: var(--bg-elevated); border: 1px solid var(--border-base);
  border-radius: 12px; box-shadow: var(--shadow-lg);
  display: flex; flex-direction: column; max-height: calc(100vh - 120px);
}
.qf-float.collapsed { width: 200px; }
.qf-head {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  padding: 10px 12px; border-bottom: 1px solid var(--border-light); flex-shrink: 0;
}
.qf-float.collapsed .qf-head { border-bottom: none; cursor: pointer; }
.qf-title { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: var(--text-primary); min-width: 0; }
.qf-title .el-icon { font-size: 14px; color: var(--text-tertiary); }
.qf-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.qf-head-right { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
.qf-ibtn { background: transparent; border: none; width: 26px; height: 26px; border-radius: var(--radius-sm); cursor: pointer; color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 14px; transition: all 0.12s; }
.qf-ibtn:hover { background: var(--bg-subtle); color: var(--text-secondary); }
.qf-ibtn.on { color: #f59e0b; }
.qf-body { padding: 12px; overflow-y: auto; }
.qf-q { font-size: 13px; line-height: 1.7; color: var(--text-secondary); }
.qf-q.clamp { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.qf-q :deep(p) { margin: 0 0 4px; }
.qf-expand { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 12px; padding: 4px 0 0; }
.qf-answer { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding: 8px 12px; border-radius: 8px; background: var(--success-bg); }
.qf-a-label { font-size: 12px; color: var(--success); opacity: 0.85; }
.qf-answer b { font-size: 15px; font-weight: 500; letter-spacing: 1px; color: var(--success); }
.qf-reveal { margin-left: auto; background: transparent; border: 1px solid var(--success); color: var(--success); cursor: pointer; font-size: 11.5px; padding: 2px 10px; border-radius: 999px; }
.qf-reveal:hover { background: var(--success); color: #fff; }
.qf-kg { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border-light); }
.qf-kg-title { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 500; color: var(--text-secondary); margin-bottom: 8px; }
.qf-kg-title .el-icon { color: #8b5cf6; }
.qf-kg-list { display: flex; flex-direction: column; gap: 2px; }
.qf-kg-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 7px; cursor: pointer; text-align: left; background: transparent; border: none; transition: background 0.12s; }
.qf-kg-item:hover { background: var(--bg-subtle); }
.qf-kg-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.qf-kg-name { flex: 1; min-width: 0; font-size: 12.5px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.qf-kg-more { width: 100%; margin-top: 6px; background: none; border: none; color: var(--text-tertiary); cursor: pointer; font-size: 12px; text-align: right; }
.qf-kg-more:hover { color: #8b5cf6; }

/* 随机一题 */
.rail-random { width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 11px 0; border-radius: var(--radius-md); border: 1px dashed var(--border-base); background: var(--bg-elevated); color: var(--text-secondary); cursor: pointer; font-size: 13px; transition: all 0.15s; }
.rail-random:hover { color: var(--primary); border-color: var(--primary); border-style: solid; }

/* 按钮 */
.btn-primary { background: var(--primary); color: #fff; border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; display: inline-flex; align-items: center; gap: 5px; }
.btn-primary:hover { background: var(--primary-dark); }
.btn-primary:disabled { opacity: 0.5; }
.btn-default { background: var(--bg-subtle); color: var(--text-secondary); border: 1px solid var(--border-base); padding: 8px 14px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; display: inline-flex; align-items: center; gap: 5px; }
.btn-default:hover { color: var(--primary); border-color: var(--primary); }
.btn-default.pinned, .btn-default.pinned:hover { color: var(--primary); border-color: var(--primary); background: var(--primary-bg); }
.btn-default.small { padding: 4px 12px; font-size: 12px; }
.btn-ghost { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 13px; padding: 4px 0; display: inline-flex; align-items: center; gap: 4px; }
.btn-ghost:hover { color: var(--primary); }

/* 重新归类 */
.rc-tip { font-size: 12.5px; color: var(--text-secondary); line-height: 1.7; margin: 0 0 10px; }
.rc-tree { max-height: 320px; overflow-y: auto; border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 6px; }
.rc-path { margin-top: 10px; font-size: 13px; color: var(--text-secondary); }
.rc-path b { color: var(--primary); }

/* 生成笔记弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-elevated); border-radius: var(--radius-lg); width: 720px; max-width: 92vw; max-height: 86vh; display: flex; flex-direction: column; }
.modal-header { padding: 16px 20px; border-bottom: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.modal-header h3 { margin: 0; font-size: 16px; display: flex; align-items: center; gap: 6px; }
.modal-body { padding: 20px; overflow-y: auto; flex: 1; }
.modal-footer { padding: 16px 20px; border-top: 1px solid var(--border-light); display: flex; justify-content: flex-end; gap: 8px; }
.btn-icon { background: var(--bg-subtle); border: none; width: 28px; height: 28px; border-radius: var(--radius-sm); cursor: pointer; display: flex; align-items: center; justify-content: center; }
.btn-icon:hover { color: var(--danger); }
.note-tip { font-size: 12px; color: var(--text-secondary); line-height: 1.7; padding: 10px 12px; background: var(--warning-bg); border-radius: var(--radius-md); margin-bottom: 12px; }
.note-input { width: 100%; padding: 12px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 13px; background: var(--bg-base); color: var(--text-primary); font-family: 'Consolas', 'Monaco', monospace; resize: vertical; }
.note-input:focus { outline: none; border-color: var(--primary); }
.note-preview { margin-top: 16px; padding: 14px; background: var(--bg-subtle); border-radius: var(--radius-md); border: 1px solid var(--border-light); }
.np-title { font-size: 12px; color: var(--text-tertiary); font-weight: 600; margin-bottom: 8px; }
.np-code { background: var(--bg-elevated); padding: 10px; border-radius: var(--radius-sm); font-size: 12px; white-space: pre-wrap; font-family: 'Consolas', 'Monaco', monospace; border: 1px solid var(--border-light); margin: 0 0 10px; }
.np-row { font-size: 13px; margin-bottom: 6px; line-height: 1.7; }
.np-block { font-size: 13px; margin-top: 8px; }
.np-block b { display: block; margin-bottom: 4px; }

@media (max-width: 1100px) {
  /* 窄屏：收起右侧控制栏，右下角悬浮跟随卡独立常驻，正文占满，右侧不留白 */
  .qd-grid { grid-template-columns: 220px minmax(0, 1fr); }
  .qd-rail { display: none; }
}
@media (max-width: 760px) {
  .qd-grid { grid-template-columns: minmax(0, 1fr); }
  .qd-tree { display: none; }
  .qf-float { right: 12px; bottom: 12px; width: calc(100vw - 24px); max-width: 340px; }
}
</style>
