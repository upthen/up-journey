import DOMPurify from 'dompurify'

const ALLOWED_TAGS = [
  'p', 'h1', 'h2', 'h3', 'h4', 'strong', 'b', 'em', 'i', 'u', 's', 'sub', 'sup',
  'blockquote', 'ul', 'ol', 'li', 'a', 'img', 'figure', 'figcaption',
  'br', 'hr', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'span', 'div', 'section',
]
const ALLOWED_ATTR = ['src', 'alt', 'href', 'title', 'colspan', 'rowspan']

/** 展示端 v-html 前的净化：白名单标签 + 图片只允许本应用图片服务（相册路径由服务端二次校验）。 */
export function sanitizeContent(html: string | null | undefined): string {
  if (!html) return ''
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'IMG') {
      const src = node.getAttribute('src') || ''
      if (!src.startsWith('/api/v1/photos/')) {
        node.removeAttribute('src')
      }
    }
    if (node.tagName === 'A') {
      const href = node.getAttribute('href') || ''
      if (!href.startsWith('/') && !href.startsWith('#')) {
        node.removeAttribute('href')
      }
    }
  })
  try {
    return DOMPurify.sanitize(html, { ALLOWED_TAGS, ALLOWED_ATTR })
  } finally {
    DOMPurify.removeAllHooks()
  }
}
