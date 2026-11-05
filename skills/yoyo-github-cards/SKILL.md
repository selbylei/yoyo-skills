---
name: yoyo-github-cards
description: GitHub 热门开源六卡图文（抖音 1242×1656）出图/换内容重出。用户说"六卡换成 X 天内容"「重做 GitHub 图文卡」「按 X 文档出 6 张卡」时使用。内容源 = 个人文档 GitHub-Trending 日报，版式 = 已定稿浅色参考风，管线 = 改 cards.html → 拉头像 → 体检 0 溢出 → hypit screenshot。
---

# GitHub 六卡图文管线

工作目录 `F:\learn\hypit`。版式 2026-11-03 定稿（参考帖 7703407329438531791 像素采样），之后各期只换内容不动版式。

## 事实源与产物

| 是什么 | 路径 |
|---|---|
| 内容源（每期） | `F:\obsidian\个人文档\数据采集\GitHub-Trending\<YYYY-MM-DD>.md`（每项目含 一句话简介/Stars/语言/许可/亮点/注意） |
| 设计+内容唯一源 | `F:\learn\hypit\assets\cards\cards.html`（6 个 `<section id="c1..c6">`，各 1242×1656） |
| 头像 | `F:\learn\hypit\assets\cards\avatars\<owner>.png`（已存在的直接复用） |
| 出图 | `F:\learn\hypit\assets\cards\01-06.png`（1242×1656，抖音图文 3:4） |
| 参考图/色样工具 | `references/7703407329438531791/all/slide-01..06.webp`（用户 11-03 确认保留）、`scripts/sample-ref.py`、`scripts/compare-colors.py` |

## 版式（勿改，只填内容）

- **c1 封面**：顶栏「开源周报 · GitHub 热门开源」+ 页码 → hero「本期热门开源 + TOPN」→ 主线大字（蓝）→ 语言说明 → 数据源/日期 meta → 全宽排行行（蓝等宽序号 + 52px 头像 + 名+org + 星数），内容填到页面 ~95%
- **c2-c6 单项目满版页**（11-05 起每期 1 项目/卡；旧版 2 项目/卡的 `.item` 可并排）：
  `hd`（等宽蓝序号 46px + 80px 圆角头像 + repo 名 104px/长名 56px + org 灰 20px + 右侧「本期净增⭐」46px）→ `oneline` 一句话黑 900 40px → `badges`（语言/许可/榜单/年龄，首枚蓝）→ `cols`（左 504px 浅蓝面板 3 步流程+说明 / 右灰字描述 24px + 蓝分类 28px）→ `points`（▸ 蓝前导亮点）→ `warn`（⚠ 灰）→ `foot`（repo 等宽灰 + 页码蓝）

## 设计令牌（`cards.html` :root，像素采样实测，勿凭记忆改）

bg `#fafbf8` / 黑 `#000` / 灰 `#7a7a7a` `#7e7e7e` / 说明灰 `#6d6d6d` / 线 `#dadad8` / 面板 `#f1f4ff` / 主蓝 `#174bb9`（渲染后众数 `#1048b8`）；正文 **Noto Sans SC**（本机有，勿换回 YaHei），等宽 **Consolas**。

## 出图步骤

1. **定当天**：`date` 查系统时钟；内容源文件名 = 当天日期。会话残留可能带旧日期，日期戳一律以系统时钟为准
2. **读文档** Top5：一句话/星数/净增/语言/许可/亮点2-3条/注意/榜单徽标
3. **头像**：`avatars/` 里没有的 owner，`curl -s https://api.github.com/repos/<owner>/<repo>` 取 `avatar_url` 下载到 `avatars/<owner>.png`
4. **改 `cards.html`** 填 6 段内容；repo 名超 ~10 字符给 `<h2 class="long">`（自动降 56px），长名别靠体检发现 clip 才改
5. **体检**（全 0 才出图）：`hypit capture run scripts/check-cards.mjs --channel chrome` → 每卡 `纵向溢出=0 横向溢出元素=0`
6. **出图**（拒覆盖，先删旧 png）：
   ```
   cd F:/learn/hypit && for i in 1 2 3 4 5 6; do n=$(printf "%02d" $i);
   rm -f assets/cards/$n.png
   hypit capture screenshot F:/learn/hypit/assets/cards/cards.html --selector "#c$i" --to "assets/cards/$n.png" --viewport 1242x1656 --channel chrome
   done
   ```
7. **验尺寸**：`tools\ffprobe.exe -v error -show_entries stream=width,height -of csv assets/cards/01.png` → 1242×1656
8. **汇报**（≤5 行）：出图位置 + 待用户 ①目检 ②上传文案（标题/正文/话题从文档提炼，正文一句话串 5 项目，话题 `#GitHub #开源项目 #开源 #AI工具 #开发工具`）；上传抖音图文由用户自己操作

## 坑（全踩过）

- `hypit capture screenshot` 必带 `--channel chrome`（默认找 puppeteer 缓存没有；Chrome 装在 `C:\Program Files (x86)`）；输出拒覆盖 → 先删/备份
- 截图不覆盖时别 `--full-page`，用 `--selector "#cN"` 单元素截
- 104px 大名字遇长名 clip，被体检的 `wide` 计数抓到 → 源头加 `.long`，别等体检
- 参考图签名 URL 会过期（`x-expires`），别重新拉，本地 6 张 slide 全量在手
- Agnes 模型单次请求 ≤4 图：agent 不逐张读 6 张出图，体检走文本数值；要目检让用户看或拼 1 张 montage（占 1 图位）
