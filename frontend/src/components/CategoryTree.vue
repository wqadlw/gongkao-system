<template>
  <ul class="cat-tree" :class="{ 'is-root': isRoot }">
    <li v-for="node in nodes" :key="node.id" class="cat-node">
      <div class="cat-row"
        :class="{ active: String(activeId) === String(node.id) || isActive(node), 'on-path': isOnPath(node) && !isActive(node) }"
        @click="onRowClick(node)">
        <button v-if="hasChildren(node)" class="cat-caret" @click.stop="toggle(node)" :class="{ open: isOpen(node) }">▸</button>
        <span v-else class="cat-caret placeholder"></span>
        <span v-if="node.level === 1" class="cat-dot" :style="{ background: modColor(node.module) }"></span>
        <span class="cat-name">{{ node.name }}</span>
        <span v-if="node.question_count" class="cat-count" :class="{ err: node.error_count > 0 }">{{ node.question_count }}</span>
      </div>
      <CategoryTree
        v-if="hasChildren(node) && isOpen(node)"
        :nodes="node.children"
        :active-id="activeId"
        :active-path="activePath"
        :path-names="nodePathOf(node)"
        :selectable="selectable"
        :is-root="false"
        @select="$emit('select', $event)"
      />
    </li>
  </ul>
</template>

<script setup>
import { reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { modColor } from '../utils/constants'

const props = defineProps({
  nodes: { type: Array, default: () => [] },
  activeId: { type: [Number, String], default: null },
  activePath: { type: Array, default: null },   // 当前题目的 level1..level5 名称数组，用于高亮其题型
  pathNames: { type: Array, default: () => [] }, // 递归累计的路径名（内部使用）
  selectable: { type: Boolean, default: false },
  isRoot: { type: Boolean, default: true },
})
const emit = defineEmits(['select'])
const router = useRouter()

const expanded = reactive({})
function hasChildren(node) {
  return node.children && node.children.length > 0
}
function isOpen(node) {
  if (expanded[node.id] === undefined) return true
  return expanded[node.id]
}
function toggle(node) {
  expanded[node.id] = !isOpen(node)
}

function nodePathOf(node) {
  return [...props.pathNames, node.name]
}
// activePath 前缀匹配：本节点路径是否为 activePath 的前缀
function matchPrefix(p) {
  const ap = props.activePath
  if (!ap || !ap.length) return false
  if (p.length > ap.length) return false
  for (let i = 0; i < p.length; i++) if (p[i] !== ap[i]) return false
  return true
}
function isOnPath(node) {
  return matchPrefix(nodePathOf(node))
}
// 最深层匹配节点才是高亮（active）；其祖先仅作 on-path 弱高亮
function isActive(node) {
  if (!isOnPath(node)) return false
  if (!hasChildren(node)) return true
  return !node.children.some(c => matchPrefix([...nodePathOf(node), c.name]))
}

// 进入详情页时，自动展开 activePath 的所有祖先，确保当前题型可见
function expandToActive(list, prefix) {
  for (const n of list) {
    const p = [...prefix, n.name]
    if (matchPrefix(p)) {
      expanded[n.id] = true
      if (hasChildren(n)) expandToActive(n.children, p)
    }
  }
}
function ensureVisible() {
  if (props.isRoot && props.activePath && props.activePath.length) {
    expandToActive(props.nodes, [])
  }
}
onMounted(ensureVisible)
watch(() => props.activePath, ensureVisible)

function onRowClick(node) {
  if (props.selectable) {
    emit('select', node)
    return
  }
  router.push({ path: '/question-list', query: { cat: node.id } })
}
</script>

<style scoped>
.cat-tree {
  list-style: none;
  margin: 0;
  padding: 0;
}
.cat-tree.is-root {
  padding: 4px 0;
}
.cat-tree:not(.is-root) {
  margin-left: 14px;
  border-left: 1px solid var(--border-light);
  padding-left: 4px;
}
.cat-node {
  margin: 1px 0;
}
.cat-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}
.cat-row:hover {
  background: var(--bg-subtle);
}
.cat-row.on-path {
  background: var(--bg-subtle);
}
.cat-row.active {
  background: var(--primary-bg);
  box-shadow: inset 2px 0 0 var(--primary);
}
.cat-row.active .cat-name {
  color: var(--primary);
  font-weight: 700;
}
.cat-row.on-path .cat-name {
  color: var(--primary);
  font-weight: 600;
}
.cat-caret {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s;
  padding: 0;
}
.cat-caret.open {
  transform: rotate(90deg);
}
.cat-caret.placeholder {
  cursor: default;
}
.cat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.cat-name {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cat-count {
  font-size: 11px;
  color: var(--text-tertiary);
  background: var(--bg-subtle);
  padding: 0 6px;
  border-radius: 10px;
  flex-shrink: 0;
}
.cat-count.err {
  color: var(--danger);
  background: var(--danger-bg);
}
</style>
