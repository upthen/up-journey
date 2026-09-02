import { createRouter, createWebHistory } from 'vue-router'

import { api } from '@/api'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ---- 展示端（v4 流程式：地图即首页）----
    { path: '/', name: 'map', component: () => import('@/views/MapHome.vue') },
    { path: '/timeline', name: 'timeline', component: () => import('@/views/TimelineView.vue') },
    { path: '/list', name: 'list', component: () => import('@/views/JournalListView.vue') },
    { path: '/trip/:slug', name: 'trip', component: () => import('@/views/TripDetailView.vue') },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      // 鉴权守卫：公网部署前已启用管理员密码；展示端路由不经过这里
      children: [
        { path: '', redirect: '/admin/trips' },
        { path: 'login', name: 'admin-login', component: () => import('@/views/admin/AdminLoginView.vue') },
        { path: 'trips', name: 'admin-trips', component: () => import('@/views/admin/TripListView.vue'), meta: { auth: true } },
        { path: 'trips/new', name: 'admin-trip-new', component: () => import('@/views/admin/TripEditView.vue'), meta: { auth: true } },
        { path: 'trips/:id(\\d+)', name: 'admin-trip-edit', component: () => import('@/views/admin/TripEditView.vue'), meta: { auth: true } },
        { path: 'members', name: 'admin-members', component: () => import('@/views/admin/MembersView.vue'), meta: { auth: true } },
        { path: 'tags', name: 'admin-tags', component: () => import('@/views/admin/TagsView.vue'), meta: { auth: true } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior(_to, _from, saved) {
    return saved ?? { top: 0 }
  },
})

router.beforeEach(async (to) => {
  if (!to.meta.auth) return true
  try {
    await api.admin.session()
    return true
  } catch {
    return { name: 'admin-login', query: { next: to.fullPath } }
  }
})
