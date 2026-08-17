<template>
  <div class="sl-page">
    <!-- 左：分类导航（按模块 / 按类型 / 按考点 三重维度） -->
    <aside class="sl-side">
      <div class="sl-side-head"><el-icon><Lightning /></el-icon> 解题库</div>
      <div class="sl-nav">
        <button class="sl-nav-item" :class="{ on: activeModule === 'all' && activeType === 'all' && !kaodianPath.length }" @click="reset">
          <span class="sl-nav-dot" style="background: #64748b"></span>
          <span class="sl-nav-name">全部</span>
          <span class="sl-nav-n">{{ allItems.length }}</span>
        </button>
      </div>

      <div class="sl-side-sec">按模块</div>
      <div class="sl-nav">
        <button v-for="m in MODULES" :key="m" class="sl-nav-item" :class="{ on: activeModule === m && !kaodianPath.length }" @click="setModule(m)">
          <span class="sl-nav-dot" :style="{ background: modColor(m) }"></span>
          <span class="sl-nav-name">{{ m }}</span>
          <span class="sl-nav-n">{{ moduleCount(m) }}</span>
        </button>
      </div>

      <div class="sl-side-sec">按类型</div>
      <div class="sl-nav">
        <button v-for="t in SOLVE_TYPES" :key="t.key" class="sl-nav-item" :class="{ on: activeType === t.key && !kaodianPath.length }" @click="setType(t.key)">
          <span class="sl-nav-dot" :style="{ background: t.color }"></span>
          <span class="sl-nav-name">{{ t.key }}</span>
          <span class="sl-nav-n">{{ typeCount(t.key) }}</span>
        </button>
      </div>

      <div class="sl-side-sec">按考点</div>
      <div class="sl-nav sl-nav-kaodian">
        <template v-for="n1 in kaodianTree" :key="'k1-' + n1.path.join('>')">
          <button class="sl-nav-item sl-kd" :class="{ on: isKdActive(n1.path) }" @click="onKaodian(n1.path)">
            <span v-if="n1.children.length" class="sl-kd-caret" @click.stop="toggleKdExpand(n1.path.join('>'))">{{ expandedKd.has(n1.path.join('>')) || isKdActive(n1.path) ? '▾' : '▸' }}</span>
            <span v-else class="sl-kd-caret empty"></span>
            <span class="sl-nav-name sl-kd-name">{{ n1.name }}</span>
            <span class="sl-nav-n">{{ n1.count }}</span>
          </button>
          <template v-if="n1.children.length && (expandedKd.has(n1.path.join('>')) || isKdActive(n1.path))">
            <button v-for="n2 in n1.children" :key="'k2-' + n2.path.join('>')" class="sl-nav-item sl-kd lvl2" :class="{ on: isKdActive(n2.path) }" @click="onKaodian(n2.path)">
              <span v-if="n2.children.length" class="sl-kd-caret" @click.stop="toggleKdExpand(n2.path.join('>'))">{{ expandedKd.has(n2.path.join('>')) || isKdActive(n2.path) ? '▾' : '▸' }}</span>
              <span v-else class="sl-kd-caret empty"></span>
              <span class="sl-nav-name sl-kd-name">{{ n2.name }}</span>
              <span class="sl-nav-n">{{ n2.count }}</span>
            </button>
            <button v-for="n3 in n2Children(n1)" :key="'k3-' + n3.path.join('>')" class="sl-nav-item sl-kd lvl3" :class="{ on: isKdActive(n3.path) }" @click="onKaodian(n3.path)">
              <span class="sl-kd-caret empty"></span>
              <span class="sl-nav-name sl-kd-name">{{ n3.name }}</span>
              <span class="sl-nav-n">{{ n3.count }}</span>
            </button>
          </template>
        </template>
        <div v-if="!kaodianTree.length" class="sl-nav-empty">暂无考点</div>
      </div>
    </aside>

    <!-- 右：解题内容 -->
    <section class="sl-main">
      <div class="sl-toolbar">
        <div class="sl-search">
          <el-icon class="sl-ico"><Search /></el-icon>
          <input v-model="keyword" placeholder="搜索解题条目标题 / 内容 / 标签…" />
        </div>
        <div class="sl-tools">
          <div class="sl-view">
            <button class="sl-view-btn" :class="{ on: viewMode === 'flat' }" @click="viewMode = 'flat'" title="平铺">平铺</button>
            <button class="sl-view-btn" :class="{ on: viewMode === 'byModule' }" @click="viewMode = 'byModule'" title="按模块分组">按模块</button>
            <button class="sl-view-btn" :class="{ on: viewMode === 'byType' }" @click="viewMode = 'byType'" title="按类型分组">按类型</button>
            <button class="sl-view-btn" :class="{ on: viewMode === 'byKaodian' }" @click="viewMode = 'byKaodian'" title="按考点分组">按考点</button>
          </div>
          <select v-model="sortMode" class="sl-select">
            <option value="default">默认排序</option>
            <option value="title">按标题</option>
            <option value="difficulty">难度↓</option>
            <option value="updated">最近更新</option>
          </select>
          <button class="sl-act" @click="showCreate = true"><el-icon><Plus /></el-icon> 新建</button>
          <button class="sl-act" @click="openBatch"><el-icon><Upload /></el-icon> 批量导入</button>
          <button class="sl-act primary" @click="showPrompt = true"><el-icon><MagicStick /></el-icon> 提示词助手</button>
        </div>
      </div>

      <div class="sl-filterbar" v-if="kaodianPath.length">
        <span class="sl-filter-chip">考点筛选：<b>{{ kaodianPath.join(' › ') }}</b>
          <button class="sl-filter-x" @click="onKaodian([])">×</button>
        </span>
        <span class="sl-filter-hint">点击卡片上的考点面包屑可定位到对应位置</span>
      </div>

      <div class="sl-scroll">
        <template v-if="filtered.length">
          <div v-for="g in displayGroups" :key="g.key" class="sl-group" :class="{ flat: viewMode === 'flat' }">
            <div class="sl-group-head" v-if="viewMode !== 'flat'" :style="{ '--gc': g.color }">
              <span class="sl-group-dot" :style="{ background: g.color }"></span>
              <span class="sl-group-name">{{ g.label }}</span>
              <span class="sl-group-n">{{ g.items.length }} 条</span>
            </div>
            <div class="sl-list">
              <article v-for="k in g.items" :key="k.id" :id="'s' + k.id" class="sl-card"
                :style="{ '--tc': solveTypeColor(k.solve_type) }" @click="openDetail(k)">
                <div class="sl-card-head">
                  <span class="sl-tag" :style="{ color: solveTypeColor(k.solve_type) }">
                    <span class="sl-tag-dot" :style="{ background: solveTypeColor(k.solve_type) }"></span>{{ k.solve_type }}
                  </span>
                  <span class="sl-mod"><span class="sl-mod-dot" :style="{ background: modColor(k.module) }"></span>{{ k.module }}</span>
                  <span class="sl-card-ops">
                    <button class="sl-op" @click.stop="editItem(k)" title="编辑"><el-icon><Edit /></el-icon></button>
                    <button class="sl-op danger" @click.stop="removeItem(k)" title="删除"><el-icon><Delete /></el-icon></button>
                  </span>
                </div>
                <h3 class="sl-title">{{ cardTitle(k) }}</h3>
                <div class="sl-tags" v-if="cardTags(k).length">
                  <span v-for="t in cardTags(k)" :key="t" class="sl-tagchip" @click.stop="onKaodian([t])">{{ t }}</span>
                </div>
                <div class="sl-summary" v-if="cardSummary(k)" @click.stop>{{ cardSummary(k) }}</div>
                <div class="sl-content md-body" v-else :class="{ clamp: !expanded.has(k.id) }" v-html="md(k.content)"></div>
                <button v-if="!cardSummary(k) && k.content && k.content.length > 120" class="sl-expand" @click.stop="toggleExpand(k.id)">
                  {{ expanded.has(k.id) ? '收起' : '展开全文' }}
                </button>
                <div class="sl-crumb" v-if="pathArr(k).length" @click.stop>
                  <el-icon class="sl-crumb-ico"><Location /></el-icon>
                  <button v-for="(lv, i) in pathArr(k)" :key="i" class="sl-crumb-item"
                    :class="{ on: kaodianPath.length === i + 1 && kaodianPath[i] === lv }"
                    @click="onKaodian(pathArr(k).slice(0, i + 1))">{{ lv }}</button>
                </div>
                <div class="sl-foot">
                  <span class="sl-rel" v-if="k.source" title="来源">{{ k.source }}</span>
                  <div class="sl-foot-right">
                    <button v-if="k.source_question_id" class="sl-source" @click.stop="goSource(k.source_question_id)" title="查看来源题目">
                      <el-icon><Link /></el-icon>来源题目
                    </button>
                    <button class="sl-practice" @click.stop="goPractice(k.module)"><el-icon><Promotion /></el-icon> 练该模块题</button>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </template>
        <EmptyState v-else-if="isEmptyLibrary" icon="DocumentDelete" title="解题库还是空的"
          desc="建议先用「提示词助手」让 AI 帮你生成一批可复用解题模板，或手动新建 / 批量导入。">
          <template #actions>
            <button class="btn-primary" @click="showPrompt = true"><el-icon><MagicStick /></el-icon> 提示词助手</button>
            <button class="btn-default" @click="showCreate = true"><el-icon><Plus /></el-icon> 新建</button>
            <button class="btn-default" @click="openBatch"><el-icon><Upload /></el-icon> 批量导入</button>
          </template>
        </EmptyState>
        <EmptyState v-else icon="🔍" :title="kaodianPath.length ? '该考点下没有匹配的解题条目' : '没有匹配的解题条目'"
          desc="试着调整左侧筛选、搜索词或视图模式。">
          <template #actions>
            <button v-if="hasFilter" class="btn-default" @click="reset">清除筛选</button>
          </template>
        </EmptyState>
      </div>
    </section>

    <!-- 详情抽屉 -->
    <el-dialog v-model="showDetail" :title="detailItem ? detailItem.title : ''" width="640px" align-center @closed="detailItem = null">
      <div class="sl-detail" v-if="detailItem">
        <div class="sl-detail-meta">
          <span class="sl-tag" :style="{ color: solveTypeColor(detailItem.solve_type) }">
            <span class="sl-tag-dot" :style="{ background: solveTypeColor(detailItem.solve_type) }"></span>{{ detailItem.solve_type }}
          </span>
          <span class="sl-mod"><span class="sl-mod-dot" :style="{ background: modColor(detailItem.module) }"></span>{{ detailItem.module }}</span>
          <span class="sl-diff" v-if="detailItem.difficulty">{{ '●'.repeat(detailItem.difficulty) }}<i>{{ '●'.repeat(5 - detailItem.difficulty) }}</i></span>
        </div>
        <div class="sl-crumb" v-if="pathArr(detailItem).length">
          <el-icon class="sl-crumb-ico"><Location /></el-icon>
          <span v-for="(lv, i) in pathArr(detailItem)" :key="i" class="sl-crumb-static">{{ lv }}</span>
        </div>
        <div class="sl-detail-cardinfo" v-if="cardSummary(detailItem)">
          <div class="sl-detail-summary">{{ cardSummary(detailItem) }}</div>
          <div class="sl-detail-tags" v-if="cardTags(detailItem).length">
            <span v-for="t in cardTags(detailItem)" :key="t" class="sl-tagchip">{{ t }}</span>
          </div>
        </div>
        <div class="sl-detail-content md-body" v-html="md(detailItem.content)"></div>
        <div class="sl-detail-foot" v-if="detailItem.tags">
          <span v-for="t in detailItem.tags.split(/[，,/、]/).filter(Boolean)" :key="t" class="sl-tagslice">#{{ t }}</span>
        </div>
        <div class="sl-detail-ops">
          <button v-if="detailItem.source_question_id" class="btn-default" @click="goSource(detailItem.source_question_id)"><el-icon><Link /></el-icon> 查看来源题目</button>
          <button class="btn-default" @click="editFromDetail"><el-icon><Edit /></el-icon> 编辑</button>
          <button class="btn-default danger" @click="removeFromDetail"><el-icon><Delete /></el-icon> 删除</button>
        </div>
      </div>
    </el-dialog>

    <!-- 新建 / 编辑 -->
    <el-dialog v-model="showCreate" :title="editing ? '编辑解题条目' : '新建解题条目'" width="560px" align-center @closed="resetForm">
      <div class="sf-form">
        <div class="sf-row">
          <label>模块 *</label>
          <select v-model="form.module" class="sf-input">
            <option v-for="m in MODULES" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="sf-row">
          <label>类型 *</label>
          <select v-model="form.solve_type" class="sf-input">
            <option v-for="t in SOLVE_TYPES" :key="t.key" :value="t.key">{{ t.key }}</option>
          </select>
        </div>
        <div class="sf-row">
          <label>标题 *</label>
          <input v-model="form.title" class="sf-input" placeholder="解题条目标题" />
        </div>
        <div class="sf-row">
          <label>正文</label>
          <textarea v-model="form.content" class="sf-input" rows="6" placeholder="支持 Markdown"></textarea>
        </div>
        <div class="sf-row">
          <label>考点定位</label>
          <div class="sf-levels">
            <input v-model="form.level1" class="sf-input sm" placeholder="一级" />
            <input v-model="form.level2" class="sf-input sm" placeholder="二级" />
            <input v-model="form.level3" class="sf-input sm" placeholder="三级" />
            <input v-model="form.level4" class="sf-input sm" placeholder="四级" />
          </div>
        </div>
        <div class="sf-row">
          <label>标签</label>
          <input v-model="form.tags" class="sf-input" placeholder="用 / 或中文逗号分隔" />
        </div>
        <div class="sf-row">
          <label>卡片标题</label>
          <input v-model="form.card_title" class="sf-input" placeholder="列表卡片主标题（≤18字，AI 生成）" />
        </div>
        <div class="sf-row">
          <label>卡片标签</label>
          <input v-model="form.card_tags" class="sf-input" placeholder="用 ｜ 分隔短词，如 隔板法｜排列组合" />
        </div>
        <div class="sf-row">
          <label>卡片摘要</label>
          <textarea v-model="form.card_summary" class="sf-input" rows="2" placeholder="列表卡片两行速记（≤70字，AI 生成）"></textarea>
        </div>
        <div class="sf-row">
          <label>难度</label>
          <div class="sf-rate"><el-rate v-model="form.difficulty" :max="5" /></div>
        </div>
        <div class="sf-row">
          <label>出处</label>
          <input v-model="form.source" class="sf-input" placeholder="来源（可选）" />
        </div>
      </div>
      <template #footer>
        <button class="btn-default" @click="showCreate = false">取消</button>
        <button class="btn-primary" :disabled="!form.title || !form.module || saving" @click="saveForm">{{ saving ? '保存中…' : '保存' }}</button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="showBatch" title="批量导入解题条目" width="640px" align-center>
      <div class="imp">
        <div class="imp-tabs">
          <button class="imp-tab" :class="{ on: batchTab === 'paste' }" @click="batchTab = 'paste'">粘贴 JSON</button>
          <button class="imp-tab" :class="{ on: batchTab === 'file' }" @click="batchTab = 'file'">上传文件</button>
        </div>
        <div v-if="batchTab === 'paste'" class="imp-body">
          <textarea v-model="batchText" class="imp-text" rows="10" placeholder="粘贴 AI 输出的 JSON 数组（可含```json 代码围栏或前后说明文字，系统会自动提取数组）"></textarea>
        </div>
        <div v-else class="imp-body">
          <input type="file" accept=".json,.txt,.md" @change="onFile" class="imp-file" />
          <p class="imp-hint">支持 .json / .txt / .md，内容为 JSON 数组。</p>
        </div>
        <div class="imp-preview" v-if="batchPreview">
          <div class="imp-pv-head">
            解析预览：<b>{{ batchPreview.items.length }}</b> 条待导入
            <span v-if="batchPreview.errors.length" class="imp-err"> · {{ batchPreview.errors.length }} 条异常已跳过</span>
          </div>
          <div class="imp-pv-list">
            <div v-for="(it, i) in batchPreview.items.slice(0, 6)" :key="i" class="imp-pv-item">
              <span class="imp-pv-mod" :style="modStyle(it.module)">{{ it.module }}</span>
              <span class="imp-pv-title">{{ it.title }}</span>
            </div>
            <div v-if="batchPreview.items.length > 6" class="imp-pv-more">…还有 {{ batchPreview.items.length - 6 }} 条</div>
          </div>
        </div>
        <details class="imp-schema">
          <summary>查看导入结构模板</summary>
          <pre class="imp-code">{{ schemaTemplate }}</pre>
        </details>
      </div>
      <template #footer>
        <button class="btn-default" @click="showBatch = false">取消</button>
        <button class="btn-default" @click="previewBatch" :disabled="!batchText.trim()">解析预览</button>
        <button class="btn-primary" :disabled="!batchPreview || !batchPreview.items.length || importing" @click="confirmBatch">{{ importing ? '导入中…' : '确认导入' }}</button>
      </template>
    </el-dialog>

    <!-- 提示词助手 -->
    <el-dialog v-model="showPrompt" title="提示词助手 · 让 AI 帮你整理解题方法" width="720px" align-center>
      <div class="pa">
        <p class="pa-tip">把下面这段提示词复制给任意 AI（ChatGPT / 通义 / 文心 / Kimi 等），让它输出可直接导入本系统的结构化解题条目；再把 AI 的回复粘贴到下方即可一键入库。提示词已与系统模块/类型严格对齐（单一事实源）。</p>
        <div class="pa-block">
          <div class="pa-block-head">
            <span>① 复制给 AI 的提示词</span>
            <button class="pa-copy" @click="copy(promptText, '提示词已复制')"><el-icon><CopyDocument /></el-icon> 复制</button>
          </div>
          <pre class="pa-pre">{{ promptText }}</pre>
        </div>
        <div class="pa-block">
          <div class="pa-block-head">
            <span>② AI 应输出的代码结构（可一并给 AI 参考）</span>
            <button class="pa-copy" @click="copy(schemaTemplate, '结构模板已复制')"><el-icon><CopyDocument /></el-icon> 复制</button>
          </div>
          <pre class="pa-pre">{{ schemaTemplate }}</pre>
        </div>
        <div class="pa-block">
          <div class="pa-block-head"><span>③ 粘贴 AI 回复并导入</span></div>
          <textarea v-model="promptText2" class="pa-text" rows="6" placeholder="在此粘贴 AI 返回的 JSON 数组或其回复（系统会自动提取数组）"></textarea>
          <div class="pa-import-row">
            <span v-if="promptPreview" class="pa-pv">解析到 <b>{{ promptPreview.items.length }}</b> 条<span v-if="promptPreview.errors.length"> · {{ promptPreview.errors.length }} 条异常</span></span>
            <button class="btn-default" @click="previewPrompt" :disabled="!promptText2.trim()">解析</button>
            <button class="btn-primary" :disabled="!promptPreview || !promptPreview.items.length || importing" @click="confirmPromptImport">{{ importing ? '导入中…' : '解析并导入' }}</button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { solveLibraryApi } from '../api'
import { renderMarkdown } from '../utils/md'
import { MODULES, modColor, modStyle, SOLVE_TYPES, solveStyle } from '../utils/constants'
import { ElMessage, ElMessageBox } from 'element-plus'
import EmptyState from '../components/EmptyState.vue'

const md = renderMarkdown
const route = useRoute()
const router = useRouter()

const allItems = ref([])
const activeModule = ref('all')
const activeType = ref('all')
const kaodianPath = ref([])
const expandedKd = ref(new Set())
const keyword = ref('')
const sortMode = ref('default')
const viewMode = ref('byModule')
const expanded = ref(new Set())

function toggleExpand(id) {
  const s = new Set(expanded.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expanded.value = s
}
const solveTypeColor = (t) => (SOLVE_TYPES.find(x => x.key === t) || {}).color || '#64748b'

// 考点定位：取非空的 level1~5
function pathArr(k) {
  return [k.level1, k.level2, k.level3, k.level4, k.level5].filter(Boolean)
}

// 卡片缩略信息：优先用提示词生成的 card_title/tags/summary，缺失则回退 title/tags/content
function cardTitle(k) {
  return (k.card_title && k.card_title.trim()) || (k.title && k.title.trim()) || '（无标题）'
}
function cardTags(k) {
  const raw = (k.card_tags && k.card_tags.trim()) || (k.tags && k.tags.trim()) || ''
  if (!raw) return []
  return raw.split(/[｜|/、,，]/).map(s => s.trim()).filter(Boolean)
}
function cardSummary(k) {
  return (k.card_summary && k.card_summary.trim()) || ''
}

const showCreate = ref(false)
const showBatch = ref(false)
const showPrompt = ref(false)
const showDetail = ref(false)
const detailItem = ref(null)
const editing = ref(null)
const saving = ref(false)
const importing = ref(false)

const form = ref(blankForm())
const batchTab = ref('paste')
const batchText = ref('')
const batchPreview = ref(null)
const promptText2 = ref('')
const promptPreview = ref(null)

function blankForm() {
  return { module: MODULES[0], solve_type: '解题方法', title: '', content: '', tags: '', difficulty: 2, source: '', level1: '', level2: '', level3: '', level4: '', card_title: '', card_tags: '', card_summary: '' }
}

function setModule(m) { activeModule.value = m; activeType.value = 'all'; kaodianPath.value = [] }
function setType(t) { activeType.value = t; activeModule.value = 'all'; kaodianPath.value = [] }
function onKaodian(path) {
  // path 为空数组 → 清除考点筛选；否则切换选中路径
  if (!path || !path.length) { kaodianPath.value = [] }
  else {
    const joined = path.join('>')
    kaodianPath.value = (kaodianPath.value.join('>') === joined) ? [] : path.slice()
  }
  activeModule.value = 'all'; activeType.value = 'all'
}
function toggleKdExpand(p) {
  const s = new Set(expandedKd.value)
  if (s.has(p)) s.delete(p); else s.add(p)
  expandedKd.value = s
}
function isKdActive(path) { return path.join('>') === kaodianPath.value.join('>') }
function n2Children(n1) { return n1.children.flatMap(n2 => n2.children) }

async function loadAll() {
  try {
    const res = await solveLibraryApi.getList({ page: 1, page_size: 2000 })
    allItems.value = res.data.items || []
  } catch (e) { console.error(e) }
}

const moduleCount = (m) => allItems.value.filter(k => k.module === m).length
const typeCount = (t) => allItems.value.filter(k => k.solve_type === t).length

// 按考点：构建层级 L1 > L2 > L3 的树（常识判断-地理国情-自然地理），含聚合计数
const kaodianTree = computed(() => {
  const root = {}
  for (const k of allItems.value) {
    const arr = pathArr(k)
    if (!arr.length) continue
    let node = root
    const acc = []
    for (const name of arr) {
      acc.push(name)
      if (!node[name]) node[name] = { name, path: acc.slice(), children: {}, count: 0 }
      node[name].count++
      node = node[name].children
    }
  }
  const toArr = (obj) => Object.values(obj)
    .map(n => ({ ...n, children: toArr(n.children) }))
    .sort((a, b) => b.count - a.count)
  return toArr(root)
})

// 选中路径前缀匹配：题目考点路径前 N 级与 kaodianPath 完全一致
function matchKaodian(k) {
  if (!kaodianPath.value.length) return true
  const arr = pathArr(k)
  if (arr.length < kaodianPath.value.length) return false
  for (let i = 0; i < kaodianPath.value.length; i++) {
    if (arr[i] !== kaodianPath.value[i]) return false
  }
  return true
}

const filtered = computed(() => {
  let list = allItems.value
  if (activeModule.value !== 'all') list = list.filter(k => k.module === activeModule.value)
  if (activeType.value !== 'all') list = list.filter(k => k.solve_type === activeType.value)
  if (kaodianPath.value.length) list = list.filter(matchKaodian)
  const kw = keyword.value.trim()
  if (kw) list = list.filter(k => (k.title || '').includes(kw) || (k.content || '').includes(kw) || (k.tags || '').includes(kw))
  const arr = list.slice()
  if (sortMode.value === 'title') arr.sort((a, b) => (a.title || '').localeCompare(b.title, 'zh'))
  else if (sortMode.value === 'difficulty') arr.sort((a, b) => (b.difficulty || 0) - (a.difficulty || 0))
  else if (sortMode.value === 'updated') arr.sort((a, b) => (b.update_time || '').localeCompare(a.update_time || ''))
  else arr.sort((a, b) => (MODULES.indexOf(a.module) - MODULES.indexOf(b.module)) || (SOLVE_TYPES.findIndex(t => t.key === a.solve_type) - SOLVE_TYPES.findIndex(t => t.key === b.solve_type)) || (a.title || '').localeCompare(b.title, 'zh'))
  return arr
})

const displayGroups = computed(() => {
  const list = filtered.value
  if (viewMode.value === 'byModule') {
    const map = {}
    for (const k of list) (map[k.module] = map[k.module] || []).push(k)
    return Object.keys(map).sort((a, b) => MODULES.indexOf(a) - MODULES.indexOf(b))
      .map(m => ({ key: m, label: m, color: modColor(m), items: map[m] }))
  }
  if (viewMode.value === 'byType') {
    const map = {}
    for (const k of list) (map[k.solve_type] = map[k.solve_type] || []).push(k)
    return SOLVE_TYPES.filter(t => map[t.key]).map(t => ({ key: t.key, label: t.key, color: t.color, items: map[t.key] }))
  }
  if (viewMode.value === 'byKaodian') {
    const map = {}
    for (const k of list) {
      const arr = pathArr(k)
      if (!arr.length) continue
      const path = arr.join(' › ')
      ;(map[path] = map[path] || []).push(k)
    }
    return Object.keys(map).sort((a, b) => MODULES.indexOf(map[a][0].module) - MODULES.indexOf(map[b][0].module))
      .map(p => ({ key: p, label: p, color: modColor(map[p][0].module), items: map[p] }))
  }
  return [{ key: 'all', label: '', color: '', items: list }]
})

// 首跑引导 / 筛选态判定（用于空态组件）
const isEmptyLibrary = computed(() => allItems.value.length === 0)
const hasFilter = computed(() =>
  activeModule.value !== 'all' || activeType.value !== 'all' || keyword.value ||
  sortMode.value !== 'default' || viewMode.value !== 'flat' || kaodianPath.value.length
)

function goPractice(module) {
  router.push('/question-list?module=' + encodeURIComponent(module))
}
function goSource(qid) {
  if (!qid) return
  showDetail.value = false
  router.push('/question/' + qid)
}
function openDetail(k) {
  detailItem.value = k
  showDetail.value = true
}
function editFromDetail() {
  if (detailItem.value) editItem(detailItem.value)
  showDetail.value = false
}
async function removeFromDetail() {
  if (detailItem.value) await removeItem(detailItem.value)
  showDetail.value = false
}
function reset() {
  activeModule.value = 'all'
  activeType.value = 'all'
  kaodianPath.value = []
  expandedKd.value = new Set()
  keyword.value = ''
  sortMode.value = 'default'
  viewMode.value = 'flat'
}

function resetForm() {
  editing.value = null
  form.value = blankForm()
}
function editItem(k) {
  editing.value = k
  form.value = {
    module: k.module, solve_type: k.solve_type, title: k.title, content: k.content || '',
    tags: k.tags || '', difficulty: k.difficulty || 2, source: k.source || '',
    level1: k.level1 || '', level2: k.level2 || '', level3: k.level3 || '', level4: k.level4 || '',
    card_title: k.card_title || '', card_tags: k.card_tags || '', card_summary: k.card_summary || '',
  }
  showCreate.value = true
}
async function saveForm() {
  if (!form.value.title || !form.value.module) { ElMessage.warning('请填写模块与标题'); return }
  saving.value = true
  try {
    if (editing.value) {
      await solveLibraryApi.update(editing.value.id, { ...form.value })
      ElMessage.success('已更新')
    } else {
      await solveLibraryApi.create({ ...form.value })
      ElMessage.success('已创建')
    }
    showCreate.value = false
    await loadAll()
  } catch (e) { ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message)) }
  finally { saving.value = false }
}
async function removeItem(k) {
  await ElMessageBox.confirm('确定删除「' + k.title + '」？', '提示', { type: 'warning' })
  try {
    await solveLibraryApi.delete(k.id)
    ElMessage.success('已删除')
    await loadAll()
  } catch (e) { ElMessage.error('删除失败') }
}

function openBatch() { batchTab.value = 'paste'; batchText.value = ''; batchPreview.value = null; showBatch.value = true }
function onFile(e) {
  const f = e.target.files[0]
  if (!f) return
  const reader = new FileReader()
  reader.onload = () => { batchText.value = String(reader.result || ''); previewBatch() }
  reader.readAsText(f)
}
function parseImportText(text) {
  let s = (text || '').trim()
  if (!s) return { items: [], errors: ['内容为空'] }
  s = s.replace(/```(?:json)?/gi, '').replace(/```/g, '')
  const a = s.indexOf('['), b = s.lastIndexOf(']')
  if (a === -1 || b === -1 || b <= a) return { items: [], errors: ['未找到 JSON 数组'] }
  let arr
  try { arr = JSON.parse(s.slice(a, b + 1)) }
  catch (err) { return { items: [], errors: ['JSON 解析失败：' + err.message] } }
  if (!Array.isArray(arr)) arr = [arr]
  const items = []
  const errors = []
  arr.forEach((it, i) => {
    if (!it || typeof it !== 'object') { errors.push({ index: i, reason: '非对象' }); return }
    const module = (it.module || '').toString().trim()
    const title = (it.title || '').toString().trim()
    if (!module || !title) { errors.push({ index: i, reason: '缺少 module 或 title' }); return }
    items.push({
      module, solve_type: (it.solve_type || '解题方法').toString().trim() || '解题方法',
      title, content: (it.content || '').toString(),
      tags: (it.tags || '').toString(),
      source: (it.source || '批量导入').toString(), difficulty: Number(it.difficulty) || 2,
      level1: (it.level1 || '').toString(), level2: (it.level2 || '').toString(),
      level3: (it.level3 || '').toString(), level4: (it.level4 || '').toString(),
    })
  })
  return { items, errors }
}
function previewBatch() {
  batchPreview.value = parseImportText(batchText.value)
  if (batchPreview.value.errors.length && !batchPreview.value.items.length) ElMessage.warning('解析失败：' + batchPreview.value.errors[0])
}
async function confirmBatch() {
  if (!batchPreview.value || !batchPreview.value.items.length) return
  importing.value = true
  try {
    const res = await solveLibraryApi.batch(batchPreview.value.items)
    ElMessage.success(`成功导入 ${res.data.created} 条` + (res.data.errors.length ? `，${res.data.errors.length} 条异常跳过` : ''))
    showBatch.value = false
    await loadAll()
  } catch (e) { ElMessage.error('导入失败：' + (e.response?.data?.detail || e.message)) }
  finally { importing.value = false }
}

const schemaTemplate = `[
  {
    "module": "模块名（必填，见可选模块）",
    "solve_type": "类型（必填，见条目类型）",
    "title": "解题条目标题（必填）",
    "content": "正文（支持 Markdown）",
    "tags": "标签1/标签2",
    "difficulty": 2,
    "source": "出处",
    "level1": "一级考点", "level2": "二级考点", "level3": "三级考点", "level4": "四级考点"
  }
]`

const promptText = computed(() => {
  const modules = MODULES.map(m => '- ' + m).join('\n')
  const types = SOLVE_TYPES.map(t => '- ' + t.key).join('\n')
  return `你是一位行测（公务员考试《行政职业能力测验》）辅导专家。请基于你掌握的知识，整理以下模块的解题思路与技巧，并严格按照下方 JSON 数组结构输出。不要输出任何解释性文字，只输出可被程序直接解析的 JSON 数组。

可选模块（module 必须严格属于其一）：
${modules}

条目类型（solve_type 必须严格属于其一）：
${types}

每个对象的字段说明：
- module：必填，且必须是上面模块之一（如「数量关系」）
- solve_type：必填，且必须是上面类型之一（如「速算技巧」「破题逻辑」「易错提醒」）
- title：必填，条目标题（简洁明确，如「工程问题-赋值总量法」「片段阅读-转折结构主旨判定」）
- content：必填，条目的详细说明，支持 Markdown（可含公式 $...$、步骤、示例、适用前提）
- tags：可选，用中文逗号或斜杠分隔的标签（如「赋值法,工程问题,给完工时间型」）
- difficulty：可选，1-5 整数，表示掌握难度
- level1~level4：可选，条目对应的考点定位路径（与题库题型树一致，使其落到对应位置）
- source：可选，出处

要求：
1. module 与 solve_type 必须严格取自上面列表，不要自造名称；
2. 优先产出高频可复用解题模板与典型易错提醒；
3. 每个模块产出 8-15 条，覆盖破题逻辑、解题方法、速算技巧、易错提醒、题型识别等类型；
4. 只输出纯 JSON 数组，不要使用 Markdown 代码围栏，不要额外文字。

输出示例：
[
  {
    "module": "数量关系",
    "solve_type": "解题方法",
    "title": "工程问题-赋值总量法",
    "content": "当题目给完工时间（如甲单独需 5 天、乙单独需 8 天）时，可将工作总量赋值为各时间的最小公倍数（$W=40$），再求效率……",
    "tags": "赋值法/工程问题/给完工时间型",
    "difficulty": 2,
    "level1": "数量关系", "level2": "数学运算", "level3": "工程问题",
    "source": "行测解题集"
  }
]`
})

function previewPrompt() {
  promptPreview.value = parseImportText(promptText2.value)
  if (promptPreview.value.errors.length && !promptPreview.value.items.length) ElMessage.warning('解析失败：' + promptPreview.value.errors[0])
}
async function confirmPromptImport() {
  if (!promptPreview.value || !promptPreview.value.items.length) return
  importing.value = true
  try {
    const res = await solveLibraryApi.batch(promptPreview.value.items)
    ElMessage.success(`成功导入 ${res.data.created} 条` + (res.data.errors.length ? `，${res.data.errors.length} 条异常跳过` : ''))
    showPrompt.value = false
    promptText2.value = ''
    promptPreview.value = null
    await loadAll()
  } catch (e) { ElMessage.error('导入失败：' + (e.response?.data?.detail || e.message)) }
  finally { importing.value = false }
}

async function copy(text, ok) {
  try { await navigator.clipboard.writeText(text); ElMessage.success(ok) }
  catch { ElMessage.warning('复制失败，请手动选择') }
}

onMounted(async () => {
  await loadAll()
  if (route.query.module) activeModule.value = route.query.module
  if (route.query.keyword) keyword.value = String(route.query.keyword)
})
watch(() => route.query, (q) => {
  if (q.module) activeModule.value = q.module
  if (q.keyword) keyword.value = String(q.keyword)
}, { deep: false })
</script>

<style scoped>
.sl-page { display: flex; height: 100%; min-height: 0; }

/* 左导航 — 完全镜射知识库 */
.sl-side {
  width: 226px; flex-shrink: 0; display: flex; flex-direction: column;
  border-right: 1px solid var(--border-base); background: var(--bg-elevated); overflow-y: auto; padding-bottom: 12px;
}
.sl-side-head { display: flex; align-items: center; gap: 7px; padding: 16px 16px 10px; font-size: 14px; font-weight: 500; color: var(--text-primary); flex-shrink: 0; }
.sl-nav { overflow-y: auto; padding: 2px 10px 6px; display: flex; flex-direction: column; gap: 1px; flex-shrink: 0; }
.sl-nav-item {
  display: flex; align-items: center; gap: 9px; padding: 7px 10px; border-radius: 7px;
  cursor: pointer; border: none; background: none; text-align: left; transition: background 0.14s, color 0.14s; color: var(--text-secondary);
}
.sl-nav-item:hover { background: var(--bg-subtle); }
.sl-nav-item.on { background: var(--bg-subtle); color: var(--text-primary); font-weight: 500; }
.sl-nav-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.sl-nav-name { flex: 1; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sl-nav-n { font-size: 11px; color: var(--text-tertiary); font-variant-numeric: tabular-nums; }
.sl-nav-kaodian { gap: 1px; }
.sl-kd { align-items: flex-start; padding-top: 6px; padding-bottom: 6px; }
.sl-kd.lvl2 { padding-left: 22px; }
.sl-kd.lvl3 { padding-left: 40px; }
.sl-kd-name { white-space: normal; line-height: 1.35; font-size: 12.5px; }
.sl-kd-caret { width: 14px; flex-shrink: 0; font-size: 10px; color: var(--text-tertiary); cursor: pointer; user-select: none; }
.sl-kd-caret.empty { cursor: default; }
.sl-nav-empty { font-size: 12px; color: var(--text-tertiary); padding: 8px 12px; }

.sl-side-sec { padding: 14px 16px 5px; font-size: 11px; font-weight: 500; color: var(--text-tertiary); letter-spacing: 0.5px; flex-shrink: 0; }

/* 右内容 */
.sl-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.sl-toolbar { display: flex; align-items: center; gap: 10px; padding: 12px 18px; border-bottom: 1px solid var(--border-light); flex-shrink: 0; flex-wrap: wrap; }
.sl-search {
  display: flex; align-items: center; gap: 6px; background: var(--bg-subtle);
  border: 1px solid var(--border-base); border-radius: var(--radius-md); padding: 7px 12px; min-width: 200px;
}
.sl-search:focus-within { border-color: var(--primary); }
.sl-ico { font-size: 14px; opacity: 0.55; }
.sl-search input { border: none; background: transparent; outline: none; font-size: 13px; color: var(--text-primary); width: 100%; }

.sl-tools { display: flex; align-items: center; gap: 8px; margin-left: auto; flex-wrap: wrap; }
.sl-view { display: flex; background: var(--bg-subtle); border: 1px solid var(--border-base); border-radius: var(--radius-md); padding: 2px; }
.sl-view-btn { border: none; background: none; padding: 5px 10px; border-radius: var(--radius-sm); cursor: pointer; font-size: 12px; color: var(--text-secondary); transition: all 0.15s; }
.sl-view-btn.on { background: var(--bg-elevated); color: var(--primary); font-weight: 700; box-shadow: var(--shadow-sm); }
.sl-select {
  padding: 6px 28px 6px 10px; border: 1px solid var(--border-base); border-radius: var(--radius-md);
  font-size: 12.5px; background: var(--bg-base); color: var(--text-primary);
  appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6'><path d='M0 0l5 6 5-6z' fill='%2394a3b8'/></svg>");
  background-repeat: no-repeat; background-position: right 10px center;
}
.sl-act {
  display: inline-flex; align-items: center; gap: 4px; font-size: 12.5px; padding: 7px 12px; border-radius: var(--radius-md);
  border: 1px solid var(--border-base); background: var(--bg-base); color: var(--text-secondary); cursor: pointer; transition: all 0.15s;
}
.sl-act:hover { color: var(--primary); border-color: var(--primary); }
.sl-act.primary { background: var(--primary); color: #fff; border-color: var(--primary); }
.sl-act.primary:hover { background: var(--primary-dark); color: #fff; }

.sl-filterbar { display: flex; align-items: center; gap: 12px; padding: 8px 18px; border-bottom: 1px solid var(--border-light); background: var(--primary-bg); flex-shrink: 0; flex-wrap: wrap; }
.sl-filter-chip { font-size: 12.5px; color: var(--text-secondary); display: inline-flex; align-items: center; gap: 6px; background: var(--bg-base); border: 1px solid var(--border-base); padding: 4px 10px; border-radius: 999px; }
.sl-filter-chip b { color: var(--primary); }
.sl-filter-x { border: none; background: none; cursor: pointer; color: var(--text-tertiary); font-size: 15px; line-height: 1; padding: 0 2px; }
.sl-filter-x:hover { color: var(--danger); }
.sl-filter-hint { font-size: 11.5px; color: var(--text-tertiary); }

.sl-scroll { flex: 1; overflow-y: auto; padding: 18px 22px 40px; }
.sl-group { margin-bottom: 26px; max-width: 920px; }
.sl-group.flat { margin-bottom: 0; }
.sl-group-head { display: flex; align-items: center; gap: 8px; padding: 6px 2px 10px 12px; border-left: 3px solid var(--gc, var(--border-base)); border-bottom: 1px solid var(--border-light); margin-bottom: 12px; }
.sl-group-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.sl-group-name { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.sl-group-n { font-size: 12px; color: var(--text-tertiary); }

.sl-list { display: flex; flex-direction: column; gap: 8px; max-width: 920px; }
.sl-card {
  position: relative; background: var(--bg-elevated); border: 1px solid var(--border-base); border-radius: 10px;
  padding: 14px 16px 13px; transition: border-color 0.14s, background 0.14s; cursor: pointer;
}
.sl-card::before { content: ''; position: absolute; left: 0; top: 12px; bottom: 12px; width: 3px; border-radius: 0 3px 3px 0; background: var(--tc, var(--border-base)); opacity: 0.85; }
.sl-card:hover { border-color: var(--tc, var(--primary)); }
.sl-card-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.sl-tag { display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; font-weight: 500; flex-shrink: 0; }
.sl-tag-dot { width: 6px; height: 6px; border-radius: 50%; }
.sl-title { margin: 0; font-size: 14.5px; font-weight: 500; color: var(--text-primary); flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sl-diff { font-size: 8px; color: var(--warning); letter-spacing: 2px; flex-shrink: 0; line-height: 1; }
.sl-diff i { color: var(--border-base); font-style: normal; }
.sl-mod { display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; color: var(--text-tertiary); flex-shrink: 0; }
.sl-mod-dot { width: 7px; height: 7px; border-radius: 50%; }
.sl-content { font-size: 13px; line-height: 1.72; color: var(--text-secondary); }
.sl-content.clamp { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.sl-content :deep(p) { margin: 0 0 6px; }
.sl-content :deep(p:last-child) { margin-bottom: 0; }
.sl-content :deep(strong) { color: var(--text-primary); font-weight: 500; }
.sl-content :deep(ol), .sl-content :deep(ul) { padding-left: 20px; margin: 0 0 6px; }
.sl-content :deep(li) { margin-bottom: 2px; }
.sl-content :deep(code) { background: var(--bg-subtle); padding: 1px 5px; border-radius: 4px; font-size: 12px; }
/* 卡片缩略信息（提示词生成，替代大段正文） */
.sl-title { margin: 6px 0 5px; font-size: 15px; font-weight: 600; line-height: 1.45; color: var(--text-primary); white-space: normal; overflow: visible; }
.sl-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 6px; }
.sl-tagchip { font-size: 11px; font-weight: 500; padding: 2px 9px; border-radius: 999px; background: var(--primary-bg); color: var(--primary); cursor: pointer; transition: all 0.12s; }
.sl-tagchip:hover { background: var(--primary); color: #fff; }
.sl-summary { font-size: 13px; line-height: 1.62; color: var(--text-secondary); background: var(--bg-subtle); border-radius: var(--radius-md); padding: 9px 11px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.sl-detail-cardinfo { margin: 10px 0; }
.sl-detail-summary { font-size: 13.5px; line-height: 1.6; color: var(--text-secondary); background: var(--bg-subtle); border-left: 3px solid var(--primary); padding: 9px 12px; border-radius: 0 var(--radius-md) var(--radius-md) 0; }
.sl-detail-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }

.sl-crumb { display: flex; align-items: center; flex-wrap: wrap; gap: 2px; margin: 2px 0 8px; font-size: 11.5px; color: var(--text-tertiary); }
.sl-crumb-ico { font-size: 12px; color: var(--primary); margin-right: 2px; }
.sl-crumb-item { border: none; background: none; cursor: pointer; color: var(--text-tertiary); font-size: 11.5px; padding: 1px 4px; border-radius: 5px; transition: all 0.12s; }
.sl-crumb-item:hover { color: var(--primary); background: var(--primary-bg); }
.sl-crumb-item.on { color: var(--primary); background: var(--primary-bg); font-weight: 600; }
.sl-crumb-static { color: var(--text-tertiary); }
.sl-crumb-static:not(:last-child)::after { content: ' › '; }

.sl-expand { margin-top: 6px; background: none; border: none; padding: 0; color: var(--primary); font-size: 12px; cursor: pointer; }
.sl-expand:hover { text-decoration: underline; }
.sl-foot { display: flex; align-items: center; gap: 10px; margin-top: 11px; flex-wrap: wrap; }
.sl-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.sl-tagslice { font-size: 11px; color: var(--text-tertiary); }
.sl-foot-right { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.sl-rel { font-size: 11.5px; color: var(--text-tertiary); display: inline-flex; align-items: center; gap: 4px; }
.sl-rel .el-icon { font-size: 11px; }
.sl-source { display: inline-flex; align-items: center; gap: 4px; font-size: 11.5px; padding: 3px 9px; border-radius: 7px; border: 1px solid var(--border-base); background: var(--bg-base); color: var(--primary); cursor: pointer; transition: all 0.14s; }
.sl-source:hover { border-color: var(--primary); background: var(--primary-bg); }
.sl-practice { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; padding: 4px 10px; border-radius: 7px; border: 1px solid var(--border-base); background: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.14s; }
.sl-practice:hover { color: var(--primary); border-color: var(--primary); }
.sl-card-ops { display: flex; gap: 2px; flex-shrink: 0; opacity: 0; transition: opacity 0.12s; }
.sl-card:hover .sl-card-ops { opacity: 1; }
.sl-op { background: transparent; border: none; width: 26px; height: 26px; border-radius: var(--radius-sm); cursor: pointer; color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 13px; transition: all 0.12s; }
.sl-op:hover { color: var(--text-secondary); background: var(--bg-subtle); }
.sl-op.danger:hover { color: var(--danger); background: var(--danger-bg); }

.sl-empty { text-align: center; padding: 70px 20px; color: var(--text-tertiary); }
.sle-ico { font-size: 44px; }
.sl-empty div { margin: 12px 0 16px; font-size: 15px; }
.btn-default { background: var(--bg-subtle); color: var(--text-secondary); border: 1px solid var(--border-base); padding: 8px 14px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; }
.btn-default:hover { color: var(--primary); border-color: var(--primary); }
.btn-default:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: var(--primary); color: #fff; border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-primary:hover { background: var(--primary-dark); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.sl-detail { display: flex; flex-direction: column; gap: 12px; }
.sl-detail-meta { display: flex; align-items: center; gap: 10px; }
.sl-detail-content { font-size: 13.5px; line-height: 1.75; color: var(--text-secondary); max-height: 46vh; overflow-y: auto; padding-right: 4px; }
.sl-detail-content :deep(p) { margin: 0 0 8px; }
.sl-detail-content :deep(strong) { color: var(--text-primary); }
.sl-detail-content :deep(ol), .sl-detail-content :deep(ul) { padding-left: 20px; }
.sl-detail-content :deep(code) { background: var(--bg-subtle); padding: 1px 5px; border-radius: 4px; font-size: 12px; }
.sl-detail-foot { display: flex; flex-wrap: wrap; gap: 5px; }
.sl-detail-ops { display: flex; gap: 8px; flex-wrap: wrap; border-top: 1px solid var(--border-light); padding-top: 12px; }
.btn-default.danger { color: var(--danger); border-color: var(--danger); }
.btn-default.danger:hover { background: var(--danger-bg); }
.btn-default.danger .el-icon { margin-right: 3px; }

/* 表单 */
.sf-form { display: flex; flex-direction: column; gap: 12px; }
.sf-row { display: flex; align-items: center; gap: 10px; }
.sf-row label { width: 84px; flex-shrink: 0; font-size: 13px; color: var(--text-secondary); text-align: right; }
.sf-input { flex: 1; padding: 8px 10px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 13px; background: var(--bg-base); color: var(--text-primary); font-family: inherit; }
.sf-input:focus { outline: none; border-color: var(--primary); }
.sf-levels { flex: 1; display: flex; gap: 6px; }
.sf-input.sm { flex: 1; min-width: 0; padding: 7px 8px; }
textarea.sf-input { resize: vertical; font-family: 'Consolas', 'Monaco', monospace; }
.sf-rate { flex: 1; }

/* 批量导入 — 复用知识库 imp-* 命名 */
.imp-tabs { display: flex; gap: 6px; margin-bottom: 12px; }
.imp-tab { border: 1px solid var(--border-base); background: var(--bg-subtle); color: var(--text-secondary); padding: 6px 14px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; }
.imp-tab.on { color: var(--primary); border-color: var(--primary); background: var(--primary-bg); font-weight: 600; }
.imp-text, .imp-file { width: 100%; }
.imp-text { padding: 12px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 12.5px; background: var(--bg-base); color: var(--text-primary); font-family: 'Consolas', 'Monaco', monospace; resize: vertical; }
.imp-text:focus { outline: none; border-color: var(--primary); }
.imp-hint { font-size: 12px; color: var(--text-tertiary); margin: 8px 0 0; }
.imp-preview { margin-top: 12px; padding: 12px; background: var(--bg-subtle); border-radius: var(--radius-md); border: 1px solid var(--border-light); }
.imp-pv-head { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }
.imp-pv-head b { color: var(--primary); }
.imp-err { color: var(--danger); }
.imp-pv-list { display: flex; flex-direction: column; gap: 6px; max-height: 180px; overflow-y: auto; }
.imp-pv-item { display: flex; align-items: center; gap: 8px; font-size: 12.5px; }
.imp-pv-mod { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 999px; flex-shrink: 0; }
.imp-pv-title { color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.imp-pv-more { font-size: 11px; color: var(--text-tertiary); }
.imp-schema { margin-top: 12px; }
.imp-schema summary { cursor: pointer; color: var(--text-tertiary); font-size: 12px; }
.imp-code, .pa-pre { background: var(--bg-subtle); padding: 12px; border-radius: var(--radius-md); font-size: 11.5px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; font-family: 'Consolas', 'Monaco', monospace; border: 1px solid var(--border-light); max-height: 280px; overflow-y: auto; }

/* 提示词助手 — 复用知识库 pa-* 命名 */
.pa { display: flex; flex-direction: column; gap: 14px; }
.pa-tip { font-size: 12.5px; color: var(--text-secondary); line-height: 1.7; margin: 0; padding: 10px 12px; background: var(--primary-bg); border-radius: var(--radius-md); }
.pa-block-head { display: flex; align-items: center; justify-content: space-between; font-size: 13px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; }
.pa-copy { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; padding: 4px 10px; border-radius: var(--radius-sm); border: 1px solid var(--border-base); background: var(--bg-base); color: var(--text-secondary); cursor: pointer; }
.pa-copy:hover { color: var(--primary); border-color: var(--primary); }
.pa-text { width: 100%; padding: 12px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 12.5px; background: var(--bg-base); color: var(--text-primary); font-family: 'Consolas', 'Monaco', monospace; resize: vertical; }
.pa-text:focus { outline: none; border-color: var(--primary); }
.pa-import-row { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.pa-pv { font-size: 12.5px; color: var(--text-secondary); margin-right: auto; }
.pa-pv b { color: var(--primary); }

@media (max-width: 760px) {
  .sl-side { width: 100%; }
  .sl-tools { width: 100%; margin-left: 0; }
}
</style>
