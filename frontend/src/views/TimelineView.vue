<script setup lang="ts">
/** 逃生线一：编年时间轴（粘性年份钉 + 旅行主节点 + 按天子节点 + 滚动渐显）。 */
import { computed, nextTick, onMounted, ref } from 'vue'

import { api, photoUrl } from '@/api'
import DisplayNav from '@/components/DisplayNav.vue'
import { dateRange, memberLabel } from '@/utils/format'
import type { TripCard } from '@/types'

const trips = ref<TripCard[] | null>(null)
const error = ref(false)

interface YearGroup {
  year: number
  trips: TripCard[]
  totalDays: number
}

const groups = computed<YearGroup[]>(() => {
  const byYear = new Map<number, TripCard[]>()
  for (const t of trips.value ?? []) {
    byYear.set(t.year, [...(byYear.get(t.year) ?? []), t])
  }
  return [...byYear.entries()]
    .sort((a, b) => b[0] - a[0])
    .map(([year, list]) => ({
      year,
      trips: list,
      totalDays: list.reduce((s, t) => s + t.days_count, 0),
    }))
})
const firstYear = computed(() => {
  const gs = groups.value
  return gs.length ? gs[gs.length - 1].year : null
})

async function load() {
  error.value = false
  trips.value = null
  try {
    trips.value = await api.trips()
  } catch {
    error.value = true
    return
  }
  // 滚动渐显：等 DOM 渲染完再注册观察器（否则 .reveal 拿不到节点，页面会一直隐形）
  await nextTick()
  const els = document.querySelectorAll('.reveal')
  let fired = false
  const io = new IntersectionObserver(
    (es) => {
      es.forEach((e) => {
        if (e.isIntersecting) {
          fired = true
          e.target.classList.add('in')
          io.unobserve(e.target)
        }
      })
    },
    { threshold: 0.15 },
  )
  els.forEach((el) => io.observe(el))
  // 兜底：个别内嵌 webview 不派发 IO 回调，1.5s 内一次都没触发就直接全部显示
  window.setTimeout(() => {
    if (!fired) els.forEach((el) => el.classList.add('in'))
  }, 1500)
}

onMounted(load)
function hideImg(e: Event) {
  (e.target as HTMLImageElement).style.visibility = 'hidden' // 相册文件被移除等 404 场景不显示破图（#23）
}
</script>

<template>
  <div>
    <DisplayNav active="timeline" />
    <main class="wrap page-pad">
      <section class="page-head">
        <p class="kicker">Chronicle · 时间这条线</p>
        <h1>家庭编年史</h1>
        <p class="sub">地图是空间的那条线，这里是时间的——每次出发是一个节点，每一天是它的注脚。</p>
      </section>

      <div v-if="groups.length" class="tl">
        <section v-for="g in groups" :key="g.year" class="tl-group">
          <div class="tl-year reveal">
            {{ g.year }}
            <small>{{ g.trips.length }} 次出发 · {{ g.totalDays }} 天</small>
          </div>

          <article v-for="t in g.trips" :key="t.slug" class="tl-card reveal">
            <div class="row">
              <router-link v-if="t.cover_photo" class="cov" :to="`/trip/${t.slug}`">
                <img :src="photoUrl(t.cover_photo, 'thumb')" :alt="t.title" loading="lazy" @error="hideImg" />
              </router-link>
              <router-link v-else class="cov" :to="`/trip/${t.slug}`"><img class="cover-fallback" alt="" aria-hidden="true" /></router-link>
              <div class="body">
                <div class="date">{{ dateRange(t.start_date, t.end_date) }}</div>
                <h3 class="t"><router-link :to="`/trip/${t.slug}`">{{ t.title }}</router-link></h3>
                <p class="d">
                  {{ t.route.join(' → ') || t.country }} · {{ t.members.map(memberLabel).join(' ') || '—' }} ·
                  {{ t.days_count }} 天
                </p>
                <div class="foot">
                  <div class="tags">
                    <span v-for="(tag, i) in t.tags" :key="tag.id" class="tag" :class="{ hot: i === 0 }">{{ tag.name }}</span>
                  </div>
                  <div class="members">
                    <span v-for="m in t.members" :key="m.id" :title="memberLabel(m)">{{ memberLabel(m).slice(0, 1) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="t.trip_days.length" class="tl-days">
              <div v-for="d in t.trip_days" :key="d.day_index" class="day">
                <b>D{{ d.day_index }}</b><span>{{ d.title || '—' }}</span>
              </div>
            </div>
          </article>
        </section>

        <div class="tl-end reveal">
          <div class="dot"></div>
          <p>
            <template v-if="firstYear">{{ firstYear }} 是记录的起点。</template
            ><router-link to="/">回到地图，换个方式看 →</router-link>
          </p>
        </div>
      </div>

      <div v-else-if="error" class="load-error">
        <div class="big">📡</div>
        <p>编年加载失败——网络或服务暂时不可用。</p>
        <button class="retry" @click="load">重 试</button>
      </div>
      <div v-else-if="trips !== null" class="empty">
        <div class="big">🗓</div>
        <p>还没有发布任何旅行。<router-link to="/">回到地图 →</router-link></p>
      </div>
    </main>
  </div>
</template>
