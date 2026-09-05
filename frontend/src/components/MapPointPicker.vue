<script setup lang="ts">
/** 小地图选点：点一下地图落点，用于景点的精确定位（不精调则跟随城市中心）。 */
import * as echarts from 'echarts'
import { nextTick, ref, shallowRef, watch } from 'vue'

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

const mapEl = ref<HTMLDivElement>()
const chart = shallowRef<echarts.ECharts>()
const picked = ref<{ lng: number; lat: number } | null>(null)

async function init() {
  await nextTick()
  if (!echarts.getMap('china')) {
    const geo = await fetch('/china.json').then((r) => r.json())
    echarts.registerMap('china', geo)
  }
  if (!mapEl.value) return
  chart.value?.dispose()
  chart.value = echarts.init(mapEl.value)
  picked.value = props.lng !== null && props.lat !== null ? { lng: props.lng, lat: props.lat } : null
  render()

  chart.value.getZr().on('click', (e: { offsetX: number; offsetY: number }) => {
    const coord = chart.value!.convertFromPixel({ geoIndex: 0 }, [e.offsetX, e.offsetY]) as number[]
    if (!coord || Number.isNaN(coord[0])) return
    picked.value = { lng: Math.round(coord[0] * 10000) / 10000, lat: Math.round(coord[1] * 10000) / 10000 }
    render()
  })
}

function render() {
  if (!chart.value) return
  chart.value.setOption({
    geo: {
      map: 'china',
      roam: true,
      scaleLimit: { min: 1, max: 30 },
      center: picked.value ? [picked.value.lng, picked.value.lat] : [110, 33],
      zoom: picked.value ? 6 : 1.2,
      itemStyle: { areaColor: '#EDE9E1', borderColor: '#FAF8F4' },
      emphasis: { label: { show: false }, itemStyle: { areaColor: '#F6E3D9' } },
      select: { disabled: true },
    },
    series: picked.value
      ? [
          {
            type: 'scatter',
            coordinateSystem: 'geo',
            symbolSize: 14,
            itemStyle: { color: '#E8683A', borderColor: '#fff', borderWidth: 2 },
            label: {
              show: true,
              position: 'top',
              formatter: `${picked.value.lng}, ${picked.value.lat}`,
              fontSize: 11,
              fontWeight: 600,
              color: '#3E4C57',
              backgroundColor: 'rgba(255,255,255,.9)',
              borderRadius: 4,
              padding: [2, 6],
            },
            data: [{ value: [picked.value.lng, picked.value.lat] }],
          },
        ]
      : [],
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
        <template v-else>尚未选点</template>
      </p>
    </div>
    <template #footer>
      <el-button v-if="picked" @click="clearPick">清除选点</el-button>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :disabled="!picked" @click="confirm">确定</el-button>
    </template>
  </el-dialog>
</template>
