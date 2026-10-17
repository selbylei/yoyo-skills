# yoyo-skills

yoyo 的 agent skill 合集（pi coding agent / 通用 agent skill 格式），跨机、可发布、各机自备凭据。

## 安装

**pi coding agent（原生包机制，推荐）**：

```bash
pi install git:github.com/selbylei/yoyo-skills@v0.1.0    # 个人级（写 ~/.pi/agent/settings.json）
pi install git:github.com/selbylei/yoyo-skills@v0.1.0 -l # 项目级（写 .pi/settings.json，需项目信任）
```

`pi list` 查看，`pi remove git:github.com/selbylei/yoyo-skills` 卸载。

**其他 agent（Claude Code 等，npx skills CLI）**：

```bash
npx skills add selbylei/yoyo-skills
```

## 包含的 skill

| Skill | 一句话 | 环境要求 |
|---|---|---|
| `yoyo-project-memory` | 项目两层记忆同步（主快照 + 按日增量 + git 分发），跨机恢复开发上下文 | 无系统依赖，git 仓库 + 各机可 pull/push |
| `yoyo-gitee-repo` | Gitee 一句话建仓推送（bash + Open API v5） | bash/curl/git + 出网 gitee.com + 各机自备 `~/.gitee-token` |
| `yoyo-codeup-repo` | 阿里云 Codeup(云效) 一句话建仓推送（SSH 路线） | git/ssh + 出网 codeup.aliyun.com:22 + 公钥登记在阿里云账号 |

本仓库**不含任何凭据**；各 skill 依赖的 token/SSH key 由使用方在各机自备，缺失时按各 SKILL.md「环境要求」节先补齐。

## 开发 / 贡献

- 每个 skill 一个目录：`skills/<name>/SKILL.md`（+ 可选脚本）
- 自制 skill 命名带 `yoyo-` 前缀
- 修改后本地 `pi install ./` 验证，发版打 tag（`vX.Y.Z`），安装方升级 = `pi update --extensions` 或重装新 tag

## License

MIT
