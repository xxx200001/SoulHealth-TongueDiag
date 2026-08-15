import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

import LoginPage from '../pages/LoginPage.vue'
import HomePage from '../pages/HomePage.vue'
import LabPage from '../pages/LabPage.vue'
import TonguePage from '../pages/TonguePage.vue'
import QuestionnairePage from '../pages/QuestionnairePage.vue'
import ProfilePage from '../pages/ProfilePage.vue'
import ReportPage from '../pages/ReportPage.vue'
import TimelinePage from '../pages/TimelinePage.vue'
// ── 生物计算平台页面 ──
import ArchivePage from '../pages/ArchivePage.vue'
import UploadPage from '../pages/UploadPage.vue'
import AnalysisPage from '../pages/AnalysisPage.vue'
import QAPage from '../pages/QAPage.vue'

const routes = [
  { path: '/login', component: LoginPage, meta: { public: true } },
  { path: '/', component: HomePage },
  // ── 中医辨证溯源 ──
  { path: '/lab', component: LabPage },
  { path: '/tongue', component: TonguePage },
  { path: '/questionnaire', component: QuestionnairePage },
  { path: '/profile', component: ProfilePage },
  { path: '/report', component: ReportPage },
  { path: '/timeline', component: TimelinePage },
  // ── 生物计算 ──
  { path: '/archive', component: ArchivePage },
  { path: '/upload', component: UploadPage },
  { path: '/analysis', component: AnalysisPage },
  { path: '/qa', component: QAPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：未登录跳转登录页
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
