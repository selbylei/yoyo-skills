---
name: yoyo-douyin-digest
description: 'Use when the user wants the spoken content, transcript, or digest of a Douyin (抖音) video by URL, wants to batch-process Douyin videos (e.g. 收藏/favorites), or asks to transcribe a Douyin video locally. Triggers: "整理这条抖音", "抖音视频内容/逐字稿", "douyin video transcript", "把抖音收藏抓一下".'
---

# Douyin Digest（抖音视频 → 逐字稿笔记）

抖音"要口播内容"的唯一稳路线:本机 Chrome cookies 下载 + faster-whisper 本地转写。
**不依赖**系统 ffmpeg、不依赖 brew、不把 cookies 挪出机器。bsk/浏览器只用来拿收藏列表等页面元数据,不做重 CDP 操作(抖音视频页 observe/get-html 会卡死调试会话,screenshot 才可靠)。

## Quick use

在本 skill 目录下运行(脚本与 SKILL.md 同目录,相对路径):

```bash
# 一条视频 → 出稿(视频文件自动清理,只留笔记)
bash dy-digest.sh <抖音URL> [输出目录] [模型]
# 默认输出目录 ~/douyin-digests/,默认模型 small;长视频或听不清换 medium
```

产物:`<输出目录>/<视频ID>-<标题>.md`(含 URL、抓取日期、时长、带时间戳逐字稿)。
"抓一个清理一个"由脚本内置:视频落在 mktemp 临时目录,EXIT trap 删除。

## 依赖(幂等自检,缺什么装什么)

- `yt-dlp` — 缺则 `uv tool install yt-dlp`(脚本会把 `~/.local/bin` 加进 PATH;已装在别处的 uv/系统 yt-dlp 也能被找到)
- 转写走 `uv run --python 3.12 --with faster-whisper --with av`(依赖走 uv 缓存,无常驻安装)

## 环境要求

- bash + uv(macOS / Linux / Windows(WSL))
- 本机 Chrome 已有抖音登录态(脚本用 `--cookies-from-browser chrome` 现场解密,**cookies 不出机器、不进仓库**;各机自备登录态)
- 出网可达 douyin.com;转写纯本地,断网可用(uv 缓存命中时)
- 本仓不含任何凭据/cookies

## Failure table

| 症状 | 处理 |
|---|---|
| `Fresh cookies ... needed` | 确认 Chrome 装有登录态;`--cookies-from-browser chrome` 会现场解密 |
| `Requested format is not available` | 先 `yt-dlp --cookies-from-browser chrome -F <URL>` 看实际格式(每条视频不同)再选档 |
| 转写慢/机器卡 | 换 `small`;再不行就只下载不转写,笔记标注"未转写" |
| 标题乱码/特殊字符 | 脚本已做 slug 清洗;仍异常时以 `<视频ID>.md` 落盘 |

## Batch（收藏等成批场景）

1. 先拿到视频 ID 清单（收藏页等）：优先用户直接给；否则 bsk 开收藏页（`https://www.douyin.com/user/self` → 侧栏「收藏」tab）逐个取 ID。取直链一律走下面「页内 API」节，不用 DOM
2. 逐条跑 `dy-digest.sh`(串行即可,单条 3-5 分钟视频全程 ~10 分钟);一条落盘成功后再下一条
3. 非视频类收藏(图集/图文/外链)脚本不适用:记录"已跳过+原因",不硬转
4. 结束前确认输出目录文件数 == 视频收藏数,报差异

## 按收藏时间周抓取（收藏列表全量 + 周分桶，2026-11-01 验证）

目标：把收藏按**收藏时间**（不是发布/抓取时间）分周，每周只处理那周的收藏。

**关键事实**
- 收藏列表 API = `POST /aweme/v1/web/aweme/listcollection/`，页面自己带签名（a_bogus/x-secsdk-web-signature）。**页内 fetch 复刻会被风控 403**；`bsk network`/`bsk debug` 也不给响应体（debug 对 >~256KB 的 body 直接 omit）→ 唯一稳路线 = **拦截页面自己的请求**
- 页内 hook `XMLHttpRequest.prototype.open/send`（+fetch），URL 含 `listcollection` 就把 `responseText` 存进 `window.__favcap[]`（注意别存全量 text，只存解析后的紧凑字段，否则 evaluate 读回会超预算）
- 响应体：`aweme_list`（每页 10 条，字段 aweme_id/create_time/media_type/desc…）、`cursor`（**下一批最老收藏时间 ≈ ms*1000+后缀**，即页级收藏时间下界）、`has_more`。请求体 `count=10&cursor=<上页 nxt>`
- 单条收藏时间 **API 不返回**，只有页级窗口 (nxt, r]（约 3-5 天宽）；周桶 = 窗口中点的 ISO 周（W+8）
- 深页可能整页无效：`aweme_list: null` + `invalid_item_count:10`（被删/失效内容）→ 取 `its` 必须 `(j.aweme_list||[])`
- 推进游标靠**滚动**（`bsk wheel --delta-y 2500`，sleep ~4s）：重点击「收藏」tab 只会重拉前 3 页（warmup，cursor 回到 0），不前进
- 终点 = 某页 `has_more=0`
- `bsk evaluate` 读回：分块 slice（每块 ≤10 条），输出行首是 `{`；daemon 偶发打 "new bsk version" banner 到 stdout，过滤用 `grep '^{'`，**不要** `grep -v "update bsk"`（banner 不含该字样，会漏行）

**流程**（playground 实例：`docs/抖音收藏摘要/favcap/收藏周统计.md`，910 条/56 周）
1. bsk 开 `/user/self` → 点「收藏」→ 装 hook → 点「作品」再点回「收藏」触发前 3 页
2. 循环 scroll→sleep→查 `__favcap` 末条 `has_more`，直到 0
3. 分块读回 → 按链去重（r_i 必须 == 上页 nxt，0 断点才可信）
4. 每条落 `{id, create_time, media_type, desc, fav_after_ms, fav_before_ms}`（req cursor=0 → before=None「截至抓取日」；末页 nxt=0 → after=None）
5. 周桶 + 周统计落 `收藏周统计.md` / `weekly-stats.json`；之后 Batch 第 1 步改从周桶取 ID

## 取直链：页内 API（首选，2026-11-01 验证；比 DOM 稳）

- 在已登录的 bsk 会话里（任意抖音页），对每个视频 ID 页内 fetch：
  `fetch('/aweme/v1/web/aweme/detail/?aweme_id=<id>&aid=1128&device_platform=webapp', {credentials:'include'})`
  → `aweme_detail.video.play_addr.url_list` 即 CDN 直链（curl -L + 浏览器 UA + Referer 下载）
- **必须带 `aid=1128`**：不带时接口只返视频元数据，play_addr 为空
- 用 `aweme_detail.video.duration` 判视频/图文；图文看 `aweme_detail.images`。
  ⚠️ 别用 DOM 采样判图文：长视频页 `<video>` 元素渲染慢（30s 内常无 src），会被误判成图文（2026-11-01 实战坑）
  ⚠️ 部分条目 detail 接口持续返回**空 body / `aweme_detail:null`（带 `filter_detail`）** = 内容已删或风控；换 aid、慢速重试均无效，直接兜底用收藏列表字段（作者/封面缺失，在产物中标注即可）（2026-11-01 批量 184 条中 33 条如此）
- DOM 法（`<video source>` 的 `aweme/v1/play` 链接）仅作 API 失效时的备胎；`video.src` 在 MSE blob 模式下不稳，别用

## Not for

- 不需要"内容"只要"能下载视频文件"的场景:直接用 yt-dlp
- 抖音之外平台:脚本只适配抖音的格式/cookie 行为,其他平台换对应抽取器
