<template>
  <div class="input-page">
    <div class="page-header">
      <div>
        <h2>✏️ 题目录入</h2>
        <p class="sub">把外部 AI 的解析粘贴回来，系统自动判定模块与考点并归类，你只需确认</p>
      </div>
      <span class="badge">智能归类 · 模块由 AI 自动判定</span>
    </div>

    <!-- 步骤指引 -->
    <div class="steps">
      <div :class="['step', { active: activeStep >= 1, done: activeStep > 1 }]">
        <div class="step-num">1</div>
        <div class="step-text">复制通用提示词</div>
      </div>
      <div class="step-arrow">→</div>
      <div :class="['step', { active: activeStep >= 2, done: activeStep > 2 }]">
        <div class="step-num">2</div>
        <div class="step-text">粘贴 AI 返回结果</div>
      </div>
      <div class="step-arrow">→</div>
      <div :class="['step', { active: activeStep >= 3 }]">
        <div class="step-num">3</div>
        <div class="step-text">核对并入库</div>
      </div>
    </div>

    <div class="main-grid">
      <!-- 左侧：通用提示词 -->
      <div class="left-panel">
        <div class="card">
          <div class="card-header">
            <h3>① 按模块复制专属提示词</h3>
            <span v-if="matchedPrompt" class="mod-badge" :style="modStyle(effectiveModule)">{{ effectiveModule || '通用' }}</span>
            <button class="btn-primary small" @click="copyPrompt" :disabled="!matchedPrompt">📋 复制</button>
          </div>
          <div class="card-body">
            <!-- 先选模块：决定用哪套提示词 -->
            <div class="mod-select-row">
              <label>先选模块（决定 AI 用哪套提示词）</label>
              <el-select v-model="pickedModule" placeholder="不指定则 AI 自动判定" clearable size="default">
                <el-option v-for="m in MODULES" :key="m" :value="m">
                  <span class="opt-dot" :style="{ background: modColor(m) }"></span>{{ m }}
                </el-option>
              </el-select>
            </div>
            <textarea v-model="questionText" class="q-input" rows="4"
              placeholder="可在此粘贴题目文本，复制提示词时会自动代入（也可留空，复制后自行替换 {question_content}）"></textarea>
            <div v-if="matchedPrompt" class="prompt-name">{{ matchedPrompt.name }}</div>
            <pre v-if="matchedPrompt" class="prompt-content">{{ matchedPrompt.content }}</pre>
            <div v-else class="tree-loading">提示词加载中…</div>
            <div class="prompt-tip">
              💡 复制后粘贴给外部 AI。选了模块会用<strong>该模块专属提示词</strong>（分析重点与例题更贴合）；
              不选则 AI 自动判定模块并套用通用模板。AI 按一~六节作答，公式用 LaTeX。
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：粘贴 + 预览 -->
      <div class="right-panel">
        <div class="card">
          <div class="card-header">
            <h3>② 粘贴 AI 返回结果</h3>
            <div>
              <button class="btn-default small" @click="aiContent = ''">清空</button>
              <button class="btn-primary" @click="parseAI" :disabled="!aiContent">🔍 解析</button>
            </div>
          </div>
          <div class="card-body">
            <textarea v-model="aiContent" class="ai-input"
              placeholder="将外部 AI 返回的完整内容粘贴到这里（顶部『题目』+ 一~六节结构化 Markdown）…

系统会自动抽取题目、判定模块与考点路径完成归类，公式（LaTeX）原样保留，无需手动填写任何字段。"
              rows="18"></textarea>

            <div v-if="parseValidation" :class="['parse-result', parseValidation.ok ? 'success' : 'warning']">
              <span>{{ parseValidation.ok ? '✅' : '⚠️' }} {{ parseValidation.message }}</span>
            </div>
          </div>
        </div>

        <!-- 解析完成：跳转「核对并入库」页（/deposit）核对题面 + 勾选知识卡片 -->
        <div class="parsed-ok" v-if="parsedPreview">
          ✅ 解析完成，正在打开<router-link to="/deposit">「核对并入库」页面</router-link>…（如未自动跳转请点此）
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { promptApi, questionApi } from '../api'
import { useAppStore } from '../stores/app'
import { ElMessage } from 'element-plus'
import { renderMarkdown } from '../utils/md'
import { MODULES, modStyle, modColor } from '../utils/constants'

const md = renderMarkdown

const router = useRouter()
const store = useAppStore()

const activeStep = ref(1)
const prompts = ref([])

// 当前生效模块：解析结果优先，其次手动校正，其次用户预选
const pickedModule = ref('')
const questionText = ref('')
const effectiveModule = computed(() =>
  (parsedPreview.value && parsedPreview.value.level1) ||
  pickedModule.value || ''
)
const matchedPrompt = computed(() => {
  const list = prompts.value
  return list.find(p => p.type === effectiveModule.value) ||
    list.find(p => p.type === '通用') ||
    list[0] || null
})

// 录入预览：AI 判定徽标样式

const aiContent = ref('')
const parsedPreview = ref(null)
const parseValidation = ref(null)
// 卡片缩略信息预览：把存储的「｜」分隔字符串拆成标签数组
const cardPreviewTags = computed(() =>
  (parsedPreview.value?.card_tags || '').split('｜').map(s => s.trim()).filter(Boolean)
)

async function loadData() {
  const [promptRes] = await Promise.all([
    promptApi.getList(),
  ])
  prompts.value = promptRes.data || []
  if (!store.categoryTree.length) await store.loadCategories()
}

async function copyPrompt() {
  if (!matchedPrompt.value) return
  try {
    const res = await promptApi.build(matchedPrompt.value.id, {
      question_content: questionText.value || '',
      extra_info: '',
    })
    await navigator.clipboard.writeText(res.data.text)
    ElMessage.success('已复制「' + (effectiveModule.value || '通用') + '」专属提示词' +
      (questionText.value ? '（已代入题目）' : '') + '，去粘贴给 AI 吧')
    activeStep.value = 2
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

async function parseAI() {
  if (!aiContent.value) { ElMessage.warning('请先粘贴 AI 返回内容'); return }
  try {
    const res = await questionApi.parseOnly({ ai_content: aiContent.value })
    parsedPreview.value = res.data.parsed
    if (res.data.parsed && res.data.parsed.level1) pickedModule.value = res.data.parsed.level1
    const v = res.data.validation
    parseValidation.value = {
      ok: v.is_valid && !(v.warnings && v.warnings.length),
      message: v.message + (v.warnings && v.warnings.length ? '（' + v.warnings.join('；') + '）' : ''),
    }
    activeStep.value = 3
    // 暂存草稿并跳转「核对并入库」页：在那里核对题面 + 勾选知识卡片
    localStorage.setItem('gk_pending_deposit', JSON.stringify({
      ai_content: aiContent.value,
      parsed: res.data.parsed,
    }))
    ElMessage.success('解析完成，正在打开核对页…')
    router.push('/deposit')
  } catch (e) {
    ElMessage.error('解析失败：' + (e.response?.data?.detail || e.message))
  }
}

// 返回录入页时恢复未完成的解析草稿（用户在「核对并入库」页点「返回修改」会回到这里）
onMounted(async () => {
  await loadData()
  const raw = localStorage.getItem('gk_pending_deposit')
  if (raw) {
    try {
      const d = JSON.parse(raw)
      aiContent.value = d.ai_content || ''
      parsedPreview.value = d.parsed || null
      if (d.parsed && d.parsed.level1) pickedModule.value = d.parsed.level1
    } catch (e) { /* 草稿损坏则忽略 */ }
  }
})
</script>

<style scoped>
.input-page { max-width: 1400px; margin: 0 auto; }
.page-header {
  display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;
}
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; }
.page-header .sub { margin: 4px 0 0; font-size: 13px; color: var(--text-tertiary); }
.badge {
  background: var(--success-bg); color: var(--success);
  padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; white-space: nowrap;
}

.steps {
  display: flex; align-items: center; justify-content: center; gap: 12px;
  margin-bottom: 24px; padding: 16px; background: var(--bg-elevated);
  border-radius: var(--radius-lg); border: 1px solid var(--border-light);
}
.step { display: flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: var(--radius-md); transition: all 0.2s; }
.step.active { background: var(--primary-bg); }
.step.done { background: var(--success-bg); }
.step-num {
  width: 24px; height: 24px; border-radius: 50%; background: var(--bg-subtle);
  color: var(--text-secondary); display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
}
.step.active .step-num { background: var(--primary); color: white; }
.step.done .step-num { background: var(--success); color: white; }
.step-text { font-size: 13px; color: var(--text-secondary); }
.step.active .step-text { color: var(--primary); font-weight: 500; }
.step-arrow { color: var(--text-tertiary); font-size: 14px; }

.main-grid { display: grid; grid-template-columns: 460px 1fr; gap: 16px; align-items: start; }
@media (max-width: 1100px) { .main-grid { grid-template-columns: 1fr; } }

.card {
  background: var(--bg-elevated); border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm); border: 1px solid var(--border-light);
  overflow: hidden; margin-bottom: 16px;
}
.card-header {
  padding: 12px 16px; border-bottom: 1px solid var(--border-light);
  display: flex; justify-content: space-between; align-items: center;
}
.card-header h3 { margin: 0; font-size: 14px; font-weight: 600; }
.card-body { padding: 16px; }

.prompt-name { font-size: 14px; font-weight: 600; color: var(--primary); margin-bottom: 8px; }
.prompt-content {
  background: var(--bg-base); padding: 12px; border-radius: var(--radius-md);
  font-size: 11px; line-height: 1.6; max-height: 360px; overflow-y: auto;
  white-space: pre-wrap; word-break: break-word; border: 1px solid var(--border-light);
  font-family: 'Consolas', 'Monaco', monospace;
}
.prompt-tip {
  margin-top: 8px; font-size: 12px; color: var(--text-tertiary);
  padding: 10px 12px; background: var(--warning-bg); border-radius: var(--radius-sm); line-height: 1.6;
}
.prompt-tip strong { color: var(--text-secondary); }

.mod-badge {
  font-size: 12px; font-weight: 700; padding: 2px 10px; border-radius: 999px;
  border: 1px solid transparent; margin-right: auto;
}
.mod-select-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.mod-select-row label { font-size: 12.5px; color: var(--text-secondary); white-space: nowrap; }
.mod-select-row :deep(.el-select) { width: 240px; }
.opt-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
.q-input {
  width: 100%; padding: 10px; border: 1px solid var(--border-base);
  border-radius: var(--radius-md); font-size: 13px; background: var(--bg-base);
  color: var(--text-primary); resize: vertical; margin-bottom: 10px;
}
.q-input:focus { outline: none; border-color: var(--primary); }

.tree-loading { color: var(--text-tertiary); font-size: 13px; padding: 12px; }

.ai-input {
  width: 100%; padding: 12px; border: 1px solid var(--border-base);
  border-radius: var(--radius-md); font-size: 13px; background: var(--bg-base);
  color: var(--text-primary); font-family: 'Consolas', 'Monaco', monospace; resize: vertical;
}
.ai-input:focus { outline: none; border-color: var(--primary); }

.parse-result { margin-top: 12px; padding: 8px 12px; border-radius: var(--radius-md); font-size: 13px; }
.parse-result.success { background: var(--success-bg); color: var(--success); }
.parse-result.warning { background: var(--warning-bg); color: var(--warning); }

.auto-mod {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 10px 12px; border-radius: var(--radius-md);
  background: var(--bg-subtle); margin-bottom: 12px;
}
.am-label { font-size: 12px; color: var(--text-secondary); font-weight: 600; }
.am-chip {
  font-size: 13px; font-weight: 700; padding: 3px 14px; border-radius: 999px;
  border: 1px solid transparent;
}
.am-hint { font-size: 11px; color: var(--danger); }

.cat-path-box {
  background: linear-gradient(135deg, var(--primary-bg) 0%, var(--bg-subtle) 100%);
  border: 1px solid var(--primary-light); border-radius: var(--radius-md);
  padding: 12px 14px; margin-bottom: 12px;
}
.cp-label { font-size: 12px; color: var(--text-secondary); font-weight: 600; margin-bottom: 6px; }
.cp-path { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.cp-seg {
  font-size: 14px; font-weight: 600; color: var(--primary);
  background: var(--bg-elevated); padding: 2px 10px; border-radius: 8px;
}
.cp-sep { color: var(--text-tertiary); font-weight: 700; }
.cp-empty { font-size: 13px; color: var(--danger); font-weight: 500; }
.cp-source { margin-top: 8px; font-size: 11px; }
.cp-source.auto { color: var(--text-tertiary); }
.cp-source.manual { color: var(--primary); font-weight: 600; }

.link-btn {
  background: none; border: none; color: var(--primary); cursor: pointer;
  font-size: 13px; padding: 4px 0; margin-bottom: 8px;
}
.tree-picker {
  max-height: 280px; overflow-y: auto; border: 1px solid var(--border-light);
  border-radius: var(--radius-md); padding: 6px; background: var(--bg-base); margin-bottom: 12px;
}

.parsed-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0; }
.parsed-item { background: var(--bg-subtle); padding: 10px 12px; border-radius: var(--radius-md); }
.parsed-label { font-size: 11px; color: var(--text-tertiary); margin-bottom: 4px; }
.parsed-value { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.parsed-value.answer { font-size: 18px; font-weight: 700; color: var(--success); }
.parsed-section { margin-bottom: 12px; }
.parsed-label.s { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; font-weight: 500; }
.parsed-content {
  font-size: 13px; color: var(--text-primary); line-height: 1.7; padding: 10px 14px;
  background: var(--bg-subtle); border-radius: var(--radius-md);
}

.kg-suggest-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
.kg-suggest {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: var(--bg-subtle); border-radius: var(--radius-md); cursor: pointer;
}
.kg-type {
  font-size: 11px; font-weight: 600; padding: 1px 8px; border-radius: 999px;
  border: 1px solid transparent; flex-shrink: 0;
}
.kg-title { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.kg-save { margin-top: 2px; }
.kg-nodeposit { font-size: 12.5px; color: var(--text-tertiary); line-height: 1.6; padding: 10px 12px; background: var(--bg-subtle); border-radius: var(--radius-md); }

/* 候选沉淀条目（用户勾选决定入库） */
.kg-deposit-group { margin-bottom: 12px; }
.kg-deposit-head { display: flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.kg-deposit-head .el-icon { font-size: 14px; color: var(--primary); }
.kg-suggest input[type="checkbox"] { width: 16px; height: 16px; accent-color: var(--primary); cursor: pointer; flex-shrink: 0; }
.kg-suggest.off { opacity: 0.5; }
.kg-suggest.off .kg-title { text-decoration: line-through; }
.kg-cardtitle { font-size: 11px; color: var(--text-tertiary); margin-left: auto; flex-shrink: 0; }

.deposit-judge .judge-row { display: flex; gap: 10px; flex-wrap: wrap; }
.judge-chip { font-size: 12.5px; font-weight: 500; padding: 5px 12px; border-radius: 999px; border: 1px solid var(--border-base); }
.judge-chip.need { color: #047857; background: #ecfdf5; border-color: #a7f3d0; }
.judge-chip.no-need { color: #b45309; background: #fffbeb; border-color: #fde68a; }
.judge-chip.unknown { color: var(--text-tertiary); background: var(--bg-subtle); }
.judge-chip.method { color: #4338ca; background: #eef2ff; border-color: #c7d2fe; font-weight: 600; }
.judge-chip.method.memory { color: #7c3aed; background: #f5f3ff; border-color: #ddd6fe; }
.judge-chip.method.solve { color: #0369a1; background: #f0f9ff; border-color: #bae6fd; }
.judge-chip.method.both { color: #b45309; background: #fffbeb; border-color: #fde68a; }
.judge-hint { font-size: 11.5px; color: var(--text-tertiary); margin-top: 6px; }

/* 解析完成 → 跳转「核对并入库」页 */
.parsed-ok { margin-top: 12px; padding: 12px 14px; border-radius: var(--radius-md); background: var(--success-bg); border: 1px solid var(--success); font-size: 13px; color: var(--success); }
.parsed-ok a { color: var(--primary); font-weight: 600; }

/* 卡片缩略信息预览（模拟列表卡片外观） */
.card-preview .cp-card {
  border: 1px solid var(--border-base); border-radius: var(--radius-md);
  padding: 12px 14px; background: var(--bg-elevated); border-left: 3px solid var(--primary);
}
.cpc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.cpc-mod { font-size: 11px; font-weight: 600; padding: 2px 9px; border-radius: 999px; }
.cpc-type { font-size: 12px; color: var(--text-secondary); }
.cpc-type::before { content: '·'; margin-right: 6px; color: var(--text-tertiary); }
.cpc-ans { margin-left: auto; font-size: 12.5px; font-weight: 600; color: var(--success); background: var(--success-bg); padding: 1px 10px; border-radius: 6px; }
.cpc-title { font-size: 15px; font-weight: 600; line-height: 1.45; color: var(--text-primary); margin-bottom: 6px; }
.cpc-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.cpc-tag { font-size: 11.5px; padding: 2px 9px; border-radius: 999px; color: var(--info); background: var(--info-bg); }
.cpc-sum { font-size: 12.5px; line-height: 1.6; color: var(--text-tertiary); }

.btn-primary {
  background: var(--primary); color: white; border: none; padding: 8px 16px;
  border-radius: var(--radius-md); cursor: pointer; font-size: 13px; font-weight: 500;
}
.btn-primary:hover { background: var(--primary-dark); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary.small { padding: 4px 12px; font-size: 12px; }
.btn-default {
  background: var(--bg-subtle); color: var(--text-secondary); border: none; padding: 8px 16px;
  border-radius: var(--radius-md); cursor: pointer; font-size: 13px;
}
.btn-default.small { padding: 4px 12px; font-size: 12px; }

.checkbox-label {
  display: inline-flex; align-items: center; gap: 4px; font-size: 13px;
  cursor: pointer; margin-right: 12px;
}
.checkbox-label input { width: 16px; height: 16px; }
</style>
