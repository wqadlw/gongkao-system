<template>
  <div class="ql-page">
    <!-- 左：题型树（独立面板，舒适） -->
    <aside class="ql-tree" :class="{ collapsed: treeCollapsed }">
      <div class="ql-tree-head">
        <span class="qth-title"><el-icon><Files /></el-icon> 题型树</span>
        <button class="qth-toggle" @click="treeCollapsed = !treeCollapsed" :title="treeCollapsed ? '展开' : '收起'">
          <el-icon><Fold /></el-icon>
        </button>
      </div>

      <div class="ql-tree-scroll" v-if="!treeCollapsed">
        <CategoryTree v-if="store.categoryTree.length" :nodes="store.categoryTree" :active-id="route.query.cat" />
        <div v-else class="ql-tree-loading">题型树加载中…</div>
      </div>

      <!-- 收起态：仅模块色点，点击按模块筛选 -->
      <div v-else class="ql-tree-rail">
        <button v-for="m in MODULES" :key="m" class="rail-dot" :style="{ background: modColor(m) }"
          :title="m" @click="quickModule(m)"></button>
      </div>
    </aside>

    <!-- 右：题目列表（舒适密度） -->
    <section class="ql-main">
      <div class="ql-toolbar">
        <div class="ql-search">
          <el-icon class="ql-ico"><Search /></el-icon>
          <input v-model="keyword" @keyup.enter="noop" placeholder="搜索题干…" />
        </div>
        <div class="ql-chips">
          <button v-for="c in chipDefs" :key="c.key" class="chip" :class="{ on: activeChip === c.key }"
            @click="activeChip = c.key">
            {{ c.label }}<span v-if="c.key !== 'all'" class="chip-n">{{ chipCount(c.key) }}</span>
          </button>
        </div>
        <div class="ql-right">
          <select v-model="filters.sort" class="ql-select">
            <option value="new">最新</option>
            <option value="old">最早</option>
            <option value="difficulty">难度↓</option>
            <option value="mastery_low">掌握度↓</option>
          </select>
          <button class="ql-add" @click="$router.push('/question-input')"><el-icon><Plus /></el-icon> 录入</button>
        </div>
      </div>

      <div class="ql-crumb" v-if="activeCrumb.length">
        <el-icon><Files /></el-icon>
        <template v-for="(seg, i) in activeCrumb" :key="i">
          <span class="cb-seg">{{ seg }}</span>
        </template>
        <button class="cb-clear" @click="clearCategory">清除筛选</button>
      </div>

      <div class="ql-scroll">
        <div v-if="groups.length" class="ql-groups">
          <section v-for="g in groups" :key="g.name" class="ql-group">
            <header class="qlg-head" @click="toggleGroup(g.name)">
              <el-icon class="qlg-caret" :class="{ open: !collapsedGroups.has(g.name) }"><ArrowRight /></el-icon>
              <span class="qlg-dot" :style="{ background: modColor(g.name) }"></span>
              <span class="qlg-name">{{ g.name }}</span>
              <span class="qlg-count">{{ g.count }} 题</span>
              <span v-if="g.errCount" class="qlg-err">错 {{ g.errCount }}</span>
            </header>
            <div v-show="!collapsedGroups.has(g.name)" class="ql-rows">
              <article v-for="(q, i) in g.items" :key="q.id" class="ql-card"
                :class="{ active: route.params && Number(route.params.id) === q.id, err: q.is_error }"
                :style="{ '--mc': modColor(q.level1) }" @click="openDetail(q)">
                <span class="qlc-idx">{{ i + 1 }}</span>
                <div class="qlc-body">
                  <div class="qlc-head">
                    <span class="qlc-mod" :style="{ background: modColor(q.level1), color: '#fff' }">{{ q.level1 }}</span>
                    <span class="qlc-type">{{ typeLabel(q) }}</span>
                    <span class="qlc-diff" :title="'难度 ' + (q.difficulty || 3)">{{ '●'.repeat(q.difficulty || 3) }}<i>{{ '●'.repeat(5 - (q.difficulty || 3)) }}</i></span>
                    <span class="qlc-ans" :class="{ err: q.is_error }" title="答案">{{ q.answer || '—' }}</span>
                  </div>
                  <h3 class="qlc-title" :title="cardTitle(q)">{{ cardTitle(q) }}</h3>
                  <div class="qlc-tags" v-if="cardTags(q).length">
                    <button v-for="t in cardTags(q)" :key="t" class="qlc-tag" @click.stop="gotoKnowledge(t)"
                      :title="'在知识库检索：' + t"><el-icon><Collection /></el-icon>{{ t }}</button>
                  </div>
                  <p class="qlc-sum" v-if="q.card_summary">{{ q.card_summary }}</p>
                  <div class="qlc-foot">
                    <div class="qlc-flags">
                      <span v-if="q.is_error" class="qlc-flag err">错题</span>
                      <span v-if="q.question_type_tag === '母题'" class="qlc-flag mother">母题</span>
                      <span v-if="q.is_favorite" class="qlc-flag fav">收藏</span>
                      <span v-if="q.card_summary" class="qlc-has">含速记</span>
                    </div>
                    <div class="qlc-actions" @click.stop>
                      <button class="qlc-btn" :class="{ on: q.is_favorite }" @click="toggleFav(q)" :title="q.is_favorite ? '取消收藏' : '收藏'"><el-icon><Star /></el-icon></button>
                      <button class="qlc-btn danger" @click="handleDelete(q)" title="删除"><el-icon><Delete /></el-icon></button>
                    </div>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </div>
        <div v-else class="ql-empty">
          <el-icon class="qe-ico"><DocumentDeleted /></el-icon>
          <div>暂无符合条件的题目</div>
          <button class="btn-primary" @click="$router.push('/question-input')">去录入第一道题</button>
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { questionApi, categoryApi } from '../api'
import { useAppStore } from '../stores/app'
import { renderMarkdown, renderInline } from '../utils/md'
import { ElMessage, ElMessageBox } from 'element-plus'
import CategoryTree from '../components/CategoryTree.vue'
import { MODULES, modColor, modStyle } from '../utils/constants'

const md = renderMarkdown
const mdInline = renderInline
const router = useRouter()
const route = useRoute()
const store = useAppStore()

const allQuestions = ref([])
const keyword = ref('')
const activeChip = ref('all')
const treeCollapsed = ref(false)
const collapsedGroups = reactive(new Set())
const collapsedSubs = reactive(new Set())
const filters = reactive({ sort: 'new' })

const activeNodeLevels = ref({})   // 题型树选中节点的 level1~5（用于过滤）
const activeCrumb = ref([])

const chipDefs = [
  { key: 'all', label: '全部' },
  { key: 'fav', label: '收藏' },
  { key: 'error', label: '错题' },
  { key: 'master', label: '未掌握' },
  { key: 'mother', label: '母题' },
]
function chipCount(key) {
  return allQuestions.value.filter(q => matchChip(q, key)).length
}
function matchChip(q, key) {
  if (key === 'fav') return q.is_favorite
  if (key === 'error') return q.is_error
  if (key === 'master') return (q.master_level || 0) <= 2
  if (key === 'mother') return q.question_type_tag === '母题'
  return true
}

// 题型：优先显示细分题型（level2），缺省回退模块名
function typeLabel(q) {
  return q.level2 && q.level2 !== '全部' ? q.level2 : (q.level1 || '未分类')
}
// 卡片主标题：优先用 AI 生成的卡片标题（一句话概括），缺省回退题干前几句
function cardTitle(q) {
  const t = (q.card_title || '').trim()
  if (t) return t
  return (q.question_raw || '（无题干）').replace(/\n+/g, ' ').slice(0, 60)
}
// 考点短标签：把存储的「｜」分隔字符串拆成数组（AI 生成的短标签，非完整题型树路径）
function cardTags(q) {
  return (q.card_tags || '').split('｜').map(s => s.trim()).filter(Boolean)
}

function masteryColor(level) {
  if (level <= 1) return '#ef4444'
  if (level <= 2) return '#f59e0b'
  if (level <= 3) return '#eab308'
  if (level <= 4) return '#84cc16'
  return '#10b981'
}

// 题型树选中节点作为过滤条件（按层级前缀匹配）
function matchNode(q) {
  const lv = activeNodeLevels.value
  for (let i = 1; i <= 5; i++) {
    const v = lv['level' + i]
    if (v && (q['level' + i] || '') !== v) return false
  }
  return true
}

const filtered = computed(() => {
  let list = allQuestions.value
  const kw = keyword.value.trim()
  if (kw) list = list.filter(q => (q.question_raw || '').includes(kw))
  if (Object.keys(activeNodeLevels.value).length) list = list.filter(matchNode)
  list = list.filter(q => matchChip(q, activeChip.value))
  const arr = list.slice()
  if (filters.sort === 'new') arr.sort((a, b) => b.id - a.id)
  else if (filters.sort === 'old') arr.sort((a, b) => a.id - b.id)
  else if (filters.sort === 'difficulty') arr.sort((a, b) => (b.difficulty || 3) - (a.difficulty || 3))
  else if (filters.sort === 'mastery_low') arr.sort((a, b) => (a.master_level || 0) - (b.master_level || 0))
  return arr
})

const groups = computed(() => {
  const map = {}
  for (const q of filtered.value) {
    const m = q.level1 || '未分类'
    if (!map[m]) map[m] = { name: m, items: [], sub: {} }
    map[m].items.push(q)
    const l2 = q.level2 || '未分组'
    if (!map[m].sub[l2]) map[m].sub[l2] = []
    map[m].sub[l2].push(q)
  }
  const ordered = Object.keys(map).sort((a, b) => {
    const ia = MODULES.indexOf(a), ib = MODULES.indexOf(b)
    if (ia === -1 && ib === -1) return a.localeCompare(b, 'zh')
    if (ia === -1) return 1
    if (ib === -1) return -1
    return ia - ib
  })
  return ordered.map(m => {
    const g = map[m]
    const subKeys = Object.keys(g.sub).sort((a, b) => g.sub[b].length - g.sub[a].length)
    const avg = g.items.length ? g.items.reduce((s, x) => s + (x.master_level || 0), 0) / g.items.length : 0
    const errCount = g.items.filter(x => x.is_error).length
    return {
      name: m, count: g.items.length, avg, errCount,
      items: g.items,
      sub: subKeys.map(l2 => ({ name: l2, items: g.sub[l2], count: g.sub[l2].length })),
    }
  })
})

async function toggleFav(q) {
  try {
    await questionApi.update(q.id, { is_favorite: !q.is_favorite })
    q.is_favorite = !q.is_favorite
    ElMessage.success(q.is_favorite ? '已收藏' : '已取消收藏')
  } catch (e) {
    ElMessage.error('操作失败：' + (e.response?.data?.detail || e.message))
  }
}

async function reload() {
  try {
    const res = await questionApi.getList({ page: 1, page_size: 5000, sort: 'new' })
    allQuestions.value = res.data.items || []
  } catch (e) { console.error(e) }
}

function toggleGroup(name) {
  if (collapsedGroups.has(name)) collapsedGroups.delete(name)
  else collapsedGroups.add(name)
}
function toggleSub(key) {
  if (collapsedSubs.has(key)) collapsedSubs.delete(key)
  else collapsedSubs.add(key)
}

function openDetail(q) {
  router.push('/question/' + q.id)
}

// 耦合：点击题目卡片的「考点标签」→ 跳转知识库并按该短标签关键词检索
function gotoKnowledge(kw) {
  if (!kw) return
  router.push('/knowledge?keyword=' + encodeURIComponent(kw))
}

async function handleDelete(q) {
  await ElMessageBox.confirm('确定删除这道题目？', '提示', { type: 'warning' })
  await questionApi.delete(q.id)
  ElMessage.success('删除成功')
  reload()
  store.loadCategories()
}

async function applyCatFilter(catId) {
  try {
    const res = await categoryApi.getNode(catId)
    const d = res.data
    activeNodeLevels.value = {
      level1: d.level1, level2: d.level2, level3: d.level3, level4: d.level4, level5: d.level5,
    }
    activeCrumb.value = [d.level1, d.level2, d.level3, d.level4, d.level5].filter(Boolean)
  } catch {
    activeNodeLevels.value = {}
    activeCrumb.value = []
  }
}
function quickModule(m) {
  activeNodeLevels.value = { level1: m }
  activeCrumb.value = [m]
}

// 从知识库「练该模块题」带 ?module= 进入：按模块名直接筛选（系统耦合）
function applyModuleFilter(m) {
  activeNodeLevels.value = { level1: m }
  activeCrumb.value = [m]
}
function clearCategory() {
  activeNodeLevels.value = {}
  activeCrumb.value = []
  router.replace({ path: '/question-list' })
}

function noop() {}

watch(() => route.query, async (q) => {
  if (q.module) applyModuleFilter(q.module)
  else if (q.cat) await applyCatFilter(q.cat)
  else { activeNodeLevels.value = {}; activeCrumb.value = [] }
}, { deep: false })

onMounted(async () => {
  if (!store.categoryTree.length) await store.loadCategories()
  if (route.query.module) applyModuleFilter(route.query.module)
  else if (route.query.cat) await applyCatFilter(route.query.cat)
  reload()
})
</script>

<style scoped>
.ql-page { display: flex; height: 100%; min-height: 0; }

/* 左：题型树 */
.ql-tree {
  width: 280px; flex-shrink: 0; display: flex; flex-direction: column;
  border-right: 1px solid var(--border-base); background: var(--bg-elevated); overflow: hidden;
  transition: width 0.2s;
}
.ql-tree.collapsed { width: 56px; }
.ql-tree-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 14px 10px; border-bottom: 1px solid var(--border-light); flex-shrink: 0;
}
.qth-title { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 700; color: var(--text-primary); }
.qth-toggle { background: var(--bg-subtle); border: none; width: 28px; height: 28px; border-radius: var(--radius-sm); cursor: pointer; color: var(--text-secondary); display: flex; align-items: center; justify-content: center; }
.qth-toggle:hover { color: var(--primary); }
.ql-tree-scroll { flex: 1; overflow-y: auto; padding: 6px 8px; }
.ql-tree-loading { padding: 20px; color: var(--text-tertiary); font-size: 13px; }
.ql-tree-rail { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 10px; padding-top: 16px; }
.rail-dot { width: 16px; height: 16px; border-radius: 50%; border: none; cursor: pointer; padding: 0; }
.rail-dot:hover { transform: scale(1.15); }

/* 右：列表 */
.ql-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.ql-toolbar { display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-bottom: 1px solid var(--border-light); flex-shrink: 0; flex-wrap: wrap; }
.ql-search {
  display: flex; align-items: center; gap: 6px; background: var(--bg-subtle);
  border: 1px solid var(--border-base); border-radius: var(--radius-md); padding: 7px 12px; min-width: 220px;
}
.ql-search:focus-within { border-color: var(--primary); }
.ql-ico { font-size: 14px; opacity: 0.55; }
.ql-search input { border: none; background: transparent; outline: none; font-size: 13px; color: var(--text-primary); width: 100%; }
.ql-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px;
  padding: 6px 12px; border-radius: 999px; cursor: pointer;
  background: var(--bg-subtle); border: 1px solid var(--border-base); color: var(--text-secondary);
  transition: all 0.15s;
}
.chip:hover { color: var(--primary); border-color: var(--primary); }
.chip.on { color: #fff; background: var(--primary); border-color: var(--primary); }
.chip-n { font-size: 11px; opacity: 0.8; background: rgba(255,255,255,0.25); padding: 0 6px; border-radius: 8px; }
.chip:not(.on) .chip-n { background: var(--bg-base); color: var(--text-tertiary); }
.ql-right { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.ql-select {
  padding: 6px 28px 6px 10px; border: 1px solid var(--border-base); border-radius: var(--radius-md);
  font-size: 12.5px; background: var(--bg-base); color: var(--text-primary);
  appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6'><path d='M0 0l5 6 5-6z' fill='%2394a3b8'/></svg>");
  background-repeat: no-repeat; background-position: right 10px center;
}
.ql-add { display: inline-flex; align-items: center; gap: 4px; background: var(--primary); color: #fff; border: none; padding: 7px 14px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.ql-add:hover { background: var(--primary-dark); }

.ql-crumb { display: flex; align-items: center; gap: 6px; padding: 8px 16px; font-size: 12.5px; color: var(--text-secondary); border-bottom: 1px solid var(--border-light); flex-shrink: 0; }
.cb-seg { background: var(--primary-bg); color: var(--primary); padding: 2px 9px; border-radius: 6px; font-weight: 600; }
.cb-clear { margin-left: auto; background: none; border: 1px solid var(--border-base); color: var(--text-secondary); border-radius: var(--radius-sm); cursor: pointer; font-size: 12px; padding: 2px 9px; }
.cb-clear:hover { border-color: var(--danger); color: var(--danger); }

.ql-scroll { flex: 1; overflow-y: auto; padding: 18px 20px 40px; }

/* 分组：极简标题行 */
.ql-group { margin-bottom: 26px; }
.qlg-head {
  display: flex; align-items: center; gap: 9px; padding: 4px 2px 10px; cursor: pointer;
  border-bottom: 1px solid var(--border-light); margin-bottom: 12px;
}
.qlg-caret { font-size: 12px; color: var(--text-tertiary); transition: transform 0.15s; flex-shrink: 0; }
.qlg-caret.open { transform: rotate(90deg); }
.qlg-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.qlg-name { font-size: 14px; font-weight: 500; color: var(--text-primary); letter-spacing: 0.2px; }
.qlg-count { font-size: 12px; color: var(--text-tertiary); }
.qlg-err { font-size: 11px; color: var(--danger); background: var(--danger-bg); padding: 1px 8px; border-radius: 999px; }

/* 卡片列表 */
.ql-rows { display: flex; flex-direction: column; gap: 8px; }
.ql-card {
  position: relative; display: flex; gap: 12px; cursor: pointer;
  padding: 13px 15px 13px 14px; border-radius: 10px;
  background: var(--bg-elevated); border: 1px solid var(--border-base);
  transition: border-color 0.14s, background 0.14s;
}
.ql-card::before {
  content: ''; position: absolute; left: 0; top: 10px; bottom: 10px; width: 3px;
  border-radius: 0 3px 3px 0; background: var(--mc, var(--border-base)); opacity: 0.85;
}
.ql-card:hover { border-color: var(--mc, var(--primary)); background: var(--bg-hover); }
.ql-card.active { border-color: var(--primary); background: var(--primary-bg); }
.ql-card.err::before { background: var(--danger); }

.qlc-idx {
  flex-shrink: 0; width: 22px; text-align: center; font-size: 12px; font-variant-numeric: tabular-nums;
  color: var(--text-tertiary); padding-top: 2px; user-select: none;
}
.qlc-body { flex: 1; min-width: 0; }

/* 卡片头部：模块徽章 + 题型 + 难度 + 答案 */
.qlc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; flex-wrap: wrap; }
.qlc-mod {
  font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 999px; line-height: 1.4;
  flex-shrink: 0; white-space: nowrap;
}
.qlc-type { font-size: 12px; color: var(--text-secondary); flex-shrink: 0; }
.qlc-type::before { content: '·'; margin-right: 6px; color: var(--text-tertiary); }
.qlc-diff { font-size: 8px; color: var(--warning); letter-spacing: 2px; flex-shrink: 0; line-height: 1; margin-left: auto; }
.qlc-diff i { color: var(--border-base); font-style: normal; }
.qlc-ans {
  font-size: 12.5px; font-weight: 600; color: var(--success); flex-shrink: 0;
  background: var(--success-bg); padding: 1px 10px; border-radius: 6px; font-variant-numeric: tabular-nums;
}
.qlc-ans.err { color: var(--danger); background: var(--danger-bg); }

/* 卡片主标题：AI 生成的卡片标题（一句话概括） */
.qlc-title {
  margin: 0 0 7px; font-size: 15px; font-weight: 600; line-height: 1.45; color: var(--text-primary);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
/* 考点短标签：AI 生成的彩色小标签，点击跳知识库 */
.qlc-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 7px; }
.qlc-tag {
  display: inline-flex; align-items: center; gap: 3px; font-size: 11.5px; cursor: pointer;
  padding: 2px 9px; border-radius: 999px; color: var(--info); background: var(--info-bg);
  border: 1px solid transparent; transition: all 0.13s;
}
.qlc-tag .el-icon { font-size: 11px; }
.qlc-tag:hover { border-color: var(--info); background: var(--info-bg); filter: brightness(0.96); }
/* 卡片摘要：2 行速记 */
.qlc-sum {
  margin: 0 0 9px; font-size: 12.5px; line-height: 1.6; color: var(--text-tertiary);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.qlc-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 22px; }
.qlc-flags { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.qlc-flag { font-size: 11px; padding: 1px 8px; border-radius: 999px; background: var(--bg-subtle); color: var(--text-tertiary); }
.qlc-flag.err { color: var(--danger); background: var(--danger-bg); }
.qlc-flag.mother { color: var(--info); background: var(--info-bg); }
.qlc-flag.fav { color: #f59e0b; background: #f59e0b1a; }
.qlc-has { font-size: 11px; padding: 1px 8px; border-radius: 999px; color: #0ea5e9; background: #0ea5e91a; }
.qlc-actions { display: flex; gap: 4px; flex-shrink: 0; opacity: 0; transition: opacity 0.12s; }
.ql-card:hover .qlc-actions, .ql-card.active .qlc-actions { opacity: 1; }
.qlc-btn { background: transparent; border: none; width: 28px; height: 28px; border-radius: var(--radius-sm); cursor: pointer; color: var(--text-tertiary); display: flex; align-items: center; justify-content: center; font-size: 14px; transition: all 0.12s; }
.qlc-btn:hover { background: var(--bg-subtle); color: var(--text-secondary); }
.qlc-btn.on { color: #f59e0b; }
.qlc-btn.danger:hover { background: var(--danger-bg); color: var(--danger); }

.ql-empty { text-align: center; padding: 70px 20px; color: var(--text-tertiary); }
.qe-ico { font-size: 44px; }
.ql-empty div { margin: 12px 0 16px; font-size: 15px; }

.btn-primary { background: var(--primary); color: white; border: none; padding: 8px 16px; border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-primary:hover { background: var(--primary-dark); }

@media (max-width: 900px) {
  .ql-tree { width: 100%; }
  .ql-tree.collapsed { width: 100%; }
}
</style>
