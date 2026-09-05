<script setup lang="ts">
/** 旅行录入/编辑（user stories 1–14 的管理端表面）。

结构对齐 docs/prototype/admin.html：基本信息 → 封面 → 城市与路线 →
景点与相册目录 → 按天行程 → 成员与标签 → 游记正文（相册插图）。
*/
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, onUnmounted, reactive, ref, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, photoUrl } from '@/api'
import AlbumBrowser from '@/components/AlbumBrowser.vue'
import MapPointPicker from '@/components/MapPointPicker.vue'
import { useMetaStore } from '@/stores/meta'
import type { AttractionInput, City, TripCityInput, TripDetail, TripInput } from '@/types'
import { albumToolbarKeys, registerAlbumImageMenu, setAlbumPickerOpener } from '@/utils/editor'

let keySeq = 0
const nextKey = () => ++keySeq

const route = useRoute()
const router = useRouter()
const meta = useMetaStore()

const tripId = computed(() => {
  const id = Number(route.params.id)
  return Number.isInteger(id) && id > 0 ? id : null
})

/* ---------- 字典 ---------- */
const cities = ref<City[]>([])
const cityByCode = computed(() => new Map(cities.value.map((c) => [c.code, c])))
const provinceOptions = computed(() => {
  const provinces = cities.value.filter((c) => c.level === 1)
  return provinces.map((p) => ({
    value: p.code,
    label: p.name,
    children: cities.value
      .filter((c) => c.level === 2 && c.province_code === p.code)
      .map((c) => ({ value: c.code, label: c.name })),
  }))
})

/* ---------- 表单 ---------- */
interface CityRow {
  key: number
  city_code: string | null
  city_name: string | null
  lng: number | null
  lat: number | null
}
interface AttrRow {
  key: number
  name: string
  city_code: string | null
  album_rel_path: string | null
  lng: number | null
  lat: number | null
  note: string
}
interface DayRow {
  key: number
  date: string
  title: string
  note: string
}

const form = reactive({
  title: '',
  slug: '',
  dates: [] as string[],
  status: 'draft' as 'draft' | 'published',
  isForeign: false,
  country: '',
  summary: '',
  content: '',
  cover_photo: null as string | null,
  cities: [] as CityRow[],
  attractions: [] as AttrRow[],
  days: [] as DayRow[],
  member_ids: [] as number[],
  tag_ids: [] as number[],
})

const loading = ref(false)
const coverCandidates = ref<{ dir: string; photos: string[] }[]>([])

/* ---------- 本地草稿（#12：会话过期/误关页面时输入不丢） ---------- */
// 每次表单变化防抖写入 localStorage；进入编辑页时若草稿与已加载数据不同，
// 弹窗询问恢复。401 整页跳登录不影响草稿，重登回来即可恢复。
const draftKey = computed(() => `uj-trip-draft:${tripId.value ?? 'new'}`)
const restoring = ref(true)
let draftTimer: number | undefined

function draftPayload() {
  const { title, slug, dates, status, isForeign, country, summary, content, cover_photo, cities, attractions, days, member_ids, tag_ids } = form
  return { title, slug, dates, status, isForeign, country, summary, content, cover_photo, cities, attractions, days, member_ids, tag_ids }
}

// 行内 key 是渲染用的自增序号，比较内容时剔除
function formSig() {
  const d = draftPayload()
  const strip = (rows: { key: number }[]) => rows.map(({ key, ...rest }) => rest)
  return JSON.stringify({ ...d, cities: strip(d.cities), attractions: strip(d.attractions), days: strip(d.days) })
}

function savedSig(data: ReturnType<typeof draftPayload>) {
  const strip = (rows: { key: number }[]) => rows.map(({ key, ...rest }) => rest)
  return JSON.stringify({ ...data, cities: strip(data.cities), attractions: strip(data.attractions), days: strip(data.days) })
}

function writeDraft() {
  if (restoring.value) return
  try {
    localStorage.setItem(draftKey.value, JSON.stringify({ at: Date.now(), data: draftPayload() }))
  } catch {
    /* 隐私模式/存储满：草稿静默降级 */
  }
}

function clearDraft() {
  try {
    localStorage.removeItem(draftKey.value)
  } catch {}
}

watch(form, () => {
  if (restoring.value) return
  window.clearTimeout(draftTimer)
  draftTimer = window.setTimeout(writeDraft, 400)
}, { deep: true })

function flushDraft() {
  if (restoring.value) return
  window.clearTimeout(draftTimer)
  writeDraft()
}
window.addEventListener('beforeunload', flushDraft)
onUnmounted(() => window.removeEventListener('beforeunload', flushDraft))

function applyDraft(data: ReturnType<typeof draftPayload>) {
  form.title = data.title ?? ''
  form.slug = data.slug ?? ''
  form.dates = data.dates ?? []
  form.status = data.status ?? 'draft'
  form.isForeign = data.isForeign ?? false
  form.country = data.country ?? ''
  form.summary = data.summary ?? ''
  form.content = data.content ?? ''
  form.cover_photo = data.cover_photo ?? null
  form.cities = (data.cities ?? []).map((c) => ({ ...c, key: nextKey() }))
  form.attractions = (data.attractions ?? []).map((a) => ({ ...a, key: nextKey() }))
  form.days = (data.days ?? []).map((d) => ({ ...d, key: nextKey() }))
  form.member_ids = data.member_ids ?? []
  form.tag_ids = data.tag_ids ?? []
}

async function maybeRestoreDraft() {
  let saved: { at: number; data: ReturnType<typeof draftPayload> } | null = null
  try {
    saved = JSON.parse(localStorage.getItem(draftKey.value) ?? 'null')
  } catch {
    saved = null
  }
  if (saved?.data && savedSig(saved.data) !== formSig()) {
    const at = new Date(saved.at).toLocaleString()
    try {
      await ElMessageBox.confirm(`检测到未保存的本地草稿（${at}），恢复后当前表单内容将被覆盖。`, '恢复草稿', {
        confirmButtonText: '恢复草稿',
        cancelButtonText: '丢弃草稿',
        type: 'warning',
      })
      applyDraft(saved.data)
    } catch {
      /* 用户选择丢弃 */
    }
  }
  clearDraft()
  restoring.value = false
}

const domesticCities = computed(() => form.cities.filter((c) => c.city_code))

function cityRowLabel(c: CityRow): string {
  if (c.city_code) {
    const city = cityByCode.value.get(c.city_code)
    return city ? `${city.province_name} ${city.name}` : c.city_code
  }
  return c.city_name || '?'
}

/* ---------- 城市与路线 ---------- */
function addDomesticCity(code: string) {
  if (form.cities.some((c) => c.city_code === code)) return
  form.cities.push({ key: nextKey(), city_code: code, city_name: null, lng: null, lat: null })
}
function moveCity(i: number, delta: -1 | 1) {
  const j = i + delta
  if (j < 0 || j >= form.cities.length) return
  ;[form.cities[i], form.cities[j]] = [form.cities[j], form.cities[i]]
}
function removeCity(i: number) {
  const row = form.cities[i]
  form.cities.splice(i, 1)
  form.attractions.forEach((a) => {
    if (a.city_code === row.city_code) a.city_code = null
  })
}

/* 境外城市手填对话框 */
const foreignDialog = ref(false)
const foreignForm = ref({ city_name: '', lng: '' as number | string, lat: '' as number | string })
function addForeignCity() {
  const name = foreignForm.value.city_name.trim()
  if (!name) {
    ElMessage.warning('城市名必填，如 京都')
    return
  }
  const toNum = (v: number | string | '') => (v === '' || v === null ? null : Number(v))
  form.cities.push({
    key: nextKey(),
    city_code: null,
    city_name: name,
    lng: toNum(foreignForm.value.lng),
    lat: toNum(foreignForm.value.lat),
  })
  foreignDialog.value = false
  foreignForm.value = { city_name: '', lng: '', lat: '' }
}

/* ---------- 景点与相册 ---------- */
function addAttraction() {
  form.attractions.push({
    key: nextKey(),
    name: '',
    city_code: domesticCities.value[0]?.city_code ?? null,
    album_rel_path: null,
    lng: null,
    lat: null,
    note: '',
  })
}
const albumDialog = reactive({ visible: false, targetKey: 0 })
function openAlbumPicker(row: AttrRow) {
  albumDialog.targetKey = row.key
  albumDialog.visible = true
}
function onAlbumDirSelected({ path }: { path: string }) {
  const row = form.attractions.find((a) => a.key === albumDialog.targetKey)
  if (row) row.album_rel_path = path || null
  loadCoverCandidates()
}

const pointDialog = reactive({ visible: false, targetKey: 0 })
function openPointPicker(row: AttrRow) {
  pointDialog.targetKey = row.key
  pointDialog.visible = true
}
function onPointPicked({ lng, lat }: { lng: number; lat: number }) {
  const row = form.attractions.find((a) => a.key === pointDialog.targetKey)
  if (row) {
    row.lng = lng
    row.lat = lat
  }
}

/* ---------- 按天行程 ---------- */
function addDay() {
  const last = form.days[form.days.length - 1]
  const base = last?.date ?? form.dates[1] ?? form.dates[0] ?? new Date().toISOString().slice(0, 10)
  const next = new Date(base)
  if (last || form.days.length === 0) next.setDate(next.getDate() + 1)
  form.days.push({ key: nextKey(), date: next.toISOString().slice(0, 10), title: '', note: '' })
}
function fillDaysFromRange() {
  if (form.dates.length !== 2) {
    ElMessage.warning('先选择起止日期')
    return
  }
  form.days = []
  const d = new Date(form.dates[0])
  const end = new Date(form.dates[1])
  while (d <= end) {
    form.days.push({ key: nextKey(), date: d.toISOString().slice(0, 10), title: '', note: '' })
    d.setDate(d.getDate() + 1)
  }
}

/* ---------- 封面候选 ---------- */
async function loadCoverCandidates() {
  const dirs = [...new Set(form.attractions.filter((a) => a.album_rel_path).map((a) => a.album_rel_path!))]
  const results = await Promise.all(
    dirs.map(async (dir) => {
      try {
        const album = await api.admin.album(dir)
        return { dir, photos: album.photos }
      } catch {
        return { dir, photos: [] }
      }
    }),
  )
  coverCandidates.value = results.filter((r) => r.photos.length)
}
function pickCover(path: string) {
  form.cover_photo = form.cover_photo === path ? null : path
}

/* ---------- 富文本 ---------- */
registerAlbumImageMenu()
const editorRef = shallowRef()
const toolbarConfig = {
  insertKeys: { index: 0, keys: albumToolbarKeys },
  // 图片唯一来源是 NAS 相册（相册插图），后端无上传接口——移除内置上传/网络图片与视频入口
  excludeKeys: ['group-image', 'group-video', 'insertImage', 'uploadImage', 'insertVideo', 'uploadVideo'],
}
const editorConfig = { placeholder: '写下游记正文…… 可用「相册插图」从 NAS 相册插图，图片不会重复上传。' }

/* 游记插图选图器（复用 AlbumBrowser，从全相册浏览） */
const insertDialog = ref(false)
setAlbumPickerOpener(() => {
  insertDialog.value = true
})
function onInsertPhotoSelected({ path }: { path: string }) {
  const editor = editorRef.value
  if (!editor) return
  // 选图对话框会夺走编辑器焦点；先恢复最后的光标位置再插入，避免静默失败。
  editor.restoreSelection?.()
  editor.insertNode({
    type: 'image',
    src: photoUrl(path, 'full'),
    alt: '',
    children: [{ text: '' }],
  })
}
function handleCreated(editor: unknown) {
  editorRef.value = editor
}
onUnmounted(() => {
  editorRef.value?.destroy()
  setAlbumPickerOpener(null)
})

/* ---------- 加载 ---------- */
async function loadTrip(id: number) {
  loading.value = true
  try {
    const t: TripDetail = await api.admin.trip(id)
    form.title = t.title
    form.slug = t.slug
    form.dates = [t.start_date, t.end_date]
    form.status = t.status as 'draft' | 'published'
    form.isForeign = !!t.country || t.cities.some((c) => !c.city_code)
    form.country = t.country || ''
    form.summary = t.summary || ''
    form.content = t.content || ''
    form.cover_photo = t.cover_photo
    form.cities = t.cities.map((c) => ({
      key: nextKey(),
      city_code: c.city_code,
      city_name: c.city_name,
      lng: c.lng,
      lat: c.lat,
    }))
    form.attractions = t.attractions.map((a) => ({
      key: nextKey(),
      name: a.name,
      city_code: a.city_code,
      album_rel_path: a.album_rel_path,
      lng: a.lng,
      lat: a.lat,
      note: a.note || '',
    }))
    form.days = t.trip_days.map((d) => ({ key: nextKey(), date: d.date, title: d.title || '', note: d.note || '' }))
    form.member_ids = t.members.map((m) => m.id)
    form.tag_ids = t.tags.map((x) => x.id)
    await loadCoverCandidates()
  } finally {
    loading.value = false
  }
}

/* ---------- 保存 ---------- */
function buildPayload(): TripInput {
  const cityInputs: TripCityInput[] = form.cities.map((c) =>
    c.city_code ? { city_code: c.city_code } : { city_name: c.city_name!, lng: c.lng ?? undefined, lat: c.lat ?? undefined },
  )
  const attractionInputs: AttractionInput[] = form.attractions
    .filter((a) => a.name.trim())
    .map((a) => ({
      name: a.name.trim(),
      city_code: a.city_code,
      album_rel_path: a.album_rel_path || null,
      lng: a.lng,
      lat: a.lat,
      note: a.note.trim() || null,
    }))
  return {
    title: form.title.trim(),
    slug: form.slug.trim() || undefined,
    start_date: form.dates[0],
    end_date: form.dates[1],
    summary: form.summary.trim() || null,
    content: form.content || null,
    cover_photo: form.cover_photo,
    country: form.isForeign ? form.country.trim() || null : null,
    status: form.status,
    cities: cityInputs,
    attractions: attractionInputs,
    days: form.days.filter((d) => d.date).map((d) => ({ date: d.date, title: d.title.trim() || null, note: d.note.trim() || null })),
    member_ids: form.member_ids,
    tag_ids: form.tag_ids,
  }
}

const saving = ref(false)

async function save(status?: 'draft' | 'published') {
  if (saving.value) return
  if (!form.title.trim()) {
    ElMessage.warning('标题必填')
    return
  }
  if (form.dates.length !== 2) {
    ElMessage.warning('请选择起止日期')
    return
  }
  if (form.isForeign && !form.country.trim()) {
    ElMessage.warning('境外旅行需填写国家')
    return
  }
  if (status) form.status = status
  const payload = buildPayload()
  saving.value = true
  try {
    if (tripId.value) {
      await api.admin.updateTrip(tripId.value, payload)
    } else {
      await api.admin.createTrip(payload)
    }
    ElMessage.success(form.status === 'published' ? '已发布' : '已保存草稿')
    clearDraft()
    router.push('/admin/trips')
  } catch (e: unknown) {
    const err = e as { response?: { status?: number; data?: { detail?: string } } }
    const detail = err.response?.data?.detail
    // 422（表单校验）才指向表单本身；500/网络问题指向服务并安抚——内容已在本地草稿里（#12/#15）
    if (err.response?.status === 422) {
      ElMessage.error(detail || '保存失败，请检查表单')
    } else {
      ElMessage.error(detail || '保存失败：服务暂时不可用，内容已保留在本地草稿中')
    }
  } finally {
    saving.value = false
  }
}

const citiesError = ref(false)

onMounted(async () => {
  await meta.ensure()
  try {
    cities.value = await api.admin.cities()
  } catch {
    citiesError.value = true
  }
  if (tripId.value) await loadTrip(tripId.value)
  await maybeRestoreDraft()
})
</script>

<template>
  <div v-loading="loading">
    <section class="ad-panel">
      <h4>基本信息</h4>
      <p class="hint">标题用于展示与卡片；slug 决定详情页地址，留空按标题自动生成。</p>
      <el-form label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="标题" required><el-input v-model="form.title" maxlength="128" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="Slug"><el-input v-model="form.slug" maxlength="64" placeholder="自动生成" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="起止日期" required>
              <el-date-picker
                v-model="form.dates"
                type="daterange"
                value-format="YYYY-MM-DD"
                start-placeholder="出发"
                end-placeholder="返回"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="form.status" style="width: 160px">
                <el-option label="已发布" value="published" />
                <el-option label="草稿（展示端不可见）" value="draft" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="境内 / 境外">
              <el-radio-group v-model="form.isForeign">
                <el-radio-button :value="false">境内</el-radio-button>
                <el-radio-button :value="true">境外 · 需填国家</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col v-if="form.isForeign" :span="12">
            <el-form-item label="国家" required><el-input v-model="form.country" maxlength="32" placeholder="如 日本" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="卡片摘要">
          <el-input v-model="form.summary" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="名录与卡片上的一句话摘要" />
        </el-form-item>
      </el-form>
    </section>

    <section class="ad-panel">
      <h4>封面</h4>
      <p class="hint">从本旅行已配置相册目录的图片中挑选一张作为卡片与首页封面。</p>
      <div v-if="coverCandidates.length" class="picker-grid">
        <div
          v-for="p in coverCandidates.flatMap((c) => c.photos)"
          :key="p"
          class="pk"
          :class="{ on: form.cover_photo === p }"
          @click="pickCover(p)"
        >
          <img :src="photoUrl(p, 'thumb')" loading="lazy" alt="" />
        </div>
      </div>
      <p v-else class="text-sm text-gray-400">先在下方「景点与相册目录」配置相册目录，这里会出现候选封面。</p>
    </section>

    <section class="ad-panel">
      <h4>城市与路线</h4>
      <p v-if="citiesError" class="hint warn-hint">⚠️ 城市字典加载失败——路线/景点无法选择，请刷新页面重试。</p>
      <p class="hint">按到访顺序添加城市，地图路线与统计由此生成；顺序可调整。</p>
      <div class="trip-cities mb-3">
        <span v-for="(c, i) in form.cities" :key="c.key" class="chip">
          <span class="idx">{{ i + 1 }}</span> {{ cityRowLabel(c) }}
          <span class="ops">
            <button title="上移" @click="moveCity(i, -1)">↑</button>
            <button title="下移" @click="moveCity(i, 1)">↓</button>
            <button class="del" title="移除" @click="removeCity(i)">✕</button>
          </span>
        </span>
        <el-cascader
          v-if="!form.isForeign"
          :options="provinceOptions"
          filterable
          placeholder="＋ 添加城市（可搜索，省 / 市）"
          @change="(v: string[]) => v[1] && addDomesticCity(v[1])"
        />
        <el-button v-else @click="foreignDialog = true">＋ 添加境外城市</el-button>
      </div>
    </section>

    <section class="ad-panel">
      <h4>景点与相册目录</h4>
      <p class="hint">相册目录填 NAS 共享相册内的子目录（相对路径），保存后实时扫描，无需上传图片；坐标不精调则跟随城市中心。</p>
      <el-table :data="form.attractions" size="small" class="edit-table">
        <el-table-column label="景点名称" width="170">
          <template #default="{ row }"><el-input v-model="row.name" maxlength="64" placeholder="如 洱海" /></template>
        </el-table-column>
        <el-table-column label="所属城市" width="170">
          <template #default="{ row }">
            <el-select v-if="!form.isForeign" v-model="row.city_code" placeholder="选择" clearable>
              <el-option v-for="c in domesticCities" :key="c.city_code!" :label="cityByCode.get(c.city_code!)?.name" :value="c.city_code!" />
            </el-select>
            <span v-else class="text-xs text-gray-400">境外景点</span>
          </template>
        </el-table-column>
        <el-table-column label="相册目录" min-width="240">
          <template #default="{ row }">
            <div class="flex gap-1 items-center">
              <el-input :model-value="row.album_rel_path || ''" readonly placeholder="2024云南/大理洱海" @click="openAlbumPicker(row)" />
              <el-button link type="primary" @click="openAlbumPicker(row)">浏览</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="精确坐标" width="190">
          <template #default="{ row }">
            <template v-if="row.lng !== null && row.lat !== null">
              <span class="text-xs" style="color: var(--lake)">{{ row.lng }}, {{ row.lat }}</span>
              <el-button link size="small" @click="row.lng = null; row.lat = null">清除</el-button>
            </template>
            <el-button v-else link type="primary" size="small" @click="openPointPicker(row)">🗺 地图选点</el-button>
          </template>
        </el-table-column>
        <el-table-column label="一句话回忆" min-width="180">
          <template #default="{ row }"><el-input v-model="row.note" maxlength="255" placeholder="故事面板的 blurb（可选）" /></template>
        </el-table-column>
        <el-table-column label="操作" width="70">
          <template #default="{ $index }">
            <el-button link type="danger" @click="form.attractions.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="mt-4 flex gap-2">
        <el-button link type="primary" @click="addAttraction">＋ 添加景点</el-button>
        <el-button v-if="form.attractions.length" link @click="loadCoverCandidates">刷新封面候选</el-button>
      </div>
    </section>

    <section class="ad-panel">
      <h4>按天行程</h4>
      <p class="hint">对应详情页「按天行程」与编年页的天级子节点，可留空。</p>
      <el-table :data="form.days" size="small" class="edit-table">
        <el-table-column label="天" width="64">
          <template #default="{ $index }"><b style="color: var(--coral)">D{{ $index + 1 }}</b></template>
        </el-table-column>
        <el-table-column label="日期" width="180">
          <template #default="{ row }"><el-date-picker v-model="row.date" type="date" value-format="YYYY-MM-DD" style="width: 150px" /></template>
        </el-table-column>
        <el-table-column label="当天行程" min-width="220">
          <template #default="{ row }"><el-input v-model="row.title" maxlength="128" placeholder="洱海 S 湾骑行" /></template>
        </el-table-column>
        <el-table-column label="备注" min-width="180">
          <template #default="{ row }"><el-input v-model="row.note" maxlength="500" /></template>
        </el-table-column>
        <el-table-column label="操作" width="70">
          <template #default="{ $index }">
            <el-button link type="danger" @click="form.days.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="mt-4 flex gap-2">
        <el-button link type="primary" @click="addDay">＋ 添加一天</el-button>
        <el-button link @click="fillDaysFromRange">按起止日期生成全部天</el-button>
      </div>
    </section>

    <section class="ad-panel">
      <h4>同行成员与标签</h4>
      <p class="hint">成员与标签在左侧菜单里维护，这里只做勾选。</p>
      <div class="mb-4">
        <div class="text-xs text-gray-400 mb-2">同行成员</div>
        <div class="chips">
          <span
            v-for="m in meta.members"
            :key="m.id"
            class="chip"
            :class="{ on: form.member_ids.includes(m.id), child: m.is_child }"
            @click="form.member_ids.includes(m.id) ? (form.member_ids = form.member_ids.filter((x) => x !== m.id)) : form.member_ids.push(m.id)"
          >
            {{ m.nickname || m.name }}
          </span>
        </div>
      </div>
      <div>
        <div class="text-xs text-gray-400 mb-2">标签</div>
        <div class="chips">
          <span
            v-for="t in meta.tags"
            :key="t.id"
            class="chip"
            :class="{ on: form.tag_ids.includes(t.id) }"
            @click="form.tag_ids.includes(t.id) ? (form.tag_ids = form.tag_ids.filter((x) => x !== t.id)) : form.tag_ids.push(t.id)"
          >
            {{ t.name }}
          </span>
        </div>
      </div>
    </section>

    <section class="ad-panel">
      <h4>游记正文</h4>
      <p class="hint">富文本编辑；「相册插图」从共享相册选图插入，图片仍存于 NAS 相册、不重复上传。</p>
      <div class="editor-wrap">
        <div class="toolbar border-b"><Toolbar :editor="editorRef" :default-config="toolbarConfig" mode="simple" /></div>
        <div class="text-area"><Editor v-model="form.content" :default-config="editorConfig" mode="simple" @on-created="handleCreated" /></div>
      </div>
    </section>

    <div class="ad-actions-bar">
      <el-button size="large" :disabled="saving" @click="save('draft')">保存草稿</el-button>
      <el-button size="large" type="primary" :loading="saving" @click="save('published')">发　布</el-button>
    </div>

    <!-- 对话框们 -->
    <AlbumBrowser v-model="albumDialog.visible" mode="dir" title="选择相册目录" :initial-path="form.attractions.find((a) => a.key === albumDialog.targetKey)?.album_rel_path || ''" @select="onAlbumDirSelected" />
    <AlbumBrowser v-model="insertDialog" mode="photo" title="从相册插图" @select="onInsertPhotoSelected" />
    <MapPointPicker v-model="pointDialog.visible" :lng="form.attractions.find((a) => a.key === pointDialog.targetKey)?.lng ?? null" :lat="form.attractions.find((a) => a.key === pointDialog.targetKey)?.lat ?? null" :hint-city="cityByCode.get(form.attractions.find((a) => a.key === pointDialog.targetKey)?.city_code || '')?.name" @picked="onPointPicked" />

    <el-dialog v-model="foreignDialog" title="添加境外城市" width="420px">
      <el-form label-width="90px">
        <el-form-item label="城市名" required><el-input v-model="foreignForm.city_name" placeholder="如 京都" /></el-form-item>
        <el-form-item label="经度（可选）"><el-input-number v-model="foreignForm.lng as number" :controls="false" style="width: 100%" /></el-form-item>
        <el-form-item label="纬度（可选）"><el-input-number v-model="foreignForm.lat as number" :controls="false" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="foreignDialog = false">取消</el-button>
        <el-button type="primary" @click="addForeignCity">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>
