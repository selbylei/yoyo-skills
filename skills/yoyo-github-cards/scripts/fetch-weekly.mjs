#!/usr/bin/env node
// fetch-weekly.mjs — 周榜 TOP10 一键数据 + 草稿（yoyo-github-cards skill 随附）
// 零外部依赖（Node ≥18 全局 fetch）。用法（在任意项目根目录）：
//   node <skill>/scripts/fetch-weekly.mjs [--top 10] [--out .github-cards]
// 产物（默认 <CWD>/.github-cards/）：
//   data.json          TOP N 全字段（rank/owner/repo/stars/weekly/license/created/desc/issues/pushed）
//   avatars/*.png      owner 头像（每期现抓）
//   readmes/*.md       各仓 README 前 200 行（agent 提炼文案用）
//   cards.html         按 assets/cards-weekly10.html 模板填好机械字段的草稿（TODO 文案待 agent 补）
// 依赖：出图另需全局 hypit CLI + Chrome（`hypit capture ...`），与本脚本无关。

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'

const arg = (k, d) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : d }
const TOP = Number(arg('--top', 10))
const OUT = resolve(arg('--out', '.github-cards'))
const LANGS = ['python', 'rust', 'typescript', 'javascript', 'go', 'cpp', 'c', 'java', 'swift', 'kotlin']
const UA = { 'User-Agent': 'yoyo-github-cards-fetch/1.0' }

const get = async (url) => { const r = await fetch(url, UA); if (!r.ok) throw new Error(`${url} → ${r.status}`); return r }

function parseTrending(html) {
  const out = []
  for (const b of html.matchAll(/<article class="Box-row">([\s\S]*?)<\/article>/g)) {
    const blk = b[1]
    const m = blk.match(/<h2 class="h3 lh-condensed">[\s\S]*?<a href="\/([^"]+?)"/)
    if (!m) continue
    let repo = m[1]
    if (repo.endsWith('/stargazers')) repo = repo.slice(0, -'/stargazers'.length)
    const sm = blk.match(/href="[^"]*\/stargazers"[\s\S]*?([\d,]+)\s*<\/a>/)
    const w = blk.match(/([\d,]+) stars this (?:week|day)/)
    const l = blk.match(/itemprop="programmingLanguage"[^>]*>([^<]+)</)
    out.push({ repo, stars: sm ? sm[1] : null, weekly: w ? Number(w[1].replace(/,/g, '')) : 0, lang: l ? l[1].trim() : '' })
  }
  return out
}

const lic = (s) => (s || 'No license').replace('BSD-3-Clause', 'BSD-3').replace('Apache', 'Apache')
const age = (iso) => {
  const m = Math.max(0, Math.round((Date.now() - new Date(iso)) / (1000 * 86400 * 30.44) * 2) / 2)
  if (m < 1) return '不到 1 个月'
  if (m < 12) return Number.isInteger(m) ? `${m} 个月` : `${m - 0.5}个半月`
  return `${Math.max(1, Math.round(m / 12))} 年`
}
const today = () => { const d = new Date(); return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}` }

function itemBlock(i, d) {
  const name = d.repo.split('/')[1]
  const h2 = name.length > 10 ? `<h2 class="long">${name}</h2>` : `<h2>${name}</h2>`
  const badges = `<span class="bdg">${d.lang || '—'}</span><span class="bdg">${d.license}</span><span class="bdg">周榜第 ${i}</span><span class="bdg">${d.age}</span>`
  return `<div class="ihead">
    <span class="num">${String(i).padStart(2, '0')}</span><img class="ava" src="avatars/${d.owner}.png" alt="${d.owner}">
    <span class="nm">${h2}<div class="org">${d.repo}</div></span>
    <span class="gain"><span class="lb">本周净增⭐</span><span class="v">+${d.weekly.toLocaleString('en-US')}</span></span>
  </div>
  <div class="oneline">TODO: ${name} 一句话简介（读 readmes/ 首段提炼，≤20 字）</div>
  <div class="badges">${badges}</div>
  <div class="cols">
    <div class="panel">
      <div class="step"><div class="t">TODO ①</div><div class="d">TODO: 三步流程（面板 3 步，标题 4-6 字 + 说明一行）</div></div>
    </div>
    <div class="right">
      <div class="desc">TODO: 描述（2-3 行，灰字区）</div>
      <div class="cat">TODO: 分类</div>
    </div>
  </div>
  <div class="points">
    <p><span class="k">▸</span>TODO: 亮点 1-2 条（各 ≤20 字）</p>
  </div>
  <div class="warn"><span class="k">⚠</span>TODO: 注意（1 行）</div>`
}

function c1Row(i, d) {
  const name = d.repo.split('/')[1]
  const cls = i <= 3 ? ` r${i}` : ''
  return `<div class="row${cls}"><span class="num">${String(i).padStart(2, '0')}</span><img class="ava" src="avatars/${d.owner}.png" alt="${d.owner}">
      <span class="nm"><span class="name">${name}</span><br><span class="od">TODO: 短标签（≤10 字）</span></span><span class="stars">+${d.weekly.toLocaleString('en-US')}</span></div>`
}

async function main() {
  console.log(`[1/5] 抓取周榜（全站 + ${LANGS.length} 语言分榜, since=weekly）...`)
  const slugs = ['all', ...LANGS]
  const pages = await Promise.allSettled(slugs.map(s => get(`https://github.com/trending/${s === 'all' ? '' : s + '/'}?since=weekly`).then(r => r.text())))
  const union = new Map()
  let got = 0
  for (const p of pages) {
    if (p.status !== 'fulfilled') { console.log('  ! 分榜抓取失败（页面结构可能变化），跳过:', p.reason); continue }
    for (const d of parseTrending(p.value)) {
      got++
      if (!union.has(d.repo)) union.set(d.repo, d)
      else { union.get(d.repo).weekly = Math.max(union.get(d.repo).weekly, d.weekly) }
    }
  }
  const top = [...union.values()].sort((a, b) => b.weekly - a.weekly).slice(0, TOP)
  console.log(`[2/5] ${got} 席并集 → 按周净增取 TOP${TOP}，核对 API 元数据 + 头像 + README...`)
  mkdirSync(join(OUT, 'avatars'), { recursive: true }); mkdirSync(join(OUT, 'readmes'), { recursive: true })
  for (const d of top) {
    const [owner, repo] = d.repo.split('/')
    d.owner = owner; d.repoName = repo
    const meta = await (await get(`https://api.github.com/repos/${d.repo}`)).json().catch(() => ({}))
    d.stars = meta.stargazers_count ?? Number((d.stars || '0').replace(/,/g, ''))
    d.license = lic(meta.license?.spdx_id); d.created = meta.created_at?.slice(0, 10) || ''
    d.pushed = meta.pushed_at?.slice(0, 10) || ''; d.issues = meta.open_issues_count ?? 0
    d.desc = meta.description || ''; d.age = d.created ? age(d.created) : '?'
    const u = await (await get(`https://api.github.com/users/${owner}`)).json().catch(() => ({}))
    if (u.avatar_url) {
      const a = join(OUT, 'avatars', `${owner}.png`)
      if (!existsSync(a)) { const img = await get(u.avatar_url); writeFileSync(a, Buffer.from(await img.arrayBuffer())) }
    }
  }

  for (const d of top) {
    let ok = false
    for (const fn of ['README.md', 'readme.md', 'Readme.md']) {
      const r = await fetch(`https://raw.githubusercontent.com/${d.repo}/HEAD/${fn}`, UA).catch(() => null)
      if (r?.ok) {
        const lines = (await r.text()).split('\n').slice(0, 200).join('\n')
        writeFileSync(join(OUT, 'readmes', `${d.owner}_${d.repoName}.md`), lines); ok = true; break
      }
    }
    if (!ok) console.log(`  ! ${d.repo} 没抓到 README（文案靠 API desc）`)
  }
  writeFileSync(join(OUT, 'data.json'), JSON.stringify(top.map((d, i) => ({ rank: i + 1, ...d })), null, 2))

  console.log('[3/5] 生成 cards.html 草稿...')
  const tplPath = join(dirname(new URL(import.meta.url).pathname), '..', 'assets', 'cards-weekly10.html')
  const tpl = readFileSync(tplPath, 'utf8')
  const cnt = top.map(d => d.lang || '?')
  const topCnt = (l) => cnt.filter(c => c === l).length
  const mainLang = topCnt([...new Set(cnt)].sort((a, b) => topCnt(b) - topCnt(a))[0])
  const langLine = `${TOP} 项跨 ${new Set(cnt).size} 语言（${[...new Set(cnt)].sort((a, b) => topCnt(b) - topCnt(a)).slice(0, 2).map(l => `${l}${topCnt(l) > 1 ? `×${topCnt(l)}` : ''}`).join('、')}）· 净增 = GitHub 周榜读数`
  let html = tpl
  html = html.replace('{{HERO_L1}}', '本周热门开源').replace('{{HERO_L2}}', '周榜项目').replace('{{HERO_TOPN}}', `TOP${TOP}`)
  html = html.replace('{{LANG_LINE}}', langLine).replace('{{META_LINE}}', `GitHub Trending 周榜 · ${today()}`)
  html = html.replace('{{C1_ROWS}}', top.map((d, i) => c1Row(i + 1, d)).join('\n'))
  for (let i = 0; i < 10; i++) {
    const n = i + 1
    if (i < top.length) html = html.replace(`{{ITEM_${n}}}`, itemBlock(n, top[i]))
  }
  // FOOT_k = 第 k 张卡（含项 2k-1、2k）页脚用第二项的 repo
  for (let k = 1; k <= 5; k++) {
    const n = 2 * k
    if (n <= top.length) html = html.replace(`{{FOOT_${k}}}`, top[n - 1].repo)
  }
  writeFileSync(join(OUT, 'cards.html'), html)

  console.log('[4/5] 摘要')
  top.forEach((d, i) => console.log(`  ${String(i + 1).padStart(2, '0')} ${d.repo}  +${d.weekly.toLocaleString('en-US')}/周  ${d.license} ${d.age}`))
  const todo = (readFileSync(join(OUT, 'cards.html'), 'utf8').match(/TODO/g) || []).length
  console.log(`[5/5] 完成。草稿 ${join(OUT, 'cards.html')}（${todo} 处 TODO 待 agent 填）；后续：填 TODO → hypit capture run <skill>/scripts/check-cards.mjs 体检 → 出图 01-06.png`)
}
main().catch(e => { console.error('FAILED:', e.message); process.exit(1) })
