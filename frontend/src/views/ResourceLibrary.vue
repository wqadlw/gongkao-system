<template>
  <div class="reslib-page">
    <div class="page-header">
      <h2><el-icon><FolderOpened /></el-icon> 行测资料库</h2>
      <span class="reslib-meta">共 {{ total }} 份资料 · 思维导图/考点精讲/材料档案/外部链接</span>
    </div>

    <!-- 类型筛选 -->
    <div class="type-chips">
      <button class="type-chip" :class="{ active: !currentType }" @click="currentType = ''; page = 1">全部</button>
      <button
        v-for="(cnt, type) in typeCounts" :key="type"
        class="type-chip" :class="{ active: currentType === type }"
        @click="currentType = type; page = 1"
      >{{ type }} <i>{{ cnt }}</i></button>
    </div>

    <div class="reslib-layout">
      <!-- 左侧层级树（模块优先） -->
      <aside class="card reslib-side">
        <button class="cat-item root" :class="{ active: !selectedPath && !onlyFavorite }" @click="selectNode(null)">
          <span>全部资料</span><span class="cat-count">{{ total }}</span>
        </button>
        <button class="cat-item root" :class="{ active: onlyFavorite }" @click="toggleFavoriteFilter">
          <span><el-icon><Star /></el-icon> 我的收藏</span><span class="cat-count">{{ favoriteCount }}</span>
        </button>
        <ResourceTree
          :nodes="tree"
          :expanded="expanded"
          :selected-path="selectedPath"
          @select="onTreeNodeSelect"
          @toggle="toggleExpand"
        />
      </aside>

      <!-- 右侧列表 -->
      <section class="reslib-main">
        <div class="card reslib-toolbar">
          <el-input v-model="keyword" placeholder="搜索资料名称或路径" clearable style="width: 260px" @input="onSearchInput">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <span class="toolbar-meta">{{ filteredTotal }} 份结果</span>
        </div>

        <div v-loading="loading" class="reslib-list">
          <!-- 思维导图：图片卡片 -->
          <div
            v-for="r in list" :key="r.id"
            class="card res-card" :class="{ 'is-text': r.resource_type !== 'mindmap' }"
            @click="openDetail(r)"
          >
            <span
              class="fav-star" :class="{ on: r.is_favorite }"
              title="收藏" @click.stop="toggleFavorite(r)"
            ><el-icon><StarFilled v-if="r.is_favorite" /><Star v-else /></el-icon></span>
            <template v-if="r.resource_type === 'mindmap'">
              <div class="res-thumb">
                <img v-if="r.image_path" :src="imageUrl(r.image_path)" :alt="r.title" loading="lazy" />
                <div v-else class="res-thumb-empty"><el-icon><Link /></el-icon></div>
              </div>
              <div class="res-info">
                <div class="res-title">{{ r.title }}</div>
                <div class="res-path">{{ r.sub_path || r.category }}</div>
              </div>
            </template>
            <template v-else>
              <div class="text-row">
                <div class="text-head">
                  <span class="res-type">{{ r.resource_type }}</span>
                  <span class="res-title">{{ r.title }}</span>
                </div>
                <div class="text-excerpt">{{ r.excerpt }}…</div>
                <div class="text-meta">
                  <span class="res-path">{{ r.sub_path }}</span>
                  <span v-if="r.qid_count" class="qid-badge">关联 {{ r.qid_count }} 题</span>
                </div>
              </div>
            </template>
          </div>
          <div v-if="!loading && list.length === 0" class="empty-tip">无匹配资料</div>
        </div>

        <el-pagination
          v-if="filteredTotal > pageSize" layout="prev, pager, next"
          :total="filteredTotal" :page-size="pageSize" :current-page="page"
          @current-change="p => { page = p; loadList() }"
        />
      </section>
    </div>

    <!-- 详情 -->
    <el-dialog
      v-model="detailVisible" :title="detail?.title || '资料详情'"
      :width="dialogFullscreen ? '100%' : '860px'" :fullscreen="dialogFullscreen" top="4vh"
    >
      <template #header>
        <div class="dlg-header">
          <span class="dlg-title">{{ detail?.title }}</span>
          <button class="fav-star big" :class="{ on: detail?.is_favorite }" title="收藏" @click="toggleFavorite(detail, false)">
            <el-icon><StarFilled v-if="detail?.is_favorite" /><Star v-else /></el-icon>
          </button>
          <el-button size="small" text @click="dialogFullscreen = !dialogFullscreen">
            <el-icon><FullScreen /></el-icon> {{ dialogFullscreen ? '退出全屏' : '全屏阅读' }}
          </el-button>
        </div>
      </template>
      <template v-if="detail">
        <div class="detail-meta">
          <span class="res-type">{{ detail.resource_type }}</span>
          <span class="detail-path">{{ detail.sub_path || detail.category }}</span>
          <span class="detail-source">{{ detail.source }}</span>
        </div>
        <p v-if="detail.description" class="detail-desc">{{ detail.description }}</p>

        <!-- 思维导图：大图 -->
        <div v-if="detail.resource_type === 'mindmap' && detail.image_path" class="detail-img-wrap">
          <img :src="imageUrl(detail.image_path)" :alt="detail.title" />
        </div>

        <!-- 文本类：markdown 正文 -->
        <div v-if="detail.content" class="detail-content md-body" :class="{ fullscreen: dialogFullscreen }" v-html="md(detail.content)"></div>

        <!-- 关联题目 -->
        <div v-if="related.length" class="related">
          <div class="related-title">关联真题（已入库 {{ related.length }} 道）</div>
          <div class="related-chips">
            <button
              v-for="q in related" :key="q.question_id"
              class="related-chip" @click="$router.push('/question/' + q.question_id)"
            >
              {{ q.bank_qid }} <b>{{ q.answer }}</b>
            </button>
          </div>
        </div>
      </template>
      <template #footer>
        <el-button @click="dialogFullscreen = !dialogFullscreen">
          <el-icon><FullScreen /></el-icon> {{ dialogFullscreen ? '退出全屏' : '全屏阅读' }}
        </el-button>
        <el-button v-if="detail?.source_url" @click="openLink(detail)">
          <el-icon><Link /></el-icon> 打开来源
        </el-button>
        <a v-if="detail?.file_path" :href="fileUrl(detail.file_path)" download>
          <el-button type="primary"><el-icon><Download /></el-icon> 下载原文件</el-button>
        </a>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { resourceApi } from '../api'
import { renderMarkdown } from '../utils/md'
import ResourceTree from '../components/ResourceTree.vue'

const md = renderMarkdown

const categories = ref([])
const typeCounts = ref({})
const tree = ref([])
const expanded = ref({})
const selectedPath = ref('')
const currentFilters = ref({})
const currentType = ref('')
const onlyFavorite = ref(false)
const favoriteCount = ref(0)
const keyword = ref('')
const list = ref([])
const filteredTotal = ref(0)
const total = ref(0)
const page = ref(1)
const pageSize = 24
const loading = ref(false)
const detailVisible = ref(false)
const detail = ref(null)
const related = ref([])
const dialogFullscreen = ref(false)

const imageUrl = (p) => '/api/resources/image?path=' + encodeURIComponent(p)
const fileUrl = (p) => '/api/resources/file?path=' + encodeURIComponent(p)

// 树节点选择：节点自带过滤参数（module_prefix/resource_type/category/sub_prefix）
function onTreeNodeSelect(node, path) {
  currentFilters.value = node.filter || {}
  selectedPath.value = path
  onlyFavorite.value = false
  page.value = 1
  // 自动展开祖先由 keyPrefix 机制处理；展开当前节点
  expanded.value[path] = true
  loadList()
}

function toggleFavoriteFilter() {
  onlyFavorite.value = !onlyFavorite.value
  if (onlyFavorite.value) {
    currentFilters.value = {}
    selectedPath.value = ''
  }
  page.value = 1
  loadList()
}

function toggleExpand(key) {
  expanded.value[key] = !expanded.value[key]
}

async function loadFavoriteCount() {
  try {
    const res = await resourceApi.list({ favorite: 1, page_size: 1 })
    favoriteCount.value = res.data.total
  } catch { /* 忽略 */ }
}

async function loadCategories() {
  try {
    const res = await resourceApi.categories()
    typeCounts.value = res.data.type_counts || {}
  } catch { /* 类型计数加载失败不阻塞 */ }
}

async function loadTree() {
  try {
    const res = await resourceApi.tree()
    tree.value = res.data.items
    total.value = res.data.total
  } catch { ElMessage.error('分类树加载失败') }
}

async function loadList() {
  loading.value = true
  try {
    const f = currentFilters.value || {}
    const res = await resourceApi.list({
      category: f.category || undefined,
      resource_type: currentType.value || f.resource_type || undefined,
      sub_prefix: f.sub_prefix || undefined,
      module_prefix: f.module_prefix || undefined,
      favorite: onlyFavorite.value ? 1 : undefined,
      keyword: keyword.value || undefined,
      page: page.value, page_size: pageSize,
    })
    list.value = res.data.items
    filteredTotal.value = res.data.total
  } catch { ElMessage.error('资料列表加载失败') }
  finally { loading.value = false }
}

let searchTimer = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadList() }, 300)
}

watch(currentType, () => { page.value = 1; loadList() })

async function toggleFavorite(r, stop = true) {
  try {
    const res = await resourceApi.toggleFavorite(r.id)
    r.is_favorite = res.data.is_favorite
    if (detail.value?.id === r.id) detail.value.is_favorite = res.data.is_favorite
    loadFavoriteCount()
    if (onlyFavorite.value && stop) loadList()
  } catch { ElMessage.error('收藏操作失败') }
}

async function openDetail(r) {
  try {
    const res = await resourceApi.detail(r.id)
    detail.value = res.data
    detailVisible.value = true
    dialogFullscreen.value = false
    related.value = []
    if (r.qid_count) {
      const qres = await resourceApi.relatedQuestions(r.id)
      related.value = qres.data.items
    }
  } catch { ElMessage.error('详情加载失败') }
}

function openLink(r) {
  if (r.source_url) window.open(r.source_url, '_blank')
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadTree(), loadList(), loadFavoriteCount()])
})
</script>

<style scoped>
.reslib-page { max-width: 1280px; margin: 0 auto; }
.page-header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 12px; flex-wrap: wrap; }
.page-header h2 { margin: 0; }
.reslib-meta { font-size: 12px; color: var(--text-tertiary); }

.type-chips { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.type-chip {
  padding: 5px 14px; border: 1px solid var(--border-base); border-radius: 999px;
  background: var(--bg-elevated); font-size: 13px; color: var(--text-secondary);
  cursor: pointer; transition: all 0.15s;
}
.type-chip i { font-style: normal; font-size: 11px; color: var(--text-tertiary); margin-left: 3px; }
.type-chip.active { background: var(--primary); border-color: var(--primary); color: #fff; }
.type-chip.active i { color: rgba(255,255,255,0.8); }

.reslib-layout { display: flex; gap: 16px; align-items: flex-start; }
.reslib-side { width: 220px; flex-shrink: 0; padding: 10px; position: sticky; top: 16px; }
.cat-item {
  display: flex; justify-content: space-between; align-items: center; width: 100%;
  padding: 9px 12px; border: none; background: none; border-radius: var(--radius-md);
  font-size: 13.5px; color: var(--text-secondary); cursor: pointer; transition: all 0.15s;
}
.cat-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.cat-item.root { font-weight: 600; color: var(--text-primary); }
.cat-caret { display: inline-block; width: 14px; color: var(--text-tertiary); transition: transform 0.15s; font-size: 11px; }
.cat-caret.open { transform: rotate(90deg); }
.cat-name { flex: 1; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-lv1 .cat-item { padding-left: 26px; font-size: 12.5px; }
.tree-lv1 .cat-item.lv2 { padding-left: 42px; font-size: 12px; }

.cat-item.active { background: var(--primary-bg); color: var(--primary); font-weight: 600; }
.cat-count { font-size: 12px; color: var(--text-tertiary); }
.sub-facets { border-top: 1px dashed var(--border-light); margin-top: 8px; padding-top: 8px; }
.facet-title { font-size: 11px; color: var(--text-tertiary); font-weight: 700; padding: 4px 12px; letter-spacing: 1px; }
.cat-item.sub { padding: 7px 12px; font-size: 12.5px; }

.reslib-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.reslib-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; }
.toolbar-meta { font-size: 12.5px; color: var(--text-tertiary); }

.reslib-list {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px;
  min-height: 200px; align-items: start;
}
.res-card { position: relative; padding: 0; overflow: hidden; cursor: pointer; transition: transform 0.18s, box-shadow 0.18s; }
.res-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
.res-thumb {
  height: 170px; background: var(--bg-subtle); display: flex; align-items: center;
  justify-content: center; overflow: hidden;
}
.res-thumb img { width: 100%; height: 100%; object-fit: cover; object-position: top center; transition: transform 0.25s; }
.res-card:hover .res-thumb img { transform: scale(1.04); }
.res-thumb-empty { font-size: 40px; color: var(--text-tertiary); }
.res-info { padding: 10px 12px 12px; }
.res-title { font-size: 14px; font-weight: 600; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.res-path { font-size: 12px; color: var(--text-tertiary); margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 文本类卡片 */
.res-card.is-text { padding: 14px 16px; }
.text-row { display: flex; flex-direction: column; gap: 7px; }
.text-head { display: flex; align-items: center; gap: 8px; min-width: 0; }
.text-head .res-title { flex: 1; }
.res-type { flex-shrink: 0; font-size: 11px; padding: 1px 8px; border-radius: 999px; background: var(--primary-bg); color: var(--primary); }
.text-excerpt {
  font-size: 12.5px; color: var(--text-secondary); line-height: 1.6;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.text-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.qid-badge { flex-shrink: 0; font-size: 11px; padding: 1px 8px; border-radius: 999px; background: var(--success-bg); color: var(--success); }

.empty-tip { grid-column: 1 / -1; text-align: center; color: var(--text-tertiary); padding: 40px 0; }

.detail-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.detail-path { font-size: 12.5px; color: var(--text-secondary); }
.detail-source { font-size: 12px; color: var(--text-tertiary); }
.detail-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.7; }
.detail-img-wrap { max-height: 62vh; overflow: auto; border: 1px solid var(--border-light); border-radius: var(--radius-md); background: var(--bg-subtle); }
.detail-img-wrap img { width: 100%; display: block; }
.detail-content { max-height: 62vh; overflow: auto; font-size: 13.5px; }
.fav-star {
  position: absolute; top: 8px; right: 8px; z-index: 2;
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.9); color: var(--text-tertiary);
  cursor: pointer; transition: all 0.15s; border: 1px solid var(--border-light);
}
.fav-star:hover { color: var(--warning); transform: scale(1.1); }
.fav-star.on { color: var(--warning); }
.fav-star.big { position: static; width: 30px; height: 30px; }
.dlg-header { display: flex; align-items: center; gap: 12px; padding-right: 24px; }
.dlg-title { font-size: 16px; font-weight: 700; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.detail-content.fullscreen { max-height: calc(100vh - 200px); }
.detail-content { max-height: 62vh; overflow: auto; }

.related { margin-top: 14px; }
.related-title { font-size: 13px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.related-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.related-chip {
  border: 1px solid var(--border-base); background: var(--bg-elevated); color: var(--text-secondary);
  border-radius: 999px; padding: 3px 12px; font-size: 12px; cursor: pointer; transition: all 0.15s;
}
.related-chip b { color: var(--success); margin-left: 4px; }
.related-chip:hover { border-color: var(--primary); color: var(--primary); }

@media (max-width: 900px) {
  .reslib-layout { flex-direction: column; }
  .reslib-side { width: 100%; position: static; }
}
</style>
