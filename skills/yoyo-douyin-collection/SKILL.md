---
name: yoyo-douyin-collection
description: 抖音收藏 → 本地 Obsidian 摘要归档：按收藏时间周桶批量转写视频，产出「主旨 + 3 要点 + 留/杀建议」体例的 collection-YYYYMM.md（对齐 个人文档/数据采集/抖音收藏/ 既有格式）。用户说「归档 N 月抖音收藏」「做收藏摘要」「按 collection 格式整理收藏」时使用。只处理抖音收藏；热点抓取、文案发布、视频出片不在范围（出片用 yoyo-douyin-release-card）。
---

# Douyin Collection（收藏 → Obsidian 摘要归档）

把「抖音收藏夹某月/某几周的收藏」变成 Obsidian 里的摘要文档（`collection-YYYYMM.md`），体例对齐
`~/Documents/obsidian/个人文档/数据采集/抖音收藏/collection-202609.md` / `collection-202610.md`：
每条 = 一句话主旨 + 要点 + 留/杀/挂建议，跳过项成表，末尾速览 + 全月汇总。

依赖：
- **yoyo-douyin-digest**（必需）：周桶抓取（`weekly-stats.json` + `favorites-full.json`，见其「按收藏时间周抓取」节）+ `dy_transcribe.py` 转写引擎
- bsk（已连接浏览器 + 抖音登录态）、uv（转写走 uv 缓存，无常驻安装）

## 流程（五步）

### 1. 定范围 + 拿 ID 清单
- 已有周桶数据 → 直接用 `weekly-stats.json`（按 `week` 取 ids）；没有 → 先跑 digest skill 的周抓取
- 过滤 `media_type == 4`（视频；图文/其他 `!= 4` 不转写，留给跳过表）
- **排除已摘要过的 id**：扫目标目录下已有 collection-*.md / 试点摘要文件里的 `aweme_id`，避免重复（同一视频可被收藏多次）

```bash
python3 - <<'EOF'
import json
ws = json.load(open('<favcap>/weekly-stats.json'))
full = {str(it['id']): it for it in json.load(open('<favcap>/favorites-full.json'))}
ids = [str(i) for w in ws if w['week'] in ('2026-W40',) for i in w['ids']]  # 选要做的周
vids = [i for i in ids if full[i]['media_type'] == 4]
json.dump(vids, open('/tmp/batch-ids.json','w'))
json.dump([i for i in ids if i not in vids], open('/tmp/skip-ids.json','w'))  # 图文/其他 → 跳过表用
print(len(vids), 'videos,', len(ids)-len(vids), 'skips')
EOF
```

### 2. 批量转写（脚本，中间物全落 workdir）
```bash
python3 <skill>/fav-batch.py /tmp/batch-ids.json /tmp/fav-work small
# 完成判据: tail /tmp/fav-work/batch.log 出现 BATCH DONE ok=N/M
```
- 耗时估算：音频总量 × 1~2 ÷ 2 路并行；5.7h 音频实测 ≈ 3h（4 核 Intel MBP）
- 机器休眠会挂起不报错，长批次避开合盖时段
- 少量失败（直链过期/风控小文件）：把失败 id 单独存 json 重跑一遍脚本即可（脚本幂等）

### 3. 写摘要文档（agent 活，照模板）
读 workdir 下全部 `<id>.txt`（按周分组），逐条写：

```markdown
---
date: <采集日>
type: 抖音收藏摘要
tags: [抖音, 收藏夹, 摘要]
collection_month: YYYY-MM
source: 抖音收藏夹 YYYY 年 M 月（Wxx~Wxx，收藏时间窗口归属）；yoyo-douyin-digest 方案B（页内 API 直链 + faster-whisper 本地转写）
---

# 抖音收藏摘要 - YYYY年M月

> 读法：每条 = 一句话主旨 + 3 要点 + 留/杀建议，按收藏周分节，编号全月连续（1 起）。
> 进度：<N 条完成>；中间产物不留档。

## 2026-Wxx（收藏窗口 MM-DD~MM-DD）：<V> 视频已转写 + <I> 图文跳过

### <序号>. <标题（desc 截断/转写纠正）>（<时长>s · [原链接](https://www.douyin.com/video/<id>)）

**主旨**：<一句话，说清这条视频到底讲了什么/推了什么工具>

**要点**：
- <事实要点 1，保留数字/星数/命令等硬信息>
- <事实要点 2>
- <事实要点 3>

**建议**：<📌 留 / ⏸ 挂起 / 🔪 杀>——<一句理由，尽量对照本机已有工具/需求>

（周节末尾）

### 跳过 <N> 条（S<起>–S<止>，图文不转写）

| # | 标题（收藏列表 desc） | 链接 | 备注 |
|---|---|---|---|
| S9 | <desc 截断> | [<id>](https://www.douyin.com/video/<id>) | 图文 + 详情无返回体（如有） |
```

### 4. 判定规则（留/挂/杀，对齐既有文件习惯）
- **📌 留**：方法可直接抄 / 工具与本机需求对口 / 素材可取（素材类标「留（素材）」并归堆「素材包」）
- **⏸ 挂起**：项目名/仓库「名待定」（whisper 专名误读多，一律标**需回查 + 给检索关键词**）；需求未出现的备选工具
- **🔪 杀**：无口播短片（转写 0 行）、「扣 1/私信领」引流体、榜单/必装清单重复条、与本机方向无关
- 每条建议都先想「本机对照」：与本机已有 skill/工具/仓库同题的，写明「第 N 次本机已有工具上榜/同题」——这是既有文件的固定观察项
- 长视频（>5 分钟）要点取前 1/3 为主；B 站/口播腔转写专名误读要人工纠偏后再写进文档

### 5. 落盘 + 收尾
- 路径：`~/Documents/obsidian/个人文档/数据采集/抖音收藏/collection-YYYYMM.md`（月份与收藏窗口归属月一致；跨月周按窗口中点归月并在节标题标注）
- obsidian 仓不 commit/push、脏文件不处置（全局规则）
- **中间物不留**：文档写完后 `rm -rf` workdir（mp4/txt/log 全清）；用户要留逐字稿才改存 `~/douyin-digests/`
- 文档末尾固定两节：`## 全月留/杀速览`（统计表 + 留/挂行动项行；杀项不逐条列）+ `## 本机对照观察`（同题家族/套路统计）

## Failure table

| 症状 | 处理 |
|---|---|
| detail 接口返回空 / `aweme_detail:null`（带 `filter_detail`） | 内容已删或风控，慢速重试无效 → meta.json 里记 `cdn_ok:false`，摘要按收藏列表 desc 兜底 + 文档标注 |
| 下载到 <20KB 文件（常见 552B 风控页） | 直链过期/被拦 → 单独重跑失败 id（脚本会重取新直链）；批量重取不了再逐条 bsk 取链 |
| `UnicodeEncodeError: 'utf-8' codec can't encode ... surrogates` | bsk 回读含 emoji 孤立代理字符 → JSON 一律 `ensure_ascii=True` 落盘（脚本已内置） |
| 转写 0 行（无口播短片） | 正常：纯演示/纯 BGM/字幕歌。摘要标「无口播/无转写行」，判杀 |
| whisper 把项目名念错 | 不照抄转写名，标「名待定 + 回查关键词」（如「github UI 设计系统 120k stars」） |
| 机器休眠批次挂起 | 批次恢复后自动续跑（脚本按 id 幂等）；预估时长要避开合盖 |

## Not for
- 只要视频文件不要内容 → yt-dlp（digest skill 已覆盖）
- 单条视频整理 → yoyo-douyin-digest（`dy-digest.sh`）
- 卡片/出片 → yoyo-douyin-release-card
- 抖音以外平台收藏 → 不适用（风控/接口/cookie 行为均为抖音专属）
