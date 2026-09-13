// 管理端 390 走查：登录 -> 列表 -> 编辑页 -> 表格 -> 弹窗
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SHELL =
  process.env.HOME +
  "/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell";
const W = 390, H = 844;
const EV = "http://localhost:5173";
const OUT = new URL("./evidence/", import.meta.url).pathname;

const profile = mkdtempSync(join(tmpdir(), "audit-admin-"));
const chrome = spawn(SHELL, [`--remote-debugging-port=0`, `--user-data-dir=${profile}`, `--no-first-run`, `--hide-scrollbars`, `--window-size=${W},${H}`, "about:blank"], { stdio: ["ignore", "pipe", "pipe"] });
const wsUrl = await new Promise((res, rej) => {
  let buf = "";
  chrome.stderr.on("data", (d) => { buf += d; const m = buf.match(/DevTools listening on (ws:\/\/\S+)/); if (m) res(m[1]); });
  setTimeout(() => rej(new Error("chrome start timeout")), 15000);
});
const ws = new WebSocket(wsUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let msgId = 0; const pending = new Map();
ws.onmessage = (ev) => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
const send = (method, params = {}, sessionId) => new Promise((res, rej) => { const id = ++msgId; pending.set(id, (m) => (m.error ? rej(new Error(method + ": " + JSON.stringify(m.error))) : res(m.result))); ws.send(JSON.stringify({ id, method, params, sessionId })); });
const { targetInfos } = await send("Target.getTargets");
const pageTarget = targetInfos.find((t) => t.type === "page");
const { sessionId } = await send("Target.attachToTarget", { targetId: pageTarget.targetId, flatten: true });
const S = (method, params) => send(method, params, sessionId);
await S("Page.enable");
await S("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 2, mobile: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shot = async (name) => { const { data } = await S("Page.captureScreenshot", { format: "png" }); writeFileSync(OUT + name, Buffer.from(data, "base64")); console.log("saved", name); };
const nav = async (url, settle = 3000) => { await S("Page.navigate", { url }); await sleep(settle); };
const evalJs = async (expr) => {
  const r = await S("Runtime.evaluate", { expression: expr, returnByValue: true });
  if (r.exceptionDetails) { console.log("EVAL-ERR:", JSON.stringify(r.exceptionDetails).slice(0, 400)); return "EXCEPTION"; }
  return r.result.value;
};

// 1. 登录页
await nav(EV + "/admin/login", 2500);
await shot("17-admin-login.png");

// 2. 登录
const fillRes = await evalJs(`(() => {
  const i = document.querySelector('input[type=password]');
  if (!i) return 'no-input';
  const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
  set.call(i, 'local-dev-only');
  i.dispatchEvent(new Event('input', { bubbles: true }));
  return 'filled len=' + i.value.length;
})()`);
console.log("fill:", fillRes);
await S("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: 195, y: 533 }] });
await S("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
await sleep(2500);
console.log("url after login:", await evalJs("location.pathname"));

// 3. 旅行列表
await nav(EV + "/admin/trips", 3000);
await evalJs("window.scrollTo(0, 400)");
await sleep(600);
await shot("18-admin-trips-list.png");

// 4. 编辑页顶部
await nav(EV + "/admin/trips/1", 3500);
await shot("19-admin-edit-top.png");

// 5. 编辑页滚动到景点表格
const tablePos = await evalJs(`(() => {
  const el = [...document.querySelectorAll('*')].find(e => /添加景点|行程|景点/.test(e.textContent) && e.children.length === 0);
  return document.documentElement.scrollHeight;
})()`);
await evalJs(`window.scrollTo(0, 1600)`);
await sleep(800);
await shot("20-admin-edit-table.png");

// 6. 打开一个弹窗（点含「添加」的按钮）
const dlg = await evalJs(`(() => {
  const btn = [...document.querySelectorAll('button')].find(b => /添加景点|新增|添加一天/.test(b.textContent));
  if (!btn) return 'no-btn';
  btn.click(); return 'clicked ' + btn.textContent.trim();
})()`);
console.log("dialog:", dlg);
await sleep(1500);
await shot("21-admin-edit-dialog.png");

// 弹窗宽度测量
const dlgMeasure = await evalJs(`(() => {
  const d = document.querySelector('.el-dialog, .el-overlay');
  if (!d) return 'no-dialog';
  const target = d.classList.contains('el-dialog') ? d : d.querySelector('.el-dialog');
  const r = target ? target.getBoundingClientRect() : d.getBoundingClientRect();
  return { cls: target ? 'el-dialog' : 'overlay', x: Math.round(r.x), w: Math.round(r.width), vw: innerWidth };
})()`);
console.log("dialog measure:", dlgMeasure);
chrome.kill();
process.exit(0);
