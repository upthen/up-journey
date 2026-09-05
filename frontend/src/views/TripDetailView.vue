<script setup lang="ts">
/** 第三幕：完整游记（hero 大图 + 富文本正文 + 按景点图库 + 行程小地图 + 按天行程）。 */
import * as echarts from 'echarts'
import { computed, onMounted, onUnmounted, ref, shallowRef, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

import { api, photoUrl } from '@/api'
import DisplayNav from '@/components/DisplayNav.vue'
import { lightbox } from '@/composables/lightbox'
import type { TripDetail } from '@/types'
import { dateRange, mdDate, memberLabel } from '@/utils/format'
import { sanitizeContent } from '@/utils/sanitize'

const route = useRoute()
const trip = ref<TripDetail | null>(null)
const notFound = ref(false)
const loadError = ref(false)

const safeContent = computed(() => sanitizeContent(trip.value?.content))
const cover = computed(() => {
  const t = trip.value
  if (!t) return null
  return t.cover_photo ?? t.gallery.find((g) => g.photos.length)?.photos[0] ?? null
})
const routeText = computed(() => {
  const t = trip.value
  if (!t) return ''
  const names = t.cities.map((c) => c.display)
  return t.country ? `${t.country} · ${names.join(' → ')}` : names.join(' → ')
})

/* ---------- 行程小地图（景点级路线） ---------- */
const miniMapEl = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()
let resizeHandler = () => chart.value?.resize()

function renderMiniMap(t: TripDetail) {
  const inChina = ([lng, lat]: number[]) => lng >= 73 && lng <= 135.5 && lat >= 17 && lat <= 54
  const spots = t.attractions
    .filter((a) => a.resolved_lng !== null && a.resolved_lat !== null)
    .map((a) => ({ name: a.name, value: [a.resolved_lng!, a.resolved_lat!] }))
    .filter((s) => inChina(s.value))
  const cityPath = t.cities
    .filter((c) => c.lng !== null && c.lat !== null)
    .map((c) => [c.lng!, c.lat!])
    .filter(inChina)
  if (!spots.length && !cityPath.length) return

  const lons = [...spots.map((s) => s.value[0]), ...cityPath.map((c) => c[0])]
  const lats = [...spots.map((s) => s.value[1]), ...cityPath.map((c) => c[1])]
  const center: [number, number] = [(Math.min(...lons) + Math.max(...lons)) / 2, (Math.min(...lats) + Math.max(...lats)) / 2]
  const span = Math.max(Math.max(...lons) - Math.min(...lons), Math.max(...lats) - Math.min(...lats))
  const zoom = Math.min(9, Math.max(1.2, 10 / (span + 1)))

  const lines: { coords: [number, number][] }[] = []
  for (let i = 0; i < cityPath.length - 1; i++) {
    lines.push({ coords: [cityPath[i], cityPath[i + 1]] as [number, number][] })
  }

  chart.value?.dispose()
  if (!miniMapEl.value) return
  chart.value = echarts.init(miniMapEl.value)
  chart.value.setOption({
    animation: false,
    geo: {
      map: 'china',
      roam: true,
      scaleLimit: { min: 1, max: 16 },
      center,
      zoom,
      itemStyle: { areaColor: '#EDE9E1', borderColor: '#FAF8F4', borderWidth: 1 },
      emphasis: { label: { show: false }, itemStyle: { areaColor: '#F6E3D9' } },
      select: { disabled: true },
    },
    series: [
      ...(lines.length
        ? [
            {
              type: 'lines',
              coordinateSystem: 'geo',
              lineStyle: { color: '#E8683A', width: 2, opacity: 0.8, curveness: 0.2 },
              data: lines,
            },
          ]
        : []),
      ...(spots.length
        ? [
            {
              type: 'effectScatter',
              coordinateSystem: 'geo',
              symbolSize: 8,
              itemStyle: { color: '#14586B', borderColor: '#fff', borderWidth: 1.5 },
              rippleEffect: { scale: 2.6, brushType: 'stroke' },
              label: {
                show: true,
                position: 'top',
                formatter: (p: { name: string }) => p.name,
                fontSize: 10,
                color: '#3E4C57',
                fontWeight: 600,
                backgroundColor: 'rgba(255,255,255,.85)',
                borderRadius: 4,
                padding: [1, 5],
              },
              labelLayout: { hideOverlap: true },
              data: spots,
            },
          ]
        : []),
    ],
  })
}

async function load(slug: string) {
  notFound.value = false
  loadError.value = false
  trip.value = null
  try {
    trip.value = await api.trip(slug)
  } catch (e: unknown) {
    // 404 才是「不存在/未发布」；500/网络故障是服务问题，文案不混用（#23）
    notFound.value = (e as { response?: { status?: number } })?.response?.status === 404
    loadError.value = !notFound.value
    return
  }
  if (!echarts.getMap('china')) {
    const res = await fetch('/china.json')
    if (!res.ok) return // 地图小卡片缺图层时正文照常，只是卡片为空
    echarts.registerMap('china', await res.json())
  }
  renderMiniMap(trip.value)
}

watchEffect(() => {
  const slug = route.params.slug
  if (slug && typeof slug === 'string' && route.name === 'trip') load(slug)
})
onMounted(() => window.addEventListener('resize', resizeHandler))
onUnmounted(() => {
  window.removeEventListener('resize', resizeHandler)
  chart.value?.dispose()
})
function hideImg(e: Event) {
  (e.target as HTMLImageElement).style.visibility = 'hidden' // 相册文件被移除等 404 场景不显示破图（#23）
}
</script>

<template>
  <div>
    <DisplayNav active="list" />
    <main v-if="trip" class="wrap page-pad">
      <router-link class="back-map" to="/">← 回到地图</router-link>

      <section class="trip-hero">
        <div class="ph">
          <img v-if="cover" :src="photoUrl(cover, 'full')" :alt="trip.title" @error="hideImg" />
          <div v-else class="ph-empty">🏔️</div>
        </div>
        <div class="veil2"></div>
        <div class="body">
          <div class="meta">
            <span>{{ dateRange(trip.start_date, trip.end_date) }}</span><span>·</span>
            <span>{{ routeText || '未记录路线' }}</span><span v-if="trip.members.length">·</span>
            <span v-if="trip.members.length">{{ trip.members.map(memberLabel).join(' ') }}</span>
          </div>
          <h1>{{ trip.title }}</h1>
          <div class="tags">
            <span v-for="(tag, i) in trip.tags" :key="tag.id" class="tag" :class="{ hot: i === 0 }">{{ tag.name }}</span>
          </div>
        </div>
      </section>

      <div class="trip-layout">
        <article class="article">
          <!-- eslint-disable-next-line vue/no-v-html — 已过 DOMPurify 白名单 + 图片本域校验 -->
          <div v-html="safeContent"></div>

          <div v-for="g in trip.gallery.filter((x) => x.count)" :key="g.album_dir" class="gallery-attr">
            <div class="g-head">
              <h3>{{ g.attraction }}</h3>
              <span>{{ g.album_dir }} · {{ g.count }} 张</span>
            </div>
            <div class="g-grid">
              <div
                v-for="p in g.photos"
                :key="p"
                class="ph"
                role="button"
                tabindex="0"
                @click="lightbox.open(p)"
                @keydown.enter="lightbox.open(p)"
              >
                <img :src="photoUrl(p, 'thumb')" :alt="g.attraction" loading="lazy" @error="hideImg" />
              </div>
            </div>
          </div>
        </article>

        <aside class="side">
          <div class="side-card">
            <h4>这次旅行</h4>
            <div class="kv"><span class="k">日期</span><span class="v">{{ dateRange(trip.start_date, trip.end_date) }}</span></div>
            <div class="kv"><span class="k">天数</span><span class="v">{{ trip.days_count }} 天</span></div>
            <div class="kv"><span class="k">路线</span><span class="v">{{ routeText || '—' }}</span></div>
            <div class="kv">
              <span class="k">同行</span>
              <span class="v">{{ trip.members.map(memberLabel).join(' · ') || '—' }}</span>
            </div>
            <div class="kv">
              <span class="k">照片</span>
              <span class="v">{{ trip.photo_count }} 张 · {{ trip.gallery.filter((x) => x.count).length }} 个相册目录</span>
            </div>
          </div>

          <div v-if="trip.attractions.some((a) => a.resolved_lng !== null) || trip.cities.some((c) => c.lng !== null)" class="side-card">
            <h4>行程地图</h4>
            <div class="mini-map-frame"><div ref="miniMapEl" style="height: 260px"></div></div>
          </div>

          <div v-if="trip.trip_days.length" class="side-card days-list">
            <h4>按天行程</h4>
            <div v-for="d in trip.trip_days" :key="d.day_index" class="day">
              <b>D{{ d.day_index }}</b><span>{{ d.title || '—' }}</span><span class="dt">{{ mdDate(d.date) }}</span>
            </div>
          </div>
        </aside>
      </div>

      <nav v-if="trip.prev || trip.next" class="pn">
        <router-link v-if="trip.prev" :to="`/trip/${trip.prev.slug}`">
          <span class="lab">← 上一篇</span>
          <div class="t">{{ trip.prev.title }}</div>
        </router-link>
        <span v-else></span>
        <router-link v-if="trip.next" class="next" :to="`/trip/${trip.next.slug}`">
          <span class="lab">下一篇 →</span>
          <div class="t">{{ trip.next.title }}</div>
        </router-link>
      </nav>
    </main>

    <main v-else-if="notFound" class="wrap page-pad">
      <div class="empty">
        <div class="big">🗺</div>
        <p>这篇游记不存在或尚未发布。<router-link to="/">回到地图 →</router-link></p>
      </div>
    </main>
    <main v-else-if="loadError" class="wrap page-pad">
      <div class="load-error">
        <div class="big">📡</div>
        <p>游记加载失败——网络或服务暂时不可用。</p>
        <button class="retry" @click="load(String(route.params.slug))">重 试</button>
      </div>
    </main>
    <main v-else class="wrap page-pad">
      <div class="loading-dots"><i></i><i></i><i></i></div>
    </main>
  </div>
</template>
