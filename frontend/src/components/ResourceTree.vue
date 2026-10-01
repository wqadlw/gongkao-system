<template>
  <div v-for="node in nodes" :key="keyPrefix + '/' + node.name">
    <button
      class="cat-item"
      :class="{ active: selectedPath === keyPrefix + '/' + node.name }"
      :style="{ paddingLeft: indent + 'px' }"
      @click="$emit('select', node, keyPrefix + '/' + node.name)"
    >
      <span
        v-if="node.children.length"
        class="cat-caret" :class="{ open: expanded[keyPrefix + '/' + node.name] }"
        @click.stop="$emit('toggle', keyPrefix + '/' + node.name)"
      >▸</span>
      <span v-else class="cat-caret placeholder"></span>
      <span class="cat-name">{{ node.name }}</span>
      <span class="cat-count">{{ node.count }}</span>
    </button>
    <div v-if="node.children.length && expanded[keyPrefix + '/' + node.name]">
      <ResourceTree
        :nodes="node.children"
        :expanded="expanded"
        :selected-path="selectedPath"
        :key-prefix="keyPrefix + '/' + node.name"
        :indent="indent + 16"
        @select="(n, p) => $emit('select', n, p)"
        @toggle="(k) => $emit('toggle', k)"
      />
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'ResourceTree' })
defineProps({
  nodes: { type: Array, default: () => [] },
  expanded: { type: Object, default: () => ({}) },
  selectedPath: { type: String, default: '' },
  keyPrefix: { type: String, default: '' },
  indent: { type: Number, default: 12 },
})
defineEmits(['select', 'toggle'])
</script>

<style scoped>
/* 子组件自带样式：父页面的 scoped 样式作用不到本组件内部 */
.cat-item {
  display: flex; align-items: center; gap: 6px; width: 100%;
  padding: 8px 12px; border: none; background: none; border-radius: var(--radius-md);
  font-size: 13px; color: var(--text-secondary); cursor: pointer; transition: all 0.15s;
}
.cat-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.cat-item.active { background: var(--primary-bg); color: var(--primary); font-weight: 600; }
.cat-caret {
  display: inline-block; width: 14px; flex-shrink: 0; text-align: center;
  color: var(--text-tertiary); transition: transform 0.15s; font-size: 11px;
}
.cat-caret.open { transform: rotate(90deg); }
.cat-caret.placeholder { visibility: hidden; }
.cat-name { flex: 1; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cat-count { flex-shrink: 0; font-size: 11.5px; color: var(--text-tertiary); }
</style>
