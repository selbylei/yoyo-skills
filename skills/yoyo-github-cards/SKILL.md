---
name: yoyo-github-cards
description: github-trending 热榜期出片（ai_ask 项目日榜 TOP5 视频）：抓当日 GitHub 日榜 → 选 5 仓定主线 → 8 卡 paper 主题 cards.json → edge-tts 口播 + 音画对齐 → classic 成片 + HyperFrames 动效版双管线 → 抽帧验 + 提交。用户说「出今天/某天的 github-trending」「出一期热榜视频」「epNN 出片」时使用。周榜六卡图文（1242×1656 图文素材）不在本 skill 范围。
---

# github-trending 热榜期出片（日榜 TOP5 → 双管线视频）

作用域：仅 `F:/learn/ai_ask/github-trending/<date>/` 日榜视频期（每周一期，期号 = 顺延）。周榜/图文六卡不是本 skill 的活。

## 前置事实

- 工作目录 `github-trending/<date>/`（date = 系统时钟当天）；期号看 TODO.md 最近一期 +1；主线/选品历史看 TODO.md 各期行
- 上期目录照抄：`classic/paper-bg.jpg` 拷过来（cards.json 的 `bg_image` 引用它）
- 期目录结构：`classic/`(cards.json, tts.txt, tts.mp3, boundaries.json, cards_html/, cards_png/, video_NN.mp4) + `hyperframes/`(index.html, assets/, renders/) + `readmes/` + `check_*_tNN.png`
- 发布：用户照 `doc/发布流程.md`；封面 = `classic/cards_png/card01.png`（= 成片第 1 帧，发布预览里选第 1 帧即可，不用传图）

## 管线（8 步）

| 步 | 命令/动作 | 产物 |
|---|---|---|
| 1 抓取 | `python tools/trending_fetch.py`（**强制走代理**，见坑#1）→ `github-trending/fetch/trending-<date>.json`（24h 榜+周榜 26 页） | fetch json |
| 2 选品 | 读 `top5_24h`（全站+语言分榜并集按 24h 净增）+ 周榜补强；定 5 仓 + 一条主线（如「agent 值一整班」）；license 为 NOASSERTION 的翻 LICENSE 原文定性 | 选品清单 |
| 3 REST+README | `tf.repo_detail(repo)` × 5（直接调函数，见坑#3）写回 fetch json `repos`；README raw 抓前 200 行存 `<date>/readmes/` | repos 明细 + readmes |
| 4 cards.json | `<date>/classic/cards.json`：episode 号、theme paper、flow `flows/default-8pages.json`、`foot_right`/`h1font`/`bg_image` 照抄上期；8 卡 = C1 钩子（封面+列表合并）+ 5×PROJECT 01-05 + SUMMARY + CTA；每卡 say/duration 占位（align 会改写） | cards.json |
| 5 TTS | say 全部**单行拼接**写 `tts.txt` → `python tools/tts.py <date>/classic/tts.txt flows/default-8pages.json` | tts.mp3 + boundaries.json |
| 6 对齐+classic | `python tools/align.py <date>/classic/cards.json`（自动写回时长 + cards.py 重渲染 8 卡 + assemble.py 合成） | video_NN.mp4 |
| 7 HF 动效 | `python tools/gen_hf.py github-trending/<date>/classic` → `set -a && . ./skill-lab/.env && cd <date>/hyperframes && npx --yes hyperframes@0.8.91 render`（~10-12min，**跑前告知用户**） | hyperframes/renders/*.mp4 |
| 8 验+提交 | imageio-ffmpeg ffprobe 验两版（h264+aac 1080×1920 30fps）；抽帧 t=12/50/100 落盘 `check_{classic,hf}_tNN.png`；TODO.md 补期行；`git add github-trending/<date> TODO.md` 提交（**不加 fetch/**，见坑#4） | commit |

## 文案规则（口播/cards，既定不重议）

- star 语义 = **收藏/星**，口播与文案说「收藏/★」，不说「分」
- 首页(封面)与列表页合并为一张 C1 卡，不出稀首页
- 口播不用「拆/拆解」，用「推荐/看」；开头句式「今天推荐5个GitHub热门项目」
- C1 钩子要有本期主线（一句把 5 项串起来的判断），SUMMARY 收口回扣主线；CTA 固定三行（每天推荐5个 / 项目名在卡片上去GitHub搜 / 评论区扣1）
- 每仓 3 条 items 要具体（数字/对比/边界），⚠ 注意要可操作（许可坑/自托管前提/授权边界等）

## 坑（全部 2026-11-17 ep13 实测踩过）

1. **直连抖慢 → 抓取超时**：trending_fetch 先探直连（10s 内响应判健康），直连偶发 20+s/页，26 页必超 900s。跑法：`import importlib.util` 加载脚本后 `tf._direct_healthy = lambda: False` 强制代理再 `tf.main()`（代理 ~5s/页，全程 ~155s）
2. **本机 `python3` 是 WindowsApps 商店 stub**：静默退出码 49 不干活。所有工具链一律 `python`（C:/python312/python）；命令退 49 先怀疑它
3. **`--repos` 不能单独跑**：main() 只吃 sys.argv、且会重抓全部榜单页。REST 明细直接 `tf.repo_detail(owner/name)` 循环调，结果写回 fetch json 的 `repos` 键
4. **git add 忽略路径会断 && 链**：`github-trending/fetch/` 在 .gitignore（本地草稿不入库）。add 时只列有效路径，否则「The following paths are ignored」使 add 退 1、`&&` 后续 commit 全部不执行
5. **tts.mp3 24kHz mono**：正常值（edge-tts 原声），发布流程异常预案里的 44.1kHz 重包只在抖音报音频不兼容时才做
6. **HF render 是重资源**（~11min CPU 密集）：跑前告知；renders/ 在 gitignore（成片留本地，不进库）

## 事实源

| 是什么 | 位置 |
|---|---|
| 抓取器 | `tools/trending_fetch.py`（日榜+周榜解析 + REST repo_detail） |
| 出片工具 | `tools/cards.py`(渲染) / `tts.py` / `align.py`(对齐+合成) / `assemble.py` / `gen_hf.py` |
| 主题系统 | `tools/cards.py` PALETTES：paper/corporate/tech/sketch（本 skill 固定 paper） |
| 8 卡流程 | `flows/default-8pages.json`（音色 zh-CN-YunxiNeural +10%，1080×1920 30fps） |
| 期历史/主线 | `TODO.md`（每期一行：选品+主线+时长+验帧位置） |
| 发布 | `doc/发布流程.md`（用户侧） |
