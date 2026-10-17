# yoyo-skills

yoyo 的 agent skill 合集（pi coding agent / 通用 agent skill 格式），跨机、可发布、各机自备凭据。

## 安装

**pi coding agent（原生包机制，推荐）**：

```bash
pi install git:github.com/selbylei/yoyo-skills@v0.2.0    # 个人级（写 ~/.pi/agent/settings.json）
pi install git:github.com/selbylei/yoyo-skills@v0.2.0 -l # 项目级（写 .pi/settings.json，需项目信任）
```

`pi list` 查看，`pi remove git:github.com/selbylei/yoyo-skills` 卸载。

**其他 agent（npx skills CLI，通用 Agent Skills 格式，70+ agent 通用）**：

```bash
npx skills add selbylei/yoyo-skills -g                     # 自动探测本机已装的 agent，装进各自 skills 目录（用户级）
npx skills add selbylei/yoyo-skills -a claude-code -g      # 指定 agent（-a 后跟多个：-a codex opencode goose）
npx skills add selbylei/yoyo-skills -a '*' -g              # 全部支持的 agent
```

- 不带 `-g` 装到**项目级**（当前目录的 agent 项目 skills 目录）
- 升级：`npx skills update`；卸载：`npx skills remove selbylei/yoyo-skills`
- 默认软链方式安装；`--copy` 可改为复制文件

各主流 agent 的安装命令（用户级，各跑一条即可；`-a` 值与目标目录已核实）：

```bash
# Claude Code
npx skills add selbylei/yoyo-skills -a claude-code -g
# Codex
npx skills add selbylei/yoyo-skills -a codex -g
# Gemini CLI
npx skills add selbylei/yoyo-skills -a gemini-cli -g
# OpenCode
npx skills add selbylei/yoyo-skills -a opencode -g
# Cursor
npx skills add selbylei/yoyo-skills -a cursor -g
# Roo Code
npx skills add selbylei/yoyo-skills -a roo -g
# Cline
npx skills add selbylei/yoyo-skills -a cline -g
# Windsurf
npx skills add selbylei/yoyo-skills -a windsurf -g
# Zed
npx skills add selbylei/yoyo-skills -a zed -g
# GitHub Copilot CLI
npx skills add selbylei/yoyo-skills -a github-copilot -g
# Qwen Code
npx skills add selbylei/yoyo-skills -a qwen-code -g
# Kimi Code
npx skills add selbylei/yoyo-skills -a kimi-code-cli -g
# Goose
npx skills add selbylei/yoyo-skills -a goose -g
# Trae
npx skills add selbylei/yoyo-skills -a trae -g
```

注：Codex/Cline/Zed/Kimi/Gemini(项目级) 等共用 `~/.agents/skills/`，给其中任一个装即覆盖全部；其余 50+ agent 的 `-a` 值见上游 CLI 文档：https://github.com/vercel-labs/skills

> pi 也可以用这套 CLI（`-a pi`），但 pi 推荐走上面的原生包安装：版本可控、`pi update` 一键升级。

## 包含的 skill

| Skill | 一句话 | 环境要求 |
|---|---|---|
| `yoyo-project-memory` | 项目两层记忆同步（主快照 + 按日增量 + git 分发），跨机恢复开发上下文 | 无系统依赖，git 仓库 + 各机可 pull/push |
| `yoyo-gitee-repo` | Gitee 一句话建仓推送（bash + Open API v5） | bash/curl/git + 出网 gitee.com + 各机自备 `~/.gitee-token` |
| `yoyo-codeup-repo` | 阿里云 Codeup(云效) 一句话建仓推送（SSH 路线） | git/ssh + 出网 codeup.aliyun.com:22 + 公钥登记在阿里云账号 |
| `yoyo-douyin-digest` | 抖音视频 → 逐字稿笔记（本机 Chrome cookies 下载 + faster-whisper 本地转写，自带脚本） | bash/uv + 出网 douyin.com + 本机 Chrome 抖音登录态（cookies 各机自备，不进仓） |

本仓库**不含任何凭据**；各 skill 依赖的 token/SSH key 由使用方在各机自备，缺失时按各 SKILL.md「环境要求」节先补齐。

## 开发 / 贡献

- 每个 skill 一个目录：`skills/<name>/SKILL.md`（+ 可选脚本）
- 自制 skill 命名带 `yoyo-` 前缀
- 修改后本地 `pi install ./` 验证，发版打 tag（`vX.Y.Z`），安装方升级 = `pi update --extensions` 或重装新 tag

## License

MIT
