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
