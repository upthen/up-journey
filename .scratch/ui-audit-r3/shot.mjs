// UI 验收 r3 截图工具：headless Chromium + CDP
// 用法: node shot.mjs <url> <out.png> [--w 390] [--h 844] [--scroll 2000]
//       [--click x,y] [--eval "<js>"] [--settle 3000]
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SHELL =
  process.env.HOME +
  "/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell";

const args = process.argv.slice(2);
const url = args[0];
const out = args[1];
const opt = (name, def) => {
  const i = args.indexOf("--" + name);
  return i >= 0 ? args[i + 1] : def;
};
const W = +opt("w", 390);
const H = +opt("h", 844);
const scrollY = +opt("scroll", 0);
const click = opt("click", null);
const evalJs = opt("eval", null);
const settle = +opt("settle", 3000);

const profile = mkdtempSync(join(tmpdir(), "audit-chrome-"));
const chrome = spawn(
  SHELL,
  [
    `--remote-debugging-port=0`,
    `--user-data-dir=${profile}`,
    `--no-first-run`,
    `--hide-scrollbars`,
    `--window-size=${W},${H}`,
    "about:blank",
  ],
  { stdio: ["ignore", "pipe", "pipe"] },
);

const wsUrl = await new Promise((res, rej) => {
  let buf = "";
  const tick = (d) => {
    buf += d;
    const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
    if (m) res(m[1]);
  };
  chrome.stderr.on("data", tick);
  setTimeout(() => rej(new Error("chrome start timeout: " + buf.slice(-300))), 15000);
});

const { webcrypto } = await import("node:crypto");
// Node 22 全局 WebSocket
const ws = new WebSocket(wsUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

let msgId = 0;
const pending = new Map();
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
const send = (method, params = {}, sessionId) =>
  new Promise((res, rej) => {
    const id = ++msgId;
    pending.set(id, (m) => (m.error ? rej(new Error(method + ": " + JSON.stringify(m.error))) : res(m.result)));
    ws.send(JSON.stringify({ id, method, params, sessionId }));
  });

const { targetInfos } = await send("Target.getTargets");
const pageTarget = targetInfos.find((t) => t.type === "page");
const { sessionId } = await send("Target.attachToTarget", { targetId: pageTarget.targetId, flatten: true });

const S = (method, params) => send(method, params, sessionId);
await S("Page.enable");
await S("Emulation.setDeviceMetricsOverride", { width: W, height: H, deviceScaleFactor: 2, mobile: true });
await S("Emulation.setTouchEmulationEnabled", { enabled: true });
await S("Page.navigate", { url });
await new Promise((r) => setTimeout(r, settle));

if (scrollY) await S("Runtime.evaluate", { expression: `window.scrollTo(0, ${scrollY})` });
if (evalJs) await S("Runtime.evaluate", { expression: evalJs });
if (click) {
  const [x, y] = click.split(",").map(Number);
  // 触屏点按
  await S("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y }] });
  await S("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
}
await new Promise((r) => setTimeout(r, 1500));

const { data } = await S("Page.captureScreenshot", { format: "png" });
writeFileSync(out, Buffer.from(data, "base64"));
// 顺手输出溢出检查
const { result } = await S("Runtime.evaluate", {
  expression: `JSON.stringify({w: innerWidth, scrollW: document.documentElement.scrollWidth, overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth})`,
  returnByValue: true,
});
console.log(out, result.value);
chrome.kill();
process.exit(0);
