import { createRouter, createWebHistory } from 'vue-router'

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
      // 鉴权预留：未来反代公网前在此挂路由守卫（访客密码/管理员密码），无需改架构
      children: [
        { path: '', redirect: '/admin/trips' },
        { path: 'trips', name: 'admin-trips', component: () => import('@/views/admin/TripListView.vue') },
        { path: 'trips/new', name: 'admin-trip-new', component: () => import('@/views/admin/TripEditView.vue') },
        { path: 'trips/:id(\\d+)', name: 'admin-trip-edit', component: () => import('@/views/admin/TripEditView.vue') },
        { path: 'members', name: 'admin-members', component: () => import('@/views/admin/MembersView.vue') },
        { path: 'tags', name: 'admin-tags', component: () => import('@/views/admin/TagsView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior(_to, _from, saved) {
    return saved ?? { top: 0 }
  },
})
