# GitHub 六卡图文管线

版式 2026-11-03 定稿（参考帖 7703407329438531791 像素采样），之后各期只换内容不动版式。

## 配置（三值：工作目录 / 内容源 / 出图目录）

**取值优先级**（取到即停）：
1. 用户会话中给的机器值（说「本机卡片工作目录在 …」时用它的）
2. 本地配置文件 `<工作目录>/assets/cards/local.md`（机器级，不进仓；只存三行路径，首次部署时写）
3. 都没有 → 先跑「新机器部署」补齐再开工

| 配置 | 说明 |
|---|---|
| 工作目录 | 卡片工作目录（**任意目录，不需要 hypit 项目**）：含 `assets/cards/cards.html`（设计+内容源）、`assets/cards/avatars/`（头像缓存，可空）、`scripts/check-cards.mjs`（体检脚本）。出图管线用全局 `hypit` CLI，与任何项目无关 |
| 内容源 | 每期日报目录 `<...>/GitHub-Trending/<YYYY-MM-DD>.md`，每项目含 一句话简介/Stars/语言/许可/亮点/注意 |
| 出图目录 | 固定 `<工作目录>/assets/cards/01-06.png`（1242×1656，抖音图文 3:4） |

**依赖**：hypit CLI（`npm i -g @hypit/hypit`；`hypit capture screenshot` 是独立命令，可直接截本地 HTML 文件，**不依赖 hypit 项目工程**）、Chrome（`hypit capture` 带 `--channel chrome`）、图片尺寸校验工具（ffprobe 或等价）、Noto Sans SC 字体（本机没有时换同类 CJK 无衬线，勿换回 YaHei）。

### 新机器部署（配置缺失时）

1. 装 hypit CLI：`npm i -g @hypit/hypit`，验 `hypit --version`
2. 选/建任意目录作「工作目录」：`mkdir -p <工作目录>/assets/cards/avatars <工作目录>/scripts`
3. 取三个产物（从原配置机拷贝，或日后从本仓取；**不 clone 任何 hypit 项目**）：`cards.html` → `assets/cards/`、`check-cards.mjs` → `scripts/`、`avatars/`（没有就跳过，出图流程会自动下载缺的头像）
4. 定位/新建内容源：优先找该机已有的 `GitHub-Trending/` 日报目录（如 obsidian 个人文档）；没有就问用户每期日报存哪，要能跨机分发才建进 obsidian 库
5. 字体：查 Noto Sans SC（mac 查系统字体目录或 `system_profiler SPFontsDataType`；Linux 用 `fc-list | grep -i "noto sans sc"`），没有就装或按依赖节降级（mac 无 Noto Sans SC 时用 PingFang SC）
6. 把三值写入 `<工作目录>/assets/cards/local.md`（格式：三行 `key: value`），汇报取值来源后继续出图流程

（原始配置机 `win` 的取值：工作目录 `F:\learn\hypit`（该机的恰好是 hypit 项目，但管线只用到里面的 `assets/cards/` 和 `scripts/check-cards.mjs`；新机器照上面 1-6 步部署即可，不必 clone 该项目），内容源 `F:\obsidian\个人文档\数据采集\GitHub-Trending\`。）

## 事实源与产物

| 是什么 | 位置（相对配置区） |
|---|---|
| 设计+内容唯一源 | `<工作目录>/assets/cards/cards.html`（6 个 `<section id="c1..c6">`，各 1242×1656） |
| 头像 | `<工作目录>/assets/cards/avatars/<owner>.png`（已存在的直接复用） |
| 参考图 | 不入仓（本机可存 `<skill目录>/references/7703407329438531791/`，`all/slide-01..06.webp` + 采样脚本）；签名 URL 会过期（`x-expires`），有本地图就绝不重拉 |

## 版式（勿改，只填内容）

- **c1 封面**：顶栏「开源周报 · GitHub 热门开源」+ 页码 → hero「本期热门开源 + TOPN」→ 主线大字（蓝）→ 语言说明 → 数据源/日期 meta → 全宽排行行（蓝等宽序号 + 52px 头像 + 名+org + 星数），内容填到页面 ~95%
- **c2-c6 单项目满版页**（11-05 起每期 1 项目/卡；旧版 2 项目/卡的 `.item` 可并排）：
  `hd`（等宽蓝序号 46px + 80px 圆角头像 + repo 名 104px/长名 56px + org 灰 20px + 右侧「本期净增⭐」46px）→ `oneline` 一句话黑 900 40px → `badges`（语言/许可/榜单/年龄，首枚蓝）→ `cols`（左 504px 浅蓝面板 3 步流程+说明 / 右灰字描述 24px + 蓝分类 28px）→ `points`（▸ 蓝前导亮点）→ `warn`（⚠ 灰）→ `foot`（repo 等宽灰 + 页码蓝）

## 设计令牌（`cards.html` :root，像素采样实测，勿凭记忆改）

bg `#fafbf8` / 黑 `#000` / 灰 `#7a7a7a` `#7e7e7e` / 说明灰 `#6d6d6d` / 线 `#dadad8` / 面板 `#f1f4ff` / 主蓝 `#174bb9`（渲染后众数 `#1048b8`）；正文 **Noto Sans SC**（本机没有时换同类 CJK 无衬线，勿换回 YaHei），等宽 **Consolas**。

## 出图步骤

1. **定当天**：`date` 查系统时钟；内容源文件名 = 当天日期。会话残留可能带旧日期，日期戳一律以系统时钟为准
2. **读文档** Top5：一句话/星数/净增/语言/许可/亮点 2-3 条/注意/榜单徽标
3. **头像**：`avatars/` 里没有的 owner，`curl -s https://api.github.com/repos/<owner>/<repo>` 取 `avatar_url` 下载到 `avatars/<owner>.png`
4. **改 `cards.html`** 填 6 段内容；repo 名超 ~10 字符给 `<h2 class="long">`（自动降 56px），长名别靠体检发现 clip 才改
5. **体检**（全 0 才出图）：`hypit capture run scripts/check-cards.mjs --channel chrome` → 每卡 `纵向溢出=0 横向溢出元素=0`（数值走文本判断，不要逐张把出图读进上下文；目检拼 1 张 montage）
6. **出图**（拒覆盖，先删旧 png）：
   ```
   cd <工作目录> && for i in 1 2 3 4 5 6; do n=$(printf "%02d" $i);
   rm -f assets/cards/$n.png
   hypit capture screenshot <工作目录>/assets/cards/cards.html --selector "#c$i" --to "assets/cards/$n.png" --viewport 1242x1656 --channel chrome
   done
   ```
7. **验尺寸**：ffprobe（或任意图片尺寸工具）查 png → 1242×1656
8. **汇报**（≤5 行）：出图位置 + 待用户 ①目检 ②上传文案（标题/正文/话题从文档提炼，正文一句话串 5 项目，话题 `#GitHub #开源项目 #开源 #AI工具 #开发工具`）；上传抖音图文由用户自己操作

## 坑（全踩过）

- `hypit capture screenshot` 必带 `--channel chrome`（默认找 puppeteer 缓存，常没有）；输出拒覆盖 → 先删/备份
- 截图不覆盖时别 `--full-page`，用 `--selector "#cN"` 单元素截
- 104px 大名字遇长名 clip，被体检的 `wide` 计数抓到 → 源头加 `.long`，别等体检
- 参考图签名 URL 过期别重拉，用本地 `references/`（本机留存，不入仓）
