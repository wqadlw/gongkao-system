<template>
  <header class="gk-page-head">
    <div class="gk-page-head__main">
      <h1 class="gk-page-head__title">
        <el-icon v-if="icon" class="ico"><component :is="icon" /></el-icon>
        <span>{{ title }}</span>
      </h1>
      <p v-if="subtitle" class="gk-page-head__sub">{{ subtitle }}</p>
    </div>
    <div class="gk-page-head__extra"><slot name="extra" /></div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  icon: { type: String, default: '' },
})
</script>
