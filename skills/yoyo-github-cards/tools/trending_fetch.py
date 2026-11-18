#!/usr/bin/env python3
"""GitHub Trending 抓取器(ai_ask 自有, 纯标准库): 榜单页解析 + REST 仓库明细。
不依赖 WorkBuddy 任何脚本。

用法:
  python tools/trending_fetch.py                          # 日榜+周榜, 默认语言分榜
  python tools/trending_fetch.py --periods daily --langs python,rust
  python tools/trending_fetch.py --repos EpicGames/raddebugger,owner/name   # REST 明细
输出: <out>/trending-<YYYY-MM-DD>.json (默认 out=github-trending/fetch)
  {fetched_at, boards:{"daily":[{repo,desc,lang,stars,stars_period}],...}, repos:{...}}
网络: 先直连, 失败走 127.0.0.1:7897(各试 3 次, 兼容僵尸系统代理)。REST 无认证, 60 次/时。
"""
import argparse, json, os, re, ssl, sys, time, urllib.parse, urllib.request
from datetime import date, datetime, timezone, timedelta

PROXY = "http://127.0.0.1:7897"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
DEFAULT_LANGS = ["python", "typescript", "rust", "go", "c", "c++", "c#", "swift", "kotlin", "java", "javascript", "zig"]
TZ8 = timezone(timedelta(hours=8))


def _direct_healthy():
    """10s 探针判定直连可用性(每进程缓存一次); 直连挂死时全 run 走代理优先, 避免 30 页 × 70s 白耗"""
    global _DIRECT_OK
    if _DIRECT_OK is None:
        try:
            ph = urllib.request.ProxyHandler({})
            op = urllib.request.build_opener(ph, urllib.request.HTTPSHandler(context=_PROBE_CTX))
            op.addheaders = [("User-Agent", UA)]
            op.open("https://github.com/trending?since=daily", timeout=10).read()
            _DIRECT_OK = True
        except Exception:
            _DIRECT_OK = False
    return _DIRECT_OK

_PROBE_CTX = ssl.create_default_context()
_PROBE_CTX.check_hostname = False
_PROBE_CTX.verify_mode = ssl.CERT_NONE
_DIRECT_OK = None


def fetch(url, is_api=False):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    last = None
    order = (False, True) if _direct_healthy() else (True, False)
    for use_proxy in order:
        ph = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY} if use_proxy else {})
        op = urllib.request.build_opener(ph, urllib.request.HTTPSHandler(context=ctx))
        op.addheaders = [("User-Agent", UA) if not is_api else ("User-Agent", "ai_ask-trending-fetch")]
        for _ in range(3):
            try:
                return op.open(url, timeout=60).read().decode("utf-8", "replace")
            except Exception as e:
                last = e
                time.sleep(1.5)
    raise last


def parse_board(html):
    out = []
    for part in re.split(r'<article\s+class="Box-row"', html)[1:]:
        m = re.search(r'<h2[^>]*>.*?href="/([^"]+)"', part, re.S)
        if not m:
            continue
        repo = m.group(1)
        desc = re.search(r'<p\s+class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', part, re.S)
        lang = re.search(r'itemprop="programmingLanguage">([^<]+)<', part)
        stars = re.findall(r'href="/[^"]+/stargazers"[^>]*>.*?([\d,]+)\s*</a>', part, re.S)
        sp = re.search(r'([\d,]+)\s+stars\s+(today|this week)', part)
        out.append({
            "repo": repo,
            "desc": re.sub(r'<[^>]+>', '', desc.group(1)).strip() if desc else "",
            "lang": lang.group(1).strip() if lang else "",
            "stars": int(stars[0].replace(",", "")) if stars else None,
            "stars_period": int(sp.group(1).replace(",", "")) if sp else None,
            "period_kind": sp.group(2) if sp else "",
        })
    return out


def repo_detail(full):
    j = json.loads(fetch("https://api.github.com/repos/" + full, is_api=True))
    return {
        "stars": j.get("stargazers_count"), "forks": j.get("forks_count"),
        "open_issues": j.get("open_issues_count"),
        "license": (j.get("license") or {}).get("spdx_id"),
        "created_at": j.get("created_at"), "pushed_at": j.get("pushed_at"),
        "default_branch": j.get("default_branch"),
        "issue_ratio": round(j.get("open_issues_count", 0) / max(j.get("stargazers_count", 1), 1), 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--periods", default="daily,weekly")
    ap.add_argument("--langs", default=",".join(DEFAULT_LANGS))
    ap.add_argument("--repos", default="", help="REST 明细: owner/name,owner/name")
    ap.add_argument("--out", default="github-trending/fetch")
    ap.add_argument("--top", default="5", help="输出 24h 增量 Top N")
    args = ap.parse_args()
    topn = int(args.top)

    boards = {}
    for p in [x.strip() for x in args.periods.split(",") if x.strip()]:
        url = "https://github.com/trending" + ("?since=" + p if p != "daily" else "")
        boards[p] = parse_board(fetch(url))
        time.sleep(1)
    for lg in [x.strip() for x in args.langs.split(",") if x.strip()]:
        for p in [x.strip() for x in args.periods.split(",") if x.strip()]:
            url = "https://github.com/trending/" + urllib.parse.quote(lg) + "?since=" + p
            boards[f"{p}:{lg}"] = parse_board(fetch(url))
            time.sleep(1)

    repos = {}
    for r in [x.strip() for x in args.repos.split(",") if x.strip()]:
        try:
            repos[r] = repo_detail(r)
            time.sleep(0.5)
        except Exception as e:
            repos[r] = {"error": str(e)}

    # 24h 增量 Top N: 全部 daily 榜(全站+语言分榜)去重, 按 stars_period 降序
    seen, cand = {}, []
    for k, v in boards.items():
        if not k.startswith("daily"):
            continue
        for x in v:
            if x["repo"] not in seen and x.get("stars_period") is not None:
                seen[x["repo"]] = True
                cand.append(dict(x, board=k))
    cand.sort(key=lambda x: -x["stars_period"])
    top = cand[:topn]

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"trending-{date.today().isoformat()}.json")
    data = {"fetched_at": datetime.now(TZ8).isoformat(), "top5_24h": top, "boards": boards, "repos": repos}
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"★ 24h 增量 Top{topn}:")
    for i, x in enumerate(top, 1):
        print(f"  {i}. {x['repo']}  +{x['stars_period']} (共{x['stars']}) [{x['board']}]")
    for k, v in boards.items():
        print(f"{k}: {len(v)} 项, Top3: " + " / ".join(x["repo"] for x in v[:3]))
    for k, v in repos.items():
        print(f"REST {k}: " + json.dumps(v, ensure_ascii=False)[:120])
    print("→", path)


if __name__ == "__main__":
    main()
