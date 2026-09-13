# UI 验收第三轮报告：移动端专项（ui-audit-r3）

日期：2026-09-13 · 执行：UI 验收大师（章程 `docs/agents/ui-acceptance-master.md`）
产出：新增 issue **#34–#38**（P1×1 / P2×2 / P3×2），全部带截图证据与 file:line 修复建议。

## 方法

- 双轨：只读子代理静态审查（根因定位 file:line）→ 主代理浏览器逐一复现，**复现成立才立 issue**；
- 视口：390×844 专项（touch 仿真），关键缺陷在 1440 交叉验证（叠字跨端、贴边跨端显形）；
- 工具备注：IAB 截图管线间歇性冻结（r2 已记录过同类问题），展示端早期截图用 IAB 完成，
  后半程与管理端切 **headless Chromium + CDP**（`shot.mjs` / `admin.mjs` / `measure.mjs`，
  含 touch 仿真与登录流程），两套环境结论一致；
- 环境全程本地 dev server + 演示数据（4 篇旅行），未触碰 NAS 生产库，未增删业务数据。

## 缺陷清单

| # | 定级 | 模块 | 标题 | 一行根因 |
|---|---|---|---|---|
| #34 | P1 | admin | 390 下管理端内容 1086/1104px 且被 body overflow-x:hidden 裁死，右侧 ~700px 永久不可达 | `admin.css:26` 窄屏 `1fr` 退化为 minmax(auto,1fr)，被表格列宽合计（1002/1020px）撑爆 |
| #35 | P2 | public | `.page-pad` shorthand 覆盖 `.wrap` 左右内边距，三个文本页窄视口内容贴屏幕边缘 | `flow.css:205` 同特异性后声明整段覆盖 `flow.css:148`；桌面靠 max-width 居中 margin 掩盖 |
| #36 | P2 | public | 地图相邻景点标签叠字不可读（1440 与 390 均复现，2024 筛选后仍叠） | `MapHome.vue:153` `moveOverlap:'shiftY'` 只纵向平移，水平相邻点错开后仍交叠 |
| #37 | P3 | public | 灯箱零可见控件：无 ✕/翻页/计数，仅键盘 ←/→，移动端无手势只能盲点关闭 | `App.vue:20-23` 模板只有一张 img；`.cap` 样式存在但未使用 |
| #38 | P3 | public | 「回到地图」悬浮胶囊常驻右下，窄屏阅读时盖住提示框/信息卡文字 | `BackHome.vue` fixed 常驻，页面无底部让位预留 |

## 走查中确认正常（未立案）的项

- 展示端四页 390 均无水平溢出（`scrollWidth` 全等 390）；
- 景点面板：✕ 可关、面板布局/图组/链接卡在 390 表现良好（回归 #11 成立）；
- 涟漪圆点本体可点（命中层生效，回归 #17 成立）、年份筛选 chips 触控目标充足、过滤联动正常；
- 编年页年份标题不再 sticky 压卡、轴线/圆点对齐正常；
- 名录卡片封面/标签 wrap 正常、无封面兜底不适用（演示数据全有封面）；
- 详情页两列照片墙、行程地图、按天行程、上一篇卡在 390 排版正常；
- 管理端登录页 390 完好；EP 弹窗未见固定宽溢出（回归 #20 方向成立）；
- 灯箱打开时 body 滚动锁正常（回归 #23 子项成立）、图片加载失败有文案兜底（未实拍，代码有 `lb-fallback`）。

## 修复批次建议

1. **批次 A（一行修复，性价比最高）**：#34 `admin.css:26` `1fr`→`minmax(0,1fr)`；#35 `flow.css:205` shorthand 改分写。两个合计两行 CSS，消除 P1+P2 主体；
2. **批次 B（#34 收尾）**：编辑页 `el-col :xs="24"` 断点、`body overflow-x:hidden` 作用域收窄到展示端；
3. **批次 C（#36）**：小屏标签 formatter 减负 + `hideOverlap` 兜底（依赖 #17 命中层已就位）；
4. **批次 D（P3）**：#37 灯箱控件条 + 触摸手势（顺带启用闲置的 `.cap`）；#38 胶囊滚动感知隐藏或底部让位。

遵循 AGENTS.md Git workflow：`fix/<issue#>-<slug>` 新分支，按编号顺序依次合回 main，
commit 沿用 `fix(scope): 描述（#N）`，合并即关闭对应 issue。

## 覆盖矩阵

| 页面/模块 | 390 走查 | 交叉验证 | 结果 |
|---|---|---|---|
| `/` 地图首页（hero/展开/面板/筛选/圆点） | ✅ | 1440 | #36 |
| `/timeline` 编年（头部/卡片/天行/悬浮件） | ✅ | — | #38（与详情页同源） |
| `/list` 名录（标题/卡片/标签） | ✅ | — | #35 |
| `/trip/:slug` 详情（hero/正文/照片墙/灯箱/信息卡/小地图） | ✅ | — | #35 #37 #38 |
| `/admin/login` | ✅ | — | 正常 |
| `/admin/trips` 列表（筛选条/表格） | ✅ | headless 实测 1086px | #34 |
| `/admin/trips/1` 编辑（表单/封面/路线/景点表） | ✅ | headless 实测 1104px | #34 |
| 管理端弹窗 | 未深走（「添加景点」为行内添加，非弹窗） | — | 回归 #20 方向成立 |

## 环境与产物记录

- 证据：`evidence/01–22*.png`（已入库，issue 内以 raw 链接引用）；
- 工具：`shot.mjs`（CDP 截图，支持 touch/scroll/click/eval）、`admin.mjs`（登录后多页连拍）、
  `measure.mjs`（溢出与可达性测量）；本地专用，不影响仓库；
- 已知环境问题：IAB 截图管线间歇冻结（重开标签/等待可部分恢复），与 r2 记录一致，
  建议后续验收直接默认 headless Chromium + CDP 路径。

## 修复轮（同日）

#34–#38 已全部修复合入 main 并关闭，反馈环 `verify.mjs` 12/12 全绿：

| Issue | 修复分支/合并 | 关键改动 | 390 症状 | PC 闸门 |
|---|---|---|---|---|
| #34 | fix/34-admin-narrow-viewport → 625cd43 | `admin.css:26` 轨道 `minmax(0,1fr)`；编辑表单 `:xs="24"` 单列 | scrollWidth 1086/1104→390，表格内部滚动可达操作列 | pc2：1440 布局与基线一致 |
| #35 | fix/35-page-pad-zero-padding → bdee0ae | `.page-pad` 分写上下；`.wrap` max-width `+2*--pad` 补偿 | padding-left 0→20px | pc1：内容列 1120/h1 left=160 与基线一致（桌面零变化） |
| #36 | fix/36-map-label-declutter → e6ef064 | 应用层像素聚类，每簇一标签；小屏标签去年份缩字号 | 交叠 5 对→0 | pc4：1440 交叠 2→0（两端一致修复） |
| #37 | fix/37-lightbox-controls → 85b7f51 | ✕/‹›/N-M 控件条 + 触屏滑动翻页 + role=dialog | 控件齐全 | pc6：桌面同样获得控件（预期增强） |
| #38 | fix/38-backhome-overlap → 3054788 | ≤640 下滑收起/上滑即回（偏离规范 §2.6 已在 issue 记录理由） | 下滑后 opacity 1→0 | pc5：桌面恒显不变 |

验证脚本：`verify.mjs`（390 症状断言 + 1440 PC 基线闸门，基线 `pc-baseline.json`）；
修复后证据 `23–27-fixed-*.png`。`vue-tsc` 与生产构建通过。
