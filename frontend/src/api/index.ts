import axios from 'axios'

import type {
  Album,
  City,
  Footprints,
  Member,
  Stats,
  Tag,
  TripCard,
  TripDetail,
  TripInput,
} from '@/types'

export const http = axios.create({ baseURL: '/api/v1' })

// 管理端会话过期 → 跳登录页（展示端公开接口没有 401，不受影响）。
// 已在登录页时不再跳转，防止 401 → 跳转 → 又 401 的整页刷新循环。
http.interceptors.response.use(undefined, (error) => {
  const status = error?.response?.status
  const url: string = error?.config?.url ?? ''
  if (status === 401 && url.includes('/admin') && !url.endsWith('/login')) {
    if (window.location.pathname === '/admin/login') return Promise.reject(error)
    window.location.href = `/admin/login?next=${encodeURIComponent(window.location.pathname)}`
  }
  return Promise.reject(error)
})

export function photoUrl(path: string, size: 'thumb' | 'full' = 'thumb'): string {
  return `/api/v1/photos/${size}?path=${encodeURIComponent(path)}`
}

export const api = {
  health: () => http.get<{ status: string }>('/health').then((r) => r.data),
  stats: () => http.get<Stats>('/stats').then((r) => r.data),
  trips: (params?: { year?: number; tag?: string }) =>
    http.get<TripCard[]>('/trips', { params }).then((r) => r.data),
  trip: (slug: string) => http.get<TripDetail>(`/trips/${slug}`).then((r) => r.data),
  footprints: () => http.get<Footprints>('/footprints').then((r) => r.data),
  meta: () =>
    http.get<{ members: Member[]; tags: Tag[] }>('/meta').then((r) => r.data),

  admin: {
    session: () => http.get<{ ok: boolean }>('/admin/session').then((r) => r.data),
    login: (password: string) => http.post<{ ok: boolean }>('/admin/login', { password }).then((r) => r.data),
    logout: () => http.post('/admin/logout'),
    trips: (params?: { year?: number; tag?: string; status?: string; q?: string }) =>
      http.get<TripCard[]>('/admin/trips', { params }).then((r) => r.data),
    trip: (id: number) => http.get<TripDetail>(`/admin/trips/${id}`).then((r) => r.data),
    createTrip: (payload: TripInput) =>
      http.post<TripDetail>('/admin/trips', payload).then((r) => r.data),
    updateTrip: (id: number, payload: TripInput) =>
      http.put<TripDetail>(`/admin/trips/${id}`, payload).then((r) => r.data),
    deleteTrip: (id: number) => http.delete(`/admin/trips/${id}`),
    members: () => http.get<Member[]>('/admin/members').then((r) => r.data),
    createMember: (payload: { name: string; nickname?: string; is_child?: boolean }) =>
      http.post<Member>('/admin/members', payload).then((r) => r.data),
    updateMember: (id: number, payload: { name?: string; nickname?: string; is_child?: boolean }) =>
      http.put<Member>(`/admin/members/${id}`, payload).then((r) => r.data),
    deleteMember: (id: number) => http.delete(`/admin/members/${id}`),
    tags: () => http.get<Tag[]>('/admin/tags').then((r) => r.data),
    createTag: (name: string) => http.post<Tag>('/admin/tags', { name }).then((r) => r.data),
    updateTag: (id: number, name: string) =>
      http.put<Tag>(`/admin/tags/${id}`, { name }).then((r) => r.data),
    deleteTag: (id: number) => http.delete(`/admin/tags/${id}`),
    cities: (params?: { province?: string; level?: number }) =>
      http.get<City[]>('/admin/cities', { params }).then((r) => r.data),
    album: (path?: string) =>
      http.get<Album>('/admin/album', { params: { path: path || '' } }).then((r) => r.data),
  },
}
