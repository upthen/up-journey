/** 展示端日期/文案格式化（与 v4 原型一致的排版：2024.05.01 — 05.07）。 */

function ymd(iso: string): string {
  return iso.replaceAll('-', '.')
}

function md(iso: string): string {
  return iso.slice(5).replace('-', '.')
}

export function dateRange(start: string, end: string): string {
  const [sy, ey] = [start.slice(0, 4), end.slice(0, 4)]
  return sy === ey ? `${sy}.${md(start)} — ${md(end)}` : `${ymd(start)} — ${ymd(end)}`
}

export function mdDate(iso: string): string {
  return iso.slice(5).replaceAll('-', '.')
}

export function memberLabel(m: { name: string; nickname: string | null }): string {
  return m.nickname || m.name
}

export function memberInitial(m: { name: string; nickname: string | null }): string {
  return memberLabel(m).slice(0, 1)
}
