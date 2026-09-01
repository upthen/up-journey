/** 与后端 app/schemas.py 一一对应的 DTO。 */

export type PhotoSize = 'thumb' | 'full'

export interface Member {
  id: number
  name: string
  nickname: string | null
  is_child: boolean
}

export interface Tag {
  id: number
  name: string
}

export interface City {
  code: string
  name: string
  province_code: string
  province_name: string
  level: number
  lng: number
  lat: number
}

export interface TripDay {
  day_index: number
  date: string
  title: string | null
  note: string | null
}

export interface TripCard {
  id: number
  slug: string
  title: string
  start_date: string
  end_date: string
  year: number
  days_count: number
  summary: string | null
  cover_photo: string | null
  country: string | null
  status: string
  tags: Tag[]
  members: Member[]
  route: string[]
  trip_days: TripDay[]
}

export interface Attraction {
  id: number
  name: string
  city_code: string | null
  city_display: string | null
  album_rel_path: string | null
  lng: number | null
  lat: number | null
  resolved_lng: number | null
  resolved_lat: number | null
  note: string | null
}

export interface TripCity {
  city_code: string | null
  city_name: string | null
  lng: number | null
  lat: number | null
  sort_order: number
  display: string
}

export interface GalleryGroup {
  attraction: string
  album_dir: string
  count: number
  photos: string[]
}

export interface Neighbor {
  slug: string
  title: string
}

export interface TripDetail extends TripCard {
  content: string | null
  attractions: Attraction[]
  cities: TripCity[]
  gallery: GalleryGroup[]
  photo_count: number
  prev: Neighbor | null
  next: Neighbor | null
}

export interface Stats {
  years: number
  provinces: number
  cities: number
  attractions: number
  countries: number
  trips: number
  days: number
  with_kids: number
}

export interface Spot {
  name: string
  year: number
  lng: number
  lat: number
  city: string
  photo_count: number
  note: string | null
  trip_slug: string
  trip_title: string
  photos: string[]
}

export interface Route {
  year: number
  trip_slug: string
  trip_title: string
  coords: number[][]
}

export interface TimelineYear {
  year: number
  trip_count: number
  total_days: number
}

export interface Footprints {
  years: number[]
  provinces: Record<string, number>
  spots: Spot[]
  routes: Route[]
  timeline: TimelineYear[]
}

export interface AlbumDir {
  path: string
  name: string
}

export interface Album {
  current: string
  parent: string | null
  dirs: AlbumDir[]
  photos: string[]
}

// ---------- 管理端入参 ----------

export interface TripCityInput {
  city_code?: string
  city_name?: string
  lng?: number
  lat?: number
}

export interface AttractionInput {
  name: string
  city_code?: string | null
  album_rel_path?: string | null
  lng?: number | null
  lat?: number | null
  note?: string | null
}

export interface TripDayInput {
  date: string
  title?: string | null
  note?: string | null
}

export interface TripInput {
  title: string
  slug?: string
  start_date: string
  end_date: string
  summary?: string | null
  content?: string | null
  cover_photo?: string | null
  country?: string | null
  status: 'draft' | 'published'
  cities: TripCityInput[]
  attractions: AttractionInput[]
  days: TripDayInput[]
  member_ids: number[]
  tag_ids: number[]
}
