# 公网暴露方案（阿里云域名 + 移动家宽）

> **2026-09-03 实施结论**：IPv6 直连路线已完整部署验证（DDNS + 证书 + 8443 TLS 全部就绪），
> 但**移动光猫（ZXHN F653GV9）的 IPv6 入站无法放行**——固件未暴露 IPv6 防火墙开关，
> IPv4 防火墙等级调「低」亦无效，外部连接被静默丢弃（NAS 抓包零到达）。
> **产品决策：v1 维持内网使用**（`http://192.168.1.18:8100`）；公网组件已停用但保留
> （ddns-go 配置、Let's Encrypt 证书卷、nginx 8443 监听），将来重开公网走本文档
> **Cloudflare Tunnel 路线**（NAS→CF 边缘出站已验证畅通），而非继续与光猫纠缠。
> 阿里云 DNS 中 journey AAAA 记录仍指向 NAS，因入站被光猫拦截，不构成暴露面。

> 前置状态（2026-09-02 已就绪）：管理端密码鉴权已上线（98 后端测试覆盖）；
> MySQL 不暴露端口；图片路径防穿越；富文本过 DOMPurify。
> 展示端按产品决策**免密**开放；`/admin/*` 需要管理员密码（NAS `.env` 的 `ADMIN_PASSWORD`）。

## 网络现状（实测）

| 项 | 实测值 | 结论 |
|---|---|---|
| IPv4 出口 | `111.60.87.81`（移动） | 大概率运营商共享出口（移动家宽基本不给个人公网 v4），**不可依赖** |
| IPv6 | NAS 已有 GUA 地址 `2409:8a4c:...` | 移动 IPv6 敞开，**主路线** |
| 80/443 入站 | 国内家宽普遍封 | 用非标端口（如 `8443`）或 HTTPS 反代 |

## 路线 A（推荐）：IPv6 直连 + 阿里云 DDNS + DNS-01 证书

访问者需要 IPv6（2026 年国内手机流量与多数家庭宽带均已覆盖；亲友中若有纯 v4
网络，走路线 B 兜底）。

1. **路由器**（管理界面）：
   - 关闭"IPv6 防火墙"中对 NAS 入站的拦截，或添加放行规则：TCP `8443`（或你选的端口）→ NAS 内网地址。
   - 若光猫桥接 + 路由器拨号，在路由器上放行；若光猫路由一体，在它的"安全/防火火墙"里放行。
2. **阿里云 DNS**（console.aliyun.com → 云解析 DNS）：
   - 给域名加一条 `AAAA` 记录指向 NAS 当前 IPv6（之后由 DDNS 自动维护）；
   - 创建一个 **AccessKey**（RAM 访问控制 → 仅授权 `AliyunDNSFullAccess`，给 DDNS 和证书签发共用）。
3. **DDNS**（NAS 上跑，自动更新 AAAA 记录）：
   绿联应用中心若有 DDNS 插件直接用（选"阿里云"服务商，填 AccessKey，类型 AAAA）；
   没有的话在 Docker 里跑 `jeessy/ddns-go`（一条命令：`docker run -d --restart unless-stopped --network host jeessy/ddns-go`，Web 界面里配阿里云 + IPv6）。
4. **HTTPS 证书**（80 被封，用 DNS-01 验证；NAS 上跑 acme.sh）：
   ```bash
   docker run -d --restart unless-stopped --name acme \
     -v /volume1/docker/up-journey/certs:/acme/certs \
     neilpang/acme.sh daemon \
     --issue --dns dns_ali -d travel.example.com \
     -Ak Ali_Key=xxx -Ak Ali_Secret=xxx \
     --keylength ec-256 --install
   ```
   （`Ali_Key/Ali_Secret` 即上面的 AccessKey；acme.sh 会自动每 60 天续期）
5. **nginx 挂证书**：`deploy/nginx.conf` 的 server 段加 `listen 8443 ssl;` +
   `ssl_certificate` 指向证书卷；compose 的 nginx 服务加 `8443:8443` 端口映射与证书卷挂载。
   —— 这一步说一声，我来改配置并重新部署。

## 路线 B（兜底/加速）：Cloudflare Tunnel

不依赖公网 IP/IPv6，亲友在纯 v4 网络也能访问；代价是国内速度一般。

1. 阿里云域名无需转移注册商：到 Cloudflare 添加站点，把阿里云的 **NS 记录**改成 Cloudflare 给的两台；
2. NAS 上跑 `cloudflare/cloudflared` 容器，`tunnel` 指向 `nginx:8100`（容器网络内）；
3. Cloudflare 面板开 HTTPS（边缘证书自动）。

两条路线可以并存：AAAA 直连为主，Tunnel 做备份入口（不同子域）。

## 备案提示

- 域名解析到国内家宽 IP 的**非标端口**（8443）实践中不查备案；80/443 未备案会被拦截且不可用。
- 若介意合规风险，路线 B 全程经 Cloudflare 海外边缘，不涉及国内备案问题。

## 安全清单（挂公网前逐项确认）

- [x] `ADMIN_PASSWORD` 已配置（管理端 503→401/200 行为已在 NAS 验证）
- [x] MySQL 未映射宿主机端口
- [x] 图片服务目录穿越返回 403（已验证）
- [x] 展示端免密（产品决策），管理端强密码 + HttpOnly cookie
- [ ] HTTPS 上线（路线 A 第 4-5 步或路线 B 第 3 步）
- [ ] 定期备份：`deploy/db-backup.sh` 已就位，建议在 NAS 计划任务里每日执行
