<template>
  <div class="brand-logo" aria-label="公考行测知识库">
    <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="gk-logo-g" x1="4" y1="4" x2="44" y2="44" gradientUnits="userSpaceOnUse">
          <stop stop-color="#2563EB" />
          <stop offset="1" stop-color="#06B6D4" />
        </linearGradient>
      </defs>
      <!-- 圆角渐变底 -->
      <rect x="2" y="2" width="44" height="44" rx="12" fill="url(#gk-logo-g)" />
      <!-- 学士帽：菱形帽顶 + 帽座 + 流苏 -->
      <path d="M24 9 L39 16 L24 23 L9 16 Z" fill="#fff" />
      <path d="M15.5 20.5 V26 C15.5 28.5 19 30.5 24 30.5 C29 30.5 32.5 28.5 32.5 26 V20.5 L24 24.5 Z"
            fill="#fff" opacity="0.85" />
      <path d="M37.5 17.5 V25" stroke="#fff" stroke-width="1.8" stroke-linecap="round" opacity="0.9" />
      <circle cx="37.5" cy="27" r="2" fill="#FDE047" />
      <!-- 摊开的书 -->
      <path d="M10 34 C15 31.5 20.5 31.5 24 34.5 C27.5 31.5 33 31.5 38 34 V40 C33 37.8 27.5 37.8 24 40.5 C20.5 37.8 15 37.8 10 40 Z"
            fill="#fff" opacity="0.95" />
      <path d="M24 34.5 V40" stroke="#0891B2" stroke-width="1.4" />
    </svg>
  </div>
</template>

<style scoped>
.brand-logo {
  width: 32px; height: 32px; flex-shrink: 0;
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
}
.brand-logo svg { width: 100%; height: 100%; display: block; }
</style>
