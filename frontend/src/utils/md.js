// Markdown + LaTeX 数学公式渲染器
// 思路：先把 $$...$$ / $...$ 数学片段抽出占位 → marked 渲染 Markdown → 用 KaTeX 回注公式
// 这样可避免 marked 破坏 LaTeX 中的 \、_、* 等字符。
import { marked } from 'marked'
import katex from 'katex'

marked.setOptions({ breaks: true, gfm: true })

function renderTex(tex, displayMode) {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      strict: false,
      trust: false,
    })
  } catch (e) {
    return `<code class="tex-error">${escapeHtml(tex)}</code>`
  }
}

function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/**
 * 渲染 Markdown（含数学公式）为 HTML 字符串。
 * @param {string} src 原始 Markdown 文本
 * @returns {string} 可用于 v-html 的 HTML
 */
export function renderMarkdown(src) {
  if (!src) return ''
  const blocks = []

  // 1) 抽取数学公式（先块级 $$...$$，再行内 $...$），用占位符替换
  let s = String(src)
    // 保护代码块中的 $，避免误判：这里简单处理——代码块里的公式较少，接受少量误差
    .replace(/\$\$([\s\S]+?)\$\$/g, (m, tex) => {
      blocks.push({ tex: tex.trim(), display: true })
      return `\u0000MATH${blocks.length - 1}\u0000`
    })
    .replace(/(?<!\\)\$([^\$\n]+?)(?<!\\)\$/g, (m, tex) => {
      blocks.push({ tex: tex.trim(), display: false })
      return `\u0000MATH${blocks.length - 1}\u0000`
    })

  // 2) Markdown → HTML
  let html = marked.parse(s)

  // 3) 回注 KaTeX 渲染结果
  html = html.replace(/\u0000MATH(\d+)\u0000/g, (m, i) => {
    const b = blocks[Number(i)]
    return b ? renderTex(b.tex, b.display) : m
  })

  return html
}

/**
 * 行内渲染（不产生 <p> 包裹），用于短字段。
 */
export function renderInline(src) {
  if (!src) return ''
  const blocks = []
  let s = String(src)
    .replace(/\$\$([\s\S]+?)\$\$/g, (m, tex) => {
      blocks.push({ tex: tex.trim(), display: true })
      return `\u0000MATH${blocks.length - 1}\u0000`
    })
    .replace(/(?<!\\)\$([^\$\n]+?)(?<!\\)\$/g, (m, tex) => {
      blocks.push({ tex: tex.trim(), display: false })
      return `\u0000MATH${blocks.length - 1}\u0000`
    })
  let html = marked.parseInline(s)
  html = html.replace(/\u0000MATH(\d+)\u0000/g, (m, i) => {
    const b = blocks[Number(i)]
    return b ? renderTex(b.tex, b.display) : m
  })
  return html
}
