#!/usr/bin/env python3
"""卡片渲染器:cards.json → 每张卡一个 HTML(1080×1920),再用 headless Chrome 截图出 PNG。
用法:python3 tools/cards.py doc/video01/cards.json
产物:<json 同目录>/cards_html/cardNN.html + cards_png/cardNN.png
本机无 brew 依赖,仅标准库 + /Applications/Google Chrome.app
"""
import glob, json, os, re, shutil, subprocess, sys

CHROME = next((p for p in [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",  # Windows
    "C:/Program Files/Google/Chrome/Application/chrome.exe",        # Windows
] if os.path.exists(p)), None)
if CHROME is None:  # 回落: Playwright 自带 Chromium(取最新版) → Edge
    _pw = sorted(glob.glob("C:/Users/*/AppData/Local/ms-playwright/chromium-*"))
    CHROME = (_pw[-1] + "/chrome-win64/chrome.exe" if _pw
              else "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
if not os.path.exists(CHROME):
    sys.exit(f"找不到可用浏览器: {CHROME}")
_PAPER_GRAIN = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='420' height='420'%3E"
                 "%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E"
                 "%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E"
                 "%3Crect width='420' height='420' filter='url(%23n)' opacity='0.055'/%3E%3C/svg%3E\"),")
PALETTES = {
  "paper": {  # 米白纸感编辑风(抖音账号默认)
    "bg": ("radial-gradient(900px 600px at 85% 8%, rgba(217,72,31,.07), transparent 60%),"
           " radial-gradient(1200px 900px at 10% 95%, rgba(25,23,19,.06), transparent 60%),"
           + _PAPER_GRAIN +
           " repeating-linear-gradient(0deg, rgba(25,23,19,.022) 0px, rgba(25,23,19,.022) 1px, transparent 1px, transparent 90px),"
           " repeating-linear-gradient(90deg, rgba(25,23,19,.022) 0px, rgba(25,23,19,.022) 1px, transparent 1px, transparent 90px), #f5f1e8"),
    "ink": "#191713", "ink2": "#5c564a", "accent": "#d9481f", "line": "#c9c2b2",
    "cardbg": "#fffdf7", "thbg": "#191713", "thfg": "#f5f1e8", "onaccent": "#fff",
    "ghostc": "rgba(25,23,19,.05)", "shadow": "rgba(25,23,19,.12)",
    "codebg": "#fffdf7", "codehd": "#efe9db", "codetx": "#191713",
    "h1font": "'Songti SC','Noto Serif SC',serif" },
  "corporate": {  # 深蓝金(企业宣传片)
    "bg": "radial-gradient(900px 640px at 82% 6%, rgba(212,168,63,.16), transparent 60%),"
         " radial-gradient(1200px 900px at 8% 96%, rgba(35,80,150,.25), transparent 65%), linear-gradient(180deg,#0d1c36 0%,#081120 100%)",
    "ink": "#eef1f7", "ink2": "#8fa0bd", "accent": "#d4a83f", "line": "#243a5f",
    "cardbg": "#0f1e3a", "thbg": "#d4a83f", "thfg": "#0d1c36", "onaccent": "#0d1c36",
    "ghostc": "rgba(212,168,63,.09)", "shadow": "rgba(0,0,0,.5)",
    "codebg": "#0f1e3a", "codehd": "#0b1830", "codetx": "#dbe4f2",
    "h1font": "'Songti SC','Noto Serif SC',serif" },
  "tech": {  # 近黑青(技术/产品盘点风,参考 douyin/ref/deepseek-harness-ai-daily)
    "bg": "radial-gradient(900px 600px at 85% 8%, rgba(34,211,238,.10), transparent 60%),"
         " radial-gradient(1200px 900px at 10% 95%, rgba(30,80,160,.18), transparent 60%), linear-gradient(180deg,#070b12 0%,#04060a 100%)",
    "ink": "#e8eef6", "ink2": "#7f8ea3", "accent": "#22d3ee", "line": "#1b2940",
    "cardbg": "#0b1220", "thbg": "#101a2c", "thfg": "#e8eef6", "onaccent": "#04060a",
    "ghostc": "rgba(34,211,238,.16)", "shadow": "rgba(0,0,0,.6)",
    "codebg": "#0d1420", "codehd": "#111a29", "codetx": "#d9e6f2",
    "h1font": "'PingFang SC','Noto Sans SC',sans-serif" },
  "sketch": {  # 黑底手绘风(dark-demo 11-02: 近黑底+白虚线圆角框+黄大标题+贴纸, 参考@小涵不秃头)
    "bg": "radial-gradient(1000px 700px at 50% 0%, rgba(255,214,10,.05), transparent 60%), linear-gradient(180deg,#0d0d11 0%,#09090b 100%)",
    "ink": "#f2f0e6", "ink2": "#8b8b94", "accent": "#ffd60a", "line": "rgba(242,240,230,.45)",
    "cardbg": "#131317", "thbg": "#ffd60a", "thfg": "#0d0d11", "onaccent": "#0d0d11",
    "ghostc": "rgba(255,214,10,.07)", "shadow": "rgba(0,0,0,.6)",
    "codebg": "#0e0e12", "codehd": "#16161b", "codetx": "#e8e8ee",
    "h1font": "'PingFang SC','Noto Sans SC',sans-serif" },
}

CSS = """
:root {{ --ink:{ink}; --ink2:{ink2}; --accent:{accent}; --line:{line}; --cardbg:{cardbg};
        --thbg:{thbg}; --thfg:{thfg}; --onaccent:{onaccent}; --ghostc:{ghostc}; --shadow:{shadow}; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:1080px; height:1920px; overflow:hidden; }}
body {{ background:{bgimg}{bg}; color:var(--ink); font-family:'PingFang SC','Noto Sans SC',sans-serif; position:relative; }}
.serif {{ font-family:'Songti SC','Noto Serif SC',serif; }}
.head {{ position:absolute; top:70px; left:80px; right:80px; display:flex; justify-content:space-between; align-items:center;
       border-bottom:4px solid var(--ink); padding-bottom:30px; }}
.kicker {{ display:flex; align-items:center; gap:22px; font-size:36px; font-weight:600; letter-spacing:4px; }}
.kicker::before {{ content:''; width:26px; height:26px; background:var(--accent); }}
.idx {{ font-size:38px; font-weight:700; color:var(--accent); letter-spacing:4px; }}
.wrap {{ position:absolute; top:300px; bottom:0; left:80px; right:80px; }}  /* bottom:0 撑到页面底, .cap 绝对定位才锚定页面底(统一胶囊落点) */
h1 {{ font-family:{h1font}; font-size:94px; line-height:1.3; font-weight:700; letter-spacing:2px; }}
h1 strong {{ color:var(--accent); }}
.sub {{ margin-top:40px; font-size:42px; color:var(--ink2); line-height:1.5; }}
ol {{ margin-top:70px; list-style:none; counter-reset:it; }}
li {{ counter-increment:it; font-size:45px; line-height:1.5; padding:24px 0 24px 78px; position:relative;
     border-bottom:2px solid var(--line); }}
li::before {{ content:counter(it,decimal-leading-zero); position:absolute; left:0; top:26px;
     font-family:'Songti SC',serif; font-size:40px; color:var(--accent); font-weight:700; }}
li strong {{ color:var(--accent); font-weight:600; }}
.flow {{ display:flex; align-items:center; justify-content:center; gap:16px; margin-top:140px; flex-wrap:wrap; }}
.chip {{ border:3px solid var(--ink); border-radius:10px; padding:30px 36px; font-size:48px; font-weight:600;
       font-family:'Songti SC',serif; background:var(--cardbg); box-shadow:6px 6px 0 var(--shadow); }}
.arrow {{ color:var(--accent); font-size:52px; font-weight:800; }}
table {{ margin-top:90px; border-collapse:collapse; width:100%; background:var(--cardbg); box-shadow:8px 8px 0 var(--shadow); }}
th,td {{ font-size:42px; padding:28px 26px; text-align:left; border:2px solid var(--line); }}
th {{ background:var(--thbg); color:var(--thfg); font-size:44px; }}
th:first-child, td:first-child {{ color:var(--ink2); width:210px; background:var(--cardbg); font-weight:400; }}
th:first-child {{ color:transparent; }}
td strong {{ color:var(--accent); font-weight:600; }}

.codebox {{ margin-top:70px; border:2px solid var(--line); border-radius:12px; overflow:hidden;
        background:var(--codebg); box-shadow:8px 8px 0 var(--shadow); }}
.codehead {{ display:flex; justify-content:space-between; padding:24px 34px; background:var(--codehd);
        font-family:'SF Mono',Menlo,monospace; font-size:30px; color:var(--ink2);
        border-bottom:2px solid var(--line); letter-spacing:1px; }}
pre.code {{ padding:34px 38px; font-family:'SF Mono',Menlo,monospace; font-size:31px; line-height:1.55;
        color:var(--codetx); white-space:pre-wrap; }}

.gh {{ margin-top:56px; font-size:36px; color:var(--ink2); letter-spacing:1px; border:2px solid var(--line);
     border-radius:10px; padding:22px 28px; display:inline-block; background:var(--codebg); }}
.gh strong {{ color:var(--accent); font-size:40px; font-weight:700; }}

.bar {{ margin-top:60px; background:var(--ink); color:var(--cardbg); border-radius:14px; padding:32px 40px;
      display:flex; justify-content:space-between; align-items:center; gap:30px; box-shadow:8px 8px 0 var(--shadow); }}
.bar .bl {{ font-size:42px; font-weight:700; letter-spacing:1px; }}
.bar .bl strong {{ color:var(--accent); }}
.bar .br {{ font-size:30px; opacity:.85; letter-spacing:1px; }}

.cap {{ position:absolute; bottom:182px; left:80px; right:80px; display:flex; justify-content:center;  /* 基准=card05 落点 */
     z-index:5; pointer-events:none; }}
.capf {{ margin-top:40px; display:flex; justify-content:center; }}
.cap > div, .capf > div {{ background:var(--cardbg); border:3px solid var(--ink); border-radius:999px; padding:24px 54px;
     font-size:44px; font-weight:700; box-shadow:8px 8px 0 var(--shadow); max-width:900px; text-align:center; }}

/* dy77 借鉴(10-09): 标题色块 / 圆角描边框 / 章节码 / 多栏卡 */
.blk {{ background:var(--accent); color:var(--onaccent); padding:4px 24px; border-radius:14px; display:inline-block; }}
.panel {{ margin-top:70px; border:3px solid var(--ink); border-radius:26px; padding:10px 34px; background:var(--cardbg);
      box-shadow:10px 10px 0 var(--shadow); transform:rotate(-.5deg); }}
.panel ol {{ margin-top:0; }}
.cols {{ display:flex; gap:26px; margin-top:70px; }}
.cols > div {{ flex:1; border:3px solid var(--ink); border-radius:22px; background:var(--cardbg);
      box-shadow:8px 8px 0 var(--shadow); padding:34px 30px; }}
.cols .ch {{ font-size:38px; font-weight:800; color:var(--accent); letter-spacing:2px; }}
.cols .cs {{ font-size:26px; color:var(--ink2); margin-top:10px; }}
.cols ul {{ margin-top:26px; list-style:none; counter-reset:ci; }}
.cols li {{ counter-increment:ci; font-size:30px; padding:16px 0 16px 52px; border-bottom:2px solid var(--line); }}
.cols li:last-child {{ border-bottom:0; }}
.cols li::before {{ content:counter(ci,decimal-leading-zero); font-size:26px; top:16px; }}  # 列内序号缩小让位, 防窄列叠字
.cols .cf {{ margin-top:22px; padding-top:18px; border-top:2px solid var(--line); font-size:28px; color:var(--ink2); }}

.img {{ margin-top:70px; display:flex; justify-content:center; }}
.img img {{ max-height:560px; max-width:840px; object-fit:contain; }}
.img-cap {{ margin-top:28px; font-size:32px; color:var(--ink2); text-align:center; letter-spacing:2px; }}
.ghost {{ position:absolute; right:60px; bottom:230px; font-family:'Songti SC',serif; font-size:420px; font-weight:700;
        color:var(--ghostc); line-height:1; pointer-events:none; }}
.cta {{ margin-top:110px; }}
.follow {{ display:inline-block; background:var(--accent); color:var(--onaccent); border-radius:14px; padding:38px 72px;
         font-size:62px; font-weight:700; letter-spacing:6px; box-shadow:10px 10px 0 var(--shadow); }}
.next {{ margin-top:56px; font-size:44px; color:var(--ink2); line-height:1.6; }}
.next strong {{ color:var(--accent); font-weight:600; }}
.foot {{ position:absolute; bottom:64px; left:80px; right:80px; display:flex; justify-content:space-between; gap:20px;
       font-size:30px; color:var(--ink2); border-top:2px solid var(--line); padding-top:32px; letter-spacing:2px; white-space:nowrap; }}
.fl {{ display:flex; flex-direction:column; gap:20px; align-items:flex-start; }}
.prog {{ display:flex; gap:12px; }}
.prog span {{ width:56px; height:8px; background:var(--line); }}
.prog span.on {{ background:var(--accent); }}
.wrap.cv {{ top:640px; }}  # 稀卡内容块整体下移, 纵向居中, 避免上挤下空

/* dark-demo sketch 主题(11-02): 白虚线描边框 + 黄色大标题(CONTENTS 风) + 贴纸, 仅 sketch 主题拼进 style */
.sketch .panel, .sketch .cols > div, .sketch .gh, .sketch .chip, .sketch .codebox, .sketch table,
.sketch .cap > div, .sketch .capf > div, .sketch .bar, .sketch .follow {{ border-style:dashed; }}
.sketch h1.hey {{ color:var(--accent); letter-spacing:4px; }}
.sketch h1.hey strong {{ color:var(--accent); }}
.sketch .stkr {{ position:absolute; font-size:88px; z-index:4; opacity:.95; filter:drop-shadow(4px 4px 0 rgba(0,0,0,.5)); }}
.sketch .stkr.a {{ top:300px; right:110px; transform:rotate(10deg); }}
.sketch .stkr.b {{ bottom:330px; left:110px; transform:rotate(-12deg); }}
"""

# sketch 主题(11-02 黑底手绘 demo): 专属 CSS 已在主 CSS 模板内(.sketch 前缀作用域, 其它主题不受影响)
def build_style(meta, accent=None):
    p = dict(PALETTES.get(meta.get("theme", "paper"), PALETTES["paper"]))
    if accent:
        p["accent"] = accent  # 章节配色: 单卡覆色(card.accent)
    if meta.get("h1font"):
        p["h1font"] = meta["h1font"]  # 标题字体覆写(视频式黑体: meta.h1font)
    p["bgimg"] = "url('bg-image.jpg') center/cover no-repeat, " if meta.get("bg_image") else ""  # 实拍纸底(meta.bg_image, 已拷进 cards_html/)
    return CSS.format(**p)


def strongify(s: str) -> str:
    s = re.sub(r"\[\[(.+?)\]\]", r'<span class="blk">\1</span>', s)  # [[色块]] 先处理
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

def _sparse(c):
    return not (c.get("items") or c.get("cols") or c.get("flow") or c.get("table") or c.get("code")
                or c.get("image") or c.get("gh") or c.get("bar") or c.get("cta"))  # 只有标题/副题的稀卡

def render_card(card, i, n, meta):
    ktext = card.get("section", meta["kicker"])  # 章节码: 单卡可覆写左上■旁文案
    sparse = _sparse(card)
    parts = [f'<div class="head"><div class="kicker">{ktext} VOL.{meta["episode"]}</div>'
             f'<div class="idx">{i:02d} / {n:02d}</div></div>',
             f'<div class="ghost serif">{i:02d}</div>',
             f'<div class="wrap{" cv" if sparse else ""}"><h1{" hey" if card.get("hey") else ""}>{strongify(card["title"])}</h1>']
    if card.get("stkr"):  # sketch 贴纸(emoji, 卡角装饰)
        parts.append(f'<div class="stkr {"b" if i % 2 else "a"}">{card["stkr"]}</div>')
    if card.get("sub"):
        parts.append(f'<div class="sub">{strongify(card["sub"])}</div>')
    if card.get("items") and not card.get("cta"):
        parts.append('<div class="panel"><ol>' + ''.join(f'<li>{strongify(x)}</li>' for x in card["items"]) + '</ol></div>')
    if card.get("cols"):
        cs = []
        for c in card["cols"]:
            cs.append('<div><div class="ch">' + strongify(c.get("head", "")) + '</div>'
                      + (f'<div class="cs">{strongify(c["sub"])}</div>' if c.get("sub") else "")
                      + '<ul>' + ''.join(f'<li>{strongify(x)}</li>' for x in c.get("items", [])) + '</ul>'
                      + (f'<div class="cf">{strongify(c["foot"])}</div>' if c.get("foot") else "") + '</div>')
        parts.append(f'<div class="cols">{"".join(cs)}</div>')
    if card.get("flow"):
        chips = ' '.join([f'<div class="chip">{s}</div><span class="arrow">→</span>' for s in card["flow"][:-1]]
                         + [f'<div class="chip">{card["flow"][-1]}</div>'])
        parts.append(f'<div class="flow">{chips}</div>')
    if card.get("table"):
        t = card["table"]
        head = ''.join(f'<th>{c}</th>' for c in t["headers"])
        rows = ''.join('<tr>' + ''.join(f'<td>{strongify(c)}</td>' for c in r) + '</tr>' for r in t["rows"])
        parts.append(f'<table><tr>{head}</tr>{rows}</table>')
    if card.get("code"):
        import html as _h
        head = f'<div class="codehead"><span>{_h.escape(card.get("code_header","$ console"))}</span><span>● ● ●</span></div>'
        parts.append(f'<div class="codebox">{head}<pre class="code">{_h.escape(card["code"])}</pre></div>')
    if card.get("image"):
        img = f'<div class="img"><img src="__IMG__" alt="illustration"></div>'
        if card.get("image_caption"):
            img += f'<div class="img-cap">{strongify(card["image_caption"])}</div>'
        parts.insert(4 if card.get("sub") else 3, img)
    if card.get("gh"):
        parts.append(f'<div class="gh">GitHub 搜:{strongify(card["gh"])}</div>')
    if card.get("bar"):
        b = card["bar"]
        right = f'<div class="br">{strongify(b["right"])}</div>' if b.get("right") else ""
        parts.append(f'<div class="bar"><div class="bl">{strongify(b.get("left", ""))}</div>{right}</div>')
    if card.get("caption"):
        parts.append('<div class="cap"><div>' + strongify(card["caption"]) + '</div></div>')  # 胶囊统一绝对定位(按 card05 落点 bottom:182px)
    if card.get("cta"):
        parts.append(f'<div class="cta"><div class="follow">{card.get("cta_text","关注我")}</div>' +
                     ''.join(f'<div class="next">{strongify(x)}</div>' for x in card["items"]) + '</div>')
    seg = ''.join('<span class="on"></span>' if k <= i else '<span></span>' for k in range(1, n + 1))
    foot_r = meta.get("foot_right", "每天拆一个 AI 概念")
    parts.append(f'</div><div class="foot"><div class="fl"><div class="prog">{seg}</div>'
                 f'<span>{meta["kicker"]} VOL.{meta["episode"]}</span></div><span>{foot_r}</span></div>')
    body = '\n'.join(parts)
    style = build_style(meta, card.get("accent"))  # 章节配色: card.accent 覆单卡强调色
    bcls = ' class="sketch"' if meta.get("theme") == "sketch" else ""  # sketch 专属 CSS 作用域开关
    return (f'<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><style>{style}</style></head>'
            f'<body{bcls}>{body}</body></html>')

def _resolve_flow(meta, base_dir):
    """按 cards.json 的 flow 指针(相对项目根)向上逐层找配方文件;找不到返回 None"""
    rel = meta.get("flow")
    if not rel or not rel.startswith("flows/"):
        return None
    d = os.path.abspath(base_dir)
    while True:
        cand = os.path.join(d, rel)
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent

def main(path):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out_dir_abs = os.path.abspath(os.path.dirname(path))
    out_html, out_png = os.path.join(out_dir_abs, "cards_html"), os.path.join(out_dir_abs, "cards_png")
    os.makedirs(out_html, exist_ok=True); os.makedirs(out_png, exist_ok=True)  # 先建目录, 再拷 bg(新目录首跑不挂)
    meta = json.load(open(path, encoding="utf-8"))
    if meta.get("bg_image"):  # 实拍纸底图: 拷进 cards_html/ 供 CSS 引用
        shutil.copy(os.path.join(out_dir_abs, meta["bg_image"]), os.path.join(out_html, "bg-image.jpg"))
    # 主题优先级: cards.json 显式 theme > flow 配方里的 theme > 兜底 paper
    if not meta.get("theme"):
        fp = _resolve_flow(meta, out_dir_abs)
        meta["theme"] = (json.load(open(fp, encoding="utf-8")).get("theme") or "paper") if fp else "paper"
    n = len(meta["cards"])
    for i, card in enumerate(meta["cards"], 1):
        html = os.path.join(out_html, f"card{i:02d}.html")
        page = render_card(card, i, n, meta)
        if card.get("image"):
            page = page.replace("__IMG__", os.path.relpath(os.path.join(out_dir_abs, card["image"]), out_html))
        open(html, "w", encoding="utf-8").write(page)
        out = os.path.join(out_png, f"card{i:02d}.png")
        cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
               "--window-size=1080,1920", f"--screenshot={out}", html]
        for attempt in (1, 2):
            subprocess.run(cmd, check=True, capture_output=True, timeout=150)
            if os.path.exists(out):
                break
            if attempt == 2:
                raise SystemExit(f"card{i:02d} 截图失败,重试仍无 png")
        print(f"card{i:02d}.png ✓ ({card.get('duration', '?')}s)")
    print(f"合计 {sum(c.get('duration', 0) for c in meta['cards'])}s")

if __name__ == "__main__":
    main(sys.argv[1])
