# Issue #32 设计规范：品牌更名「足迹」+ 双脚印 Logo（左大右小）

> 范围：frontend 全部站名与图标资产。`docs/prototype/**` 历史原型稿、
> `.scratch/feature-30-nav-ball/design.md` 历史验收记录，均不改。
> 本规范所有 SVG 已实际渲染核验（512 / 48 / 16px 三档），可直接复制使用。

---

## 0. 结论速览

**品牌一句话**：橙色 `--coral` 圆角方底（favicon 沿用 rx 128，系统自动裁圆即「圆底」）上两只白色小脚丫——成人脚左、儿童脚右（1 : 0.76），脚掌长椭圆 + 足跟圆重叠成足弓剪影，轻微外八、同基线站立；站名全面极简化为「足迹」，仅 PWA manifest name 保留「Up Journey」英文副标用于启动器检索。

### 逐处定稿表

| # | 位置（已核实行号） | 现状 | 定稿 |
| --- | --- | --- | --- |
| 1 | `frontend/index.html:10` | `<title>游迹 · Up Journey</title>` | `<title>足迹</title>` |
| 2 | `frontend/vite.config.ts:18` | `name: '游迹 · Up Journey'` | `name: '足迹 · Up Journey'` |
| 3 | `frontend/vite.config.ts:19` | `short_name: '游迹'` | `short_name: '足迹'` |
| 4 | `frontend/src/views/admin/AdminLoginView.vue:55` | `<h1>游迹 · 管理端</h1>` | `<h1>足迹 · 管理端</h1>` |
| 5 | `frontend/src/views/admin/AdminLoginView.vue:54` | `<div class="mark">🧭</div>` | `<div class="mark">` + 内嵌脚印 SVG（§2.2） |
| 6 | `frontend/src/views/admin/AdminLayout.vue:39` | `<span class="mark">🧭</span> 游迹 <span class="badge">管理端</span>` | `<span class="mark">` + 内嵌脚印 SVG（§2.2）`</span> 足迹 <span class="badge">管理端</span>` |
| 7 | `frontend/src/components/NavBall.vue:49` | 球内容 `🧭`（文本节点） | 球内容替换为内嵌脚印 SVG（§2.1） |
| 8 | `frontend/src/components/NavBall.vue:56` | `<span class="nb-brand">游迹</span>` | `<span class="nb-brand">足迹</span>` |
| 9 | `frontend/src/views/MapHome.vue:342` | `🧭 还没有足迹——` | `👣 还没有足迹——`（见 §2.4） |
| 10 | `frontend/public/favicon.svg` | 白罗盘整文件 | 整文件替换为双脚印 SVG（§1.3） |
| 11 | `favicon.ico` / `apple-touch-icon.png` / `icons/pwa-192.png` / `icons/pwa-512.png` / `icons/pwa-maskable-512.png` | 罗盘位图 | 按 §2.4 命令从新 SVG 重新生成（文件名不变） |

不改动项：`vite.config.ts` 的 `theme_color` / `background_color`（#F8F6F2）与 `description`（「家庭足迹」为通用名词，无「游迹」字样）；`index.html` 的 favicon `<link>` 三行（文件名不变）。

### 文案取舍理由

- **title 用「足迹」两字**，不带「Up Journey」：#30 已立极简先例；标签页/收藏夹/分享卡中 2 字最干净。英文副标的检索价值由 PWA name 承担，两处不必重复。
- **PWA manifest `name: '足迹 · Up Journey'`**：启动器设置页与商店检索场景需要更长的识别名，中英并列利于搜「足迹」和「journey」都命中；`short_name: '足迹'` 供桌面图标标签（4 字内不折叠）。
- **管理端 h1 与顶栏保留「管理端」标识**（h1「足迹 · 管理端」、顶栏「足迹 + badge 管理端」）：管理端是独立入口页，需要自述身份，结构与现状对称，改动最小。
- **NavBall 尾部 `nb-brand` 保留**，改「足迹」：它是展开菜单里的品牌落款（12px 灰字、letter-spacing 0.2em），与 #30 的胶囊菜单设计共存，不属于残留。

---

## 1. Logo 图形规格

### 1.1 形态决策

| 决策点 | 结论 | 理由 |
| --- | --- | --- |
| 脚印语言 | **脚掌长椭圆 + 足跟圆，二者重叠 ~16 单位**，交界自然收腰成足弓剪影 | 分离式（脚掌 + 独立脚跟点）在 16~32px 会读成两个感叹号「!!」（已渲染证实）；重叠式在任何尺寸都是连续的「脚丫」剪影。全部用 `ellipse`/`circle`，无 path |
| 大小比例 | **成人脚 : 儿童脚 = 1 : 0.76**（高 221 : 168，宽 120 : 90） | 落在需求带 0.75~0.8 内；0.8 以上大小感趋弱，0.75 以下儿童脚在 16px 消失 |
| 左右布局 | **成人脚在左、儿童脚在右** | 用户明确意象：大人带小孩 |
| 旋转 | **轻微外八：成人 -10°、儿童 +12°（脚尖朝外上）**，**同基线站立**（两脚跟底 y≈353 对齐），**不采用行走态** | 外八是亲子并肩站立的天然姿态，比直立多一分活泼；行走态的前后错位在 16px 会被误读为"没对齐"。儿童比成人大 2°，添一点孩童的雀跃 |
| 颜色 | 脚印纯白 `#FFFFFF`，底 `--coral #E8683A` | 与全站令牌一致；深色标签栏（≈#35363A）上 #E8683A 色块对比 ≈3.2:1，可辨，白脚印是主识别元素 |
| favicon 容器 | **沿用圆角方 rx 128，不改正圆** | ① rx 128/512 = 25% ≈ iOS squircle 圆角率，16px 下观感即圆，「圆底」意象成立；改正圆在 16~32px 栅格损失四角橙色面积，深色标签栏里识别块更小。② 各系统自行裁形：Android 走 maskable 满幅源、iOS 自裁圆角、桌面 PWA 原样显示——源图保持圆角方不会出现"圆中圆"二次裁切。③ 同名覆盖现有资产，manifest 与 `<link>` 零改动 |

### 1.2 几何参数（512 画布）

每只脚在**本地坐标系**（脚中心为原点）内定义，再用 `translate + rotate` 落位；双脚外再包一层 `scale(1.1)`（绕画布中心）放大到最终占幅。

| 部件 | 本地坐标 | 尺寸 | 备注 |
| --- | --- | --- | --- |
| 成人脚 · 脚掌 | `ellipse cx=0 cy=-45` | `rx=60 ry=78` | 长椭圆，长:短 = 1.3:1 |
| 成人脚 · 足跟 | `circle cx=0 cy=58` | `r=40` | 足跟宽 80 = 脚掌宽的 67%；与脚掌重叠 16 单位，腰线（足弓）宽 ≈28 |
| 成人脚 · 变换 | `translate(169 268) rotate(-10)` | 整脚跨 221 高 × 120 宽 | 逆时针 10°，脚尖朝左外八 |
| 儿童脚 · 脚掌 | `ellipse cx=0 cy=-34` | `rx=45 ry=60` | = 成人 × 0.756 |
| 儿童脚 · 足跟 | `circle cx=0 cy=44` | `r=30` | 与脚掌重叠 ~14 单位 |
| 儿童脚 · 变换 | `translate(341 292) rotate(12)` | 整脚跨 168 高 × 90 宽 | 顺时针 12°，脚尖朝右外八 |
| 全组放大 | `translate(256 256) scale(1.1) translate(-256 -256)` | — | 绕画布中心放大 1.1 倍 |

整体占幅与安全区（已按最终坐标核算）：

- favicon.svg（圆角方 512）：内容包盒 **304 × 241**，位于 x 104~408、y 135~376，光学居中；占画布宽 59%，四边距 ≥104 单位（≥20%），圆角裁切安全。
- maskable（满幅 512）：同一组脚印再乘 0.9，内容最远点距画布中心 ≈175 单位 < **204.8（80% 安全区半径）**，任意遮罩（圆 / 圆角方 / 花瓣）下双脚完整。

### 1.3 最终 SVG ①：`frontend/public/favicon.svg`（整文件替换）

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <!-- 足迹 logo：珊瑚圆角方底（rx 128，系统裁圆即"圆底"）+ 白色双脚印（左大右小，亲子并肩）；
       规格见 .scratch/feature-32-brand-footprints/design.md -->
  <rect width="512" height="512" rx="128" fill="#E8683A"/>
  <g transform="translate(256 256) scale(1.1) translate(-256 -256)">
    <!-- 成人脚（左 · 大）：脚掌长椭圆 + 足跟圆重叠成足弓，外八 -10° -->
    <g fill="#FFFFFF" transform="translate(169 268) rotate(-10)">
      <ellipse cx="0" cy="-45" rx="60" ry="78"/>
      <circle cx="0" cy="58" r="40"/>
    </g>
    <!-- 儿童脚（右 · 小 = 0.76 倍）：外八 +12°，与成人脚跟同基线 -->
    <g fill="#FFFFFF" transform="translate(341 292) rotate(12)">
      <ellipse cx="0" cy="-34" rx="45" ry="60"/>
      <circle cx="0" cy="44" r="30"/>
    </g>
  </g>
</svg>
```

### 1.4 最终 SVG ②：maskable 源（生成 `pwa-maskable-512.png`，也用于 `apple-touch-icon.png`）

与 ① 仅两处不同：**满幅橙底（无 rx、无透明）** + 脚印组再乘 **0.9**（80% 安全区，见 §1.2）。
实现时不落新文件到仓库——保存为 `/tmp/ft-maskable.svg` 后按 §2.4 命令出图：

```bash
sed 's|<rect width="512" height="512" rx="128" fill="#E8683A"/>|<rect width="512" height="512" fill="#E8683A"/>|; s|<g transform="translate(256 256) scale(1.1) translate(-256 -256)">|<g transform="translate(256 256) scale(0.99) translate(-256 -256)">|' frontend/public/favicon.svg > /tmp/ft-maskable.svg
```

（1.1 × 0.9 = 0.99，等效于"脚印组缩至 0.9"；改完可打开 `/tmp/ft-maskable.svg` 目检背景为满幅橙色。）

---

## 2. 各落位替换

### 2.1 NavBall 球（48px，`NavBall.vue:49`）

球本身已是 `--coral` 正圆（`border-radius: 50%`），内部只放**无底脚印 SVG**。无双脚印 emoji 可用，必须内嵌 inline SVG；viewBox 从 512 全画布**裁到内容紧贴区 `45 47 422 418`**，脚印即可放大占满球内（复用同一套几何，不另画）。

`NavBall.vue` 模板第 49 行 `🧭` 替换为：

```html
<svg class="nb-feet" viewBox="45 47 422 418" aria-hidden="true">
  <g fill="currentColor" transform="translate(256 256) scale(1.1) translate(-256 -256)">
    <g transform="translate(169 268) rotate(-10)">
      <ellipse cx="0" cy="-45" rx="60" ry="78"/>
      <circle cx="0" cy="58" r="40"/>
    </g>
    <g transform="translate(341 292) rotate(12)">
      <ellipse cx="0" cy="-34" rx="45" ry="60"/>
      <circle cx="0" cy="44" r="30"/>
    </g>
  </g>
</svg>
```

`<style scoped>` 配套两处：

```css
/* .nb-ball 内：删除原 font-size: 20px（emoji 尺寸，已无用），加： */
.nb-feet { width: 100%; height: 100%; display: block; }
```

- `fill="currentColor"` 继承 `.nb-ball` 的 `color: #fff`，球 hover/焦点样式不用动；`aria-hidden` + 既有 `aria-label="导航菜单"` 不变。
- viewBox 已含呼吸边：48px 球内脚印实宽 ≈34.6px，最远像素距圆心 22px < 半径 24px，不贴边（已渲染核验）。

### 2.2 管理端顶栏 mark（`AdminLayout.vue:39`；实际 32px，样式在 `admin.css:20`，盘点所称 34px 以代码为准）与登录页 mark（`AdminLoginView.vue:54`，52px）

与 §2.1 **同款 inline SVG**（viewBox 相同，仅外层容器不同），`.mark` 已是定宽高 flex 居中盒，svg 直接充满：

```html
<span class="mark"><svg class="mark-feet" viewBox="45 47 422 418" aria-hidden="true">…同 §2.1 内部两脚…</svg></span> 足迹 <span class="badge">管理端</span>
```

```css
/* admin.css（顶栏）与 AdminLoginView <style scoped>（.login-card .mark）各加一条： */
.mark-feet { width: 100%; height: 100%; display: block; }
/* 同时删除两处原 emoji 字号 font-size（admin.css .mark 无字号可不动；.login-card .mark 的 font-size: 26px 删除） */
```

32px 下脚印实宽 ≈23px、52px 下 ≈37.5px，足弓腰线均可辨（比例同 48px 核验结论）。

### 2.3 favicon.ico / PNG 全家生成命令（rsvg-convert + magick，二件套）

本机（macOS）当前两者均未安装，先装一次：

```bash
brew install librsvg imagemagick
```

栅格一律用 rsvg-convert（SVG 渲染质量优于 ImageMagick 内置），`.ico` 打包用 magick（rsvg-convert 不产 ico）。在 `frontend/public` 下执行：

```bash
cd frontend/public

# favicon.ico：16/32/48 三档（index.html sizes="48x48" 声明不变）
rsvg-convert -w 16 -h 16 favicon.svg > /tmp/ft16.png
rsvg-convert -w 32 -h 32 favicon.svg > /tmp/ft32.png
rsvg-convert -w 48 -h 48 favicon.svg > /tmp/ft48.png
magick /tmp/ft16.png /tmp/ft32.png /tmp/ft48.png favicon.ico

# apple-touch-icon：180，用满幅源（iOS 自裁圆角，不要预置圆角/透明）
rsvg-convert -w 180 -h 180 /tmp/ft-maskable.svg > apple-touch-icon.png

# PWA：any 用圆角方源；maskable 用满幅源（文件名与 manifest 声明保持一致）
rsvg-convert -w 192 -h 192 favicon.svg > icons/pwa-192.png
rsvg-convert -w 512 -h 512 favicon.svg > icons/pwa-512.png
rsvg-convert -w 512 -h 512 /tmp/ft-maskable.svg > icons/pwa-maskable-512.png
```

### 2.4 MapHome 空态 🧭（`MapHome.vue:342`）

**结论：换，🧭 → 👣。** 它是句子里的文字 emoji（同屏已有 🛫 / 👆 的 emoji 文案体系），不是品牌 logo，不应换成品牌 SVG；但罗盘是旧品牌的残响，`👣`（双脚印）与「还没有足迹」语义完全对应、各主流平台均可渲染，是顺势之举：

```diff
- 🧭 {{ currentYear === 'all' ? '还没有足迹——' : currentYear + ' 年暂无境内足迹——' }}
+ 👣 {{ currentYear === 'all' ? '还没有足迹——' : currentYear + ' 年暂无境内足迹——' }}
```

---

## 3. 验收清单

- [ ] **favicon 深色标签栏可辨**：`#E8683A` 圆角方在深/浅两种标签栏下均为醒目色块，白色双脚印清晰；16px 下验收标准为「两只白脚印、左大右小」可辨，**不要求**足弓腰线可辨（0.5px 级，允许融为剪影）；细节用 32px（HiDPI）核对。
- [ ] **三档脚印可辨不糊**：48px（NavBall 球）、32px（管理端顶栏 mark）、16px（标签页）下「左大右小」均可辨；SVG 透明底版本在珊瑚底上无锯齿脏边。
- [ ] **管理端两处 mark 正常**：顶栏 32px、登录页 52px 显示双脚印，白脚在 `--coral` 底上，无 emoji 残留。
- [ ] **PWA 安装图标正常**：`pwa-192/512.png` 为圆角方新 logo；`pwa-maskable-512.png` 满幅橙底，圆形/圆角方遮罩下双脚完整不贴边（内容距边 ≥26% 画布）；DevTools → Application → Manifest 显示 name「足迹 · Up Journey」、short_name「足迹」。
- [ ] **站名无残留**：`grep -rn "游迹" frontend/` 零命中；`docs/prototype/**` 与 `.scratch/feature-30-nav-ball/design.md` 为历史记录，白名单不改。
- [ ] **空态文案**：地图空态显示「👣 还没有足迹——」，emoji 正常渲染。
- [ ] `npm run build` 通过；部署后标签页 favicon、iOS 添加主屏、Android PWA 安装三端图标为新 logo。

---

## 附：渲染验证记录（本规范撰写时）

- 工具：macOS QuickLook（qlmanage）实渲染 SVG。
- 512px：双脚剪影完整、足弓腰线自然、外八姿态与同基线成立，左大右小一目了然。
- 48px 球模拟（圆形容器 + 裁边 viewBox）：脚印占球宽 ≈72%，双脚可辨不贴边。
- 16px 栅格（放大检视）：橙色块内两道白色脚印、左大右小可辨，符合验收口径。
- maskable 512：满幅橙底、脚印居中，安全区核算通过。
