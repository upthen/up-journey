<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

import { useMetaStore } from '@/stores/meta'

const route = useRoute()
const meta = useMetaStore()

onMounted(() => meta.ensure())
</script>

<template>
  <div class="ad-shell">
    <header class="ad-topbar">
      <div class="brand">
        <span class="mark">🧭</span> 游迹 <span class="badge">管理端</span>
      </div>
      <router-link to="/">返回展示端 →</router-link>
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
