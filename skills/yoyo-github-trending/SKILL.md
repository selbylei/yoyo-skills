---
name: yoyo-github-trending
description: github-trending 热榜期出片（日榜 TOP5 → 双管线视频，自包含可跨机安装）：skill 自带 tools/ 六脚本+flow+纸底+HF 环境脚本，在任意项目根目录抓当日 GitHub 日榜 → 选 5 仓定主线 → 8 卡 paper 主题 cards.json → edge-tts 口播+音画对齐 → classic 成片 + HyperFrames 动效版 → 抽帧验 + 提交。用户说「出今天/某天的 github-trending」「出一期热榜视频」「epNN 出片」时使用。周榜六卡图文走 yoyo-github-cards。
---

# github-trending 热榜期出片（日榜 TOP5 → 双管线视频）

自包含 skill：管线全部随 skill 分发，装到任何客户端即可用。产物落在 `<项目根>/github-trending/<date>/`。

## 目录布局（skill 自带）

```
<skill目录>/
  tools/          trending_fetch / cards / tts / align / assemble / gen_hf（对齐/渲染按 <skill目录>/tools/ 兄弟关系寻径，勿拆散）
  flows/default-8pages.json   8 卡流程（zh-CN-YunxiNeural +10%，1080×1920 30fps）
  assets/paper-bg.jpg         paper 主题底图（每期拷进 classic/）
  env/hf-env.sh               HF 渲染环境（Mac/Win 自适应，无硬编码路径）
```

## 一次性前提（新机器装一遍）

- node ≥18（HF 渲染走 `npx hyperframes`）
- Chrome 标准安装（cards.py 截图用；找不到标准路径就报错，Playwright/Edge 兜底仅 Windows）
- `pip install edge-tts imageio-ffmpeg`（口播 + ffmpeg 二进制）
- ffprobe 可选：PATH 里有或 `npm i -g @ffprobe-installer`；没有 HF 仍可渲染，抽帧验改用 ffmpeg

## 管线（8 步，SK=<skill目录>，CWD=<项目根>）

| 步 | 命令/动作 | 产物 |
|---|---|---|
| 1 抓取 | `python $SK/tools/trending_fetch.py`（**强制走代理**，见坑#1）→ `github-trending/fetch/trending-<date>.json`（24h+周榜 26 页） | fetch json |
| 2 选品 | 读 `top5_24h`（全站+语言分榜并集按 24h 净增）+ 周榜补强；定 5 仓 + 一条主线；license 为 NOASSERTION 的翻 LICENSE 原文定性 | 选品清单 |
| 3 REST+README | `tf.repo_detail(repo)` ×5 写回 fetch json `repos`（见坑#3）；README raw 抓前 200 行存 `<date>/readmes/` | repos 明细 + readmes |
| 4 cards.json | `<date>/classic/cards.json`：episode 号（= 上期+1，看 TODO 或期目录）、theme paper、flow `flows/default-8pages.json`；`cp $SK/assets/paper-bg.jpg <date>/classic/`；8 卡 = C1 钩子 + 5×PROJECT + SUMMARY + CTA；say/duration 占位（align 改写） | cards.json |
| 5 TTS | say **单行拼接**写 `tts.txt` → `python $SK/tools/tts.py <date>/classic/tts.txt $SK/flows/default-8pages.json` | tts.mp3 + boundaries.json |
| 6 对齐+classic | `python $SK/tools/align.py <date>/classic/cards.json`（自动写回时长 + 重渲染 8 卡 + 合成） | video_NN.mp4 |
| 7 HF 动效 | `python $SK/tools/gen_hf.py <date>/classic` → `source $SK/env/hf-env.sh && cd <date>/hyperframes && npx --yes hyperframes@0.8.91 render`（~10-12min，**跑前告知用户**） | hyperframes/renders/*.mp4 |
| 8 验+提交 | ffprobe/imageio-ffmpeg 验两版（h264+aac 1080×1920 30fps）；抽帧 t=12/50/100 落盘 `check_{classic,hf}_tNN.png`；TODO 补期行；`git add github-trending/<date> TODO.md` 提交（**不加 fetch/**，见坑#4） | commit |

## 文案规则（口播/cards，既定不重议）

- star 语义 = **收藏/星**，口播与文案说「收藏/★」，不说「分」
- 首页(封面)与列表页合并为一张 C1 卡，不出稀首页
- 口播不用「拆/拆解」，用「推荐/看」；开头句式 **A/B/C/D 轮换**（见「防同质化」），相邻两期不重复
- C1 钩子要有本期主线（一句把 5 项串起来的判断），SUMMARY 收口回扣主线；CTA 固定三行（每天推荐5个 / 项目名在卡片上去GitHub搜 / 想看哪类评论区告诉我）
- 每仓 3 条 items 要具体（数字/对比/边界），⚠ 注意要可操作（许可坑/自托管前提/授权边界等）

## 防同质化（11-19 起，应对抖音「批量低质」风控）

- 开头句式 4 套轮换，相邻两期不重复：A「今天推荐5个GitHub热门项目」/ B「今天挑了5个GitHub热门项目」/ C「这5个GitHub项目值得看一眼」/ D「来看看今天GitHub热榜上的5个项目」
- CTA 第 3 行不用「评论区扣 1」，改「想看哪类，评论区告诉我」
- 音色默认 zh-CN-YunxiNeural；隔期可换 zh-CN-YunyangNeural（拷一份 flow json 改 tts.voice 再传给 tts.py 第 2 参）
- 每期在 TODO 期行记：用的开头套 + 音色；发布节奏照 发布流程.md 风控预案（警告后停发 48-72h）

## 坑（2026-11-17 ep13 实测踩过）

1. **直连抖慢 → 抓取超时**：trending_fetch 先探直连（10s 内响应判健康），偶发 20+s/页，26 页必超时。跑法：
   ```python
   import importlib.util
   spec = importlib.util.spec_from_file_location("tf", "<skill>/tools/trending_fetch.py")
   tf = importlib.util.module_from_spec(spec); spec.loader.exec_module(tf)
   tf._direct_healthy = lambda: False   # 强制代理(本机 127.0.0.1:7897 或系统代理)
   tf.main()                            # ~155s/全部榜单
   ```
   代理不通就改脚本里 `PROXY` 常量。
2. **`python3` 可能是商店 stub**（Windows 用户常见）：静默退出码 49 不干活。一律用真 `python`；命令退 49 先怀疑它
3. **`--repos` 不能单独跑**：main() 会重抓全部榜单页。REST 明细直接 `tf.repo_detail(owner/name)` 循环调，写回 fetch json 的 `repos` 键
4. **git add 忽略路径会断 && 链**：`github-trending/fetch/` 应加进 .gitignore（本地草稿不入库）。add 时只列有效路径，否则「The following paths are ignored」使 add 退 1、后续 `&&` 全不执行
5. **tts.mp3 24kHz mono**：正常值（edge-tts 原声），仅当抖音报音频不兼容才重包 44.1kHz
6. **HF render 是重资源**（~11min CPU 密集）：跑前告知；`renders/` 建议 gitignore（成片留本地）

## 发布（用户侧）

- 成片：`<date>/classic/video_NN.mp4`（无动效版）+ `<date>/hyperframes/renders/*.mp4`（动效版），双版验收后照发布流程传片
- 封面：`<date>/classic/cards_png/card01.png` = 成片第 1 帧，发布预览里选第 1 帧即可，不用传图
- ai_ask 项目的发布细则在 `doc/发布流程.md`（用户侧传片+文案+封面+点发布）
