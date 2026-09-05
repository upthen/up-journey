<script setup lang="ts">
/** 小地图选点：下钻式选点——点击省份下钻、点击城市居中、在已下钻的省域内点击落点。
 *  地名标注全部来自离线数据：省份名出自 china.json，城市点出自后端城市字典（含中心坐标）。 */
import * as echarts from 'echarts'
import type { ECElementEvent } from 'echarts'
import { nextTick, onUnmounted, ref, shallowRef, watch } from 'vue'

import { api } from '@/api'
import type { City } from '@/types'

const props = defineProps<{
  modelValue: boolean
  lng: number | null
  lat: number | null
  hintCity?: string
}>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'picked', coord: { lng: number; lat: number }): void
}>()

// 全国视角：省名只在低倍全览时显示，城市点放大后浮现；下钻到省后城市点始终显示。
const PROVINCE_MAX_ZOOM = 3
const CITY_MIN_ZOOM = 2.2
const CITY_ZOOM = 12
const NATION_VIEW = { center: [110, 33] as number[], zoom: 1.2 }
// china.json 的经纬度范围，用于按省面积估算下钻缩放级别
const CHINA_SPAN = { lng: 135 - 73.5, lat: 53.6 - 18 }

const mapEl = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()
const picked = ref<{ lng: number; lat: number } | null>(null)
const loadError = ref(false)
const cities = ref<City[]>([])
const drillProvince = ref<string | null>(null)
const drillCityName = ref<string | null>(null)
// 省份中心与适配缩放（打开对话框时从 china.json 一次性算好）
const provinceMeta = ref(new Map<string, { center: number[]; zoom: number }>())
// 标注显隐只在跨越阈值/切换层级时重建，roam 过程中不反复 setOption；
// georoam 回调里同步 setOption 会打断 ECharts 的 updateTransform 管线，须挪到下一个宏任务。
let labelMode = ''
let labelTimer: number | null = null
let cityCache: City[] | null = null

function scheduleLabels() {
  if (labelTimer !== null) return
  labelTimer = window.setTimeout(() => {
    labelTimer = null
    applyLabels()
  }, 0)
}

function currentMode(zoom: number): string {
  if (drillProvince.value) return 'd'
  return `${zoom < PROVINCE_MAX_ZOOM ? 'p' : ''}${zoom >= CITY_MIN_ZOOM ? 'c' : ''}`
}

function applyLabels() {
  if (!chart.value) return
  const { zoom } = currentView()
  const mode = currentMode(zoom)
  if (mode === labelMode) return
  labelMode = mode
  chart.value.setOption({
    geo: { label: { show: !drillProvince.value && zoom < PROVINCE_MAX_ZOOM } },
    series: [citySeries(zoom)],
  })
}

/** 下钻/返回：一次性设置视图层级（中心、缩放、省名标注、城市点集合）。 */
function applyView(center: number[], zoom: number) {
  if (!chart.value) return
  labelMode = currentMode(zoom)
  chart.value.setOption({
    geo: { center, zoom, label: { show: !drillProvince.value && zoom < PROVINCE_MAX_ZOOM } },
    series: [citySeries(zoom)],
  })
}

function drillToProvince(name: string) {
  const meta = provinceMeta.value.get(name)
  if (!meta) return
  drillProvince.value = name
  drillCityName.value = null
  applyView(meta.center, meta.zoom)
}

function drillToCity(city: City) {
  drillProvince.value = city.province_name
  drillCityName.value = city.name
  applyView([city.lng, city.lat], CITY_ZOOM)
}

function backToNation() {
  drillProvince.value = null
  drillCityName.value = null
  applyView([...NATION_VIEW.center], NATION_VIEW.zoom)
}

function pickAt(offsetX: number, offsetY: number) {
  const coord = chart.value!.convertFromPixel({ geoIndex: 0 }, [offsetX, offsetY]) as number[]
  if (!coord || Number.isNaN(coord[0])) return
  picked.value = { lng: Math.round(coord[0] * 10000) / 10000, lat: Math.round(coord[1] * 10000) / 10000 }
  render()
}

function citySeries(zoom: number) {
  // 下钻到省后只显示该省城市 + 建议定位城市，其余情况放大后显示全部
  const inScope = (c: City) => {
    if (drillProvince.value) return c.province_name === drillProvince.value || isHint(c)
    return zoom >= CITY_MIN_ZOOM || isHint(c)
  }
  const data = cities.value
    .filter(inScope)
    .map((c) => {
      const hint = isHint(c)
      return {
        value: [c.lng, c.lat] as number[],
        name: c.name,
        city: c,
        symbolSize: hint ? 9 : 5,
        ...(hint
          ? {
              itemStyle: { color: '#E8683A', borderColor: '#fff', borderWidth: 1 },
              label: { color: '#C2502A', fontWeight: 700 as const, fontSize: 11 },
            }
          : {}),
      }
    })
  return {
    type: 'scatter',
    coordinateSystem: 'geo',
    itemStyle: { color: '#B9987A' },
    label: {
      show: true,
      position: 'right',
      formatter: '{b}',
      fontSize: 10,
      color: '#7A6A58',
      textBorderColor: '#FAF8F4',
      textBorderWidth: 2,
    },
    labelLayout: { hideOverlap: true },
    data,
  }
}

function isHint(c: City): boolean {
  return !!props.hintCity && (props.hintCity === c.name || props.hintCity.startsWith(c.name))
}

function currentView(): { center: number[]; zoom: number } {
  const geo = (chart.value?.getOption() as { geo?: { center?: number[]; zoom?: number }[] } | undefined)?.geo?.[0]
  if (geo?.center && geo?.zoom) return { center: geo.center, zoom: geo.zoom }
  return picked.value
    ? { center: [picked.value.lng, picked.value.lat], zoom: 6 }
    : { center: [...NATION_VIEW.center], zoom: NATION_VIEW.zoom }
}

/** 从 china.json 提取每个省的包围盒 → 中心点与铺满视口的缩放级别。 */
function buildProvinceMeta(geojson: { features: { properties?: { name?: string }; geometry?: { type: string; coordinates: unknown } }[] }) {
  const meta = new Map<string, { center: number[]; zoom: number }>()
  for (const f of geojson.features) {
    const name = f.properties?.name
    if (!name || meta.has(name)) continue
    let minLng = Infinity
    let maxLng = -Infinity
    let minLat = Infinity
    let maxLat = -Infinity
    const walk = (coords: unknown) => {
      if (!Array.isArray(coords)) return
      if (typeof coords[0] === 'number') {
        const [lng, lat] = coords as number[]
        if (lng < minLng) minLng = lng
        if (lng > maxLng) maxLng = lng
        if (lat < minLat) minLat = lat
        if (lat > maxLat) maxLat = lat
        return
      }
      coords.forEach(walk)
    }
    walk(f.geometry?.coordinates)
    if (minLng === Infinity) continue
    const spanLng = maxLng - minLng
    const spanLat = maxLat - minLat
    const zoom = Math.min(25, Math.max(3, 1.2 * Math.max(CHINA_SPAN.lng / spanLng, CHINA_SPAN.lat / spanLat) * 0.9))
    meta.set(name, { center: [(minLng + maxLng) / 2, (minLat + maxLat) / 2], zoom })
  }
  return meta
}

async function loadCities() {
  if (cityCache) {
    cities.value = cityCache
  } else {
    try {
      cityCache = await api.admin.cities({ level: 2 })
      cities.value = cityCache
    } catch {
      return // 字典拉取失败不阻塞选点，只是没有城市标注
    }
  }
  labelMode = ''
  applyLabels()
}

onUnmounted(() => {
  if (labelTimer !== null) window.clearTimeout(labelTimer)
  chart.value?.dispose()
  chart.value = undefined
})

async function init() {
  await nextTick()
  let raw: object | null = null
  try {
    if (!echarts.getMap('china')) {
      const res = await fetch('/china.json')
      if (!res.ok) throw new Error(`china.json ${res.status}`)
      raw = await res.json()
      echarts.registerMap('china', raw as never)
    }
  } catch {
    loadError.value = true
    return
  }
  if (!mapEl.value) return
  if (labelTimer !== null) window.clearTimeout(labelTimer)
  chart.value?.dispose()
  chart.value = echarts.init(mapEl.value)
  picked.value = props.lng !== null && props.lat !== null ? { lng: props.lng, lat: props.lat } : null
  drillProvince.value = null
  drillCityName.value = null
  labelMode = ''
  if (raw) provinceMeta.value = buildProvinceMeta(raw as Parameters<typeof buildProvinceMeta>[0])
  render()

  // 下钻式交互：城市点下钻 → 省；省域点击 → 已下钻省则落点，未下钻省则下钻
  chart.value.on('click', (e: ECElementEvent) => {
    if (e.componentType === 'series') {
      const city = (e.data as { city?: City } | undefined)?.city
      if (e.seriesIndex === 0 && city) drillToCity(city)
      return // 点击已选点标记：忽略
    }
    if (e.componentType === 'geo' && e.name) {
      const ev = e.event as { offsetX: number; offsetY: number }
      if (drillProvince.value === e.name) pickAt(ev.offsetX, ev.offsetY)
      else drillToProvince(e.name)
    }
  })
  // 手动拖拽/缩放不重建视图，只按需切换标注显隐
  chart.value.on('georoam', () => scheduleLabels())

  loadCities()
}

function render() {
  if (!chart.value) return
  const { center, zoom } = currentView()
  chart.value.setOption({
    geo: {
      map: 'china',
      roam: true,
      scaleLimit: { min: 1, max: 30 },
      center,
      zoom,
      itemStyle: { areaColor: '#EDE9E1', borderColor: '#FAF8F4' },
      label: {
        show: !drillProvince.value && zoom < PROVINCE_MAX_ZOOM,
        color: '#A6957F',
        fontSize: 11,
      },
      emphasis: { label: { show: false }, itemStyle: { areaColor: '#F6E3D9' } },
      select: { disabled: true },
    },
    series: [
      citySeries(zoom),
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        symbolSize: 14,
        itemStyle: { color: '#E8683A', borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          position: 'top',
          formatter: picked.value ? `${picked.value.lng}, ${picked.value.lat}` : '',
          fontSize: 11,
          fontWeight: 600,
          color: '#3E4C57',
          backgroundColor: 'rgba(255,255,255,.9)',
          borderRadius: 4,
          padding: [2, 6],
        },
        data: picked.value ? [{ value: [picked.value.lng, picked.value.lat] }] : [],
      },
    ],
  })
}

function clearPick() {
  picked.value = null
  render()
}

function confirm() {
  if (picked.value) emit('picked', picked.value)
  emit('update:modelValue', false)
}

watch(
  () => props.modelValue,
  (v) => {
    if (v) init()
  },
)
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="🗺 地图选点"
    width="min(640px, calc(100vw - 24px))"
    top="6vh"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="point-picker">
      <p class="tip">
        点击省份下钻，点击城市居中，在省域内点击落点{{ hintCity ? `（建议定位：${hintCity}）` : '' }}；不选则跟随城市中心。
      </p>
      <p v-if="drillProvince" class="crumbs">
        📍 当前：{{ drillProvince }}<template v-if="drillCityName"> · {{ drillCityName }}</template>
        <el-button link size="small" @click="backToNation">返回全国</el-button>
      </p>
      <div ref="mapEl" class="map"></div>
      <p class="vals">
        <template v-if="picked">已选：{{ picked.lng }}, {{ picked.lat }}</template>
        <template v-else><span v-if="loadError">⚠️ 地图加载失败，请稍后重试</span><span v-else>尚未选点</span></template>
      </p>
    </div>
    <template #footer>
      <el-button v-if="picked" @click="clearPick">清除选点</el-button>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :disabled="!picked" @click="confirm">确定</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.crumbs {
  margin: -6px 0 8px;
  font-size: 12px;
  color: #7a6a58;
}
.crumbs .el-button {
  margin-left: 8px;
}
</style>
