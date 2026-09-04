# up-journey

家庭旅游记录应用：管理端录入旅行记录，展示端以杂志编辑风呈现家庭足迹。
技术栈：Vue 3 + FastAPI + MySQL 8，部署于绿联 NAS 的 Docker。

## Agent skills

### Issue tracker

本地 markdown：issue 与 spec 存于 `.scratch/<feature>/` 目录。见 `docs/agents/issue-tracker.md`。

### Triage labels

默认五标签：`needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`。见 `docs/agents/triage-labels.md`。

### Domain docs

单上下文布局：根目录 `CONTEXT.md` + `docs/adr/`。见 `docs/agents/domain.md`。

### UI acceptance

UI 验收大师章程：`docs/agents/ui-acceptance-master.md`。浏览器实操由主代理执行，
子代理仅做静态嫌疑清单；缺陷立 GitHub issue（`gh`，仓库私有需登录）。

### Git workflow

代码改动一律走新分支（`fix/<issue#>-<slug>`），完成后按 issue 编号顺序依次合回 `main`，
上一个合并完成再开下一个分支。commit message 沿用 `fix(scope): 描述（#N）` 格式。
纯文档/验收产物（`.scratch/` 等）可直接在 `main` 上。
