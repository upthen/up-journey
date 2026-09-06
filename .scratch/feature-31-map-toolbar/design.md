# Issue #31 设计规范：地图页操作栏（本期仅「一键还原视野」）

> 范围：仅 MapHome（地图页）。其余三个展示页与管理端严禁受影响。
> 样式全部写在组件 `<style scoped>` 内（建议新组件 `frontend/src/components/MapToolbar.vue`），
> 类名统一前缀 **`maptb-`**。⚠️ 禁用 `mt-` 前缀（与 Tailwind 的 `mt-*` margin-top 语义撞车），
> `mtb-` 又太隐蔽，取 `maptb-` 明确无歧义。不得在 `flow.css` 或任何全局层新增类。

---

## 0. 现状坐标备忘（避让依据，均已核实 flow.css / MapHome.vue）

| 元素 | 位置 | z-index |
| --- | --- | --- |
| `.stats-flag`（统计卡） | fixed left:16 top:78，max-width 220px，高约 120px（底缘 ≈198px）；**≤900px 整体 display:none** | 40 |
| `.map-hint`（提示 chip） | fixed top:78 水平居中，≤640px 换行最宽 86vw | 40 |
| `.panel`（地点故事面板） | fixed top:84 bottom:12 right:12，width min(400px, 100vw−24)，打开时占右缘最多 412px | 50 |
| `.stage-chip` | fixed left:16/12 bottom:92/84 | 40 |
| `.legend-chip` | fixed right:16/12 bottom:92（≤640 抬到 138） | 40 |
| `.year-dock`（年份坞） | fixed 底中 bottom:20，max-width calc(100vw−32px) | 40 |
| NavBall 球 | fixed (16,16)，z:60（#30） | 60 |
| `.veil` 开场帷幕 / `.lightbox` | inset:0 | 80 / 120 |
| 地图 | ECharts geo（china.json），fixed inset:0 z:1，roam 开启，center [110,33]、zoom 1.15、scaleLimit {min:1, max:14} | 1 |

地图左右两缘的垂直中部（约 35%–65% 视口高度带）四档宽度下均为空，是操作栏的落位空间。

---

## 1. 位置与形态：三个方案对比

### 方案 A「右缘中部竖条」

`right:16 top:50%` 垂直竖排。符合缩放/工具栏靠右的地图软件惯例（ECharts toolbox、Leaflet 控件皆在右上/右缘），右手鼠标路径最短。

- **致命伤：`.panel` 撞车。** 面板打开时占右缘 top:84–bottom:12、宽 ≤412px、z:50，
  竖条（z:40）会被整个压在面板下面——恰恰是用户正在看故事、拖乱地图后再想还原的场景
  并不多，但"面板开着工具栏消失/被盖"的观感很糟糕；若做联动隐藏/位移，则与面板状态耦合，
  回归面扩大。
- 右下还有 `.legend-chip`（bottom:92）、右上有面板，右缘空间实际被夹得很窄。

### 方案 B「左缘中部竖条」（推荐）

`left:16 top:50% translateY(-50%)` 垂直竖排。

- **避让天然成立，零联动**：左上 stats-flag 底缘 ≈198px（且 ≤900px 隐藏）、左下
  stage-chip 顶缘 ≈ vh−122px，中间是一条 ≥260px（768×640 最矮档实测 ≥100px）的空带；
  `.panel` 永远在右侧，几何上不相交；NavBall 在顶角不冲突。
- 缺点：与地图软件"控件靠右"的肌肉记忆略反——但全站只有这一个按钮，且用户在地图页
  的注意力在中部地图本身，左缘空带反而最安静、最不与内容抢。

### 方案 C「贴 year-dock 横条」

在年份坞左端外侧并一枚圆钮（或并入坞体）。

- 390px 下 year-dock 已 `max-width: calc(100vw - 32px)` 横向滚动，再叠按钮必然挤压年份按钮；
- 语义混杂：「还原视野」是地图操作，「年份筛选」是数据过滤，同坞职责不清；
- 与 legend/stage chip（bottom:84/92 同一水平带）拥挤。

### 结论：**推荐方案 B（左缘中部竖条）**

理由：唯一一个不需要与任何既有元素做状态联动的落位；本期只有一枚按钮，宁可位置安静，
也要保证"任何时候点得到、看得见"。右缘惯例的损失用「按钮足够醒目 + title 提示」弥补。

---

## 2. 操作栏与按钮规格（方案 B）

### 2.1 容器（竖条）

```
.maptb {
  position: fixed; left: 16px; top: 50%; transform: translateY(-50%);
  z-index: 40;                       /* 与 stage/legend/stats 同档 */
  pointer-events: none;              /* 防穿透，同 .nb 模式 */
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 6px;
  background: rgba(255,255,255,.92); backdrop-filter: blur(12px);  /* 同 stats-flag 材质 */
  border-radius: 999px; box-shadow: var(--shadow);
}
.maptb button { pointer-events: auto; }
```

- 本期仅 1 枚按钮 → 胶囊实际尺寸 ≈ **56×56px**（6px 内边距 + 44px 钮）。
- 避让计算（最不利档 768×640）：钮带 y ≈ 298–354；stats-flag 底缘 198（间隙 100px）、
  stage-chip 顶缘 518（间隙 164px）→ 通过。视口高 <430px 才会贴碰撞，属异常窗口，不做特判。

### 2.2 按钮

| 项 | 值 |
| --- | --- |
| 尺寸 | 44×44px（热区即视觉，≥44px 网格） |
| 图标 | `🎯`（U+1F3AF，聚焦/定位语义），font-size 18px，居中；全站无图标库，延续 emoji 语言（🧭/🗺️ 同族） |
| 背景 | 透明（胶囊白底即底）；hover `background: var(--bg)`（同 year-dock 按钮惯例） |
| 按压 | `:active { transform: scale(.94) }`，transition .18s |
| focus-visible | `outline: 2px solid var(--coral-deep); outline-offset: 3px`（与 nb-ball 同款） |
| aria | `aria-label="还原地图视野"`（图标钮必须有）；`title="还原地图视野"`（原生 tooltip，桌面 hover 可见） |
| 状态 | **始终可点**。不做"已在初始视野就禁用"的智能态——roam 后的 center/zoom 需监听 `georoam` 事件同步，状态机是 bug 温床，收益趋零 |
| 颜色 | 图标原生彩色，不加滤镜；不使用 coral 实色底（与 NavBall 球区分层级：导航是主、工具是次） |

### 2.3 触发行为（实现建议，非样式）

```ts
// MapHome.vue 内，还原 = 最小 merge setOption，严禁 buildOption() 重建（会重挂系列/选中态）
chart.value?.setOption(
  { geo: { center: [110, 33], zoom: 1.15 } },
)
```

- ECharts 对 geo `center/zoom` 的 setOption 变更走更新动画，由
  `animationDurationUpdate` / `animationEasingUpdate` 控制 → 在 buildOption 的 geo 节点加：
  `animationDurationUpdate: 450, animationEasingUpdate: 'cubicOut'`（无过冲、落点干净，
  与全局 .22,1,.36,1 的克制感一致；ECharts 不支持自定义 bezier 字符串，cubicOut 最接近）。
- `prefers-reduced-motion: reduce` 时（`matchMedia` 判断）置 `animationDurationUpdate: 0`，
  回位瞬时完成。
- 年份切换本身会 `setOption(buildOption())` 重建、视野随之复位——与按钮共存无冲突，
  按钮不做"记住每年视野"之类的智能。

---

## 3. 未来扩展预留（本期只做容器，不做按钮）

- 竖排 `gap: 6px`：后续按钮（如缩放 +/−、图例开关）直接向下滑落追加，胶囊自动变长；
- 超过 4 枚按钮后再引入分组分割线 `.maptb-sep { width: 24px; height: 1px; background: var(--hairline); margin: 2px 0; }`——本期不写这个类，防死样式；
- 新按钮沿用 2.2 全套规格（44px、emoji 18px、aria-label 必填）；
- 容器始终垂直居中：≤4 枚按钮（总高 ≤220px）避让计算均成立，超过则另开 issue 重新规划锚点。

---

## 4. 共存规则

| 场景 | 行为 |
| --- | --- |
| `.panel` 打开 | 桌面：面板占右缘，左缘工具栏**原位可用**（地图 roam 未被锁，还原仍有意义）；≤640px：面板宽 100vw−24 盖住工具栏（z 50 > 40），属预期——读故事时不需要地图操作，不做联动隐藏 |
| 年份筛选 / year-dock | 无几何交集；年份切换重建即复位，与按钮语义不冲突 |
| `.map-hint` / stats-flag / stage / legend chip | 垂直/水平均错开（见 0 与 2.1），零改动既有元素 |
| 开场帷幕 `.veil`（z 80） | 帷幕期间工具栏被盖住不可点，自动成立，不做特判 |
| 相册灯箱 `.lightbox`（z 120） | 压住工具栏，合理 |
| NavBall 球 | 左上角与左中无交集；z 60 > 40 亦无重叠可能 |

---

## 5. 移动端（≤640px，基准 390×844）

- 容器 `left: 12px`（与 ≤640 档 chip 的 12px 边距一致），`top: 50%` 不变；
- 按钮 44×44 不缩水（触屏热区底线）；
- 390 档实测：stats-flag 已隐藏、map-hint 换行后底缘 ≈205px、stage/legend chip 顶缘 ≈716px，
  工具栏带 y ≈ 400–456，两侧间隙均 >200px；
- 不做贴边半隐、不做拖拽换位。

---

## 6. 边界与负向清单

- **本期只放「还原视野」一枚按钮**。不做缩放 +/−、指北针、全屏、截图、图例开关——要加走后续 issue，按第 3 节规则追加；
- **禁用 ECharts 原生 `toolbox` 组件**（样式脱离设计体系，且捆着导出/数据视图等无关功能）；
- 不做"视野偏离初始值才出现/才禁用"的智能态（见 2.2）；
- 不做回位飞线、惯性插值等花哨动画——setOption 更新动画（450ms cubicOut）即全部；
- 不做可见的自定义 tooltip 气泡、不做文字标签（`title` + `aria-label` 足够）；
- 不做拖拽换位、位置记忆、滚动联动显隐；
- 不在 `flow.css` 加任何 `maptb-` 全局类，不碰管理端样式；
- 不改第 0 节列出的任何既有元素坐标/z-index；组件样式不得溢出到其他视图（仅 MapHome 引用）；
- 按钮不进 NavBall 菜单（导航三入口职责单一，地图工具是页面级控件）。

---

## 7. 验收清单（验收者逐条勾选）

**通用（四档宽度 1440 / 1024 / 768 / 390 各过一遍）**

- [ ] 左缘中部出现白色竖胶囊，内含一枚 🎯 圆钮；无其他新增按钮。
- [ ] 胶囊垂直居中于视口，与 stats-flag（≤900px 已隐藏）/ stage-chip / map-hint / legend-chip / year-dock 均无重叠、间隙 ≥40px。
- [ ] 拖拽 + 滚轮缩放把地图弄乱后点 🎯：地图以 450ms 平滑动画回到 center [110,33] / zoom 1.15，无跳帧、无白屏、无地图重挂（景点选中/tooltip 状态不被清）。
- [ ] 缩放到 scaleLimit 边界（1 或 14）后还原仍正常。
- [ ] 开启系统"减弱动态效果"后，还原瞬时完成无动画。
- [ ] 键盘 Tab 可达按钮，Enter 触发还原；焦点环（coral-deep 2px）可见。
- [ ] DevTools：按钮带 `aria-label="还原地图视野"`；容器/按钮 pointer-events 不穿透地图（按住按钮拖不出地图漂移）。

**共存专查**

- [ ] 点开任一景点面板（桌面档）：面板完整盖住右缘，左缘工具栏仍可见、可点、还原有效。
- [ ] 390px 打开面板：工具栏被面板盖住（预期），关闭面板后工具栏原位恢复。
- [ ] 切换年份筛选：视野复位（既有行为），再拖乱再点 🎯 仍有效。
- [ ] 开场帷幕期间工具栏不可见、不可提前点出；「展开地图 ↓」后正常出现。

**回归**

- [ ] 管理端任一页面外观与改动前一致（样式零污染）。
- [ ] `flow.css` 零改动（本 issue 样式全在组件 scoped 内）；全局搜索无 `maptb-` 泄漏。
- [ ] TimelineView / JournalListView / TripDetailView 不出现该工具栏。
- [ ] 构建（vue-tsc + vite build）通过。
