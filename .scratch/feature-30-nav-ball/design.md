# Issue #30 设计规范：顶部通栏导航 → 吸边悬浮小球

> 范围：仅展示端（MapHome / TimelineView / JournalListView / TripDetailView）。
> 管理端样式严禁受影响：新样式全部写在 `NavBall.vue` 的 `<style scoped>` 内，
> 类名统一前缀 `nb-`，不得在 `flow.css` 或任何全局层新增 `.nav*` 之外的全局类。

---

## 0. 现状坐标备忘（避让依据，均已核实）

| 元素 | 位置 | z-index |
| --- | --- | --- |
| `.stats-flag`（地图页统计卡） | fixed left:16 top:78 | 40 |
| `.map-hint`（地图页提示 chip） | fixed top:78 水平居中 | 40 |
| `.panel`（地点故事面板） | fixed top:84 right:12 | 50 |
| `.stage-chip` / `.legend-chip` | fixed bottom 左/右 | 40 |
| `.veil`（开场帷幕） | fixed inset:0 | 80 |
| `.lightbox` | fixed inset:0 | 120 |
| `.back-map` / `.tl-year` / `.side` | sticky top:78 / 78 / 80 | ≤30 |
| `.page-pad` | padding-top:96px | — |
| 地图 | ECharts geo，无 Leaflet 类 zoom 控件，无右上角控件冲突 | 1 |

地图页顶部 0–66px 高度带（左右两角）目前为空，是小球的落位空间。

---

## 1. 两个概念方案

### 方案 A「罗盘豆 · 贴边胶囊」（推荐）

小球吸附**左上角**，点击后沿顶边**向右展开成一条横向胶囊菜单**（球本身是胶囊最左端的一节）。

```
收起态                         展开态
┌─────────────────────────    ┌──────────────────────────────────┐
│ ◉                ·          │ ●◉│ 地图 │ 编年 │ 游记名录 ╎游迹 │
│                             └──────────────────────────────────┘
│      （页面内容）              ◉ = 珊瑚色小球（罗盘）  ● = 胶囊体
```

- 取舍：菜单是**文字**，与现有 `.nav-links` 视觉语言完全一致，信息零损耗；
  几何最简单（一维展开），键盘/读屏路径清晰，390px 也放得下。
- 弱点：仍是"一条横条"的残影，极简感略逊于纯球形；展开宽度约 300px，
  占用顶边空间（但该空间在四页均空闲）。

### 方案 B「星盘 · 径向展开」

小球吸附左上角，点击后**以球为圆心向上/向右 90° 扇形径向弹出 3 个圆形图标钮**
（🅋 地图 / 🕐 编年 / ☰ 名录），文字靠 hover tooltip 或图标下小字补足。

```
        ⊙地图
      ⊙编年        ⊙ = 44px 圆形图标钮，沿 1/4 圆弧排布
    ◉  ————  ⊙游记名录   半径 ≈ 96px
```

- 取舍：形态最"球"、展开动画最惊艳，且展开范围小、不占顶边。
- 弱点：三个目标（尤其"游记名录"）难以用图标无损表达，必须叠 tooltip / 小字，
  触达面积分散、误触率高；键盘导航需自定义环形序；移动端弧形热区难对齐 44px 网格。

### 结论：**推荐方案 A**

理由：这是一个内容型网站，导航的可读性与可预期性 > 形态炫技；方案 A 能整段沿用
现有 active/hover 视觉与无障碍习惯，改动面与回归风险最小，390px 无需特判布局。

---

## 2. 推荐方案（A）完整规格

### 2.1 收起态小球

| 项 | 值 |
| --- | --- |
| 位置 | `position: fixed; top: 16px; left: 16px`（四页统一，不随页面变化） |
| 直径 | 48px（桌面 = 移动同一尺寸，天然满足 ≥44px 热区） |
| 内容 | `🧭` emoji，字号 20px，居中 —— 延续现 `.masthead .mark` 的品牌记忆 |
| 背景 | `var(--coral)` #E8683A 实色（暖纸底与地图瓦片上均清晰，不加 backdrop-filter） |
| 圆角 | 50% |
| 阴影 | `var(--shadow)`（层级与 stage-chip / year-dock 一致，不升级到 shadow-lg） |
| hover | `transform: translateY(-1px) scale(1.05)`，阴影升 `var(--shadow-lg)`，`transition: .18s` |
| focus-visible | `outline: 2px solid var(--coral-deep); outline-offset: 3px` |
| pointer-events | 外层容器 `pointer-events: none`，球与菜单自身 `auto`（沿用现 `.nav` 的防穿透模式，避免挡住地图交互） |

### 2.2 展开交互

- **触发：点击**（Enter/Space 等价）。不做悬停展开——触屏无 hover，且地图页鼠标划过顶角易误触。
- 展开后菜单形态：**沿顶边向右生长的横向胶囊**（文字菜单），球保持原位成为胶囊最左一节。
- 菜单内容（从左到右）：
  1. 小球（原位，🧭 不变，不做 ✕ 形变）；
  2. `地图` / `编年` / `游记名录` 三个 router-link；
  3. `8px` 间距 + `1px var(--hairline)` 竖分隔线 + `游迹` 字样（12px，`var(--gray)`，
     letter-spacing .2em）——品牌字样仅在展开态保留，收起态只有球，页面更干净。
  - `UP JOURNEY` 英文副标不再保留（信息密度让位极简；帷幕页 veil 已承担品牌全称）。

### 2.3 展开态几何

```
锚点 = 球心 (left:16+24, top:16+24)

┌ 胶囊（left:16 top:16 height:48 border-radius:999px）
│  padding: 6px 14px 6px 60px   ← 60 = 48(球) + 12(间隙)，球叠压在胶囊左端之上
│  链接项：font-size 14px / font-weight 500 / padding 8px 16px / border-radius 999px / gap 4px
│  背景 rgba(255,255,255,.92) + backdrop-filter: blur(14px)（沿用现 .nav-inner 材质）
│  阴影 var(--shadow)
```

胶囊总宽 ≈ 60 + (地图 60) + (编年 60) + (游记名录 100) + 分隔与字样 70 ≈ 350px，
390px 视口下 `left:16` 起排仍有约 24px 余量，无需换行。

### 2.4 动效

| 项 | 值 |
| --- | --- |
| 展开 | 胶囊 `opacity 0→1` + `transform: translateX(-8px) scale(.96) → none`，`transform-origin: left center`；时长 **240ms**；缓动 `cubic-bezier(.22,1,.36,1)`（与现 `.panel` 一致） |
| 收起 | 同曲线反向，时长 **180ms** |
| 不做 | 逐项 stagger、球体旋转、图标形变（防过度设计） |
| reduced motion | `@media (prefers-reduced-motion: reduce)` 下去 transition，直接显隐 |

### 2.5 收起时机

1. 点击菜单外任意区域（`document` click，排除球与胶囊自身）；
2. `Esc`；
3. **路由切换后自动收起**：`watch(() => route.path, () => open = false)`——点击链接跳转即收起，外部 `/trip/:id` 直达跳转也保持收起态；
4. 再次点击小球。

### 2.6 active 当前页标识

- **球体不表达 active**（收起态保持纯净；四页共用一个球，加角标是噪音）。
- **菜单内表达**：当前页链接 `background: var(--ink); color: #fff`（与现
  `.nav-links a.active` 完全同款视觉），并设 `aria-current="page"`。
- TripDetailView 传入 `active="list"`（现状即如此），详情页展开时高亮「游记名录」。

### 2.7 移动端（≤640px，基准 390px）

- 球：`top: 12px; left: 12px;` 直径仍 48px（≥44px 热区）。
- 胶囊：仍向右展开；`font-size 13.5px`、链接 `padding 8px 12px`；尾部分隔线 +「游迹」
  字样在 ≤640px **隐藏**（宽度优先给链接）。
- 胶囊 `max-width: calc(100vw - 24px)`，超宽时不换行、按上值收缩即可容纳。
- 展开态胶囊底部距 `.stats-flag`(top:78) / `.map-hint`(top:78) 有 ≥14px 间隙，无遮挡。

### 2.8 无障碍

- 结构：`<nav class="nb" aria-label="主导航">` 包裹。
- 触发器：`<button class="nb-ball" :aria-expanded="open" aria-controls="nb-menu" aria-label="导航菜单">`。
- 菜单：普通 `<div id="nb-menu">` 内放 router-link（**站点导航，不用 ARIA menu 模式**，
  不抢 role=menu 的键盘约定）。收起时容器 `hidden`（或 `visibility:hidden`），不可 Tab 入。
- 键盘：Tab 顺序 = 球 → 地图 → 编年 → 游记名录；`Enter/Space` 开合；`Esc` 收起并把焦点
  还给球；点击链接后焦点随路由走（球收回、新页面正常从 body 起步）。
- 所有交互件提供 `:focus-visible` 样式（见 2.1）。

### 2.9 z-index 与避让规则

- 小球容器 **`z-index: 60`**（继承现 `.nav` 的层级档位），低于 veil(80) 与 lightbox(120)：
  开场帷幕期间球不可见不可点（合理）；灯箱打开时球被压住（合理）。
- 不抬到 80+：避免盖住帷幕/灯箱造成"导航浮在 Everything 上"的失控感。
- 避让核对表（均无需改动既有元素）：
  - 地图页：球占 top 16–64，`stats-flag`/`map-hint` 在 top:78 起 → 垂直不重叠；
    ECharts 无 zoom 控件 → 无角部冲突。
  - 详情页：`.back-map` sticky top:78、左缘随 `--pad`，与球（右缘 64px）垂直错开 14px。
  - 编年页：`.tl-year` sticky top:78，同上错开。
  - 面板（right:12 top:84）在右侧，与左上球永不相交。

### 2.10 随本 issue 的清理与不动项

**清理**（`DisplayNav.vue` 删除后）：`flow.css` 中 `.nav` / `.nav-inner` / `.masthead*` /
`.nav-links*` / `.nav-toggle` / `.nav-burger` 及 `@media (max-width:900px)` 里的 burger
分支（296–301 行）一并移除，不留死样式。

**不动**（数值与旧导航高度耦合，本期只换壳不改版式，防止扩散回归）：
`.page-pad`(96px)、`.back-map`(sticky 78)、`.tl-year`(78/70)、`.side`(80)、
`.panel`(84)、`.stats-flag`(78)、`.map-hint`(78)。其中 `.page-pad` 以后可减到 48px，
另开 issue。

---

## 3. 边界与负向清单

- **滚动行为：常驻**。四档宽度、任意滚动深度下球保持 top:16 left:16、全尺寸、全透明度。
  **不做**滚动缩小、半隐出屏、滚动方向感知——长文阅读时球只是静静待在角落，多余智力
  都是负担。
- **详情页返回**：返回入口仍是页内 `.back-map`（"← 回到地图"），**不在球/菜单里加返回键**；
  菜单永远是全局三入口，职责单一。
- **不要做**：
  - 不做径向/弧形展开（见方案 B 的否决理由）；
  - 不做 hover 展开、不做长按菜单；
  - 不做球体上的未读角标、active 圆点、`UP JOURNEY` 副标；
  - 不做拖拽换位、不做位置记忆；
  - 不做"滚到这里才出现"的进场动画；
  - 不在 `flow.css` 加任何 `nb-` 全局类，不碰管理端 (`views/admin/*`) 的任何样式；
  - 不改 2.10 列出的既有 sticky/fixed 偏移值。
- 长标题详情页滚动时，正文会从球下经过：球为不透明实色 + 阴影，可读性自洽，属可接受
  代价，不用加背景模糊条。

---

## 4. 验收清单（验收者逐条勾选）

**通用（四档宽度 1440 / 1024 / 768 / 390 各过一遍）**

- [ ] 顶部不再出现通栏胶囊条；页面上唯一的导航元素是左上角小球。
- [ ] 球为 48px 珊瑚色圆 + 🧭，位置 top:16 left:16（移动端 12/12），滚动前后位置与大小不变。
- [ ] 点击球展开横向胶囊：地图 / 编年 / 游记名录 / 竖线 / 游迹（≤640px 无竖线与游迹）。
- [ ] 当前页在菜单内为墨色底白字（详情页高亮"游记名录"）；球体无任何 active 痕迹。
- [ ] 点击链接：路由切换 + 菜单自动收起。
- [ ] 点击球外任意区域、按 Esc，菜单均收起；Esc 后焦点回到球。
- [ ] 连续开合动画流畅（240/180ms），无布局跳动、无横向滚动条；开启系统"减弱动态效果"后动画直接显隐。
- [ ] 键盘：Tab 可达球→三链接；球上 Enter/Space 开合；焦点环可见。

**地图页专查**

- [ ] 球不遮挡统计卡（左上 top:78）与顶部提示 chip（top:78 居中）；展开态亦不遮挡。
- [ ] 地图拖拽/缩放、年份坞、左右下角 chip 均可正常点击（球容器 pointer-events 不穿透）。
- [ ] 开场帷幕期间球不可见、不可提前点出。

**详情页专查**

- [ ] "← 回到地图" sticky 按钮滚动时不被球覆盖。
- [ ] 相册灯箱打开时球被灯箱压在下方；关闭后恢复。
- [ ] 长文滚动中球常驻不缩小、不消失。

**回归**

- [ ] 管理端任一页面外观与改动前逐像素一致（样式零污染）。
- [ ] `flow.css` 中旧 `.nav*` / burger 样式已删净，全局搜索无死引用。
- [ ] DevTools 检查：球按钮带 `aria-expanded` / `aria-controls`，当前页链接带 `aria-current="page"`。
