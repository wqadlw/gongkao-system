<template>
  <section class="gk-section">
    <div v-if="title || $slots.header || $slots.extra" class="gk-section__header">
      <h3 class="gk-section__title">
        <span class="dot" v-if="title || $slots.header"></span>
        <slot name="header">{{ title }}</slot>
      </h3>
      <div class="gk-section__extra"><slot name="extra" /></div>
    </div>
    <div class="gk-section__body" :style="noPadding ? 'padding:0' : ''">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  noPadding: { type: Boolean, default: false },
})
</script>
