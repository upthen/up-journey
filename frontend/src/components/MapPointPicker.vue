<script setup lang="ts">
/** 小地图选点：点一下地图落点，用于景点的精确定位（不精调则跟随城市中心）。
 *  地名标注全部来自离线数据：省份名出自 china.json，城市点出自后端城市字典（含中心坐标）。 */
import * as echarts from 'echarts'
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

// 省名只在低倍全览时显示；城市点放大后浮现，避免几百个城市名糊成一片。
const PROVINCE_MAX_ZOOM = 3
const CITY_MIN_ZOOM = 2.2
const DEFAULT_VIEW = { center: [110, 33] as number[], zoom: 1.2 }

const mapEl = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()
const picked = ref<{ lng: number; lat: number } | null>(null)
const loadError = ref(false)
const cities = ref<City[]>([])
// 标注显隐只在跨越缩放阈值时切换一次，roam 过程中不反复 setOption。
let labelMode = ''
let cityCache: City[] | null = null

onUnmounted(() => {
  chart.value?.dispose()
  chart.value = undefined
})

async function init() {
  await nextTick()
  try {
    if (!echarts.getMap('china')) {
      const res = await fetch('/china.json')
      if (!res.ok) throw new Error(`china.json ${res.status}`)
      echarts.registerMap('china', await res.json())
    }
  } catch {
    loadError.value = true
    return
  }
  if (!mapEl.value) return
  chart.value?.dispose()
  chart.value = echarts.init(mapEl.value)
  picked.value = props.lng !== null && props.lat !== null ? { lng: props.lng, lat: props.lat } : null
  labelMode = ''
  render()

  chart.value.getZr().on('click', (e: { offsetX: number; offsetY: number }) => {
    const coord = chart.value!.convertFromPixel({ geoIndex: 0 }, [e.offsetX, e.offsetY]) as number[]
    if (!coord || Number.isNaN(coord[0])) return
    picked.value = { lng: Math.round(coord[0] * 10000) / 10000, lat: Math.round(coord[1] * 10000) / 10000 }
    render()
  })
  // 拖拽/缩放不重建视图，只按需切换标注显隐。
  chart.value.on('georoam', () => applyLabels())

  loadCities()
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

function currentView(): { center: number[]; zoom: number } {
  const geo = (chart.value?.getOption() as { geo?: { center?: number[]; zoom?: number }[] } | undefined)?.geo?.[0]
  if (geo?.center && geo?.zoom) return { center: geo.center, zoom: geo.zoom }
  return picked.value
    ? { center: [picked.value.lng, picked.value.lat], zoom: 6 }
    : { ...DEFAULT_VIEW }
}

function applyLabels() {
  if (!chart.value || !cities.value.length) return
  const { zoom } = currentView()
  const mode = `${zoom < PROVINCE_MAX_ZOOM ? 'p' : ''}${zoom >= CITY_MIN_ZOOM ? 'c' : ''}`
  if (mode === labelMode) return
  labelMode = mode
  chart.value.setOption({
    geo: { label: { show: zoom < PROVINCE_MAX_ZOOM } },
    series: [citySeries(zoom)],
  })
}

function citySeries(zoom: number) {
  const showAll = zoom >= CITY_MIN_ZOOM
  const data = cities.value
    .map((c) => {
      const hint = !!props.hintCity && (props.hintCity === c.name || props.hintCity.startsWith(c.name))
      return { value: [c.lng, c.lat] as number[], name: c.name, hint }
    })
    .filter((d) => showAll || d.hint)
    .map((d) => ({
      value: d.value,
      name: d.name,
      symbolSize: d.hint ? 9 : 5,
      ...(d.hint
        ? {
            itemStyle: { color: '#E8683A', borderColor: '#fff', borderWidth: 1 },
            label: { color: '#C2502A', fontWeight: 700 as const, fontSize: 11 },
          }
        : {}),
    }))
  return {
    type: 'scatter',
    coordinateSystem: 'geo',
    silent: true,
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
    data,
  }
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
        show: zoom < PROVINCE_MAX_ZOOM,
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
        放大到目的地后直接点地图落点{{ hintCity ? `（建议定位：${hintCity}）` : '' }}；不选则跟随城市中心。
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
