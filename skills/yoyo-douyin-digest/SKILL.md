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

## Batch(收藏等成批场景)

1. 先拿到视频 URL 清单:优先用户直接给;否则 bsk 打开收藏页(`https://www.douyin.com/favorite`,需登录态)用 **screenshot/文本** 逐个取,不用 observe/get-html
2. 逐条跑 `dy-digest.sh`(串行即可,单条 3-5 分钟视频全程 ~10 分钟);一条落盘成功后再下一条
3. 非视频类收藏(图集/图文/外链)脚本不适用:记录"已跳过+原因",不硬转
4. 结束前确认输出目录文件数 == 视频收藏数,报差异

## Not for

- 不需要"内容"只要"能下载视频文件"的场景:直接用 yt-dlp
- 抖音之外平台:脚本只适配抖音的格式/cookie 行为,其他平台换对应抽取器
