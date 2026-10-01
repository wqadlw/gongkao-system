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
