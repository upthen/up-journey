# 设计规范：地图工具栏新增「去记录」按钮（跳转管理端录入）

> 范围：仅 `frontend/src/components/MapToolbar.vue`（仅 MapHome 引用）。其余页面与管理端样式零污染。
> 样式全部写在该组件 `<style scoped>` 内，沿用 `maptb-` 前缀；不动 `flow.css`。
> 前置先例：`.scratch/feature-31-map-toolbar/design.md`（容器落位、共存规则、扩展预留均沿袭，不重复论证）。

---

## 0. 决策摘要（一句话）

**图标 📝（font-size 与 🎯 统一 15px，不做单独调号）；排序「去记录」放 🎯 下方（先例 §3 的"向下滑落追加"规则）；本期不引入 `.maptb-sep` 分隔线（阈值仍为 >4 枚）；跳转用 `<router-link>` 指 `{ name: 'admin-trip-new' }`。**

---

## 1. 图标方案：📝

### 1.1 候选排除

| 候选 | 结论 | 理由 |
| --- | --- | --- |
| ➕ | **排除（有真坑）** | 地图工具栏语境下加号是「放大」的世界惯例（ECharts toolbox / Leaflet zoom 均如此），放进步工具栏必被误读为 zoom in |
| 📸 | 排除 | 语义是「传照片」，但录入入口是整张旅行表单（行程、日期、故事、照片），以偏概全 |
| 🧳 | 排除 | 行李 = 旅行内容意象，与全站「脚印/足迹」叙事（👣 空态、脚印 SVG 导航球）撞车；且读不出「动作」——看不出点了会发生什么 |
| ✏️ | 次选 | 铅笔偏「编辑既有内容」（对应 /admin/trips/:id），弱于「新写一篇」 |
| **📝** | **选定** | memo 便笺 = 「写一篇记录」，与按钮语义「去记录一次旅行」直译对齐；且 memo 自带"书写中"的动作感，是候选里唯一同时表达「写」与「新内容」的 |

### 1.2 尺寸与视觉平衡

- **直接沿用 `.maptb-btn`（36×36 + font-size:15px），不给 📝 单独调字号。**
- 依据：feature-31 规范 §2.2 写的 18px 是设计稿口径，实装代码已收敛为 15px（以代码为准）；两枚 emoji 同 font-size 时天然基线对齐，且按钮外框（36×36 圆 + hover 底）才是视觉对齐的主体——观察者对齐的是"两枚等大的圆形按钮"，字形本身的 1–2px 光学差被圆形外框吸收。
- 若验收时 📝 在个别平台渲染明显偏小/偏大（emoji 字形跨平台差异），允许在该元素上加 `line-height: 1` 居中修正，**禁止**为此引入独立字号或第二套按钮类。

---

## 2. 按钮规格

与 🎯 完全同款，仅元素从 `<button>` 换为 `<router-link>`（渲染为 `<a>`，需补 a 的默认样式复位）：

| 项 | 值 |
| --- | --- |
| 元素 | `<router-link class="maptb-btn maptb-go" :to="{ name: 'admin-trip-new' }">📝</router-link>` |
| 尺寸 | 36×36，圆角 999，透明底（白胶囊即底） |
| hover | `background: var(--bg)`（既有 `.maptb-btn:hover`，a 同样命中） |
| active | `transform: scale(0.94)`（既有） |
| focus-visible | `outline: 2px solid var(--coral-deep); outline-offset: 2px`（既有，对 `<a>` 同样生效） |
| aria-label | `去记录`（定稿。与 🎯 的「还原地图视野」同模式：图标钮 aria 必填，文案即动作本身；「去录入旅行」偏系统腔，「新建旅行记录」是页面标题不是动作） |
| title | `去记录`（定稿，与 aria-label 一致） |
| **a 复位（新增 `.maptb-go`）** | `text-decoration: none; color: inherit;` —— 抵消 `<a>` 默认下划线与链接色，使其与 `<button>` 视觉完全一致 |

### 最终 CSS（组件 scoped 内，新增部分）

```css
.maptb-go {
  /* router-link 渲染为 <a>，复位浏览器默认，使其与 .maptb-btn 的 button 外观一致 */
  text-decoration: none;
  color: inherit;
}
```

（`.maptb-btn` 全部既有样式不动；`prefers-reduced-motion`、≤640px 两条媒体查询自动覆盖新钮，零改动。）

### 模板最终形态

```html
<div class="maptb">
  <button class="maptb-btn" aria-label="还原地图视野" title="还原地图视野" @click="emit('reset')">🎯</button>
  <router-link class="maptb-btn maptb-go" :to="{ name: 'admin-trip-new' }" aria-label="去记录" title="去记录">📝</router-link>
</div>
```

---

## 3. 排序与分组

### 3.1 排序：📝 在 🎯 **下方**

- 先例 §3 明文：新按钮"直接向下滑落追加"——🎯 的位置是 #32 迭代时用户已建立肌肉记忆的落点，不动它，零回归；
- 语义顺序也自洽：上 = 地图操作（看/调），下 = 跳转动作（离开地图去写），"离开"类动作居末位符合竖排工具栏惯例（如编辑器工具栏的账号/退出总在底部）。

### 3.2 分隔线：**本期不引入 `.maptb-sep`**

- 分割线的存在意义是"隔开两**组**"——每组至少要有两枚钮，分割线才表达分组。现在两组各只有一枚钮，一条线隔开两个孤点，纯属视觉噪音（胶囊总高仅 84px，一条 24px 宽的线占比突兀）；
- 先例的阈值（"超过 4 枚按钮后再引入"）**维持不变**；将来出现第三类（如缩放 +/−）时再启用，CSS 就用 feature-31 §3 那份（`width:24px; height:1px; background:var(--hairline); margin:2px 0;`），本期不把该类写进组件（防死样式原则不变）；
- 🎯 与 📝 语义不同类的问题，靠**排序**（操作在上、跳转在下）+ hover/title 澄清即可，不需要线。

---

## 4. 跳转行为：`<router-link>`，指命名路由

### 4.1 结论

用 `<router-link :to="{ name: 'admin-trip-new' }">`。MapToolbar 在 router 作用域内（MapHome 挂在 `<router-view>` 下），SPA 内导航最简；不开新标签（地图页无任何表单状态，离开无损失；管理端是同一 SPA 的路由，新开标签反而造成双会话困惑）。

### 4.2 守卫链路核查（已读 `frontend/src/router/index.ts` 核实，无坑）

1. `/admin/trips/new` 带 `meta.auth` → `beforeEach` 先 `await api.admin.session()`；
2. 未登录：`return { name: 'admin-login', query: { next: to.fullPath } }` → 登录页 URL 为 `/admin/login?next=%2Fadmin%2Ftrips%2Fnew`，登录成功后按 `next` 直达录入表单。**链路闭合**；
3. 503（服务端未配管理密码）：守卫已带 `unconfigured=1`，登录页直接显示配置指引而非盲试密码（#23 既有行为）——新按钮不感知、不处理，属正确分层；
4. 已登录：直达表单，一次点击到位。

### 4.3 title 是否说明「未登录将先跳登录页」：**不写**

- title 保持纯动作语义（`去记录`），与 🎯 文案风格对齐；"未登录先跳登录"是全站统一守卫行为，属 Web 惯例，写进 tooltip 是噪音；
- 真正需要提示的异常（未配置密码 503）由登录页承接，tooltip 说了也帮不上。

---

## 5. z-index / 避让

无新增风险：容器 `.maptb` 的定位、z-index:40、pointer-events 防穿透全部不动，仅胶囊纵向自然长高（56→84px，居中锚点不变）；左右缘空带（≥260px）余量充足，`.panel` 开启时盖住工具栏的既有共存规则原样适用。

---

## 6. 验收清单

**渲染（四档宽度 1440 / 1024 / 768 / 390 各过一遍）**

- [ ] 白色竖胶囊内两枚 36×36 圆钮：上 🎯、下 📝，间距/内边距与改动前一致；📝 无下划线、无链接蓝紫色（a 复位生效）。
- [ ] 胶囊仍垂直居中，与 stats-flag / stage-chip / map-hint / legend-chip / year-dock 无重叠、间隙 ≥40px。
- [ ] 两枚钮 hover 均出 `var(--bg)` 圆底；按压缩放 .94；Tab 可达两钮、焦点环 coral-deep 2px 可见，Enter 在 📝 上触发跳转。
- [ ] DevTools：router-link 渲染为 `<a>` 且带 `aria-label="去记录"`、`title="去记录"`；按住钮拖动不产生地图漂移（pointer-events 防穿透未破坏）。

**跳转链路**

- [ ] 已登录：点 📝 SPA 内直达 `/admin/trips/new` 录入表单（无整页刷新）。
- [ ] 未登录：点 📝 → `/admin/login?next=%2Fadmin%2Ftrips%2Fnew` → 登录成功后直达录入表单。
- [ ] 服务端未配置管理密码：点 📝 → 登录页显示配置指引（unconfigured 态，#23 既有行为不被破坏）。
- [ ] 浏览器返回（Back）回到地图页，视野/年份筛选无异常重置。

**390px 专查**

- [ ] 工具栏 `right:12px` 居中，双钮胶囊完整可见、可点，不与 legend-chip / stage-chip / year-dock 相碰；打开景点面板时被面板盖住（预期），关闭后原位恢复。

**回归**

- [ ] 🎯 还原视野功能与改动前完全一致（位置、动画、状态零变化）。
- [ ] TimelineView / JournalListView / TripDetailView / 管理端均不出现新按钮；`flow.css` 零改动，全局搜索无 `maptb-` 泄漏。
- [ ] 构建（vue-tsc + vite build）通过。

---

## 修订（2026-09-13 · 用户 grilling 确认）

原 §4 的跳转目标 `/admin/trips/new` 语义错误——「直达管理端」不等于「直达新建表单」，目标页应由用户在管理端内自主选择。经确认修订：

- 目标：`/admin/trips`（管理端·旅行管理列表）
- 打开方式：**新标签页** `<a href="/admin/trips" target="_blank" rel="noopener">`，地图页保留不动
- 图标文案：维持 📝「去记录」；其余规格（36×36、hover/active/focus、排序、无分隔线）不变
- 鉴权：未登录时新标签内由既有守卫拦至登录页，登录后落在管理端列表——鉴权链路不变
