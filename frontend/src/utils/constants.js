// 行测模块单一事实源：颜色 / 图标 / 顺序 / 各模块专属功能
// 后端（提示词种子、笔记章节）与前端（录入匹配、详情功能、列表分组）都从这里取，
// 保证"题型"作为唯一驱动源，提示词、解析、存储、展示、笔记、功能全链路耦合一致。

export const MODULES = [
  '政治理论',
  '常识判断',
  '言语理解与表达',
  '数量关系',
  '判断推理',
  '资料分析',
]

export const MOD_ORDER = MODULES

// 模块取向（与后端 data_init.MODULE_PROMPT_CFG 单一事实源保持一致）：
// memory = 记忆积累型（政治理论/常识判断/言语）；solve = 解题思路型（数量/判断/资料）
export const MOD_ORIENTATION = {
  '政治理论': 'memory',
  '常识判断': 'memory',
  '言语理解与表达': 'memory',
  '数量关系': 'solve',
  '判断推理': 'solve',
  '资料分析': 'solve',
}
export const ORIENTATION_LABEL = {
  memory: '记忆积累型',
  solve: '解题思路型',
}
export function modOrientation(m) {
  return MOD_ORIENTATION[m] || 'solve'
}

export const MOD_COLORS = {
  '政治理论': '#ef4444',
  '常识判断': '#f59e0b',
  '言语理解与表达': '#4f46e5',
  '数量关系': '#10b981',
  '判断推理': '#06b6d4',
  '资料分析': '#db2777',
}

// Element Plus 图标名（字符串，配合 <component :is> 全局注册）
export const MOD_ICONS = {
  '政治理论': 'Medal',
  '常识判断': 'Sunny',
  '言语理解与表达': 'ChatDotRound',
  '数量关系': 'DataLine',
  '判断推理': 'Share',
  '资料分析': 'TrendCharts',
}

// 各模块专属功能（前端「题型功能」面板；离线，从已解析字段生成聚焦卡）
// fields 指向 Question 模型的结构化字段：sub_point / exam_intent / break_logic /
// quick_solve / identify_signal / normal_solve / step_detail / option_feature / trap_*
export const MOD_FUNCTIONS = {
  '言语理解与表达': [
    { key: 'keyword', label: '关键词提炼', icon: 'Key', fields: ['exam_intent', 'option_feature'], desc: '从考察意图与选项特征提炼文段关键词' },
    { key: 'structure', label: '文段结构', icon: 'Operation', fields: ['break_logic'], desc: '还原文段结构与中心句位置' },
    { key: 'word', label: '词语辨析', icon: 'Switch', fields: ['sub_point', 'exam_intent'], desc: '近义词语义侧重与搭配辨析' },
  ],
  '数量关系': [
    { key: 'quick', label: '秒杀技巧卡', icon: 'Lightning', fields: ['quick_solve', 'identify_signal'], desc: '本题可复用的秒杀/代入/特值解法与识别信号' },
    { key: 'signal', label: '识别信号', icon: 'Aim', fields: ['identify_signal', 'normal_solve'], desc: '题干特征 → 方法映射' },
    { key: 'verify', label: '代入验证', icon: 'Select', fields: ['normal_solve', 'step_detail'], desc: '常规解法与逐步验证步骤' },
  ],
  '判断推理': [
    { key: 'rule', label: '规律识别', icon: 'MagicStick', fields: ['break_logic', 'sub_point'], desc: '图形/定义/逻辑的规律类型与识别过程' },
    { key: 'logic', label: '逻辑链条', icon: 'Share', fields: ['break_logic', 'step_detail'], desc: '前提→结论逻辑链与削弱/加强' },
    { key: 'analogy', label: '关系图谱', icon: 'Connection', fields: ['sub_point', 'exam_intent'], desc: '词项/要素关系梳理' },
  ],
  '资料分析': [
    { key: 'formula', label: '速算公式卡', icon: 'TrendCharts', fields: ['step_detail', 'quick_solve'], desc: '列式公式 + 速算技巧与适用前提' },
    { key: 'percent', label: '百化分', icon: 'Percent', fields: ['quick_solve'], desc: '特征分数转化法速查' },
    { key: 'locate', label: '数据定位', icon: 'LocationFilled', fields: ['exam_intent', 'step_detail'], desc: '去材料何处取数、注意口径单位' },
  ],
  '常识判断': [
    { key: 'source', label: '知识点溯源', icon: 'Collection', fields: ['sub_point', 'exam_intent'], desc: '正确项释因与关联知识' },
    { key: 'option', label: '选项辨析', icon: 'Switch', fields: ['break_logic'], desc: '逐项正误辨析' },
  ],
  '政治理论': [
    { key: 'theory', label: '理论依据', icon: 'Medal', fields: ['sub_point', 'exam_intent'], desc: '权威表述与理论依据' },
    { key: 'policy', label: '时政关联', icon: 'Calendar', fields: ['exam_intent'], desc: '重要会议/论断体系化记忆' },
  ],
}

export function modColor(m) {
  return MOD_COLORS[m] || '#64748b'
}

export function modStyle(m) {
  const c = modColor(m)
  return { color: c, background: c + '1a', borderColor: c + '55' }
}

export function modIcon(m) {
  return MOD_ICONS[m] || 'Files'
}

// 功能 key → 展示用字段标题
export const FUNCTION_FIELD_LABELS = {
  exam_intent: '考察意图',
  option_feature: '选项特征',
  sub_point: '细分考点',
  break_logic: '破题逻辑',
  quick_solve: '秒杀/速算',
  identify_signal: '识别信号',
  normal_solve: '常规解法',
  step_detail: '解题步骤',
}

// 行测知识库：知识点类型（单一事实源，与后端 Knowledge.kg_type 对应）
export const KG_TYPES = [
  { key: '概念', color: '#4f46e5' },
  { key: '公式', color: '#10b981' },
  { key: '技巧', color: '#8b5cf6' },
  { key: '陷阱', color: '#ef4444' },
  { key: '易混点', color: '#f59e0b' },
  { key: '方法', color: '#06b6d4' },
  { key: '背景', color: '#0ea5e9' },
]

export function kgStyle(t) {
  const c = (KG_TYPES.find(x => x.key === t) || {}).color || '#64748b'
  return { color: c, background: c + '1a', borderColor: c + '55' }
}

// 行测解题库：解题条目类型（单一事实源，与后端 SolveItem.solve_type 对应）
export const SOLVE_TYPES = [
  { key: '破题逻辑', color: '#ef4444' },
  { key: '易错提醒', color: '#f59e0b' },
  { key: '解题方法', color: '#10b981' },
  { key: '速算技巧', color: '#8b5cf6' },
  { key: '题型识别', color: '#06b6d4' },
]

export function solveStyle(t) {
  const c = (SOLVE_TYPES.find(x => x.key === t) || {}).color || '#64748b'
  return { color: c, background: c + '1a', borderColor: c + '55' }
}
