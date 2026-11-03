#!/usr/bin/env python3
"""抖音收藏批量转写：页内 API 取直链(10/批) + curl 3 路下载 + faster-whisper 2 路转写
用法: python3 fav-batch.py <ids.json> [workdir] [model]
  ids.json = aweme_id 字符串数组（先用 yoyo-douyin-digest 周抓取线的 weekly-stats.json 过滤 media_type==4 得到）
产物（全部在 workdir，用完即清）:
  meta.json     {id: {cdn, title, dur_ms, nick}}
  <id>.mp4      视频
  <id>.txt      带时间戳逐字稿（dy_transcribe.py 格式）
  report.json   {id: {cdn_ok, dl_size, trans_ok, ...}}
  batch.log     进度日志（BATCH DONE = 完成判据）
依赖: bsk（已连接浏览器+抖音登录态）、uv、yoyo-douyin-digest 的 dy_transcribe.py
"""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

if len(sys.argv) < 2:
    sys.exit("用法: python3 fav-batch.py <ids.json> [workdir] [model]")
IDS = json.load(open(sys.argv[1]))
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/fav-work"
MODEL = sys.argv[3] if len(sys.argv) > 3 else "small"
os.makedirs(OUT, exist_ok=True)

BSK = os.path.expanduser("~/.local/bin/bsk")
UV = os.path.expanduser("~/.local/bin/uv")
SKILL = os.path.expanduser("~/.pi/agent/skills/yoyo-douyin-digest")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/150.0.0.0 Safari/537.36"
report = {}

def log(m):
    line = "[" + time.strftime("%H:%M:%S") + "] " + m
    print(line, flush=True)
    with open(os.path.join(OUT, "batch.log"), "a") as f:
        f.write(line + "\n")

def bsk(args, sid=None, timeout=180):
    cmd = [BSK] + args + (["--session", sid] if sid else [])
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

rc, out = bsk(["session", "start", "--json"])
m = re.search(r'"session_id":\s*"(\w+)"', out) or re.search(r'(\w+)', out)
if not m:
    sys.exit("bsk session start 失败: " + out)
sid = m.group(1)
log("bsk session=" + sid)
bsk(["navigate", "https://www.douyin.com/user/self"], sid)
time.sleep(6)

# ---- 阶段1: 页内 API 取直链 + 元数据（10/批，批内 4 并发，每批重试 3 轮）----
urlmap = {}
for c in range(0, len(IDS), 10):
    chunk = IDS[c:c+10]
    js = """(async () => {
      const ids = %s;
      const out = await Promise.all(ids.map(async id => {
        try {
          const r = await fetch('/aweme/v1/web/aweme/detail/?aweme_id='+id+'&aid=1128&device_platform=webapp', {credentials:'include'});
          const j = await r.json(); const d = j.aweme_detail;
          if (!d) return [id, null];
          const cdn = (d.video && d.video.play_addr && d.video.play_addr.url_list && d.video.play_addr.url_list[0]) || '';
          return [id, {cdn, title:String(d.desc||'').slice(0,80), dur:(d.video&&d.video.duration)||0, nick:(d.author&&d.author.nickname)||''}];
        } catch(e) { return [id, null]; }
      }));
      return JSON.stringify(out);
    })()""" % json.dumps(chunk)
    got = False
    for _ in range(3):
        rc, out = bsk(["evaluate", js], sid)
        for line in out.splitlines():
            if line.startswith("["):
                for a, b in json.loads(line):
                    urlmap[str(a)] = b
                got = True
                break
        if got and all(str(a) in urlmap for a in chunk):
            break
        time.sleep(5)
    log("取链 %d/%d" % (min(c+10, len(IDS)), len(IDS)))
json.dump(urlmap, open(os.path.join(OUT, "meta.json"), "w"), ensure_ascii=True)
targets = [(a, urlmap[a]) for a in IDS if urlmap.get(a) and urlmap[a].get("cdn")]
for a, b in targets:
    report[a] = {"cdn_ok": True, "title": b.get("title", ""), "dur_ms": b.get("dur", 0), "nick": b.get("nick", "")}
for a in IDS:
    if a not in report:
        report[a] = {"cdn_ok": False, "note": "detail 无返回体（删除/风控）"}
log("取链 ok=%d fail=%d" % (len(targets), len(IDS) - len(targets)))

# ---- 阶段2: curl 3 路下载（风控小文件自动重取直链再下）----
def dl(it):
    a, b = it
    pmp4 = os.path.join(OUT, a + ".mp4")
    for _ in range(2):
        subprocess.run(["curl", "-sL", "--max-time", "600", "-A", UA, "-e", "https://www.douyin.com/",
                        "-o", pmp4, b["cdn"]], capture_output=True)
        sz = os.path.getsize(pmp4) if os.path.exists(pmp4) else 0
        if sz > 20000:
            break
        time.sleep(3)
    report[a]["dl_size"] = os.path.getsize(pmp4) if os.path.exists(pmp4) else 0

with ThreadPoolExecutor(3) as ex:
    list(ex.map(dl, targets))
log("下载完成, 总 %dMB" % (sum(report[a].get("dl_size", 0) for a, _ in targets) // 1048576))

# ---- 阶段3: faster-whisper 2 路并行 ----
def trans(a):
    t0 = time.time()
    p = subprocess.run([UV, "run", "--python", "3.12", "--with", "faster-whisper", "--with", "av",
                       SKILL + "/dy_transcribe.py", os.path.join(OUT, a + ".mp4"),
                       os.path.join(OUT, a + ".txt"), MODEL],
                      capture_output=True, text=True, timeout=7200)
    ok = p.returncode == 0 and os.path.exists(os.path.join(OUT, a + ".txt"))
    report[a]["trans_ok"] = ok
    report[a]["trans_s"] = round(time.time() - t0)
    if not ok:
        report[a]["trans_err"] = (p.stdout + p.stderr)[-300:]
    log("transcribe " + a + ": " + ("OK" if ok else "FAIL"))

with ThreadPoolExecutor(2) as ex:
    list(ex.map(trans, [a for a, _ in targets]))

json.dump(report, open(os.path.join(OUT, "report.json"), "w"), ensure_ascii=True, indent=1)
oks = [a for a in IDS if report.get(a, {}).get("trans_ok")]
log("BATCH DONE ok=%d/%d fail=%s" % (len(oks), len(IDS), [a for a in IDS if a not in oks]))
bsk(["session", "stop", sid])
