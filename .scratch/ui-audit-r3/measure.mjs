import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const SHELL = process.env.HOME + "/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell";
const profile = mkdtempSync(join(tmpdir(), "m-"));
const chrome = spawn(SHELL, [`--remote-debugging-port=0`,`--user-data-dir=${profile}`,`--no-first-run`,`--window-size=390,844`,"about:blank"],{stdio:["ignore","pipe","pipe"]});
const wsUrl = await new Promise((res)=>{let b="";chrome.stderr.on("data",d=>{b+=d;const m=b.match(/DevTools listening on (ws:\/\/\S+)/);if(m)res(m[1]);});});
const ws=new WebSocket(wsUrl); await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
let id=0;const pend=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pend.has(m.id)){pend.get(m.id)(m.result);pend.delete(m.id);}};
const send=(method,params={},sid)=>new Promise(res=>{const i=++id;pend.set(i,res);ws.send(JSON.stringify({id:i,method,params,sessionId:sid}));});
let targetInfos=null;
for (let i=0;i<20;i++){ const r=await send("Target.getTargets"); targetInfos=r.targetInfos; if(targetInfos&&targetInfos.find(t=>t.type==="page")) break; await new Promise(r=>setTimeout(r,500)); }
const {sessionId}=await send("Target.attachToTarget",{targetId:targetInfos.find(t=>t.type==="page").targetId,flatten:true});
const S=(m,p)=>send(m,p,sessionId);
await S("Page.enable");
await S("Emulation.setDeviceMetricsOverride",{width:390,height:844,deviceScaleFactor:2,mobile:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const ev=async(e)=>(await S("Runtime.evaluate",{expression:e,returnByValue:true})).result?.value;
// 登录
await S("Page.navigate",{url:"http://localhost:5173/admin/login"}); await sleep(2500);
await ev(`(()=>{const i=document.querySelector('input[type=password]');const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;s.call(i,'local-dev-only');i.dispatchEvent(new Event('input',{bubbles:true}));})()`);
await S("Input.dispatchTouchEvent",{type:"touchStart",touchPoints:[{x:195,y:533}]});
await S("Input.dispatchTouchEvent",{type:"touchEnd",touchPoints:[]});
await sleep(2000);
for (const [name,url] of [["LIST","http://localhost:5173/admin/trips"],["EDIT","http://localhost:5173/admin/trips/1"]]) {
  await S("Page.navigate",{url}); await sleep(3000);
  const m = await ev(`(() => {
    const d=document.documentElement;
    const wide=[...document.querySelectorAll('*')].map(el=>{const r=el.getBoundingClientRect();return {el, r};}).filter(x=>x.r.width>391||x.r.right>391).map(x=>x.el.tagName+'.'+String(x.el.className).split(' ').slice(0,2).join('.')+' w='+Math.round(x.r.width)+' right='+Math.round(x.r.right));
    // 横向可滚？
    window.scrollTo(200,0);
    const canScroll = window.scrollX>0 || document.documentElement.scrollLeft>0;
    window.scrollTo(0,0);
    return {innerW:innerWidth, scrollW:d.scrollWidth, clientW:d.clientWidth, canScrollX:canScroll, wideCount:wide.length, wide:wide.slice(0,10)};
  })()`);
  console.log(name, JSON.stringify(m, null, 1));
}
chrome.kill();process.exit(0);
