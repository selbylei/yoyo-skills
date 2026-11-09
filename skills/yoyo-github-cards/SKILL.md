# GitHub 六卡图文管线

两种版式（均已定稿，之后各期只换内容不动版式；版式取自参考帖 7703407329438531791 像素采样）：
- **周榜 TOP10 双项版**（11-08 起主线）：c1 十行排行 + c2-c6 每卡 2 项；数据源 = GitHub 周榜（全站 + 语言分榜并集按周净增排序）
- **日榜 TOP5 单项目满版页**（旧流程）：c2-c6 每卡 1 项目；数据源 = 每期日报 `GitHub-Trending/<date>.md`

设计令牌（勿凭记忆改）：bg `#fafbf8` / 蓝 `#174bb9` / 线 `#dadad8` / 面板 `#f1f4ff` / top3 行底 `#fceeec #fcf6e6 #edf2fe`；正文 **Noto Sans SC**（缺则同类 CJK 无衬线，mac 用 PingFang SC，勿换回 YaHei），等宽 **Consolas**。

## 周榜快跑（零依赖布局，推荐）

**效果**：在任意项目根目录一条命令出数据 + 草稿，产物全在 `<项目根>/.github-cards/`，不依赖 hypit 项目、不建任何前置目录、不需要 local.md。

**一次性前提**：node ≥18 + `npm i -g @hypit/hypit`（出图引擎）+ Chrome + ffprobe（或等价尺寸校验）。

| 步 | 做什么 |
|---|---|
| 1 数据+草稿 | `cd <项目根> && node <skill>/scripts/fetch-weekly.mjs [--top 10]` → `.github-cards/`：`data.json`（TOP N 全字段）、`avatars/`（owner 头像现抓）、`readmes/`（各仓 README 前 200 行）、`cards.html` 草稿（机械字段已填：序号/头像/星数/周净增/语言/许可/年龄/榜单徽标，长名自动加 `.long`；余 ~81 处 TODO 文案） |
| 2 填文案 | agent 读 `.github-cards/readmes/*` + `data.json`，替换 cards.html 中 TODO：一句话简介（≤20 字）/ c1 短标签（≤10 字）/ 面板 3 步流程 / 描述 2-3 行 / 蓝色分类 / 亮点 1-2 条 / ⚠ 注意 1 行。质量要求同日榜版（亮点要具体、注意要可操作） |
| 3 体检 | `cd <项目根> && hypit capture run <skill>/scripts/check-cards.mjs --channel chrome`（自动定位 `.github-cards/cards.html`，旧 `assets/cards/` 布局也认）→ 6/6 全 0 才出图（数值走文本判断，别逐张读图进上下文；目检拼 1 张 montage） |
| 4 出图 | `for i in 1..6: rm -f .github-cards/NN.png && hypit capture screenshot <项目根>/.github-cards/cards.html --selector "#c$i" --to ".github-cards/NN.png" --viewport 1242x1656 --channel chrome`（拒覆盖，先删） |
| 5 验+汇报 | ffprobe 验 1242×1656；汇报 ≤5 行：出图位置 + 待用户 ①目检 ②上传文案（标题/正文一句话串 10 项/话题 `#GitHub #开源项目 #开源 #AI工具 #开发工具`）；上传抖音图文由用户自己操作 |

**口径**（11-08 定）：TOP10 = 全站 + 10 语言分榜 since=weekly 并集按周净增排序（不用官方列表顺序）；周榜读数随时段漂移（trending 页会重渲染），**以当次抓取为准**；周榜不套日报「零 Agent 技能类」排除，技能/平台类按本体收录、卡内 ⚠ 标注本体属性。

## 日榜版（旧流程）

- 内容源 = 每期日报 `GitHub-Trending/<YYYY-MM-DD>.md`（Top5：一句话/星数/净增/语言/许可/亮点/注意/榜单徽标）
- 设计+内容源 `<工作目录>/assets/cards/cards.html`（单项目满版页模板，随 skill 分发 `<skill目录>/assets/cards.html`）；头像 `assets/cards/avatars/<owner>.png`（缺的从 API `avatar_url` 现拉）
- 填内容 → 体检 → 出图 → 验尺寸 → 汇报，步骤同周榜快跑 3-5（体检/出图路径改 `assets/cards/`）
- 机器固定工作目录可写 `<工作目录>/assets/cards/local.md`（三行 `key: value`：工作目录/内容源/出图目录）；不写就用 CWD 布局

## 事实源与产物

| 是什么 | 位置 |
|---|---|
| 双项模板（周榜版） | `<skill目录>/assets/cards-weekly10.html`（占位符由 fetch-weekly.mjs 填充） |
| 单项目模板（日榜版） | `<skill目录>/assets/cards.html` |
| 数据+草稿脚本 | `<skill目录>/scripts/fetch-weekly.mjs`（零外部依赖，node ≥18） |
| 体检脚本 | `<skill目录>/scripts/check-cards.mjs`（CWD 自动定位：`.github-cards/` → `assets/cards/` → 脚本相对路径） |
| 新布局产物 | `<CWD>/.github-cards/`：data.json / readmes/ / avatars/ / cards.html / 01-06.png（1242×1656） |
| 参考图 | 不入仓（`<skill目录>/references/7703407329438531791/`：`all/slide-01..06.webp` + `sampling.py`）；签名 URL 会过期，有本地图绝不重拉 |

## 版式要点（勿改版式只填内容）

- **周榜双项**：`ihead`（蓝序号 + 56px 头像 + 名 72px/长名 40px + org + 右侧「本周净增⭐」）→ `oneline` 34px 黑 900 → `badges`（语言/许可/榜单/年龄，首枚蓝）→ `cols`（左 452px 面板 3 步 / 右灰字描述 + 蓝分类）→ `points` ▸ 蓝前导 → `warn` ⚠ 灰；c1 十行排行（前 3 行着色）
- **日榜满版**：`hd`（104px/长名 56px 大标题）→ `oneline` 40px → `badges` → `cols`（504px 面板）→ `points` → `warn` → `foot`
- 长名靠 `.long` 降字号（脚本已自动加），别等体检发现 clip 才改

## 坑（全踩过）

- `hypit capture screenshot` 必带 `--channel chrome`（默认找 puppeteer 缓存，常没有）；输出拒覆盖 → 先删
- 截图用 `--selector "#cN"` 单元素截，别 `--full-page`
- 周榜读数随时段漂移 + 官方 trending 列表非按星数排序 → 一律用 fetch 脚本「并集按周净增」口径
- fetch 脚本未认证走 60/h API 限额（10 仓 + 10 用户 = 20 次，够用）；超限/被限就设 `GH_TOKEN` 或等额度刷新
- README 缺失的仓（如本期 t3code 无 desc）文案靠 API description + 页面正文，别硬编
- 参考图签名 URL 过期别重拉，用本地 `references/`
