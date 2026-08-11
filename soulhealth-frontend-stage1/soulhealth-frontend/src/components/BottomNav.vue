<script setup>
const items = [
  { to: '/', label: '首页', icon: 'M4 11.2 12 4l8 7.2M6 10v9.5h12V10' },
  { to: '/timeline', label: '病历', icon: 'M7 4h10a1.5 1.5 0 0 1 1.5 1.5V20l-3-1.8-2.5 1.8-2.5-1.8L7.5 20V5.5A1.5 1.5 0 0 1 9 4M9.5 9h5M9.5 12.5h5' },
  { to: '/profile', label: '我的', icon: 'M12 11.5a3.6 3.6 0 1 0 0-7.2 3.6 3.6 0 0 0 0 7.2ZM5 20c.8-3.6 3.6-5.4 7-5.4s6.2 1.8 7 5.4' },
]
</script>

<template>
  <nav class="bn">
    <router-link v-for="it in items" :key="it.to" :to="it.to" class="bn-item" active-class="on"
      :exact="it.to === '/'">
      <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor"
        stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
        <path :d="it.icon" />
      </svg>
      <span>{{ it.label }}</span>
      <i class="dot"></i>
    </router-link>
  </nav>
</template>

<style scoped>
.bn {
  position: fixed; bottom: 0; left: 50%; transform: translateX(-50%);
  width: min(520px, 100%); z-index: 20;
  display: flex; justify-content: space-around;
  padding: 8px 10px calc(10px + env(safe-area-inset-bottom));
  background: color-mix(in srgb, var(--card) 90%, transparent);
  backdrop-filter: blur(12px);
  border-top: 1px solid var(--line);
}
.bn-item {
  position: relative;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 4px 18px; border-radius: 12px;
  font-size: 11px; color: var(--ink-3);
  transition: color 0.2s ease;
}
.dot { width: 4px; height: 4px; border-radius: 50%; background: transparent; margin-top: 1px; }
.bn-item.on { color: var(--primary); font-weight: 600; }
.bn-item.on .dot { background: var(--gold); }
</style>
