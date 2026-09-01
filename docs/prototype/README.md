# up-journey 高保真原型

**视觉方向已定稿：温暖手账风 · A 拼贴版（`warm/`）**，详见 `docs/adr/0001-visual-style-warm-scrapbook.md`。
其余版本（B 精修版 / 杂志风 / 画廊风）均归档参考。数据全部为假数据，地图为真实 ECharts 渲染。

## 查看

```bash
cd docs/prototype
python3 -m http.server 8613
# 打开 http://localhost:8613/compare.html（风格对比导航）
```

> 需要通过 HTTP 服务访问（地图要 fetch 本地 GeoJSON，直接双击 file:// 会跨域）。

## 定稿版页面（Vue 实装的像素级蓝本）

| 页面 | 文件 | 内容 |
|---|---|---|
| 首页 | `warm/index.html` | 拍立得堆叠 Hero、三色便签统计板、登机牌特写、拍立得墙 |
| 足迹总览 | `warm/footprints.html` | 胶带贴角地图（陶橘砂色阶）、拍立得瀑布、锯齿交替时间轴 |
| 旅行详情 | `warm/trip.html` | 楷体标题 + 拍立得封面/插图、行程小地图、按天行程、拍立得图库 |

## 归档参考（未采用）

- `warm2/`：手账 B 精修版——减法方向错误（越改越失气质），已否决
- 根目录 4 页：杂志编辑风——太正式
- `gallery/` 2 页：深色画廊风——展馆气质过重

## 其他约定

- 客户端导航**无管理端入口**；管理端原型 `admin.html`（独立的 Element Plus 后台），实装走 `/admin` 路由。
- 字体：标题/注脚楷体（Mac 上 Kaiti SC）、正文系统无衬线；生产 self-host 楷体+思源宋体子集化 woff2。
- 断点 1024 / 640；占位"照片"为 CSS 渐变色块，上线后即真实相册图。
