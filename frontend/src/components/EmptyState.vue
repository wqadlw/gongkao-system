<template>
  <div class="gk-empty">
    <el-icon v-if="icon && isCompName" class="gk-empty__icon"><component :is="icon" /></el-icon>
    <div v-else-if="icon" class="gk-empty__icon">{{ icon }}</div>
    <div class="gk-empty__title" v-if="title">{{ title }}</div>
    <div class="gk-empty__desc" v-if="desc">{{ desc }}</div>
    <div class="gk-empty__actions"><slot name="actions" /></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: String, default: '' },
  title: { type: String, default: '' },
  desc: { type: String, default: '' },
})

// 若传入的是 PascalCase 组件名（如 DocumentDeleted），用 <component :is> 渲染；否则当作 emoji/文本
const isCompName = computed(() => /^[A-Z][A-Za-z0-9]*$/.test(props.icon))
</script>
