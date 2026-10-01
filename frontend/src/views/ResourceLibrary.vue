<template>
  <div class="reslib-page">
    <div class="page-header">
      <h2><el-icon><FolderOpened /></el-icon> 行测资料库</h2>
      <span class="reslib-meta">共 {{ total }} 份资料 · 思维导图可预览与下载（来源：kuriv/civil-service-exam，MIT）</span>
    </div>

    <div class="reslib-layout">
      <!-- 左侧分类 -->
      <aside class="card reslib-side">
        <button class="cat-item" :class="{ active: !currentCategory }" @click="currentCategory = ''">
          <span>全部资料</span><span class="cat-count">{{ total }}</span>
        </button>
        <button
          v-for="c in categories" :key="c.name"
          class="cat-item" :class="{ active: currentCategory === c.name }"
          @click="currentCategory = c.name"
        >
          <span>{{ c.name }}</span><span class="cat-count">{{ c.count }}</span>
        </button>
        <div class="side-note">外部链接类资料（考公指南等）在「经验指南」分类</div>
      </aside>

      <!-- 右侧卡片墙 -->
      <section class="reslib-main">
        <div class="card reslib-toolbar">
          <el-input v-model="keyword" placeholder="搜索资料名称或路径" clearable style="width: 240px" @input="onSearchInput">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <span class="toolbar-meta">{{ list.length }} / {{ filteredTotal }} 份</span>
        </div>

        <div v-loading="loading" class="reslib-grid">
          <div v-for="r in list" :key="r.id" class="card res-card" @click="openDetail(r)">
            <div class="res-thumb">
              <img v-if="r.image_path" :src="imageUrl(r.image_path)" :alt="r.title" loading="lazy" />
              <div v-else class="res-thumb-empty"><el-icon><Link /></el-icon></div>
            </div>
            <div class="res-info">
              <div class="res-title">{{ r.title }}</div>
              <div class="res-path">{{ r.sub_path || r.category }}</div>
              <div class="res-tags">
                <span class="res-type">{{ r.resource_type === 'mindmap' ? '思维导图' : '外部链接' }}</span>
                <el-icon v-if="r.resource_type === 'link'" class="res-ext" @click.stop="openLink(r)"><Link /></el-icon>
              </div>
            </div>
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

    <!-- 详情预览 -->
    <el-dialog v-model="detailVisible" :title="detail?.title || '资料详情'" width="860px" top="4vh">
      <div class="detail-meta">
        <span class="res-type">{{ detail?.resource_type === 'mindmap' ? '思维导图' : '外部链接' }}</span>
        <span class="detail-path">{{ detail?.sub_path || detail?.category }}</span>
        <span class="detail-source">{{ detail?.source }}</span>
      </div>
      <p v-if="detail?.description" class="detail-desc">{{ detail.description }}</p>
      <div v-if="detail?.image_path" class="detail-img-wrap">
        <img :src="imageUrl(detail.image_path)" :alt="detail.title" />
      </div>
      <template #footer>
        <el-button v-if="detail?.source_url" @click="openLink(detail)">
          <el-icon><Link /></el-icon> 打开来源
        </el-button>
        <a v-if="detail?.file_path" :href="fileUrl(detail.file_path)" download>
          <el-button type="primary"><el-icon><Download /></el-icon> 下载导图原文件(.emmx)</el-button>
        </a>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { resourceApi } from '../api'

const categories = ref([])
const currentCategory = ref('')
const keyword = ref('')
const list = ref([])
const filteredTotal = ref(0)
const total = ref(0)
const page = ref(1)
const pageSize = 24
const loading = ref(false)
const detailVisible = ref(false)
const detail = ref(null)

const imageUrl = (p) => '/api/resources/image?path=' + encodeURIComponent(p)
const fileUrl = (p) => '/api/resources/file?path=' + encodeURIComponent(p)

async function loadCategories() {
  try {
    const res = await resourceApi.categories()
    categories.value = res.data.items
    total.value = res.data.total
  } catch { ElMessage.error('分类加载失败') }
}

async function loadList() {
  loading.value = true
  try {
    const res = await resourceApi.list({
      category: currentCategory.value || undefined,
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

watch(currentCategory, () => { page.value = 1; loadList() })

function openDetail(r) {
  detail.value = r
  detailVisible.value = true
}

function openLink(r) {
  if (r.source_url) window.open(r.source_url, '_blank')
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadList()])
})
</script>

<style scoped>
.reslib-page { max-width: 1280px; margin: 0 auto; }
.page-header { display: flex; align-items: baseline; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
.page-header h2 { margin: 0; }
.reslib-meta { font-size: 12px; color: var(--text-tertiary); }

.reslib-layout { display: flex; gap: 16px; align-items: flex-start; }
.reslib-side { width: 220px; flex-shrink: 0; padding: 10px; position: sticky; top: 16px; }
.cat-item {
  display: flex; justify-content: space-between; align-items: center; width: 100%;
  padding: 9px 12px; border: none; background: none; border-radius: var(--radius-md);
  font-size: 13.5px; color: var(--text-secondary); cursor: pointer; transition: all 0.15s;
}
.cat-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.cat-item.active { background: var(--primary-bg); color: var(--primary); font-weight: 600; }
.cat-count { font-size: 12px; color: var(--text-tertiary); }
.side-note { font-size: 11.5px; color: var(--text-tertiary); padding: 10px 12px 4px; line-height: 1.6; border-top: 1px dashed var(--border-light); margin-top: 6px; }

.reslib-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 12px; }
.reslib-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; }
.toolbar-meta { font-size: 12.5px; color: var(--text-tertiary); }

.reslib-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px;
  min-height: 200px;
}
.res-card { padding: 0; overflow: hidden; cursor: pointer; transition: transform 0.18s, box-shadow 0.18s; }
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
.res-tags { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
.res-type { font-size: 11px; padding: 1px 8px; border-radius: 999px; background: var(--primary-bg); color: var(--primary); }
.res-ext { color: var(--text-tertiary); cursor: pointer; }
.res-ext:hover { color: var(--primary); }

.empty-tip { grid-column: 1 / -1; text-align: center; color: var(--text-tertiary); padding: 40px 0; }

.detail-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.detail-path { font-size: 12.5px; color: var(--text-secondary); }
.detail-source { font-size: 12px; color: var(--text-tertiary); }
.detail-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.7; }
.detail-img-wrap { max-height: 62vh; overflow: auto; border: 1px solid var(--border-light); border-radius: var(--radius-md); background: var(--bg-subtle); }
.detail-img-wrap img { width: 100%; display: block; }
.reslib-page :deep(.el-dialog__footer) { text-align: right; }

@media (max-width: 900px) {
  .reslib-layout { flex-direction: column; }
  .reslib-side { width: 100%; position: static; display: flex; flex-wrap: wrap; gap: 4px; }
  .cat-item { width: auto; }
}
</style>
