<script setup lang="ts">
/**
 * 第一幕：全屏地图即首页（v4 流程式）。
 * 帷幕 → 地图（景点涟漪点 + 名字·年份标签 + 路线 + 年份坞筛选 + 统计旗）→ 地点故事面板。
 */
import * as echarts from 'echarts'
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue'

import { api, photoUrl } from '@/api'
import DisplayNav from '@/components/DisplayNav.vue'
import type { Footprints, Spot, Stats } from '@/types'

/* ---------- ADR-0001 设计 Token：地图配色 ---------- */
const T = {
  visited3: '#E8683A',
  visited2: '#F09A72',
  visited1: '#F7C7AF',
  none: '#EDE9E1',
  border: '#FAF8F4',
  cityDot: '#14586B',
  route: '#E8683A',
  label: '#3E4C57',
  legend: '#98A1AB',
  emphasis: '#F6E3D9',
}

const stats = ref<Stats | null>(null)
const footprints = ref<Footprints | null>(null)
const currentYear = ref<'all' | number>('all')
const veilGone = ref(false)
const hintGone = ref(true)
const openSpot = ref<Spot | null>(null)

const mapEl = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()
let resizeHandler = () => chart.value?.resize()

const kicker = computed(() => {
  const years = footprints.value?.years ?? []
  if (!years.length) return 'Up Journey'
  return `Up Journey · ${years[years.length - 1]} — ${years[0]}`
})
const headlineYears = computed(() => stats.value?.years ?? 0)
const headlineProvinces = computed(() => stats.value?.provinces ?? 0)

/* ---------- 地图 ---------- */
function spotData(year: 'all' | number) {
  const spots = footprints.value?.spots ?? []
  return spots
    .filter((s) => year === 'all' || s.year === year)
    .map((s) => ({ name: s.name, value: [s.lng, s.lat, s.photo_count], spot: s }))
}
function lineData(year: 'all' | number) {
  const out: { coords: [number, number][] }[] = []
  for (const r of (footprints.value?.routes ?? []).filter((r) => year === 'all' || r.year === year)) {
    for (let i = 0; i < r.coords.length - 1; i++) {
      out.push({ coords: [r.coords[i], r.coords[i + 1]] as [number, number][] })
    }
  }
  return out
}
function provinceData() {
  return Object.entries(footprints.value?.provinces ?? {}).map(([name, count]) => ({
    name,
    value: Math.min(count, 3), // 三档色阶封顶
  }))
}

function buildOption(): echarts.EChartsOption {
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,.96)',
      borderColor: '#ECE8E1',
      textStyle: { color: '#1F2A33', fontSize: 12.5 },
      formatter: (p: unknown) => {
        const item = (Array.isArray(p) ? p[0] : p) as
          | { seriesType?: string; name?: string; data?: { spot?: Spot } }
          | undefined
        const d = item?.data
        if (item?.seriesType === 'effectScatter' && d?.spot) {
          const s = d.spot
          return `<b>${s.name}</b><br/>${s.year} 年 · ${s.city} · ${s.photo_count} 张照片<br/><span style="color:#98A1AB">点击查看这里的故事</span>`
        }
        return String(item?.name ?? '')
      },
    },
    visualMap: {
      type: 'piecewise',
      show: false,
      seriesIndex: 0,
      pieces: [
        { min: 3, color: T.visited3 },
        { min: 2, max: 2, color: T.visited2 },
        { min: 1, max: 1, color: T.visited1 },
      ],
      outOfRange: { color: T.none },
    },
    geo: {
      map: 'china',
      roam: true,
      scaleLimit: { min: 1, max: 14 },
      center: [110, 33],
      zoom: 1.15,
      itemStyle: { borderColor: T.border, borderWidth: 1.2 },
      emphasis: { label: { color: T.label }, itemStyle: { areaColor: T.emphasis } },
      select: { disabled: true },
    },
    series: [
      {
        name: '足迹',
        type: 'map',
        map: 'china',
        geoIndex: 0,
        selectedMode: false,
        data: provinceData(),
      },
      {
        name: '景点',
        type: 'effectScatter',
        coordinateSystem: 'geo',
        symbolSize: (v: number[]) => 9 + Math.min(v[2] ?? 0, 60) / 12,
        itemStyle: { color: T.cityDot, borderColor: '#fff', borderWidth: 2 },
        rippleEffect: { scale: 3, brushType: 'stroke' },
        label: {
          show: true,
          position: 'top',
          distance: 7,
          formatter: (p: { data?: unknown }) => {
            const d = p.data as { spot?: Spot } | null | undefined
            return d?.spot ? `${d.spot.name} · ${d.spot.year}` : ''
          },
          color: '#3E4C57',
          fontSize: 11,
          fontWeight: 600,
          backgroundColor: 'rgba(255,255,255,.85)',
          borderRadius: 6,
          padding: [2, 7],
          shadowColor: 'rgba(31,42,51,.10)',
          shadowBlur: 6,
        },
        labelLayout: { hideOverlap: true },
        cursor: 'pointer',
        data: spotData('all'),
      },
      {
        name: '路线',
        type: 'lines',
        coordinateSystem: 'geo',
        effect: { show: true, period: 5, trailLength: 0.5, symbol: 'arrow', symbolSize: 5, color: T.route },
        lineStyle: { color: T.route, width: 1.8, opacity: 0.75, curveness: 0.25 },
        data: lineData('all'),
      },
    ],
  }
}

function applyYearFilter() {
  chart.value?.setOption({
    series: [{}, { data: spotData(currentYear.value) }, { data: lineData(currentYear.value) }],
  })
}

function selectYear(y: 'all' | number) {
  currentYear.value = y
  applyYearFilter()
}

function openPanel(spot: Spot) {
  openSpot.value = spot
  hintGone.value = true
}
function closePanel() {
  openSpot.value = null
}

/** 帷幕收起 → 地图探索提示停留 7 秒后淡出。 */
function enterMap() {
  veilGone.value = true
  hintGone.value = false
  window.setTimeout(() => {
    hintGone.value = true
  }, 7000)
}

/* ---------- 生命周期 ---------- */
onMounted(async () => {
  ;[stats.value, footprints.value] = await Promise.all([api.stats(), api.footprints()])

  // 中国 GeoJSON 随包离线（public/china.json），不依赖任何在线瓦片
  const geo = await fetch('/china.json').then((r) => r.json())
  echarts.registerMap('china', geo)
  if (!mapEl.value) return
  chart.value = echarts.init(mapEl.value, null, { renderer: 'canvas' })
  chart.value.setOption(buildOption())
  if (import.meta.env.DEV) (window as unknown as Record<string, unknown>).__ujChart = chart.value // 验收/调试用
  chart.value.on('click', (params) => {
    if (params.seriesType === 'effectScatter') {
      const d = params.data as { spot?: Spot }
      if (d?.spot) openPanel(d.spot)
    }
  })
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeHandler)
  chart.value?.dispose()
})
</script>

<template>
  <div>
    <DisplayNav active="map" />

    <!-- 第 0 幕：开场帷幕 -->
    <div class="veil" :class="{ gone: veilGone }">
      <div class="inner">
        <p class="kicker">{{ kicker }}</p>
        <h1 v-if="headlineYears > 0">
          {{ headlineYears }} 年，{{ headlineProvinces }} 个省，<br />都从一张<em>地图</em>说起
        </h1>
        <h1 v-else>把每一段家庭旅程，<br />钉在这张<em>地图</em>上</h1>
        <p>不用往下翻，也不用找菜单——每个去过的地方都在地图上，点开它，就是那次旅行的故事。</p>
        <button class="go" @click="enterMap">展开地图 ↓</button>
      </div>
    </div>

    <!-- 第一幕：全屏地图 -->
    <div class="map-stage"><div ref="mapEl"></div></div>

    <!-- 统计浮签 -->
    <aside v-if="stats" class="stats-flag" aria-label="足迹统计">
      <span class="t">这个家庭的 {{ headlineYears > 0 ? headlineYears + ' 年' : '足迹' }}</span>
      <span class="row"><span class="v">{{ stats.provinces }}</span><span class="k">省 / 行政区</span></span>
      <span class="row"><span class="v">{{ stats.cities }}</span><span class="k">座城市 · {{ stats.attractions }} 处景点</span></span>
      <span class="row"><span class="v">{{ stats.trips }}</span><span class="k">次出发 · {{ stats.days }} 天在路上</span></span>
    </aside>

    <!-- 探索路径指示 -->
    <div class="stage-chip"><b>01</b> 地图 <span class="sep"></span> 找一个想看的地方 <span class="sep"></span> <span style="color: var(--gray)">02 地点 → 03 游记</span></div>

    <!-- 图例 -->
    <div class="legend-chip">
      <span><i :style="{ background: T.visited3 }"></i>省份越深去得越多</span>
      <span><i :style="{ background: T.cityDot }"></i>景点 · 点击看故事</span>
    </div>

    <!-- 年份坞 -->
    <div v-if="footprints?.years.length" class="year-dock">
      <button :class="{ all: true, on: currentYear === 'all' }" @click="selectYear('all')">全部 {{ headlineYears > 0 ? headlineYears + ' 年' : '足迹' }}</button>
      <button v-for="y in footprints.years" :key="y" :class="{ on: currentYear === y }" @click="selectYear(y)">
        {{ y }}
      </button>
    </div>

    <!-- 探索提示 -->
    <div class="hint" :class="{ gone: hintGone }">👆 点一点地图上的景点标签——每个地点背后，都是一次旅行</div>

    <!-- 第二幕：地点故事面板 -->
    <aside v-if="openSpot" class="panel open">
      <div class="head">
        <div v-if="openSpot.photos.length" class="ph">
          <img :src="photoUrl(openSpot.photos[0], 'full')" :alt="openSpot.name" />
        </div>
        <div v-else class="ph ph-placeholder"></div>
        <button class="close" aria-label="关闭" @click="closePanel">✕</button>
        <span class="year-tag">{{ openSpot.year }} 年</span>
      </div>
      <div class="body">
        <p class="stage">02 · 在这里发生了什么</p>
        <h2>{{ openSpot.name }}</h2>
        <p class="where">{{ openSpot.city }} · {{ openSpot.year }} 年到访</p>
        <p v-if="openSpot.note" class="blurb">{{ openSpot.note }}</p>
        <div v-if="openSpot.photos.length" class="thumbs">
          <div v-for="p in openSpot.photos.slice(0, 3)" :key="p" class="ph">
            <img :src="photoUrl(p, 'thumb')" alt="" loading="lazy" />
          </div>
        </div>
        <div class="related">
          <p class="t">属于这次旅行</p>
          <router-link :to="`/trip/${openSpot.trip_slug}`">《{{ openSpot.trip_title }}》<span class="arr">→</span></router-link>
          <router-link :to="`/list?year=${openSpot.year}`">这一年还有别的行程<span class="arr">→</span></router-link>
        </div>
      </div>
      <div class="foot">
        <router-link class="cta" :to="`/trip/${openSpot.trip_slug}`">读完整游记 →</router-link>
      </div>
    </aside>
  </div>
</template>
