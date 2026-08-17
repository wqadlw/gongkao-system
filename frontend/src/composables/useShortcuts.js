import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

// 全局键盘快捷键定义（单一事实源，供帮助弹窗复用）
export const SHORTCUTS = [
  { key: 'd', desc: '首页看板', path: '/dashboard' },
  { key: 'i', desc: '题目录入', path: '/question-input' },
  { key: 'u', desc: '核对并入库', path: '/deposit' },
  { key: 'q', desc: '题库列表', path: '/question-list' },
  { key: 'k', desc: '行测知识库', path: '/knowledge' },
  { key: 'l', desc: '行测解题库', path: '/solve-library' },
  { key: 'e', desc: '错题集', path: '/errors' },
  { key: 'r', desc: '智能复习', path: '/review' },
  { key: 'n', desc: '笔记管理', path: '/notes' },
  { key: 'v', desc: '可视化大屏', path: '/visualization' },
  { key: 'c', desc: '考试倒计时', path: '/countdown' },
  { key: 'p', desc: '提示词管理', path: '/prompts' },
  { key: 's', desc: '聚焦顶部搜索框', action: 'search' },
  { key: '?', desc: '打开本快捷键帮助', action: 'help' },
]

function isTyping(target) {
  if (!target) return false
  const tag = target.tagName
  return (
    tag === 'INPUT' ||
    tag === 'TEXTAREA' ||
    tag === 'SELECT' ||
    target.isContentEditable
  )
}

// 在持久化外壳（App.vue）中调用一次即可；自动忽略输入框内的按键
export function useShortcuts({ onHelp, onSearch } = {}) {
  const router = useRouter()

  function handler(e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return
    if (isTyping(e.target)) return

    const k = e.key
    if (k === '?') {
      e.preventDefault()
      onHelp && onHelp()
      return
    }
    if (k === 's' || k === '/') {
      e.preventDefault()
      onSearch && onSearch()
      return
    }
    const found = SHORTCUTS.find((s) => s.key === k.toLowerCase())
    if (found && found.path) {
      e.preventDefault()
      router.push(found.path)
    }
  }

  onMounted(() => window.addEventListener('keydown', handler))
  onUnmounted(() => window.removeEventListener('keydown', handler))
}
