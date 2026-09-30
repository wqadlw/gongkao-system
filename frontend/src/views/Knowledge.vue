<template>
  <div class="kb-page">
    <!-- 左：分类导航（按模块 / 按类型 / 按考点 三重维度） -->
    <aside class="kb-side">
      <div class="kb-side-head"><el-icon><Reading /></el-icon> 知识库</div>
      <div class="kb-nav">
        <button class="kb-nav-item" :class="{ on: activeModule === 'all' && activeType === 'all' && !kaodianPath.length }" @click="reset">
          <span class="kb-nav-dot" style="background: #64748b"></span>
          <span class="kb-nav-name">全部</span>
          <span class="kb-nav-n">{{ allKb.length }}</span>
        </button>
      </div>

      <div class="kb-side-sec">按模块</div>
      <div class="kb-nav">
        <button v-for="m in MODULES" :key="m" class="kb-nav-item" :class="{ on: activeModule === m && !kaodianPath.length }" @click="setModule(m)">
          <span class="kb-nav-dot" :style="{ background: modColor(m) }"></span>
          <span class="kb-nav-name">{{ m }}</span>
          <span class="kb-nav-n">{{ moduleCount(m) }}</span>
        </button>
      </div>

      <div class="kb-side-sec">按类型</div>
      <div class="kb-nav">
        <button v-for="t in KG_TYPES" :key="t.key" class="kb-nav-item" :class="{ on: activeType === t.key && !kaodianPath.length }" @click="setType(t.key)">
          <span class="kb-nav-dot" :style="{ background: t.color }"></span>
          <span class="kb-nav-name">{{ t.key }}</span>
          <span class="kb-nav-n">{{ typeCount(t.key) }}</span>
        </button>
      </div>

      <div class="kb-side-sec">按考点</div>
      <div class="kb-nav kb-nav-kaodian">
        <template v-for="n1 in kaodianTree" :key="'k1-' + n1.path.join('>')">
          <button class="kb-nav-item kb-kd" :class="{ on: isKdActive(n1.path) }" @click="onKaodian(n1.path)">
            <span v-if="n1.children.length" class="kb-kd-caret" @click.stop="toggleKdExpand(n1.path.join('>'))">{{ expandedKd.has(n1.path.join('>')) || isKdActive(n1.path) ? '▾' : '▸' }}</span>
            <span v-else class="kb-kd-caret empty"></span>
            <span class="kb-nav-name kb-kd-name">{{ n1.name }}</span>
            <span class="kb-nav-n">{{ n1.count }}</span>
          </button>
          <template v-if="n1.children.length && (expandedKd.has(n1.path.join('>')) || isKdActive(n1.path))">
            <button v-for="n2 in n1.children" :key="'k2-' + n2.path.join('>')" class="kb-nav-item kb-kd lvl2" :class="{ on: isKdActive(n2.path) }" @click="onKaodian(n2.path)">
              <span v-if="n2.children.length" class="kb-kd-caret" @click.stop="toggleKdExpand(n2.path.join('>'))">{{ expandedKd.has(n2.path.join('>')) || isKdActive(n2.path) ? '▾' : '▸' }}</span>
              <span v-else class="kb-kd-caret empty"></span>
              <span class="kb-nav-name kb-kd-name">{{ n2.name }}</span>
              <span class="kb-nav-n">{{ n2.count }}</span>
            </button>
            <button v-for="n3 in n2Children(n1)" :key="'k3-' + n3.path.join('>')" class="kb-nav-item kb-kd lvl3" :class="{ on: isKdActive(n3.path) }" @click="onKaodian(n3.path)">
              <span class="kb-kd-caret empty"></span>
              <span class="kb-nav-name kb-kd-name">{{ n3.name }}</span>
              <span class="kb-nav-n">{{ n3.count }}</span>
            </button>
          </template>
        </template>
        <div v-if="!kaodianTree.length" class="kb-nav-empty">暂无考点</div>
      </div>
    </aside>

    <!-- 右：知识内容 -->
    <section class="kb-main">
      <div class="kb-toolbar">
        <div class="kb-search">
          <el-icon class="kb-ico"><Search /></el-icon>
          <input v-model="keyword" placeholder="搜索知识点标题 / 内容 / 标签…" />
        </div>
        <div class="kb-tools">
          <div class="kb-view">
            <button class="kb-view-btn" :class="{ on: viewMode === 'flat' }" @click="viewMode = 'flat'" title="平铺">平铺</button>
            <button class="kb-view-btn" :class="{ on: viewMode === 'byModule' }" @click="viewMode = 'byModule'" title="按模块分组">按模块</button>
            <button class="kb-view-btn" :class="{ on: viewMode === 'byType' }" @click="viewMode = 'byType'" title="按类型分组">按类型</button>
            <button class="kb-view-btn" :class="{ on: viewMode === 'byKaodian' }" @click="viewMode = 'byKaodian'" title="按考点分组">按考点</button>
          </div>
          <select v-model="sortMode" class="kb-select">
            <option value="default">默认排序</option>
            <option value="title">按标题</option>
            <option value="difficulty">难度↓</option>
            <option value="updated">最近更新</option>
          </select>
          <button class="kb-act" @click="showCreate = true"><el-icon><Plus /></el-icon> 新建</button>
          <button class="kb-act" @click="openBatch"><el-icon><Upload /></el-icon> 批量导入</button>
          <button class="kb-act primary" @click="showPrompt = true"><el-icon><MagicStick /></el-icon> 提示词助手</button>
        </div>
      </div>

      <div class="kb-filterbar" v-if="kaodianPath.length">
        <span class="kb-filter-chip">考点筛选：<b>{{ kaodianPath.join(' › ') }}</b>
          <button class="kb-filter-x" @click="onKaodian([])">×</button>
        </span>
        <span class="kb-filter-hint">点击卡片上的考点面包屑可定位到对应位置</span>
      </div>

      <div class="kb-scroll">
        <template v-if="filtered.length">
          <div v-for="g in displayGroups" :key="g.key" class="kb-group" :class="{ flat: viewMode === 'flat' }">
            <div class="kb-group-head" v-if="viewMode !== 'flat'" :style="{ '--gc': g.color }">
              <span class="kb-group-dot" :style="{ background: g.color }"></span>
              <span class="kb-group-name">{{ g.label }}</span>
              <span class="kb-group-n">{{ g.items.length }} 条</span>
            </div>
            <div class="kb-list">
              <article v-for="k in g.items" :key="k.id" :id="'k' + k.id" class="kb-card"
                :style="{ '--tc': kgTypeColor(k.kg_type) }" @click="openDetail(k)">
                <div class="kb-card-head">
                  <span class="kb-tag" :style="{ color: kgTypeColor(k.kg_type) }">
                    <span class="kb-tag-dot" :style="{ background: kgTypeColor(k.kg_type) }"></span>{{ k.kg_type }}
                  </span>
                  <span class="kb-mod"><span class="kb-mod-dot" :style="{ background: modColor(k.module) }"></span>{{ k.module }}</span>
                  <span class="kb-card-ops">
                    <button class="kb-op" @click.stop="editItem(k)" title="编辑"><el-icon><Edit /></el-icon></button>
                    <button class="kb-op danger" @click.stop="removeItem(k)" title="删除"><el-icon><Delete /></el-icon></button>
                  </span>
                </div>
                <h3 class="kb-title">{{ cardTitle(k) }}</h3>
                <div class="kb-tags" v-if="cardTags(k).length">
                  <span v-for="t in cardTags(k)" :key="t" class="kb-tagchip" @click.stop="onKaodian([t])">{{ t }}</span>
                </div>
                <div class="kb-summary" v-if="cardSummary(k)" @click.stop>{{ cardSummary(k) }}</div>
                <div class="kb-content md-body" v-else :class="{ clamp: !expanded.has(k.id) }" v-html="md(k.content)"></div>
                <button v-if="!cardSummary(k) && k.content && k.content.length > 120" class="kb-expand" @click.stop="toggleExpand(k.id)">
                  {{ expanded.has(k.id) ? '收起' : '展开全文' }}
                </button>
                <!-- 考点定位：落到题库对应位置 -->
                <div class="kb-crumb" v-if="pathArr(k).length" @click.stop>
                  <el-icon class="kb-crumb-ico"><Location /></el-icon>
                  <button v-for="(lv, i) in pathArr(k)" :key="i" class="kb-crumb-item"
                    :class="{ on: kaodianPath.length === i + 1 && kaodianPath[i] === lv }"
                    @click="onKaodian(pathArr(k).slice(0, i + 1))">{{ lv }}</button>
                </div>
                <div class="kb-foot">
                  <span class="kb-rel" v-if="k.related_prompt" title="关联提示词"><el-icon><Link /></el-icon>{{ k.related_prompt }}</span>
                  <div class="kb-foot-right">
                    <button v-if="k.source_question_id" class="kb-source" @click.stop="goSource(k.source_question_id)" title="查看来源题目">
                      <el-icon><Link /></el-icon>来源题目
                    </button>
                    <button class="kb-practice" @click.stop="goPractice(k.module)"><el-icon><Promotion /></el-icon> 练该模块题</button>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </template>
        <div v-else class="kb-empty">
          <el-icon class="kbe-ico"><DocumentDeleted /></el-icon>
          <div>{{ kaodianPath.length ? '该考点下没有匹配的知识点' : '没有匹配的知识点' }}</div>
          <button v-if="activeModule !== 'all' || activeType !== 'all' || keyword || sortMode !== 'default' || viewMode !== 'flat' || kaodianPath.length" class="btn-default" @click="reset">清除筛选</button>
        </div>
      </div>
    </section>

    <!-- 详情抽屉 -->
    <el-dialog v-model="showDetail" :title="detailItem ? detailItem.title : ''" width="640px" align-center @closed="detailItem = null">
      <div class="kb-detail" v-if="detailItem">
        <div class="kb-detail-meta">
          <span class="kb-tag" :style="{ color: kgTypeColor(detailItem.kg_type) }">
            <span class="kb-tag-dot" :style="{ background: kgTypeColor(detailItem.kg_type) }"></span>{{ detailItem.kg_type }}
          </span>
          <span class="kb-mod"><span class="kb-mod-dot" :style="{ background: modColor(detailItem.module) }"></span>{{ detailItem.module }}</span>
          <span class="kb-diff" v-if="detailItem.difficulty">{{ '●'.repeat(detailItem.difficulty) }}<i>{{ '●'.repeat(5 - detailItem.difficulty) }}</i></span>
        </div>
        <div class="kb-crumb" v-if="pathArr(detailItem).length">
          <el-icon class="kb-crumb-ico"><Location /></el-icon>
          <span v-for="(lv, i) in pathArr(detailItem)" :key="i" class="kb-crumb-static">{{ lv }}</span>
        </div>
        <div class="kb-detail-tags" v-if="cardTags(detailItem).length">
          <span v-for="t in cardTags(detailItem)" :key="t" class="kb-tagchip">{{ t }}</span>
        </div>
        <div class="kb-detail-content md-body" v-html="md(detailItem.content)"></div>
        <div class="kb-detail-foot" v-if="detailItem.tags">
          <span v-for="t in detailItem.tags.split(/[，,/、]/).filter(Boolean)" :key="t" class="kb-tagslice">#{{ t }}</span>
        </div>
        <div class="kb-detail-ops">
          <button v-if="detailItem.source_question_id" class="btn-default" @click="goSource(detailItem.source_question_id)"><el-icon><Link /></el-icon> 查看来源题目</button>
          <button class="btn-default" @click="editFromDetail"><el-icon><Edit /></el-icon> 编辑</button>
          <button class="btn-default danger" @click="removeFromDetail"><el-icon><Delete /></el-icon> 删除</button>
        </div>
      </div>
    </el-dialog>

    <!-- 新建 / 编辑 知识点 -->
    <el-dialog v-model="showCreate" :title="editing ? '编辑知识点' : '新建知识点'" width="560px" align-center @closed="resetForm">
      <div class="kf-form">
        <div class="kf-row">
          <label>模块 *</label>
          <select v-model="form.module" class="kf-input">
            <option v-for="m in MODULES" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="kf-row">
          <label>类型 *</label>
          <select v-model="form.kg_type" class="kf-input">
            <option v-for="t in KG_TYPES" :key="t.key" :value="t.key">{{ t.key }}</option>
          </select>
        </div>
        <div class="kf-row">
          <label>标题 *</label>
          <input v-model="form.title" class="kf-input" placeholder="知识点标题" />
        </div>
        <div class="kf-row">
          <label>正文</label>
          <textarea v-model="form.content" class="kf-input" rows="6" placeholder="支持 Markdown"></textarea>
        </div>
        <div class="kf-row">
          <label>考点定位</label>
          <div class="kf-levels">
            <input v-model="form.level1" class="kf-input sm" placeholder="一级" />
            <input v-model="form.level2" class="kf-input sm" placeholder="二级" />
            <input v-model="form.level3" class="kf-input sm" placeholder="三级" />
            <input v-model="form.level4" class="kf-input sm" placeholder="四级" />
          </div>
        </div>
        <div class="kf-row">
          <label>标签</label>
          <input v-model="form.tags" class="kf-input" placeholder="用 / 或中文逗号分隔" />
        </div>
        <div class="kf-row">
          <label>卡片标题</label>
          <input v-model="form.card_title" class="kf-input" placeholder="列表卡片主标题（≤18字，AI 生成）" />
        </div>
        <div class="kf-row">
          <label>卡片标签</label>
          <input v-model="form.card_tags" class="kf-input" placeholder="用 ｜ 分隔短词，如 科举制度｜历史常识" />
        </div>
        <div class="kf-row">
          <label>卡片摘要</label>
          <textarea v-model="form.card_summary" class="kf-input" rows="2" placeholder="列表卡片两行速记（≤70字，AI 生成）"></textarea>
        </div>
        <div class="kf-row">
          <label>关联提示词</label>
          <input v-model="form.related_prompt" class="kf-input" placeholder="默认同模块名" />
        </div>
        <div class="kf-row">
          <label>难度</label>
          <div class="kf-rate"><el-rate v-model="form.difficulty" :max="5" /></div>
        </div>
        <div class="kf-row">
          <label>出处</label>
          <input v-model="form.source" class="kf-input" placeholder="来源（可选）" />
        </div>
      </div>
      <template #footer>
        <button class="btn-default" @click="showCreate = false">取消</button>
        <button class="btn-primary" :disabled="!form.title || !form.module || saving" @click="saveForm">{{ saving ? '保存中…' : '保存' }}</button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog v-model="showBatch" title="批量导入知识点" width="640px" align-center>
      <div class="imp">
        <div class="imp-tabs">
          <button class="imp-tab" :class="{ on: batchTab === 'paste' }" @click="batchTab = 'paste'">粘贴 JSON</button>
          <button class="imp-tab" :class="{ on: batchTab === 'file' }" @click="batchTab = 'file'">上传文件</button>
        </div>
        <div v-if="batchTab === 'paste'" class="imp-body">
          <textarea v-model="batchText" class="imp-text" rows="10" placeholder="粘贴 AI 输出的 JSON 数组（可含 ```json 代码围栏或前后说明文字，系统会自动提取数组）"></textarea>
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
    <el-dialog v-model="showPrompt" title="提示词助手 · 让 AI 帮你整理知识点" width="720px" align-center>
      <div class="pa">
        <p class="pa-tip">把下面这段提示词复制给任意 AI（ChatGPT / 通义 / 文心 / Kimi 等），让它输出可直接导入本系统的结构化知识点；再把 AI 的回复粘贴到下方即可一键入库。提示词已与系统模块/类型严格对齐（单一事实源）。</p>
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
import { knowledgeApi } from '../api'
import { renderMarkdown } from '../utils/md'
import { MODULES, modColor, modStyle, KG_TYPES, kgStyle } from '../utils/constants'
import { ElMessage, ElMessageBox } from 'element-plus'

const md = renderMarkdown
const route = useRoute()
const router = useRouter()

const allKb = ref([])
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
const kgTypeColor = (t) => (KG_TYPES.find(x => x.key === t) || {}).color || '#64748b'

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
  return { module: MODULES[0], kg_type: '概念', title: '', content: '', tags: '', related_prompt: '', difficulty: 2, source: '', level1: '', level2: '', level3: '', level4: '', card_title: '', card_tags: '', card_summary: '' }
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
    const res = await knowledgeApi.getList({ page: 1, page_size: 2000 })
    allKb.value = res.data.items || []
  } catch (e) { console.error(e) }
}

const moduleCount = (m) => allKb.value.filter(k => k.module === m).length
const typeCount = (t) => allKb.value.filter(k => k.kg_type === t).length

// 按考点：构建层级 L1 > L2 > L3 的树（常识判断-地理国情-自然地理），含聚合计数
const kaodianTree = computed(() => {
  const root = {}
  for (const k of allKb.value) {
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
  let list = allKb.value
  if (activeModule.value !== 'all') list = list.filter(k => k.module === activeModule.value)
  if (activeType.value !== 'all') list = list.filter(k => k.kg_type === activeType.value)
  if (kaodianPath.value.length) list = list.filter(matchKaodian)
  const kw = keyword.value.trim()
  if (kw) list = list.filter(k => (k.title || '').includes(kw) || (k.content || '').includes(kw) || (k.tags || '').includes(kw))
  const arr = list.slice()
  if (sortMode.value === 'title') arr.sort((a, b) => (a.title || '').localeCompare(b.title, 'zh'))
  else if (sortMode.value === 'difficulty') arr.sort((a, b) => (b.difficulty || 0) - (a.difficulty || 0))
  else if (sortMode.value === 'updated') arr.sort((a, b) => (b.update_time || '').localeCompare(a.update_time || ''))
  else arr.sort((a, b) => (MODULES.indexOf(a.module) - MODULES.indexOf(b.module)) || (KG_TYPES.findIndex(t => t.key === a.kg_type) - KG_TYPES.findIndex(t => t.key === b.kg_type)) || (a.title || '').localeCompare(b.title, 'zh'))
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
    for (const k of list) (map[k.kg_type] = map[k.kg_type] || []).push(k)
    return KG_TYPES.filter(t => map[t.key]).map(t => ({ key: t.key, label: t.key, color: t.color, items: map[t.key] }))
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

// ---------- 新建 / 编辑 ----------
function resetForm() {
  editing.value = null
  form.value = blankForm()
}
function editItem(k) {
  editing.value = k
  form.value = {
    module: k.module, kg_type: k.kg_type, title: k.title, content: k.content || '',
    tags: k.tags || '', related_prompt: k.related_prompt || '', difficulty: k.difficulty || 2, source: k.source || '',
    level1: k.level1 || '', level2: k.level2 || '', level3: k.level3 || '', level4: k.level4 || '',
    card_title: k.card_title || '', card_tags: k.card_tags || '', card_summary: k.card_summary || '',
  }
  showCreate.value = true
}
async function saveForm() {
  if (!form.value.title || !form.value.module) { ElMessage.warning('请填写模块与标题'); return }
  if (!form.value.related_prompt) form.value.related_prompt = form.value.module
  saving.value = true
  try {
    if (editing.value) {
      await knowledgeApi.update(editing.value.id, { ...form.value })
      ElMessage.success('已更新')
    } else {
      await knowledgeApi.create({ ...form.value })
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
    await knowledgeApi.delete(k.id)
    ElMessage.success('已删除')
    await loadAll()
  } catch (e) { ElMessage.error('删除失败') }
}

// ---------- 批量导入 ----------
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
      module, kg_type: (it.kg_type || '概念').toString().trim() || '概念',
      title, content: (it.content || '').toString(),
      tags: (it.tags || '').toString(), related_prompt: (it.related_prompt || module).toString(),
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
    const res = await knowledgeApi.batch(batchPreview.value.items)
    ElMessage.success(`成功导入 ${res.data.created} 条` + (res.data.errors.length ? `，${res.data.errors.length} 条异常跳过` : ''))
    showBatch.value = false
    await loadAll()
  } catch (e) { ElMessage.error('导入失败：' + (e.response?.data?.detail || e.message)) }
  finally { importing.value = false }
}

// ---------- 提示词助手 ----------
const schemaTemplate = `[
  {
    "module": "模块名（必填，见可选模块）",
    "kg_type": "类型（必填，见知识点类型）",
    "title": "知识点标题（必填）",
    "content": "正文（支持 Markdown）",
    "tags": "标签1/标签2",
    "related_prompt": "所属模块名",
    "difficulty": 2,
    "source": "出处",
    "level1": "一级考点", "level2": "二级考点", "level3": "三级考点", "level4": "四级考点"
  }
]`

const promptText = computed(() => {
  const modules = MODULES.map(m => '- ' + m).join('\n')
  const types = KG_TYPES.map(t => '- ' + t.key).join('\n')
  return `你是一位行测（公务员考试《行政职业能力测验》）辅导专家。请基于你掌握的知识，整理以下模块的核心知识点，并严格按照下方 JSON 数组结构输出。不要输出任何解释性文字，只输出可被程序直接解析的 JSON 数组。

可选模块（module 必须严格属于其一）：
${modules}

知识点类型（kg_type 必须严格属于其一）：
${types}

每个对象的字段说明：
- module：必填，且必须是上面模块之一（如「数量关系」）
- kg_type：必填，且必须是上面类型之一（如「公式」）
- title：必填，知识点标题（简洁明确，如「整除特性」「类比推理·交叉关系」）
- content：必填，知识点正文，支持 Markdown（可含列表、示例、公式说明）
- tags：可选，用中文逗号或斜杠分隔的标签
- related_prompt：必填，填写所属模块名（与 module 一致），用于与本系统提示词联动
- difficulty：可选，1-5 整数，表示掌握难度
- level1~level4：可选，知识点对应的考点定位路径（与题库题型树一致，使其落到对应位置）
- source：可选，知识点出处

要求：
1. module 与 kg_type 必须严格取自上面列表，不要自造名称；
2. 每个模块产出 8-15 个知识点，覆盖概念、公式、技巧、陷阱、易混点、方法、背景等多种类型；
3. 优先产出高频考点与易错点；
4. 只输出纯 JSON 数组，不要使用 Markdown 代码围栏，不要额外文字。

输出示例：
[
  {
    "module": "数量关系",
    "kg_type": "公式",
    "title": "整除特性",
    "content": "若整数 a 能被 b 整除，则 a 的各位数字之和也能被 b 的整除因子整除……",
    "tags": "数论/整除",
    "related_prompt": "数量关系",
    "difficulty": 2,
    "level1": "数量关系", "level2": "数学运算", "level3": "数论问题",
    "source": "行测速记"
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
    const res = await knowledgeApi.batch(promptPreview.value.items)
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
.kb-page { display: flex; height: 100%; min-height: 0; }

/* 左导航 */
.kb-side {
  width: 226px; flex-shrink: 0; display: flex; flex-direction: column;
  border-right: 1px solid var(--border-base); background: var(--bg-elevated); overflow-y: auto; padding-bottom: 12px;
}
.kb-side-head { display: flex; align-items: center; gap: 7px; padding: 16px 16px 10px; font-size: 14px; font-weight: 500; color: var(--text-primary); flex-shrink: 0; }
.kb-nav { overflow-y: auto; padding: 2px 10px 6px; display: flex; flex-direction: column; gap: 1px; flex-shrink: 0; }
.kb-nav-item {
  display: flex; align-items: center; gap: 9px; padding: 7px 10px; border-radius: 7px;
  cursor: pointer; border: none; background: none; text-align: left; transition: background 0.14s, color 0.14s; color: var(--text-secondary);
}
.kb-nav-item:hover { background: var(--bg-subtle); }
.kb-nav-item.on { background: var(--bg-subtle); color: var(--text-primary); font-weight: 500; }
.kb-nav-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.kb-nav-name { flex: 1; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kb-nav-n { font-size: 11px; color: var(--text-tertiary); font-variant-numeric: tabular-nums; }
.kb-nav-kaodian { gap: 1px; }
.kb-kd { align-items: flex-start; padding-top: 6px; padding-bottom: 6px; }
.kb-kd.lvl2 { padding-left: 22px; }
.kb-kd.lvl3 { padding-left: 40px; }
.kb-kd-name { white-space: normal; line-height: 1.35; font-size: 12.5px; }
.kb-kd-caret { width: 14px; flex-shrink: 0; font-size: 10px; color: var(--text-tertiary); cursor: pointer; user-select: none; }
.kb-kd-caret.empty { cursor: default; }
.kb-nav-empty { font-size: 12px; color: var(--text-tertiary); padding: 8px 12px; }

.kb-side-sec { padding: 14px 16px 5px; font-size: 11px; font-weight: 500; color: var(--text-tertiary); letter-spacing: 0.5px; flex-shrink: 0; }

/* 右内容 */
.kb-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.kb-toolbar { display: flex; align-items: center; gap: 10px; padding: 12px 18px; border-bottom: 1px solid var(--border-light); flex-shrink: 0; flex-wrap: wrap; }
.kb-search {
  display: flex; align-items: center; gap: 6px; background: var(--bg-subtle);
  border: 1px solid var(--border-base); border-radius: var(--radius-md); padding: 7px 12px; min-width: 200px;
}
.kb-search:focus-within { border-color: var(--primary); }
.kb-ico { font-size: 14px; opacity: 0.55; }
.kb-search input { border: none; background: transparent; outline: none; font-size: 13px; color: var(--text-primary); width: 100%; }
.kb-side-sec { padding: 14px 16px 5px; font-size: 11px; font-weight: 500; color: var(--text-tertiary); letter-spacing: 0.5px; flex-shrink: 0; }

.kb-tools { display: flex; align-items: center; gap: 8px; margin-left: auto; flex-wrap: wrap; }
.kb-view { display: flex; background: var(--bg-subtle); border: 1px solid var(--border-base); border-radius: var(--radius-md); padding: 2px; }
.kb-view-btn { border: none; background: none; padding: 5px 10px; border-radius: var(--radius-sm); cursor: pointer; font-size: 12px; color: var(--text-secondary); transition: all 0.15s; }
.kb-view-btn.on { background: var(--bg-elevated); color: var(--primary); font-weight: 700; box-shadow: var(--shadow-sm); }
.kb-select {
  padding: 6px 28px 6px 10px; border: 1px solid var(--border-base); border-radius: var(--radius-md);
  font-size: 12.5px; background: var(--bg-base); color: var(--text-primary);
  appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6'><path d='M0 0l5 6 5-6z' fill='%2394a3b8'/></svg>");
  background-repeat: no-repeat; background-position: right 10px center;
}
.kb-act {
  display: inline-flex; align-items: center; gap: 4px; font-size: 12.5px; padding: 7px 12px; border-radius: var(--radius-md);
  border: 1px solid var(--border-base); background: var(--bg-base); color: var(--text-secondary); cursor: pointer; transition: all 0.15s;
}
.kb-act:hover { color: var(--primary); border-color: var(--primary); }
.kb-act.primary { background: var(--primary); color: #fff; border-color: var(--primary); }
.kb-act.primary:hover { background: var(--primary-dark); color: #fff; }

/* 考点筛选条 */
.kb-filterbar { display: flex; align-items: center; gap: 12px; padding: 8px 18px; border-bottom: 1px solid var(--border-light); background: var(--primary-bg); flex-shrink: 0; flex-wrap: wrap; }
.kb-filter-chip { font-size: 12.5px; color: var(--text-secondary); display: inline-flex; align-items: center; gap: 6px; background: var(--bg-base); border: 1px solid var(--border-base); padding: 4px 10px; border-radius: 999px; }
.kb-filter-chip b { color: var(--primary); }
.kb-filter-x { border: none; background: none; cursor: pointer; color: var(--text-tertiary); font-size: 15px; line-height: 1; padding: 0 2px; }
.kb-filter-x:hover { color: var(--danger); }
.kb-filter-hint { font-size: 11.5px; color: var(--text-tertiary); }

.kb-scroll { flex: 1; overflow-y: auto; padding: 18px 22px 40px; }
.kb-group { margin-bottom: 26px; max-width: 920px; }
.kb-group.flat { margin-bottom: 0; }
.kb-group-head { display: flex; align-items: center; gap: 8px; padding: 6px 2px 10px 12px; border-left: 3px solid var(--gc, var(--border-base)); border-bottom: 1px solid var(--border-light); margin-bottom: 12px; }
.kb-group-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.kb-group-name { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.kb-group-n { font-size: 12px; color: var(--text-tertiary); }

/* 单列列表 */
.kb-list { display: flex; flex-direction: column; gap: 8px; max-width: 920px; }
.kb-card {
  position: relative; background: var(--bg-elevated); border: 1px solid var(--border-base); border-radius: 10px;
  padding: 14px 16px 13px; transition: border-color 0.14s, background 0.14s; cursor: pointer;
}
.kb-card::before { content: ''; position: absolute; left: 0; top: 12px; bottom: 12px; width: 3px; border-radius: 0 3px 3px 0; background: var(--tc, var(--border-base)); opacity: 0.85; }
.kb-card:hover { border-color: var(--tc, var(--primary)); }
.kb-card-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.kb-tag { display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; font-weight: 500; flex-shrink: 0; }
.kb-tag-dot { width: 6px; height: 6px; border-radius: 50%; }
.kb-title { margin: 0; font-size: 14.5px; font-weight: 500; color: var(--text-primary); flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kb-diff { font-size: 8px; color: var(--warning); letter-spacing: 2px; flex-shrink: 0; line-height: 1; }
.kb-diff i { color: var(--border-base); font-style: normal; }
.kb-mod { display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; color: var(--text-tertiary); flex-shrink: 0; }
.kb-mod-dot { width: 7px; height: 7px; border-radius: 50%; }
.kb-content { font-size: 13px; line-height: 1.72; color: var(--text-secondary); }
.kb-content.clamp { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.kb-content :deep(p) { margin: 0 0 6px; }
.kb-content :deep(p:last-child) { margin-bottom: 0; }
.kb-content :deep(strong) { color: var(--text-primary); font-weight: 500; }
.kb-content :deep(ol), .kb-content :deep(ul) { padding-left: 20px; margin: 0 0 6px; }
.kb-content :deep(li) { margin-bottom: 2px; }
.kb-content :deep(code) { background: var(--bg-subtle); padding: 1px 5px; border-radius: 4px; font-size: 12px; }
/* 卡片缩略信息（提示词生成，替代大段正文） */
.kb-title { font-size: 15px; font-weight: 600; line-height: 1.45; color: var(--text-primary); margin: 8px 0 6px; }
.kb-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 6px; }
.kb-tagchip { font-size: 11px; font-weight: 500; padding: 2px 9px; border-radius: 999px; background: var(--primary-bg); color: var(--primary); cursor: pointer; transition: all 0.12s; }
.kb-tagchip:hover { background: var(--primary); color: #fff; }
.kb-summary { font-size: 13px; line-height: 1.62; color: var(--text-secondary); background: var(--bg-subtle); border-radius: var(--radius-md); padding: 9px 11px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.kb-detail-cardinfo { margin: 10px 0; }
.kb-detail-summary { font-size: 13.5px; line-height: 1.6; color: var(--text-secondary); background: var(--bg-subtle); border-left: 3px solid var(--primary); padding: 9px 12px; border-radius: 0 var(--radius-md) var(--radius-md) 0; }
.kb-detail-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }

/* 考点面包屑 */
.kb-crumb { display: flex; align-items: center; flex-wrap: wrap; gap: 2px; margin: 2px 0 8px; font-size: 11.5px; color: var(--text-tertiary); }
.kb-crumb-ico { font-size: 12px; color: var(--primary); margin-right: 2px; }
.kb-crumb-item { border: none; background: none; cursor: pointer; color: var(--text-tertiary); font-size: 11.5px; padding: 1px 4px; border-radius: 5px; transition: all 0.12s; }
.kb-crumb-item:hover { color: var(--primary); background: var(--primary-bg); }
.kb-crumb-item.on { color: var(--primary); background: var(--primary-bg); font-weight: 600; }
.kb-crumb-static { color: var(--text-tertiary); }
.kb-crumb-static:not(:last-child)::after { content: ' › '; }

.kb-expand { margin-top: 6px; background: none; border: none; padding: 0; color: var(--primary); font-size: 12px; cursor: pointer; }
.kb-expand:hover { text-decoration: underline; }
.kb-foot { display: flex; align-items: center; gap: 10px; margin-top: 11px; flex-wrap: wrap; }
.kb-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.kb-tagslice { font-size: 11px; color: var(--text-tertiary); }
.kb-foot-right { display: flex; align-items: center; gap: 12px; margin-left: auto; }
.kb-rel { font-size: 11.5px; color: var(--text-tertiary); display: inline-flex; align-items: center; gap: 4px; }
.kb-rel .el-icon { font-size: 11px; }
.kb-source { display: inline-flex; align-items: center; gap: 4px; font-size: 11.5px; padding: 3px 9px; border-radius: 7px; border: 1px solid var(--border-base); background: var(--bg-base); color: var(--primary); cursor: pointer; transition: all 0.14s; }
.kb-source:hover { border-color: var(--primary); background: var(--primary-bg); }
.kb-practice { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; padding: 4px 10px; border-radius: 7px; border: 1px solid var(--border-base); background: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.14s; }
.kb-practice:hover { color: var(--primary); border-color: var(--primary); }
.kb-card-ops { display: flex; gap: 2px; flex-shrink: 0; opacity: 0; transition: opacity 0.12s; }
.kb-card:hover .kb-card-ops { opacity: 1; }
.kb-op { background: transparent; border: none; width: 26px; height: 26px; border-radius: var(--radius-sm); cursor: pointer; color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 13px; transition: all 0.12s; }
.kb-op:hover { color: var(--text-secondary); background: var(--bg-subtle); }
.kb-op.danger:hover { color: var(--danger); background: var(--danger-bg); }

.kb-empty { text-align: center; padding: 70px 20px; color: var(--text-tertiary); }
.kbe-ico { font-size: 44px; }
.kb-empty div { margin: 12px 0 16px; font-size: 15px; }
.btn-default { background: var(--bg-subtle); color: var(--text-secondary); border: 1px solid var(--border-base); padding: 8px 14px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; }
.btn-default:hover { color: var(--primary); border-color: var(--primary); }
.btn-default:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: var(--primary); color: #fff; border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-primary:hover { background: var(--primary-dark); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

/* 详情抽屉 */
.kb-detail { display: flex; flex-direction: column; gap: 12px; }
.kb-detail-meta { display: flex; align-items: center; gap: 10px; }
.kb-detail-content { font-size: 13.5px; line-height: 1.75; color: var(--text-secondary); max-height: 46vh; overflow-y: auto; padding-right: 4px; }
.kb-detail-content :deep(p) { margin: 0 0 8px; }
.kb-detail-content :deep(strong) { color: var(--text-primary); }
.kb-detail-content :deep(ol), .kb-detail-content :deep(ul) { padding-left: 20px; }
.kb-detail-content :deep(code) { background: var(--bg-subtle); padding: 1px 5px; border-radius: 4px; font-size: 12px; }
.kb-detail-foot { display: flex; flex-wrap: wrap; gap: 5px; }
.kb-detail-ops { display: flex; gap: 8px; flex-wrap: wrap; border-top: 1px solid var(--border-light); padding-top: 12px; }
.btn-default.danger { color: var(--danger); border-color: var(--danger); }
.btn-default.danger:hover { background: var(--danger-bg); }
.btn-default.danger .el-icon { margin-right: 3px; }

/* 表单 */
.kf-form { display: flex; flex-direction: column; gap: 12px; }
.kf-row { display: flex; align-items: center; gap: 10px; }
.kf-row label { width: 84px; flex-shrink: 0; font-size: 13px; color: var(--text-secondary); text-align: right; }
.kf-input { flex: 1; padding: 8px 10px; border: 1px solid var(--border-base); border-radius: var(--radius-md); font-size: 13px; background: var(--bg-base); color: var(--text-primary); font-family: inherit; }
.kf-input:focus { outline: none; border-color: var(--primary); }
.kf-levels { flex: 1; display: flex; gap: 6px; }
.kf-input.sm { flex: 1; min-width: 0; padding: 7px 8px; }
textarea.kf-input { resize: vertical; font-family: 'Consolas', 'Monaco', monospace; }
.kf-rate { flex: 1; }

/* 批量导入 */
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

/* 提示词助手 */
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
  .kb-side { width: 100%; }
  .kb-tools { width: 100%; margin-left: 0; }
}
</style>
