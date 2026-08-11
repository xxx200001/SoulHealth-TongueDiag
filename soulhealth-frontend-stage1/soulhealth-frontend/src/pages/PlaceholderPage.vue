<script setup>
defineProps({ title: String, stage: Number })
</script>

<template>
  <div class="ph card">
    <span class="ph-seal serif">{{ title.slice(0, 1) }}</span>
    <h2 class="serif">{{ title }}</h2>
    <p>本页面将在 <b>阶段 {{ stage }}</b> 交付。数据结构与路由已就绪，届时直接替换本组件即可。</p>
    <router-link class="btn" to="/">返回首页</router-link>
  </div>
</template>

<style scoped>
.ph {
  margin-top: 12vh; padding: 40px 24px;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  text-align: center;
}
.ph-seal {
  width: 56px; height: 56px; border-radius: 12px;
  display: grid; place-items: center;
  font-size: 24px; color: #F6EFE2; background: var(--seal);
  box-shadow: inset 0 0 0 2px rgba(246, 239, 226, 0.5);
}
.ph h2 { margin: 6px 0 0; font-size: 19px; }
.ph p { margin: 0 0 10px; font-size: 13px; color: var(--ink-2); max-width: 30ch; }
.ph b { color: var(--gold); }
</style>
