import { createRouter, createWebHistory } from 'vue-router'
import NotesView from '../views/NotesView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/notes'
    },
    {
      path: '/notes',
      name: 'notes',
      component: NotesView,
      meta: { title: '笔记生成' }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { title: '设置' }
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('../views/HistoryView.vue'),
      meta: { title: '历史记录' }
    },
  ],
})

export default router
