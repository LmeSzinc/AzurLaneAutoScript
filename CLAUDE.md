# Claude Code & AI Agent Rules for Alas Fork

## ⚠️ CRITICAL SAFETY RULES (绝对安全红线)

### 1. 严禁创建任何 Pull Request (PULL REQUESTS ARE STRICTLY FORBIDDEN)
- **禁止向任何仓库（尤其是官方上游 `LmeSzinc/AzurLaneAutoScript`）发起 Pull Request！**
- **DO NOT run `gh pr create` under ANY circumstances.**
- **DO NOT call GitHub REST/GraphQL API to create pull requests, issues, or reviews.**
- 本项目是个人定制的下行分支（Fork），仅作为独立私人使用，绝不能打扰原作者或向原作者仓库提交合并申请。

### 2. 严禁向 upstream 推送 (DO NOT PUSH TO UPSTREAM)
- 严禁执行 `git push upstream`。
- 本地所有推送操作只能针对 `origin` (`git@github.com:ZerowindSE/AzurLaneAutoScript.git`)。
- 对 `upstream` 仅允许执行 `git fetch upstream` 和 `git merge upstream/master` 进行单向更新拉取。

### 3. 开发规范
- 保持原版代码 100% 纯净（零侵入）。
- 所有定制 API、MCP 模块均放置在 `module/api/` 目录下。
- 启动入口为 `python run_api.py`。
