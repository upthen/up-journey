// ui-audit-r3 修复反馈环：390 症状断言（红→绿）+ 1440 PC 回归闸门
// 用法: node verify.mjs            # 全量跑，输出 PASS/FAIL JSON
//       node verify.mjs --baseline # 首跑记录 PC 基线到 pc-baseline.json
import { spawn } from "node:child_process";
import { writeFileSync, readFileSync, existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SHELL = process.env.HOME + "/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell";
const EV = "http://localhost:5173";
const TRIP = EV + "/trip/yun-nan-huan-xian-cong-dian-chi-dao-yu-long-2024";
const BASELINE = process.argv.includes("--baseline");

const profile = mkdtempSync(join(tmpdir(), "verify-"));
const chrome = spawn(SHELL, [`--remote-debugging-port=0`, `--user-data-dir=${profile}`, `--no-first-run`, `--hide-scrollbars`, `--window-size=1440,900`, "about:blank"], { stdio: ["ignore", "pipe", "pipe"] });
const wsUrl = await new Promise((res, rej) => { let b = ""; chrome.stderr.on("data", d => { b += d; const m = b.match(/DevTools listening on (ws:\/\/\S+)/); if (m) res(m[1]); }); setTimeout(() => rej(new Error("chrome timeout")), 15000); });
const ws = new WebSocket(wsUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let msgId = 0; const pend = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); } };
const send = (method, params = {}, sessionId) => new Promise((res, rej) => { const i = ++msgId; pend.set(i, m => m.error ? rej(new Error(method + " " + JSON.stringify(m.error))) : res(m)); ws.send(JSON.stringify({ id: i, method, params, sessionId })); });

let targetInfos = null;
for (let i = 0; i < 20; i++) { const r = await send("Target.getTargets"); targetInfos = r.targetInfos; if (targetInfos?.find(t => t.type === "page")) break; await new Promise(r => setTimeout(r, 500)); }
const { sessionId } = await send("Target.attachToTarget", { targetId: targetInfos.find(t => t.type === "page").targetId, flatten: true });
const S = (m, p) => send(m, p, sessionId);
await S("Page.enable");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ev = async expr => {
  const r = await S("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error("EVAL " + JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 300));
  return r.result?.value;
};
const setVP = async (w, h, mobile) => { await S("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: mobile ? 2 : 1, mobile }); };
const nav = async (url, settle = 2800) => { await S("Page.navigate", { url }); await sleep(settle); };
// 触摸点击 DOM 定位元素
const touchEl = async (finder) => {
  const pt = await ev(`(() => { const el = (${finder}); if (!el) return null; el.scrollIntoView({block:'center'}); const r = el.getBoundingClientRect(); return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}); })()`);
  if (!pt) throw new Error("touchEl: not found " + finder.slice(0, 60));
  const { x, y } = JSON.parse(pt);
  await S("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y }] });
  await S("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
};

const overlapCheck = `(() => {
  const c = window.__ujChart; if (!c) return { err: 'no-chart' };
  const list = c.getZr().storage.getDisplayList(false);
  const rects = [];
  list.forEach(el => {
    try {
      if (el.invisible) return;
      const t = el.style && el.style.text;
      if (typeof t !== 'string' || !t.trim()) return;
      const r = el.getBoundingRect().clone();
      const m = el.getComputedTransform();
      if (m) r.applyTransform(m);
      if (r.width > 0 && r.height > 0) rects.push({ text: t.slice(0, 14), x: r.x, y: r.y, w: r.width, h: r.height });
    } catch (e) {}
  });
  const pairs = [];
  for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
    const a = rects[i], b = rects[j];
    const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
    const oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
    if (ox > 2 && oy > 2) pairs.push(a.text + ' × ' + b.text);
  }
  return { textCount: rects.length, overlaps: pairs, overlapCount: pairs.length };
})()`;

const results = {};
const record = (k, pass, detail) => { results[k] = { pass, detail }; console.log((pass ? "PASS" : "FAIL") + "  " + k + "  " + JSON.stringify(detail)); };

// ---------- 登录（一次，cookie 全程有效） ----------
await setVP(390, 844, true);
await nav(EV + "/admin/login");
await ev(`(() => { const i = document.querySelector('input[type=password]'); const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; s.call(i, 'local-dev-only'); i.dispatchEvent(new Event('input', { bubbles: true })); return 1; })()`);
await touchEl(`[...document.querySelectorAll('button')].find(b => b.textContent.replace(/\\s/g,'').includes('登录'))`);
await sleep(2200);
const loggedIn = await ev("location.pathname") === "/admin/trips";
if (!loggedIn) throw new Error("登录失败，后续管理端检查无效");

// ---------- 移动端 390 ----------
await nav(EV + "/list");
record("m1.list-pad(#35)", await ev(`parseFloat(getComputedStyle(document.querySelector('main.wrap.page-pad')).paddingLeft)`) >= 18,
  await ev(`getComputedStyle(document.querySelector('main.wrap.page-pad')).paddingLeft`));

await nav(EV + "/admin/trips");
const m2sw = await ev(`document.documentElement.scrollWidth`);
const m2scroll = await ev(`(() => { const w = document.querySelector('.el-table .el-scrollbar__wrap'); return w ? { innerScrollable: w.scrollWidth > w.clientWidth } : { innerScrollable: 'no-table' }; })()`);
record("m2.admin-list-w(#34)", m2sw <= 400 && m2scroll.innerScrollable === true, { scrollWidth: m2sw, ...m2scroll });

await nav(EV + "/admin/trips/1", 3500);
const m3sw = await ev(`document.documentElement.scrollWidth`);
const m3scroll = await ev(`(() => { const w = [...document.querySelectorAll('.el-table .el-scrollbar__wrap')].find(x => x.scrollWidth > x.clientWidth + 10); return { innerScrollable: !!w }; })()`);
record("m3.admin-edit-w(#34)", m3sw <= 400 && m3scroll.innerScrollable, { scrollWidth: m3sw, ...m3scroll });

await nav(EV + "/", 2500);
await touchEl(`[...document.querySelectorAll('button')].find(b => b.textContent.includes('展开地图'))`);
await sleep(2600);
const m4 = await ev(overlapCheck);
record("m4.map-label-overlap(#36)", m4.overlapCount === 0, m4);

await nav(TRIP, 3200);
await touchEl(`document.querySelectorAll('.g-grid .ph')[1]`); // 洱海组（3 张），单张组不显示计数是预期
await sleep(1600);
record("m5.lightbox-controls(#37)", await ev(`(() => { const lb = document.querySelector('.lightbox'); if (!lb) return false; return !!lb.querySelector('.lb-close') && !!lb.querySelector('.lb-count') && /^\\d+ \\/ \\d+$/.test(lb.querySelector('.lb-count')?.textContent || ''); })()`),
  await ev(`(() => { const lb = document.querySelector('.lightbox'); return lb ? { close: !!lb.querySelector('.lb-close'), count: lb.querySelector('.lb-count')?.textContent || null } : 'no-lightbox'; })()`));
await ev(`document.querySelector('.lightbox .lb-close')?.click()`);
await sleep(600);

await ev(`window.scrollTo(0, 1200)`);
await sleep(900);
record("m6.backhome-hides-on-scroll-down(#38)", await ev(`(() => { const b = document.querySelector('.back-home'); if (!b) return 'no-el'; const cs = getComputedStyle(b); return parseFloat(cs.opacity) < 0.1 || cs.visibility === 'hidden'; })()`),
  await ev(`(() => { const b = document.querySelector('.back-home'); const cs = getComputedStyle(b); return { opacity: cs.opacity, visibility: cs.visibility, classes: b.className }; })()`));

// ---------- PC 1440 回归闸门 ----------
await setVP(1440, 900, false);
await nav(EV + "/list");
const p1 = await ev(`(() => { const m = document.querySelector('main.wrap.page-pad'); const cs = getComputedStyle(m); const r = m.getBoundingClientRect(); const h1 = document.querySelector('h1').getBoundingClientRect(); return { contentW: Math.round(r.width - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)), h1Left: Math.round(h1.left), padL: cs.paddingLeft }; })()`);
const pcBaselineFile = new URL("./pc-baseline.json", import.meta.url).pathname;
if (BASELINE) {
  writeFileSync(pcBaselineFile, JSON.stringify({ p1 }, null, 1));
  record("pc1.list-content-baseline", true, { note: "baseline saved", ...p1 });
} else {
  const base = existsSync(pcBaselineFile) ? JSON.parse(readFileSync(pcBaselineFile, "utf8")).p1 : null;
  record("pc1.list-content-unchanged", !!base && base.contentW === p1.contentW && base.h1Left === p1.h1Left, { baseline: base, now: p1 });
}

await nav(EV + "/admin/trips");
const p2 = await ev(`(() => { const d = document.documentElement; const l = document.querySelector('.ad-layout'); return { scrollW: d.scrollWidth, clientW: d.clientWidth, cols: getComputedStyle(l).gridTemplateColumns.split(' ')[0] }; })()`);
record("pc2.admin-desktop-intact", p2.scrollW === p2.clientW && p2.cols === "220px", p2);

await nav(EV + "/", 2500);
await touchEl(`[...document.querySelectorAll('button')].find(b => b.textContent.includes('展开地图'))`);
await sleep(2600);
const p34 = await ev(`(() => { const c = window.__ujChart; const s = c.getOption().series[1]; return { moveOverlap: s.labelLayout?.moveOverlap, hideOverlap: s.labelLayout?.hideOverlap ?? null, fontSize: s.label?.fontSize }; })()`);
if (BASELINE) {
  writeFileSync(pcBaselineFile, JSON.stringify({ ...(JSON.parse(readFileSync(pcBaselineFile, "utf8"))), p34, overlapDesktop: (await ev(overlapCheck)) }, null, 1));
  record("pc3.map-config-baseline", true, { note: "saved" });
} else {
  const base = JSON.parse(readFileSync(pcBaselineFile, "utf8"));
  record("pc3.map-desktop-config-unchanged", base.p34.moveOverlap === p34.moveOverlap && base.p34.fontSize === p34.fontSize, { baseline: base.p34, now: p34 });
  const od = await ev(overlapCheck);
  // #36 修复后两端都应 0 交叠（issue 明确记录桌面端同样叠字，属两端一致修复而非 PC 破坏）
  record("pc4.map-desktop-overlap-cleared", od.overlapCount === 0, { baseline: base.overlapDesktop.overlapCount, now: od.overlapCount });
}

await nav(TRIP, 3200);
await ev(`window.scrollTo(0, 1200)`);
await sleep(900);
record("pc5.backhome-visible-desktop", await ev(`parseFloat(getComputedStyle(document.querySelector('.back-home')).opacity) > 0.9`),
  await ev(`getComputedStyle(document.querySelector('.back-home')).opacity`));
await touchEl(`document.querySelectorAll('.g-grid .ph')[1]`);
await sleep(1500);
record("pc6.lightbox-controls-desktop", await ev(`(() => { const lb = document.querySelector('.lightbox'); if (!lb) return false; return !!lb.querySelector('.lb-close') && /^\\d+ \\/ \\d+$/.test(lb.querySelector('.lb-count')?.textContent || ''); })()`),
  await ev(`(() => { const lb = document.querySelector('.lightbox'); return lb ? { close: !!lb.querySelector('.lb-close'), count: lb.querySelector('.lb-count')?.textContent || null } : 'no-lightbox'; })()`));

const fail = Object.entries(results).filter(([, v]) => !v.pass);
console.log("\n== " + (fail.length ? "FAIL: " + fail.map(([k]) => k).join(", ") : "ALL PASS") + " ==");
chrome.kill(); process.exit(fail.length ? 1 : 0);
