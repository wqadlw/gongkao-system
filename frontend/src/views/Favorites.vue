<template>
  <div class="fav-page">
    <!-- 页头：标题 + 汇总统计 -->
    <div class="fav-hero">
      <div class="hero-left">
        <h2><el-icon><StarFilled /></el-icon> 我的收藏</h2>
        <p class="hero-sub">跨题目 · 资料 · 知识点 · 解题技巧的统一收藏夹</p>
      </div>
      <div class="hero-stats">
        <button
          v-for="t in TABS" :key="t.type"
          class="stat-chip" :class="{ active: currentType === t.type }"
          @click="switchType(t.type)"
        >
          <el-icon><component :is="t.icon" /></el-icon>
          <div class="sc-body"><b>{{ counts[t.type] || 0 }}</b><i>{{ t.label }}</i></div>
        </button>
      </div>
    </div>

    <!-- 工具栏：搜索 / 排序 / 视图 / 批量 -->
    <div class="fav-toolbar card">
      <el-input v-model="searchKw" placeholder="在收藏中搜索…" clearable class="tb-search">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="sortBy" class="tb-sort">
        <el-option value="time_desc" label="最新收藏" />
        <el-option value="time_asc" label="最早收藏" />
        <el-option value="title" label="按标题" />
      </el-select>
      <div class="tb-view">
        <button class="view-btn" :class="{ active: viewMode === 'list' }" title="列表视图" @click="viewMode = 'list'">
          <el-icon><Tickets /></el-icon>
        </button>
        <button class="view-btn" :class="{ active: viewMode === 'grid' }" title="网格视图" @click="viewMode = 'grid'">
          <el-icon><Grid /></el-icon>
        </button>
      </div>
      <el-button v-if="!batchMode" size="small" @click="startBatch">
        <el-icon><Operation /></el-icon> 批量管理
      </el-button>
      <template v-else>
        <el-checkbox
          :model-value="allChecked" :indeterminate="checked.size > 0 && !allChecked"
          @change="toggleAll"
        >全选</el-checkbox>
        <el-button size="small" type="danger" :disabled="!checked.size" :loading="batchLoading" @click="batchRemove">
          取消收藏（{{ checked.size }}）
        </el-button>
        <el-button size="small" @click="batchMode = false; checked = new Set()">退出</el-button>
      </template>
    </div>

    <!-- 内容区 -->
    <div v-loading="loading" :class="viewMode === 'list' ? 'fav-rows' : 'fav-grid'">
      <template v-if="viewMode === 'list'">
        <div
          v-for="it in visibleItems" :key="it.favorite_id"
          class="row card"
          :class="{ selected: batchMode && checked.has(it.obj_id) }"
          @click="go(it)"
        >
          <el-checkbox
            v-if="batchMode" class="row-check"
            :model-value="checked.has(it.obj_id)"
            @change="toggleChecked(it.obj_id)" @click.stop
          />
          <span class="row-badge">{{ it.badge || typeLabel }}</span>
          <div class="row-main">
            <div class="row-title">{{ it.title }}</div>
            <div v-if="it.subtitle" class="row-sub">{{ it.subtitle }}</div>
            <div v-if="it.note" class="row-note"><el-icon><ChatLineSquare /></el-icon> {{ it.note }}</div>
          </div>
          <div class="row-side">
            <span class="row-time">{{ it.collect_time }}</span>
            <div class="row-actions">
              <button class="act" title="备注" @click.stop="editNote(it)"><el-icon><ChatLineSquare /></el-icon></button>
              <button class="act danger" title="取消收藏" @click.stop="removeFavorite(it)"><el-icon><StarFilled /></el-icon></button>
            </div>
          </div>
        </div>
      </template>
      <template v-else>
        <div
          v-for="it in visibleItems" :key="it.favorite_id"
          class="gcell card"
          :class="{ selected: batchMode && checked.has(it.obj_id) }"
          @click="go(it)"
        >
          <div class="g-badge">{{ it.badge || typeLabel }}</div>
          <div class="g-title">{{ it.title }}</div>
          <div class="g-sub">{{ it.subtitle }}</div>
          <div v-if="it.note" class="g-note">{{ it.note }}</div>
          <div class="g-foot">
            <span>{{ it.collect_time }}</span>
            <div class="row-actions">
              <button class="act" title="备注" @click.stop="editNote(it)"><el-icon><ChatLineSquare /></el-icon></button>
              <button class="act danger" title="取消收藏" @click.stop="removeFavorite(it)"><el-icon><StarFilled /></el-icon></button>
            </div>
          </div>
          <el-checkbox
            v-if="batchMode" class="g-check"
            :model-value="checked.has(it.obj_id)"
            @change="toggleChecked(it.obj_id)" @click.stop
          />
        </div>
      </template>
      <div v-if="!loading && visibleItems.length === 0" class="fav-empty">
        <el-icon class="empty-icon"><Star /></el-icon>
        <div class="empty-text">{{ searchKw ? '没有匹配的收藏' : `还没有收藏任何${typeLabel}` }}</div>
        <div class="empty-sub">
          {{ searchKw ? '换个关键词试试' : '在各页面的星标处点击即可收藏：题目详情、资料库、知识库、解题库' }}
        </div>
        <button v-if="!searchKw && nextNonEmpty" class="empty-cta" @click="switchType(nextNonEmpty)">
          查看已收藏的{{ typeLabelOf(nextNonEmpty) }}
        </button>
      </div>
    </div>

    <el-pagination
      v-if="!searchKw && total > pageSize" layout="prev, pager, next"
      :total="total" :page-size="pageSize" :current-page="page"
      @current-change="p => { page = p; loadList() }"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { favoritesApi } from '../api'

const router = useRouter()

const TABS = [
  { type: 'question', label: '题目', icon: 'EditPen' },
  { type: 'resource', label: '资料', icon: 'FolderOpened' },
  { type: 'knowledge', label: '知识点', icon: 'Reading' },
  { type: 'solve_item', label: '解题技巧', icon: 'Lightning' },
]

const currentType = ref('question')
const items = ref([])
const counts = ref({})
const total = ref(0)
const page = ref(1)
const pageSize = 50
const loading = ref(false)
const searchKw = ref('')
const sortBy = ref('time_desc')
const viewMode = ref('list')
const batchMode = ref(false)
const checked = ref(new Set())
const batchLoading = ref(false)

const typeLabel = computed(() => TABS.find(t => t.type === currentType.value)?.label || '')
const nextNonEmpty = computed(() => Object.entries(counts.value).find(([, v]) => v > 0)?.[0] || '')
const typeLabelOf = (t) => TABS.find(x => x.type === t)?.label || ''

// 客户端搜索 + 排序（收藏量级下体验最优）
const visibleItems = computed(() => {
  let arr = items.value
  const kw = searchKw.value.trim().toLowerCase()
  if (kw) {
    arr = arr.filter(it =>
      it.title?.toLowerCase().includes(kw) ||
      it.subtitle?.toLowerCase().includes(kw) ||
      it.note?.toLowerCase().includes(kw))
  }
  if (sortBy.value === 'time_asc') arr = [...arr].sort((a, b) => a.collect_time.localeCompare(b.collect_time))
  else if (sortBy.value === 'title') arr = [...arr].sort((a, b) => a.title.localeCompare(b.title, 'zh'))
  else arr = [...arr].sort((a, b) => b.collect_time.localeCompare(a.collect_time))
  return arr
})

const allChecked = computed(() =>
  visibleItems.value.length > 0 && visibleItems.value.every(it => checked.value.has(it.obj_id)))

function startBatch() {
  batchMode.value = true
  checked.value = new Set()
}

function toggleAll(v) {
  const next = new Set(checked.value)
  if (v) visibleItems.value.forEach(it => next.add(it.obj_id))
  else visibleItems.value.forEach(it => next.delete(it.obj_id))
  checked.value = next
}

function toggleChecked(id) {
  const next = new Set(checked.value)
  next.has(id) ? next.delete(id) : next.add(id)
  checked.value = next
}

async function batchRemove() {
  const ok = await ElMessageBox.confirm(`取消收藏选中的 ${checked.value.size} 项？`, '确认', { type: 'warning' }).catch(() => false)
  if (!ok) return
  batchLoading.value = true
  try {
    for (const id of checked.value) {
      await favoritesApi.toggle({ obj_type: currentType.value, obj_id: id })
    }
    ElMessage.success(`已取消 ${checked.value.size} 项收藏`)
    checked.value = new Set()
    loadList()
  } catch { ElMessage.error('批量操作失败') }
  finally { batchLoading.value = false }
}

function switchType(t) {
  currentType.value = t
  page.value = 1
  checked.value = new Set()
  loadList()
}

async function loadList() {
  loading.value = true
  try {
    const res = await favoritesApi.list({ obj_type: currentType.value, page: page.value, page_size: pageSize })
    items.value = res.data.items
    total.value = res.data.total
    counts.value = res.data.counts || {}
  } catch { ElMessage.error('收藏列表加载失败') }
  finally { loading.value = false }
}

async function editNote(it) {
  try {
    const { value } = await ElMessageBox.prompt('给这条收藏写个备注（为什么收藏/复习提示）：', '收藏备注', {
      inputValue: it.note || '', inputPlaceholder: '例如：错因是量级换算，考前必看',
      confirmButtonText: '保存', cancelButtonText: '取消',
    })
    await favoritesApi.updateNote({ obj_type: currentType.value, obj_id: it.obj_id, note: value || '' })
    it.note = value || ''
    ElMessage.success('备注已保存')
  } catch { /* 用户取消 */ }
}

async function removeFavorite(it) {
  const ok = await ElMessageBox.confirm('取消收藏该项？', '确认', { type: 'warning' }).catch(() => false)
  if (!ok) return
  try {
    await favoritesApi.toggle({ obj_type: currentType.value, obj_id: it.obj_id })
    ElMessage.success('已取消收藏')
    loadList()
  } catch { ElMessage.error('操作失败') }
}

function go(it) {
  if (it.route) router.push(it.route)
}

onMounted(loadList)
</script>

<style scoped>
.fav-page { max-width: 1000px; margin: 0 auto; }

/* 页头 */
.fav-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 18px; flex-wrap: wrap; }
.fav-hero h2 { margin: 0; display: flex; align-items: center; gap: 8px; color: var(--warning); }
.hero-sub { margin: 4px 0 0; font-size: 12.5px; color: var(--text-tertiary); }
.hero-stats { display: flex; gap: 10px; }
.stat-chip {
  display: flex; align-items: center; gap: 8px; padding: 8px 14px;
  border: 1px solid var(--border-base); border-radius: var(--radius-md);
  background: var(--bg-elevated); cursor: pointer; transition: all 0.15s; color: var(--text-secondary);
}
.stat-chip:hover { border-color: var(--primary); }
.stat-chip.active { background: var(--primary-bg); border-color: var(--primary); color: var(--primary); }
.stat-chip .el-icon { font-size: 18px; }
.sc-body { display: flex; flex-direction: column; line-height: 1.2; text-align: left; }
.sc-body b { font-size: 17px; font-weight: 800; }
.sc-body i { font-style: normal; font-size: 11px; opacity: 0.8; }

/* 工具栏 */
.fav-toolbar { display: flex; align-items: center; gap: 10px; padding: 10px 14px; margin-bottom: 14px; flex-wrap: wrap; }
.tb-search { width: 240px; }
.tb-sort { width: 130px; }
.tb-view { display: flex; gap: 2px; background: var(--bg-subtle); border-radius: var(--radius-sm); padding: 3px; }
.view-btn {
  border: none; background: none; padding: 5px 10px; border-radius: 4px;
  cursor: pointer; color: var(--text-tertiary); display: flex; align-items: center;
}
.view-btn.active { background: var(--bg-elevated); color: var(--primary); box-shadow: var(--shadow-sm); }

/* 列表视图 */
.fav-rows { display: flex; flex-direction: column; gap: 8px; min-height: 160px; }
.row {
  display: flex; align-items: center; gap: 12px; padding: 13px 16px;
  cursor: pointer; transition: box-shadow 0.15s, border-color 0.15s;
}
.row:hover { border-color: var(--primary); box-shadow: var(--shadow-sm); }
.row.selected { border-color: var(--danger); background: var(--danger-bg); }
.row-badge {
  flex-shrink: 0; font-size: 11px; font-weight: 600; padding: 3px 10px;
  border-radius: 999px; background: var(--primary-bg); color: var(--primary);
}
.row-main { flex: 1; min-width: 0; }
.row-title { font-size: 14px; font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-sub { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-note { font-size: 12.5px; color: var(--text-secondary); margin-top: 4px; display: flex; align-items: center; gap: 4px; }
.row-side { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }
.row-time { font-size: 11.5px; color: var(--text-tertiary); }
.row-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.15s; }
.row:hover .row-actions { opacity: 1; }
.act {
  border: none; background: none; cursor: pointer; color: var(--text-tertiary);
  padding: 6px; border-radius: var(--radius-sm); display: flex; font-size: 15px;
}
.act:hover { background: var(--bg-subtle); color: var(--primary); }
.act.danger:hover { background: var(--warning-bg); color: var(--warning); }

/* 网格视图 */
.fav-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; min-height: 160px; align-items: start; }
.gcell { position: relative; padding: 14px 16px; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
.gcell:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.gcell.selected { border-color: var(--danger); background: var(--danger-bg); }
.g-badge { display: inline-block; font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 999px; background: var(--primary-bg); color: var(--primary); margin-bottom: 8px; }
.g-title { font-size: 13.5px; font-weight: 600; color: var(--text-primary); line-height: 1.5; }
.g-sub { font-size: 11.5px; color: var(--text-tertiary); margin-top: 4px; }
.g-note { font-size: 12px; color: var(--text-secondary); margin-top: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.g-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; font-size: 11px; color: var(--text-tertiary); }
.g-check { position: absolute; top: 10px; right: 10px; }

/* 空态 */
.fav-empty { grid-column: 1 / -1; text-align: center; padding: 46px 20px; color: var(--text-tertiary); }
.empty-icon { font-size: 50px; }
.empty-text { font-size: 15px; font-weight: 600; color: var(--text-secondary); margin-top: 10px; }
.empty-sub { font-size: 12.5px; margin-top: 5px; }
.empty-cta {
  margin-top: 14px; border: none; background: var(--primary-bg); color: var(--primary);
  padding: 8px 18px; border-radius: 999px; cursor: pointer; font-size: 13px;
}
.empty-cta:hover { background: var(--primary); color: #fff; }
</style>
