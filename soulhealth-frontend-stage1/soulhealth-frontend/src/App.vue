<script setup>
import { onMounted } from 'vue'
import AppHeader from './components/AppHeader.vue'
import BottomNav from './components/BottomNav.vue'

onMounted(() => {
  const saved = localStorage.getItem('sh_theme')
  if (saved) document.documentElement.dataset.theme = saved
  else if (matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.dataset.theme = 'dark'
})
</script>

<template>
  <div class="shell">
    <AppHeader />
    <main class="page">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <BottomNav />
  </div>
</template>

<style>
.shell {
  position: relative; z-index: 1;
  max-width: 520px; margin: 0 auto;
  min-height: 100dvh;
  display: flex; flex-direction: column;
}
.page { flex: 1; padding: 14px 18px 108px; }

.page-enter-active, .page-leave-active { transition: opacity 0.22s ease, transform 0.22s ease; }
.page-enter-from { opacity: 0; transform: translateY(10px); }
.page-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
