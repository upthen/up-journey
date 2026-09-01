<script setup lang="ts">
defineProps<{ active: 'map' | 'timeline' | 'list' }>()
</script>

<template>
  <header class="nav">
    <div class="nav-inner">
      <router-link class="masthead" to="/">
        <span class="mark">🧭</span><span class="zh">游迹</span><span class="en">Up Journey</span>
      </router-link>
      <input id="navtoggle" type="checkbox" class="nav-toggle" />
      <label class="nav-burger" for="navtoggle"><span></span><span></span><span></span></label>
      <nav class="nav-links">
        <router-link to="/" :class="{ active: active === 'map' }">地图</router-link>
        <router-link to="/timeline" :class="{ active: active === 'timeline' }">编年</router-link>
        <router-link to="/list" :class="{ active: active === 'list' }">游记名录</router-link>
      </nav>
    </div>
  </header>
</template>
