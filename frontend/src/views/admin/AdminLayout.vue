<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api } from '@/api'
import { useMetaStore } from '@/stores/meta'

const route = useRoute()
const router = useRouter()
const meta = useMetaStore()
const authed = ref(false)

async function logout() {
  await api.admin.logout()
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
      <div class="brand">
        <span class="mark">🧭</span> 游迹 <span class="badge">管理端</span>
      </div>
      <div class="flex items-center gap-4">
        <a v-if="authed" href="#" style="font-size: 13px; color: var(--ink-2)" @click.prevent="logout">退出登录</a>
        <router-link to="/" style="font-size: 13px; color: var(--ink-2)">返回展示端 →</router-link>
      </div>
    </header>
    <div class="ad-layout">
      <aside class="ad-side">
        <nav class="ad-menu">
          <router-link to="/admin/trips" :class="{ active: route.name === 'admin-trips' || route.name === 'admin-trip-edit' || route.name === 'admin-trip-new' }">🗂 旅行管理</router-link>
          <router-link to="/admin/members" :class="{ active: route.name === 'admin-members' }">👨‍👩‍👦 家庭成员</router-link>
          <router-link to="/admin/tags" :class="{ active: route.name === 'admin-tags' }">🏷 标签管理</router-link>
        </nav>
      </aside>
      <main class="ad-main">
        <router-view />
      </main>
    </div>
  </div>
</template>
