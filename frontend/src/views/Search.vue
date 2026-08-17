<template>
  <div class="search-page">
    <PageHeader title="全局搜索" subtitle="跨「题目 · 行测知识库 · 行测解题库」联合检索" icon="Search" />

    <!-- 搜索框 -->
    <div class="search-bar">
      <el-icon class="sb-ico"><Search /></el-icon>
      <input
        ref="inputEl"
        v-model="keyword"
        class="sb-input"
        placeholder="输入关键词，跨库检索题目、知识点与解题模板…"
        @keyup.enter="runSearch"
      />
      <el-button v-if="keyword" text icon="Close" @click="clearSearch" />
      <el-button type="primary" @click="runSearch">搜索</el-button>
    </div>

    <!-- 加载 / 空态 -->
    <div v-if="loading" class="gk-grid gk-grid-3">
      <div v-for="i in 6" :key="i" class="gk-section"><div class="gk-section__body"><GkSkeleton :lines="3" /></div></div>
    </div>

    <EmptyState
      v-else-if="!hasSearched"
      icon="🔍"
      title="开始你的跨库检索"
      desc="支持题目题干、细分考点、知识卡片标题与内容、解题模板的联合搜索。例如搜「资料分析」「削弱」「图形推理」。"
    />

    <EmptyState
      v-else-if="hasSearched && result.total === 0"
      icon="🫥"
      title="没有匹配结果"
      desc="换个关键词试试，或检查是否存在错别字。当前库为空时请先录入题目。"
    />

    <!-- 结果 -->
    <div v-else class="result-wrap">
      <div class="result-meta">共找到 <b>{{ result.total }}</b> 条结果（题目 {{ result.questions.length }} · 知识 {{ result.knowledge.length }} · 解题 {{ result.solve.length }}）</div>

      <!-- 题目 -->
      <GkCard v-if="result.questions.length" title="📝 题目">
        <div class="res-list">
          <a v-for="r in result.questions" :key="'q'+r.id" class="res-item" :href="r.route" @click.prevent="go(r.route)">
            <span class="res-badge" :style="modStyle(r.module)">{{ r.module || '—' }}</span>
            <span class="res-main">
              <span class="res-title">{{ r.title }}</span>
              <span v-if="r.sub_point" class="res-sub">考点：{{ r.sub_point }}</span>
            </span>
            <el-icon class="res-go"><ArrowRight /></el-icon>
          </a>
        </div>
      </GkCard>

      <!-- 知识库 -->
      <GkCard v-if="result.knowledge.length" title="📚 行测知识库">
        <div class="res-list">
          <a v-for="r in result.knowledge" :key="'k'+r.id" class="res-item" :href="r.route" @click.prevent="go(r.route)">
            <span class="res-badge" :style="kgStyle(r.kg_type)">{{ r.kg_type }}</span>
            <span class="res-main">
              <span class="res-title">{{ r.title }}</span>
              <span v-if="r.snippet" class="res-sub">{{ r.snippet }}</span>
            </span>
            <el-icon class="res-go"><ArrowRight /></el-icon>
          </a>
        </div>
      </GkCard>

      <!-- 解题库 -->
      <GkCard v-if="result.solve.length" title="🛠 行测解题库">
        <div class="res-list">
          <a v-for="r in result.solve" :key="'s'+r.id" class="res-item" :href="r.route" @click.prevent="go(r.route)">
            <span class="res-badge" :style="solveStyle(r.solve_type)">{{ r.solve_type }}</span>
            <span class="res-main">
              <span class="res-title">{{ r.title }}</span>
              <span v-if="r.snippet" class="res-sub">{{ r.snippet }}</span>
            </span>
            <el-icon class="res-go"><ArrowRight /></el-icon>
          </a>
        </div>
      </GkCard>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchApi } from '../api'
import { modStyle, kgStyle, solveStyle } from '../utils/constants'

const route = useRoute()
const router = useRouter()

const keyword = ref('')
const loading = ref(false)
const hasSearched = ref(false)
const result = ref({ total: 0, questions: [], knowledge: [], solve: [] })

const inputEl = ref(null)

const initQ = route.query.q ? String(route.query.q) : ''
if (initQ) keyword.value = initQ

async function runSearch() {
  const q = keyword.value.trim()
  if (!q) return
  loading.value = true
  hasSearched.value = true
  try {
    const res = await searchApi.search(q)
    result.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function clearSearch() {
  keyword.value = ''
  hasSearched.value = false
  result.value = { total: 0, questions: [], knowledge: [], solve: [] }
  router.replace({ path: '/search' })
}

function go(routePath) {
  router.push(routePath)
}

onMounted(() => {
  if (initQ) runSearch()
  else inputEl.value?.focus()
})
</script>

<style scoped>
.search-page { max-width: 960px; margin: 0 auto; display: flex; flex-direction: column; gap: 18px; }

.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-base);
  border-radius: var(--radius-lg);
  padding: 8px 12px 8px 16px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.search-bar:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-bg); }
.sb-ico { font-size: 18px; color: var(--text-tertiary); flex-shrink: 0; }
.sb-input {
  flex: 1;
  border: none; outline: none; background: transparent;
  font-size: 15px; color: var(--text-primary); padding: 6px 0;
}

.result-meta { font-size: 13px; color: var(--text-secondary); }
.result-meta b { color: var(--primary); font-size: 15px; }

.result-wrap { display: flex; flex-direction: column; gap: 16px; }
.res-list { display: flex; flex-direction: column; gap: 8px; }
.res-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--bg-subtle);
  text-decoration: none;
  color: inherit;
  transition: all 0.15s;
  border: 1px solid transparent;
}
.res-item:hover { border-color: var(--primary); background: var(--primary-bg); transform: translateX(2px); }
.res-badge {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid;
}
.res-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.res-title {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.res-sub { font-size: 12px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.res-go { color: var(--text-tertiary); flex-shrink: 0; }
</style>
