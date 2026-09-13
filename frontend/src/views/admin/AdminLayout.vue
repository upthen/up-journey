<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api'
import { useMetaStore } from '@/stores/meta'

const route = useRoute()
const router = useRouter()
const meta = useMetaStore()
const authed = ref(false)

async function logout() {
  try {
    await api.admin.logout()
  } catch {
    ElMessage.error('退出请求失败，本地会话仍会清除')
  }
  router.push('/admin/login')
}

onMounted(async () => {
  try {
    await api.admin.session()
    authed.value = true
  } catch {
    authed.value = false
  }
  meta.ensure()
})
</script>

<template>
  <div class="ad-shell">
    <header class="ad-topbar">
      <div class="ad-topbar-inner">
        <div class="brand">
          <span class="mark">
            <svg class="mark-feet" viewBox="56 118 400 278" aria-hidden="true">
        <g fill="currentColor" transform="translate(180 246) rotate(-8)">
          <ellipse cx="4" cy="45" rx="58" ry="95"/>
          <circle cx="30" cy="-72" r="27"/>
          <circle cx="-18" cy="-82" r="22"/>
          <circle cx="-56" cy="-76" r="19"/>
          <circle cx="-82" cy="-52" r="17"/>
          <circle cx="-96" cy="-22" r="15"/>
        </g>
        <g fill="currentColor" transform="translate(356 279) scale(-0.76 0.76) rotate(-8)">
          <ellipse cx="4" cy="45" rx="58" ry="95"/>
          <circle cx="30" cy="-72" r="27"/>
          <circle cx="-18" cy="-82" r="22"/>
          <circle cx="-56" cy="-76" r="19"/>
          <circle cx="-82" cy="-52" r="17"/>
          <circle cx="-96" cy="-22" r="15"/>
        </g>
      </svg>
          </span> 足迹 <span class="badge">管理端</span>
        </div>
        <div class="flex items-center gap-4">
          <a v-if="authed" href="#" style="font-size: 13px; color: var(--ink-2)" @click.prevent="logout">退出登录</a>
          <router-link to="/" style="font-size: 13px; color: var(--ink-2)">返回展示端 →</router-link>
        </div>
      </div>
    </header>
    <div class="ad-layout">
      <aside class="ad-side">
        <nav class="ad-menu">
          <router-link to="/admin/trips" :class="{ active: route.name === 'admin-trips' || route.name === 'admin-trip-edit' || route.name === 'admin-trip-new' }">🗂 旅行管理</router-link>
        </nav>
      </aside>
      <main class="ad-main">
        <router-view />
      </main>
    </div>
  </div>
</template>
