# 返回按钮重设计 · 回家键（Back-to-Home）

- 日期：2026-09-13
- 范围：展示端全部非地图页（`/timeline`、`/list`、`/trip/:slug`）
- 仓库现状已核实：`frontend/src/components/NavBall.vue`、`frontend/src/styles/flow.css`、`frontend/src/views/TripDetailView.vue`、`frontend/src/views/TimelineView.vue`、`frontend/src/components/MapToolbar.vue`

## 0. 问题定义

详情页 `.back-map` 是**文档流内的顶部元素**（主代理已将其从 sticky 改回 static——sticky 会压正文被用户骂），页面一滚它就消失，必须滚回顶部才能返回。用户明确要求：**不用滚回顶部、不用展开 NavBall 菜单、一眼可见**的直达返回键，且**所有展示页统一**。

核心约束（已核实的代码事实）：

| 固定元素 | 位置 | z-index | 出现页面 |
| --- | --- | --- | --- |
| NavBall 球 | fixed 左上 16,16（≤640px: 12,12）48px 圆 | 60 | 全部展示页 |
| year-dock 年份坞 | fixed 底中 bottom:20，最高 ~56px | 40 | 仅地图页 |
| 🎯 还原钮 | fixed 右缘中部 right:14 | 40 | 仅地图页 |
| `.panel` 故事面板 | fixed 右侧 top:84 | 50 | 仅地图页 |
| `.pn` 上一篇/下一篇 | **文档流内**，margin `40px 0 56px` | — | 仅详情页 |
| `.lightbox` | fixed inset:0 | 120 | 全部 |
| admin 路由 | 独立 AdminLayout | — | 不在范围 |

关键结论前置：**year-dock 与返回键永远不会同屏**（year-dock 仅在地图页，而地图页不需要返回键），右下角方案不存在任何避让冲突。

## 1. 方案对比

| | A. 右下角悬浮「← 回到地图」胶囊 | B. NavBall 球双职责（非地图页变返回态） | C. 并入底部坞（year-dock / .pn） |
| --- | --- | --- | --- |
| 一句话 | 右手拇指区、全页常驻、语义独立，一眼可见 | 复用现有控件零新增，但「球=菜单」的心智被打破，菜单可达性倒退 | 元素根本不同屏，是伪方案 |
| 优点 | 不滚顶、不展开菜单即达；与 NavBall「左上=前进、右下=回家」形成稳定空间分工；组件挂 App 层一处实现 | 无新增 DOM；少一个浮窗 | 不新增浮层 |
| 缺点 | 多一个固定浮层（极小、单实例） | 点球直接跳走，菜单需要长按/角标——**不可发现、桌面端长按无意义、触屏易误触**；「去编年/名录」也要先被迫想清楚是否要返回 | year-dock 只存在于地图页（无需返回）；详情页底部是文档流内的 `.pn`，做不进 fixed 语义；且 `.pn` 是"上一篇/下一篇"，混入"回地图"是层级污染 |
| 交互风险 | 与 `.pn` 尾部有 ~8px 视觉擦边（规格中已给出补偿） | 用户骂点进去找不到菜单，返工概率最高 | 结构性不成立 |
| 结论 | **推荐** | 否决 | 否决 |

**推荐 A**：右下角悬浮「回家」胶囊。理由浓缩——用户要的三件事（不滚顶、不展开、一眼可见）只有 A 全部满足；B 牺牲了既有菜单可用性，C 与事实不符（year-dock 仅地图页、`.pn` 非固定层）。

## 2. 推荐方案完整规格：`.back-home`

### 2.1 实现位置与显示逻辑

- 新组件 `frontend/src/components/BackHome.vue`，渲染在 `App.vue` 的 `<router-view />` 之后（与 `.lightbox` 平级），**单实例、非各页面自行引入**：

  ```html
  <router-link v-if="show" class="back-home" to="/">…</router-link>
  ```

  `show = route.path !== '/' && !route.path.startsWith('/admin')`（admin 有自己的布局，绝不渲染）。
- 显示页：`/timeline`、`/list`、`/trip/:slug`。**地图页 `/` 确定不显示**（它就是家）。
- 由于是 router-link 且组件常驻，非地图页之间跳转（如详情→详情上一篇）不重挂载、不重播进场动画；仅 地图→非地图 时播一次进场。

### 2.2 位置与避让（1440 / 1024 / 768 / 390 四档）

| 档位 | 位置 | 说明 |
| --- | --- | --- |
| ≥1024（覆盖 1440） | `right: 20px; bottom: 20px` | 桌面双列布局 `.trip-layout` 右列 `.side` 宽度有限，右下角无正文遮挡 |
| 768–1023 | 同上 | 900px 起切单列，右下仍留白 |
| 641–767 | 同上 | — |
| ≤640（覆盖 390） | `right: 12px; bottom: calc(16px + env(safe-area-inset-bottom))` | 与 NavBall 移动端 12px 吸边对齐；safe-area 供 iPhone 底部小黑条 |

- **与 year-dock 的避让：无需计算**——year-dock 仅渲染于地图页，本键仅在非地图页渲染，物理上不同屏。
- **与 `.pn`（详情页）的避让**：按钮 44px 高 + bottom 20 → 顶缘距底 64px；`.pn` 现有 margin-bottom 56px，满滚动时仅剩 8px 净空且阴影可能擦边。**规格改动一行**：`.pn` 的 margin 由 `40px 0 56px` 改为 `40px 0 80px`（`.pn` 仅详情页使用，无副作用）。
- **与 `.page-pad`（timeline/list）的避让**：现 padding-bottom 60px，同样不足。改为 `padding: 96px 0 96px`（或单独补 `padding-bottom: 96px`）。
- z-index：**55**。低于 NavBall(60) 与 lightbox(120)，高于正文（auto）与所有文档流内容。不用 999 系魔法数。
- 灯箱打开时被 z:120 的 `.lightbox` 自然盖住，无需 JS 隐藏。

### 2.3 尺寸 / 颜色 / 阴影 / 圆角

```css
.back-home {
  position: fixed; right: 20px; bottom: 20px; z-index: 55;
  display: inline-flex; align-items: center; gap: 8px;
  height: 44px;                       /* 热区 ≥44px，触屏达标 */
  padding: 0 20px;
  border-radius: 999px;
  background: var(--ink);             /* #1F2A33 */
  color: #fff;
  font-size: 14px; font-weight: 700; line-height: 1;
  box-shadow: var(--shadow-lg);
  transition: background .18s, transform .18s, box-shadow .18s;
}
.back-home .arr { color: var(--coral); font-weight: 700; }  /* 「←」珊瑚色点睛 */
.back-home:hover  { background: var(--coral); }             /* 悬停点亮品牌色 */
.back-home:active { transform: scale(.96); }
.back-home:focus-visible { outline: 2px solid var(--coral-deep); outline-offset: 3px; }
@media (prefers-reduced-motion: reduce) { .back-home { transition: none; } }
```

- **为什么底色用 ink 而非 coral**：coral `#E8683A` 上白字对比度仅 ~3.2:1，14px 文字不达 AA(4.5:1)；ink 上白字 ~13:1。同时与左上 NavBall 形成材质区分：**左上珊瑚圆 = 品牌导航球，右下墨色胶囊 = 动作**，"回家"悬浮时的 coral 点亮即是品牌呼应。仓库已有同款先例：`.veil .go`（ink 底白字胶囊）。
- 宽度估算：箭头 ~16px + gap 8 + 「回到地图」4 字 ×14px = 56 + padding 40 ≈ **120px**，右下角对任何档位无压力。
- 无图标库依赖：「←」为文本字符，与现有 `.back-map`、`.pn` 用法一致。

### 2.4 文案与导航语义

- **文案固定「← 回到地图」，不做响应式短文案**。390px 下按钮全宽 ~120px，远小于 `max-width: calc(100vw - 32px)` 的年份坞，短文案「← 地图」省下的 ~40px 毫无收益，反而制造两套文案。结论：恒定「← 回到地图」。
- **导航语义：一律 `router-link to="/"`，不用 `history.back()`**。结论理由：本站可被分享深链直进（详情页直开），`history.back()` 会把用户弹出站外或无动作；"回到地图"承诺的是目的地（家），不是历史，语义上也应该是确定性的。router 已有 `scrollBehavior` 回 `{ top: 0 }`，无需额外处理。

### 2.5 各页差异

| 页面 | 显示 | 备注 |
| --- | --- | --- |
| `/` 地图首页 | **否** | 家即目标，无返回语义；且右下已有 year-dock/🎯 的密集浮层区 |
| `/timeline` | 是 | 页面底部 `.tl-end` 已有文字版"回到地图"链接，保留（它是内容性收尾，与常驻键不冲突）；`.page-pad` 底部 padding 补到 96px |
| `/list` | 是 | 同上，`.page-pad` 补 96px |
| `/trip/:slug` | 是 | 删除顶部 `.back-map`（见 §3）；`.pn` margin-bottom 补到 80px |
| `/admin/**` | **否** | 管理端自有导航，`startsWith('/admin')` 排除 |

### 2.6 状态与动效

- hover（仅 `@media (hover: hover)` 设备）：底色 ink → coral，0.18s。不位移（右下角上浮 2px 意义不大，色变已足够反馈）。
- focus-visible：2px `--coral-deep` 外描边，offset 3px——与 NavBall、MapToolbar 完全同款。
- active：scale(0.96)。
- aria：`<router-link>` 自带链接语义，可见文本「回到地图」即 accessible name，**不额外加 aria-label**（避免覆盖可见文本）；「←」`<span aria-hidden="true">`。
- **进场动效**：组件挂载时一次性 `opacity 0→1 + translateY(8px→0)`，0.28s `cubic-bezier(.22,1,.36,1)`（仓库同款缓动）。仅地图→非地图这一次播。
- **滚动态：不做任何滚动感知**——结论明确。不随滚动缩放、隐藏、变色。理由：① 位置恒定 + 恒定可见正是用户要的"一眼可见"；② 滚动监听在长文详情页（正文+图集）有持续重排/合成开销；③ 滚动后形态变化 = 又一种"蹩脚交互"。`prefers-reduced-motion` 下关过渡。

### 2.7 移动端 390 规格

- 位置：`right: 12px; bottom: calc(16px + env(safe-area-inset-bottom))`。
- 尺寸不变（44px 高热区、120px 宽），字号 14px 在 390 下清晰可读，不需要缩短文案。
- 与 NavBall（左上 12,12）对角分布，互不遮挡；地图页才有的 year-dock 底中坞不存在冲突场景。
- 触屏无 hover：仅 active 缩放反馈，focus-visible 仅供外接键盘。

### 2.8 与 NavBall 的视觉分工（写进组件注释）

```
左上 珊瑚圆球（NavBall, z:60） = 前进导航：展开菜单去 编年/名录/地图，探索入口
右下 墨色胶囊（BackHome, z:55） = 回家直达：单击回 `/`，终点动作
```

两者一圆一胶囊、一珊瑚一墨色、一左上一右下，职责正交；本键不取代 NavBall（跨页前进仍走球），球也不承担返回（§1-B 否决理由）。

## 3. 是否删除详情页顶部 `.back-map`

**结论：删除。** 明确推荐：

- 删 `TripDetailView.vue` 模板第 152 行 `<router-link class="back-map" to="/">← 回到地图</router-link>`；
- 删 `flow.css` 第 149–156 行 `.back-map` 及 `:hover` 规则；
- 它的职责被 `.back-home` 完整替代；保留会造成同一动作两个入口（顶部一次性 + 右下常驻），且顶部那颗正是用户骂的"蹩脚交互"本体；
- 删除后详情页顶部直接以 `.trip-hero` 开场，`page-pad` 顶距不变，无需补偿。

顺带记录（超出本规范范围，不改）：TripDetailView 中 `<NavBall active="list" />` 的 active 值疑似应为 "map" 或新增 "trip" 态，建议另开 issue。

## 4. 落地改动清单（供实施）

1. 新增 `frontend/src/components/BackHome.vue`（模板+样式照 §2.3/2.6，含进场动画与 reduced-motion 关闭）。
2. `frontend/src/App.vue`：引入并渲染 `BackHome`，`route.path` 判定显示（需 `useRoute`）。
3. `frontend/src/views/TripDetailView.vue`：删 `.back-map` 行；`NavBall active` 值问题另立 issue。
4. `frontend/src/styles/flow.css`：删 `.back-map` 两条规则；`.pn` margin `40px 0 56px` → `40px 0 80px`；`.page-pad` `padding: 96px 0 60px` → `padding: 96px`（即四向 96px）。

## 5. 负向清单（不要做）

- ❌ 不用 `history.back()`——深链直进会跳出站，一律 `router-link to="/"`。
- ❌ 不做滚动感知形态（滚动缩放/隐藏/变色/吸附切换）。
- ❌ 不改 NavBall 为返回态双职责（不可发现、误触、破坏菜单可达性）。
- ❌ 不把返回键并进 year-dock 或 `.pn`——前者不同屏，后者非 fixed 层且语义是篇间导航。
- ❌ 不恢复任何 sticky/absolute 顶部长条返回按钮。
- ❌ 不引入图标库——继续用「←」文本字符。
- ❌ z-index 不用 999 魔法数，不越过 NavBall(60)/lightbox(120)。
- ❌ 不在地图页与 admin 路由渲染本键。
- ❌ 不做文案的响应式双版本（恒定「← 回到地图」）。
- ❌ 不给已带可见文本的链接再叠 aria-label。

## 6. 验收清单（1440 / 1024 / 768 / 390 四档逐一过）

1. `/timeline`、`/list`、`/trip/:slug` 三页右下角均可见「← 回到地图」墨色胶囊；`/` 与 `/admin/**` 不渲染。
2. 在详情页滚到最底部：按钮不压 `.pn` 卡片（净空 ≥16px）；三档桌面 + 390 均通过。
3. timeline/list 滚到底：按钮不压 `.tl-end` / 名录尾卡。
4. 点击按钮跳回 `/`，地图页正常渲染且**无**返回键；从 `/` 深链直进 `/trip/x`（新标签）后点击仍能回到 `/`（验证非 history.back）。
5. 热区高度 ≥44px；键盘 Tab 可达，focus-visible 珊瑚描边清晰；回车跳转。
6. 390px：按钮完整可见、不横向溢出、避开 iPhone 底部安全区（env 生效）。
7. 灯箱打开时按钮被遮住、不可点（z:55 < 120）。
8. `prefers-reduced-motion: reduce` 下无进场/过渡动画。
9. 悬停（鼠标设备）底色变珊瑚、白字对比可读；触屏设备无 hover 残留。
10. 详情页顶部无任何返回元素残留（`.back-map` 已删净，`grep back-map` 无结果）。
