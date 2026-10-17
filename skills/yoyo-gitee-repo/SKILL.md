---
name: yoyo-gitee-repo
description: 一句话在 Gitee 创建远程仓库并推送本地项目。用户说"创建 gitee 仓库并推上去""这个项目放到 gitee""推到 gitee""gitee 建仓"时使用。需要本地已有 git；token 在 ~/.gitee-token（各机自备；文件不存在 = 本机未配，先按「凭据」节创建）。
---

# yoyo-gitee-repo：Gitee 一句话建仓推送

本地项目 → Gitee 远程仓库，全程 bash + Gitee Open API（api/v5），不依赖 gh CLI。

## 凭据

- token 文件：`~/.gitee-token`（本机的 Gitee 私人访问令牌，建议权限 `projects`；**各机自备**，文件不存在就先创建：Gitee 网页 个人设置 → 私人访问令牌 生成后 `echo "<token>" > ~/.gitee-token && chmod 600 ~/.gitee-token`）
- API 鉴权：参数 `?access_token=<token>`（token 是 32 位十六进制，无需转义）
- git HTTPS 推送鉴权：`https://oauth2:<token>@gitee.com/<login>/<repo>.git`

**安全红线**：token 永远不要写进 commit 内容、远端 URL 之外的仓库文件；远端 URL 里带 token 的写法仅用于 `git push` 一次性命令，push 成功后不要把带 token 的 URL 存进 `git remote -v`（用干净 URL 存 remote，push 时用临时 URL 或 credential helper）。

## 流程（对用户说一句话"建 gitee 仓库推上去"时执行）

```bash
TOK=$(cat ~/.gitee-token)
API="https://gitee.com/api/v5"
LOGIN="<你的 Gitee 账号名>"   # git config --global user.name 或 Gitee 网页确认

# 1) 本地就绪：无 .git 则 init + 全量 add + commit
#    （仓库名默认取当前目录名；用户指定了就用指定的；有 README/description 就带上）

# 2) 创建远程仓库（私有）：
curl -s -X POST "$API/user/repos?access_token=$TOK" \
  -H "Content-Type: application/json" \
  -d '{"name":"<repo>","description":"<desc>","auto_init":false,"default_branch":"main"}'
# 返回 200/201 → 建成；"资源已存在"类错误 → 说明仓库已存在，直接跳到 3)

# 3) 配 remote 并推送（带 token 的一次性 URL，不落 remote 配置）：
git remote add origin https://gitee.com/$LOGIN/<repo>.git
git push "https://oauth2:$TOK@gitee.com/$LOGIN/<repo>.git" main --force 2>&1 | grep -v "oauth2"
# 首次若默认分支不是 main：git branch -M main

# 4) 回报：仓库地址 https://gitee.com/$LOGIN/<repo>（私有）；如用户要公开，用 Gitee 网页改
```

注意：`git push` 的输出里别把带 token 的 URL 回显给用户（上面 `grep -v` 处理）。

## 相关操作

- 删仓库：API 不支持（DELETE 返回 405），只能 Gitee 网页（仓库 → 设置 → 删除仓库）
- 查已有仓库：`GET $API/user/repos?access_token=$TOK`
- 双远端（GitHub + Gitee 镜像）：remote 叫 `gitee` 而不是 `origin`，push 用 `git push gitee main`（HTTPS 认证：Gitee 支持把个人令牌当密码，或一次性用 oauth2 URL）

## 实测修正（2026-10-08 冒烟通过）

- `POST /user/repos` 的 `public` 字段传布尔值会报 `public is invalid`——**省略该字段，仓库默认私有**；要公开用 Gitee 网页改
- `DELETE /repos/:id` 返回 405——**API 不支持删仓库**
- 全链路：创建私有仓库 → oauth2 URL 推送 → API 查 commit，通过

## 环境要求

- bash + curl + git（macOS / Linux / Windows(WSL) 均可；Windows 原生 CMD 需自行套壳）
- 出网可达 gitee.com
- 各机自备 `~/.gitee-token`（本仓不含任何凭据）
