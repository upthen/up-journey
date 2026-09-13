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
            <svg class="mark-feet" viewBox="45 47 422 418" aria-hidden="true">
              <g fill="currentColor" transform="translate(256 256) scale(1.1) translate(-256 -256)">
                <g transform="translate(169 268) rotate(-10)">
                  <ellipse cx="0" cy="-45" rx="60" ry="78"/>
                  <circle cx="0" cy="58" r="40"/>
                </g>
                <g transform="translate(341 292) rotate(12)">
                  <ellipse cx="0" cy="-34" rx="45" ry="60"/>
                  <circle cx="0" cy="44" r="30"/>
                </g>
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
