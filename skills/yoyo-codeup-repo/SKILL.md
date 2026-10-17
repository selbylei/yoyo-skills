---
name: yoyo-codeup-repo
description: 一句话在阿里云 Codeup(云效)创建远程仓库并推送本地项目。用户说"创建 codeup/云效仓库""推到 codeup""放到云效""codeup 建仓"时使用。需要本地已有 git；本机 SSH 公钥需登记在阿里云账号(https://account-devops.aliyun.com/settings/ssh,默认密钥 ~/.ssh/id_rsa,各机自备)；仓库默认建在 namespace=用户 Codeup 账号下。
---

# yoyo-codeup-repo:阿里云 Codeup(云效)一句话建仓推送

本地项目 → Codeup 远程仓库,SSH 推送路线,参照 yoyo-gitee-repo 风格。

## 凭据

- **SSH(主路线)**:本机 SSH 密钥(默认 `~/.ssh/id_rsa`;各机自备,公钥需已登记在阿里云账号 `https://account-devops.aliyun.com/settings/ssh`)
  - 主机 `codeup.aliyun.com:22`;首次连接若 `Host key verification failed`,先补指纹
  - SSH URL 格式:`git@codeup.aliyun.com:<namespace>/<repo>.git`(namespace=个人账号或企业组织名)
- **个人令牌(可选,仅 API 建仓用)**:`~/.codeup-token`。Codeup 新版 OpenAPI(yunxiao devops)需要 组织 ID + 个人令牌,端点与鉴权头随版本变化,**首次使用先查官方文档确认**(help.aliyun.com 搜「Codeup OpenAPI 创建仓库」),把结论补进本节再固化流程
- 安全红线:与 yoyo-gitee-repo 相同——任何 token 不写进 commit、不写进远端 URL;SSH 路线无 token,天然干净

## 流程(对用户说「建 codeup 仓库推上去 / 推到云效」时执行)

```bash
NS="<namespace>"            # 用户的 Codeup 组织/账号名
REPO="<repo>"               # 默认取当前目录名

# 1) 本地就绪:无 .git 则 git init + add -A + commit(默认分支 main)
git init -b main 2>/dev/null || git init && git branch -M main
git add -A && git commit -m "init: <repo>"

# 2) 远程仓库
#    a. 有 ~/.codeup-token 且已确认 API:调 Codeup OpenAPI 建库
#    b. 否则:告知用户去 Codeup 网页(云效控制台 → Codeup → 新建代码库)建空仓库(不勾选初始 commit),把仓库名报给用户

# 3) 配 remote(干净 SSH URL,无凭据)并推送:
git remote add origin "git@codeup.aliyun.com:$NS/$REPO.git"
git push origin main

# 4) 回报:https://codeup.aliyun.com/$NS/$REPO
```

## 排障速查

| 症状 | 处理 |
|---|---|
| `Permission denied (publickey)` | 公钥没登记:把 `~/.ssh/id_rsa.pub` 贴到 account-devops.aliyun.com/settings/ssh;验证:`ssh -T git@codeup.aliyun.com` |
| `Host key verification failed` | 补指纹:`ssh-keyscan -T 8 codeup.aliyun.com >> ~/.ssh/known_hosts` |
| 域名解析失败 | 本机网络要能出网(必要时走本机已配的代理设置) |

## 环境要求

- git + ssh(Windows 10+ 自带 OpenSSH;Windows 原生需确认 `ssh`/`git` 在 PATH)
- 出网可达 `codeup.aliyun.com:22`(国内直连;海外机器可能需代理)
- 本机 SSH 公钥已登记在阿里云账号;本仓不含任何凭据
