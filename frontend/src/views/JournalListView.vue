<script setup lang="ts">
/** 逃生线二：游记名录（按时间倒序卡片流，支持 ?year= 过滤）。 */
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { api, photoUrl } from '@/api'
import DisplayNav from '@/components/DisplayNav.vue'
import { dateRange, memberLabel } from '@/utils/format'
import type { TripCard } from '@/types'

const route = useRoute()
const trips = ref<TripCard[] | null>(null)

const yearFilter = computed<number | null>(() => {
  const y = Number(route.query.year)
  return Number.isInteger(y) && y > 1990 ? y : null
})
const shown = computed(() =>
  (trips.value ?? []).filter((t) => yearFilter.value === null || t.year === yearFilter.value),
)

function routeText(t: TripCard): string {
  if (t.country) return `${t.country} · ${t.route.join(' → ') || '—'}`
  return t.route.join(' → ') || '—'
}

const error = ref(false)

async function load() {
  error.value = false
  trips.value = null
  try {
    trips.value = await api.trips()
  } catch {
    error.value = true
  }
}

onMounted(load)
function hideImg(e: Event) {
  (e.target as HTMLImageElement).style.visibility = 'hidden' // 相册文件被移除等 404 场景不显示破图（#23）
}
</script>

<template>
  <div>
    <DisplayNav active="list" />
    <main class="wrap page-pad">
      <section class="page-head">
        <p class="kicker">Journal · 逃生口</p>
        <h1>游记名录</h1>
        <p class="sub">
          喜欢按部就班往下翻的人走这里——按时间倒序的共 {{ shown.length }} 篇游记。<router-link
            to="/"
            style="color: var(--coral-deep); font-weight: 600"
            >回到地图探索 →</router-link
          >
          <template v-if="yearFilter">
            <span style="color: var(--gray)">　当前只看 {{ yearFilter }} 年。</span>
            <router-link to="/list" style="font-weight: 600">看全部 →</router-link>
          </template>
        </p>
      </section>

      <div v-if="shown.length" class="journal">
        <article v-for="t in shown" :key="t.slug" class="j-row">
          <router-link class="ph" :to="`/trip/${t.slug}`">
            <img v-if="t.cover_photo" :src="photoUrl(t.cover_photo, 'thumb')" :alt="t.title" loading="lazy" @error="hideImg" />
            <img v-else class="cover-fallback" alt="" aria-hidden="true" />
          </router-link>
          <div class="body">
            <div class="meta">
              {{ dateRange(t.start_date, t.end_date) }}<span class="dot"></span>{{ routeText(t)
              }}<span class="dot"></span>{{ t.days_count }} 天
            </div>
            <h3><router-link :to="`/trip/${t.slug}`">{{ t.title }}</router-link></h3>
            <p v-if="t.summary">{{ t.summary }}</p>
            <div class="foot">
              <div class="tags">
                <span v-for="(tag, i) in t.tags" :key="tag.id" class="tag" :class="{ hot: i === 0 }">{{ tag.name }}</span>
              </div>
              <div class="members">
                <span
                  v-for="m in t.members.slice(0, 4)"
                  :key="m.id"
                  :class="{ more: false }"
                  :title="memberLabel(m)"
                  >{{ memberLabel(m).slice(0, 1) }}</span
                >
                <span v-if="t.members.length > 4" class="more">…</span>
              </div>
            </div>
          </div>
        </article>
      </div>

      <div v-else-if="trips !== null" class="empty">
        <div class="big">📚</div>
        <p>还没有游记。<router-link to="/">回到地图 →</router-link></p>
      </div>
      <div v-else-if="error" class="load-error">
        <div class="big">📡</div>
        <p>游记加载失败——网络或服务暂时不可用。</p>
        <button class="retry" @click="load">重 试</button>
      </div>
      <div v-else class="loading-dots"><i></i><i></i><i></i></div>
    </main>
  </div>
</template>
