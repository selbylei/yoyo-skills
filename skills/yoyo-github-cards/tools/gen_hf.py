#!/usr/bin/env python3
"""HyperFrames 生成器:classic/cards.json(已对齐) → hyperframes/index.html(场景+GSAP+音轨)
用法:python3 tools/gen_hf.py github-trending/<日期>/classic
产物:<同级>/hyperframes/index.html, assets/(gsap 本地化 + tts.mp3 拷入)
渲染:source skill-lab/.env && cd <同级>/hyperframes && npx --yes hyperframes@0.8.91 render
"""
import html as _h
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cards import PALETTES, strongify  # 主题变量/[[色块]]与**强标**解析, 与 classic 管线同源

classic_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # GBK 控制台打 ✓ 不崩
base = os.path.join(os.path.dirname(classic_dir), "hyperframes")
os.makedirs(os.path.join(base, "assets"), exist_ok=True)
meta = json.load(open(os.path.join(classic_dir, "cards.json"), encoding="utf-8"))
cards = meta["cards"]
durs = [c["duration"] for c in cards]
starts = [0.0]
for d in durs[:-1]:
    starts.append(starts[-1] + d)
total = sum(durs) + 0.5

# gsap 本地化(渲染环境 CDN 断连, 必须本地; 从既有期的 assets 里找一份)
gdst = os.path.join(base, "assets", "gsap.min.js")
if not os.path.exists(gdst):
    # 1) 全局 vendor(上溯找 skill-lab/vendor); 2) 回落: 兄弟期 hyperframes/assets
    proj_root = None
    d = classic_dir
    while d not in (os.path.dirname(d), os.path.splitdrive(d)[0] + os.sep) and proj_root is None:
        if os.path.isdir(os.path.join(d, "skill-lab")):
            proj_root = d
        d = os.path.dirname(d)
    candidates = []
    if proj_root:
        candidates.append(os.path.join(proj_root, "skill-lab", "vendor", "gsap.min.js"))
    series_root = os.path.dirname(os.path.dirname(classic_dir))  # .../github-trending 或 .../projects
    if os.path.isdir(series_root):
        for cand in sorted(os.listdir(series_root)):
            p = os.path.join(series_root, cand, "hyperframes", "assets", "gsap.min.js")
            if os.path.exists(p):
                candidates.append(p)
    for src in candidates:
        if os.path.exists(src):
            shutil.copy(src, gdst)
            break
shutil.copy(os.path.join(classic_dir, "tts.mp3"), os.path.join(base, "assets", "tts.mp3"))
# 实拍纸底(meta.bg_image)拷入 HF assets, CSS 引用 assets/bg-image.jpg
if meta.get("bg_image"):
    shutil.copy(os.path.join(classic_dir, meta["bg_image"]), os.path.join(base, "assets", "bg-image.jpg"))
# 卡片引用的 image 素材拷入 HF assets
for c in cards:
    img = c.get("image")
    if img and img.startswith("assets/"):
        src = os.path.join(classic_dir, img)
        dst = os.path.join(base, img)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(src, dst)


def cap_span(text):
    out = _h.escape(text)
    for kw in cap_kw:
        out = out.replace(_h.escape(kw), '<b class="kw">%s</b>' % _h.escape(kw))
    return out

def scene_html(i, c):
    t = starts[i]
    codes_js[i] = c.get("code", "")
    p = []
    accent_style = ' style="--accent:%s"' % c["accent"] if c.get("accent") else ""  # 章节配色单卡覆色
    ktext = c.get("section", meta["kicker"])  # 章节码
    sparse = not (c.get("items") or c.get("cols") or c.get("flow") or c.get("table") or c.get("code")
                  or c.get("image") or c.get("gh") or c.get("bar") or c.get("cta"))  # 只有标题/副题的稀卡
    p.append('<section class="scene clip" id="s%d"%s data-start="%.1f" data-duration="%.1f" data-track-index="0">' % (i + 1, accent_style, t, durs[i]))
    p.append('  <div class="head anim" id="h%d"><span class="kicker">%s VOL.%s · %02d/%d</span></div>' % (i, _h.escape(ktext), meta["episode"], i + 1, len(cards)))
    p.append('  <div class="body%s">' % (' cv' if sparse else ''))
    p.append('    <h1 class="anim%s" id="t%d">%s</h1>' % ((" hey") if c.get("hey") else "", i, strongify(c["title"])))
    if c.get("stkr"):  # sketch 贴纸(emoji, 卡角装饰)
        p.append('    <div class="stkr %s">%s</div>' % ("b" if i % 2 else "a", c["stkr"]))
    if c.get("sub"):
        p.append('    <div class="sub anim" id="sb%d">%s</div>' % (i, strongify(c["sub"])))
    items = c.get("items")
    if items and not c.get("cta"):
        lis = ''.join('<li class="anim">0%d %s</li>' % (k + 1, strongify(x)) for k, x in enumerate(items))
        p.append('    <div class="panel"><ol>%s</ol></div>' % lis)  # 圆角描边框
    if c.get("cols"):  # 多栏卡(视频 07 卡同款)
        cs = []
        for col in c["cols"]:
            cs.append('<div class="col anim"><div class="ch">' + strongify(col.get("head", "")) + '</div>'
                      + ('<div class="cs">%s</div>' % strongify(col["sub"]) if col.get("sub") else "")
                      + '<ul>' + ''.join('<li>%s</li>' % strongify(x) for x in col.get("items", [])) + '</ul>'
                      + ('<div class="cf">%s</div>' % strongify(col["foot"]) if col.get("foot") else "") + '</div>')
        p.append('    <div class="cols">%s</div>' % "".join(cs))
    if c.get("image"):
        p.append("    <div class=\"imgwrap anim\" id=\"imgw%d\"><div class=\"imgbox\" id=\"img%d\" style=\"background-image:url('%s')\"></div>" % (i, i, c["image"]))
        if c.get("image_caption"):
            p.append('<div class="imgcap">%s</div>' % _h.escape(c["image_caption"]))
        p.append('</div>')
    if c.get("table"):
        tb = c["table"]
        head_cells = "".join("<th>%s</th>" % x for x in tb["headers"])
        row_html = []
        for r in tb["rows"]:
            tds = "".join("<td>%s</td>" % _h.escape(x).replace('**', '') for x in r)
            row_html.append('<tr class="anim">%s</tr>' % tds)
        p.append('    <table><tr>%s</tr>%s</table>' % (head_cells, "".join(row_html)))
    if c.get("code"):  # 终端打字: 文本留 CODES, pre 内空 span + 光标, GSAP 逐字写入
        p.append('    <div class="codebox anim"><div class="codehead">%s <span>● ● ●</span></div>'
                 '<pre><span id="codeT%d"></span><span class="tcur">▍</span></pre></div>' % (_h.escape(c.get("code_header", "$ console")), i))
    if c.get("flow"):
        chips = ""
        for k, x in enumerate(c["flow"]):
            chips += '<div class="chip anim">%s</div>' % _h.escape(x)
            if k < len(c["flow"]) - 1:
                chips += '<span class="arrow">→</span>'
        p.append('    <div class="flowrow">%s</div>' % chips)
    if c.get("gh"):
        p.append('    <div class="gh anim">GitHub 搜:<strong>%s</strong></div>' % c["gh"])
    if c.get("bar"):  # 结论横条
        b = c["bar"]
        right = '<div class="br">%s</div>' % strongify(b["right"]) if b.get("right") else ""
        p.append('    <div class="bar anim"><div class="bl">%s</div>%s</div>' % (strongify(b.get("left", "")), right))
    if c.get("caption"):  # 口播胶囊: 统一绝对定位(按 card05 落点)
        p.append('    <div class="cap anim" id="ccap%d"><div>%s</div></div>' % (i, strongify(c["caption"])))
    if c.get("cta"):
        p.append('    <div class="cta anim">%s</div>' % c.get("cta_text", "关注我"))
        for x in (items or []):
            p.append('    <div class="next anim">%s</div>' % strongify(x))  # CTA 条目也走 strongify, ** 不再原样打印
    p.append('  </div>')
    p.append('</section>')
    return "\n".join(p)


codes_js = {}  # scene_html 逐卡登记 code 全文, 供终端打字数据源
scenes = "\n".join(scene_html(i, c) for i, c in enumerate(cards))

# ---- 字幕轨: tts.txt 按标点切行, 时间取 boundaries.json(粗边界时块内均匀插值) ----
cap_items = []
cap_kw = [k for k in meta.get("keywords", []) if k]
cap_kw.sort(key=len, reverse=True)
bnd_path = os.path.join(classic_dir, "boundaries.json")
if os.path.exists(bnd_path):
    bnd = json.load(open(bnd_path, encoding="utf-8"))
    full_text = open(os.path.join(classic_dir, "tts.txt"), encoding="utf-8").read().strip()
    nn = len(full_text)
    char_t = []
    last_end = 0.0
    pos = 0
    for w in bnd:
        txt = w["text"]; st = w["offset_ms"] / 1000.0
        en = st + max(w.get("duration_ms", 0) / 1000.0, 0.05)
        last_end = max(last_end, en)
        i0 = full_text.find(txt, pos)
        i0 = i0 if i0 >= 0 else pos
        L = max(len(txt), 1)
        for k in range(L):
            char_t.append(st + (en - st) * (k + 0.5) / L)
        pos = i0 + L
    while len(char_t) < nn:
        char_t.append(last_end)
    # 切行新规则(09-30 用户定):①标点一律换空格 ②英文/数字词不劈 ③中文词组不劈
    PUNCT = set("，。：、；！？…,.:;!?\"'()（）《》<>~—·")
    # 词组保护: 把这些词的内部 2-gram 列入黑名单, 断点劈中 → 上移
    PROT_WORDS = ["客户端","服务端","管理后台","机器人","游戏场","竞技场","梯度奖励","周结算",
                  "三对三","预聚合","免伤","流水","结算","匹配","积分","赛季","防守","双向",
                  "同步","白嫖","扣减","中断","怪物","箭塔","技能","稀有度","模拟","伤害",
                  "公式","防御","攻击","数值","架构","件套","微信","塔防","数据库","配置",
                  "规则","验证","程序","引擎","节点","渲染","卡片","字幕","标题","时间",
                  "代码","发版","fibers","加上","它叫","项目"]
    BAD2 = set(w[k:k + 2] for w in PROT_WORDS for k in range(len(w) - 1))
    # 词化: 英文/数字连续段(不含标点)=1 原子词; 其余每字符=1 词
    words = []  # (text, i0, i1) 原文字符区间
    i = 0
    while i < nn:
        ch = full_text[i]
        if ch in PUNCT:
            i += 1
        elif ch.isascii() and not ch.isspace() and ch not in PUNCT:
            j = i
            # 原子词:字母/数字 + 内嵌 . _ - / ~ (Node.js 不劈), 遇标点或中文停
            while j < nn and full_text[j].isascii() and not full_text[j].isspace() \
                    and (full_text[j] in "._-/~" or full_text[j] not in PUNCT):
                j += 1
            words.append((full_text[i:j], i, j)); i = j
        else:
            words.append((ch, i, i + 1)); i += 1
    # 贪心打包 ≤14 字(容差: 词组保护可到 15); 前一是标点 → 词前带空格, 行首不留空格
    lines_t = []  # (disp, i0, i1)
    line, l0, l1 = "", None, None
    for w, i0, i1 in words:
        ws = (" " + w) if i0 > 0 and full_text[i0 - 1] in PUNCT else w
        if not line:
            line, l0, l1 = ws, i0, i1
            continue
        if len(line) + len(ws) > 14:
            lines_t.append((line, l0, l1))
            line, l0, l1 = ws.lstrip(" "), i0, i1
        else:
            line += ws
            l1 = i1
    if line.strip(): lines_t.append((line, l0, l1))
    # 词组保护: 断点两侧 2-gram 命中黑名单 → 把下一行首字上移, 最多 2 字
    for k in range(len(lines_t) - 1):
        for _ in range(2):
            A, B = lines_t[k][0], lines_t[k + 1][0]
            if len(A) >= 1 and len(B) >= 2 and A[-1] + B[0] in BAD2:
                lines_t[k] = (A + B[0], lines_t[k][1], lines_t[k][2])
                lines_t[k + 1] = (B[1:].lstrip(" "), lines_t[k + 1][1], lines_t[k + 1][2])
            else:
                break
    for disp, i0, i1 in lines_t:
        if not disp.strip():
            continue
        st = char_t[i0]
        en = char_t[i1 - 1] + 0.3
        cap_items.append((disp, st, max(en - st, 0.6)))

tl = ["const tl = gsap.timeline({ paused: true });\n"
      "const CODES = %s;\n"  # 终端打字数据源(逐字写入 pre)
      "function TYPE(i, t0) { const el = document.getElementById('codeT' + i); if (!el || !CODES[i]) return;"
      " const st = { n: 0 }; const full = CODES[i];"
      " tl.to(st, { n: full.length, duration: Math.max(full.length * 0.05, 1.2), ease: 'none',"
      "   onUpdate: function () { el.textContent = full.slice(0, Math.round(st.n)); } }, t0); }"
      % json.dumps(codes_js, ensure_ascii=False)]
for i in range(len(cards)):
    t0 = starts[i]
    t1 = t0 + durs[i]
    tl.append('tl.fromTo("#s%d", {opacity:0}, {opacity:1, duration:0.35, ease:"power1.out"}, %.2f);' % (i + 1, t0))
    tl.append('tl.fromTo("#h%d", {opacity:0, y:-20}, {opacity:1, y:0, duration:0.4}, %.2f);' % (i, t0 + 0.05))
    tl.append('tl.fromTo("#t%d", {opacity:0, y:36}, {opacity:1, y:0, duration:0.5, ease:"power2.out"}, %.2f);' % (i, t0 + 0.15))
    tl.append('tl.fromTo("#sb%d", {opacity:0}, {opacity:1, duration:0.4}, %.2f);' % (i, t0 + 0.35))
    tl.append('tl.from("#s%d ol li", {opacity:0, x:-30, stagger:0.28, duration:0.45, ease:"power2.out"}, %.2f);' % (i + 1, t0 + 0.45))
    tl.append('tl.from("#s%d table tr.anim, #s%d .codebox, #s%d .flowrow .chip, #s%d .cta, #s%d .next, #s%d .gh, #s%d .cols .col, #s%d .bar, #s%d [id^=ccap]", '
              '{opacity:0, y:24, stagger:0.25, duration:0.5, ease:"power2.out"}, %.2f);' % (i + 1, i + 1, i + 1, i + 1, i + 1, i + 1, i + 1, i + 1, i + 1, t0 + 0.55))
    if cards[i].get("code"):  # 终端打字: 入场后 0.4s 起逐字写入
        tl.append('TYPE(%d, %.2f);' % (i, t0 + 1.0))
    if c.get("image"):
        tl.append('tl.fromTo("#img%d", {scale: 1.0}, {scale: 1.08, duration: %.1f, ease:"none"}, %.2f);' % (i, durs[i], t0))
    tl.append('tl.to("#s%d", {opacity:0, duration:0.25, ease:"power1.in"}, %.2f);' % (i + 1, t1 - 0.25))
for k, (sg, st, du) in enumerate(cap_items):
    tl.append('tl.fromTo("#cap%d", {opacity: 0}, {opacity: 1, duration: 0.18}, %.2f);' % (k, st))
tl.append('tl.fromTo("#bar", {scaleX: 0}, {scaleX: 1, duration: %s, ease: "none"}, 0);' % total)
tl.append('window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl; tl.seek(0);')

p = dict(PALETTES.get(meta.get("theme") or "tech", PALETTES["tech"]))  # 与 classic 同源主题; 未指定 theme 默认 tech(兼容旧期)
if meta.get("h1font"):
    p["h1font"] = meta["h1font"]
CSS = """
:root { --ink:__INK__; --ink2:__INK2__; --accent:__ACCENT__; --line:__LINE__; --cardbg:__CARDBG__; --thbg:__THBG__; --thfg:__THFG__; --onaccent:__ONACCENT__; --shadow:__SHADOW__; }
* { margin:0; padding:0; box-sizing:border-box; }
@font-face { font-family:'PingFang SC'; src: local('PingFang SC'); }
@font-face { font-family:'Noto Sans SC'; src: local('Noto Sans SC'); }
@font-face { font-family:'Songti SC'; src: local('Songti SC'); }
html,body { width:1080px; height:1920px; overflow:hidden; background:__BGIMG____BG__;
  color:var(--ink); font-family:-apple-system,"PingFang SC","Noto Sans SC",sans-serif; }
.scene { position:absolute; inset:0; opacity:0; }
.head { position:absolute; top:70px; left:80px; right:80px; display:flex; justify-content:space-between;
  border-bottom:4px solid var(--ink); padding-bottom:30px; }
.kicker { display:flex; align-items:center; gap:22px; font-size:34px; font-weight:600; letter-spacing:4px; color:var(--ink2); }
.kicker::before { content:''; width:26px; height:26px; background:var(--accent); }
.body { position:absolute; top:300px; bottom:0; left:80px; right:80px; }  /* bottom:0 撑到页面底, .cap 绝对定位才锚定页面底 */
.body.cv { top:640px; }  /* 稀卡内容块整体下移, 纵向居中 */
h1 { font-size:92px; line-height:1.3; font-weight:700; letter-spacing:2px; color:var(--ink); font-family:__H1FONT__; }
h1 strong { color:var(--accent); }
.blk { background:var(--accent); color:var(--onaccent); padding:4px 26px; border-radius:14px; display:inline-block; }
.sub { margin-top:40px; font-size:42px; color:var(--ink2); line-height:1.5; }
.panel { margin-top:70px; border:3px solid var(--ink); border-radius:26px; padding:10px 34px; background:var(--cardbg);
  box-shadow:10px 10px 0 var(--shadow); transform:rotate(-.5deg); }
ol { margin-top:0; list-style:none; counter-reset:it; }
li { counter-increment:it; font-size:44px; line-height:1.5; padding:22px 0 22px 84px; position:relative;
  border-bottom:2px solid var(--line); }
li strong { color:var(--accent); font-weight:600; }
li::before { content:counter(it,decimal-leading-zero); position:absolute; left:0; top:24px;
  font-family:'Songti SC',serif; font-size:38px; color:var(--accent); font-weight:700; }
.cols { display:flex; gap:26px; margin-top:70px; }
.cols .col { flex:1; border:3px solid var(--ink); border-radius:22px; background:var(--cardbg);
  box-shadow:8px 8px 0 var(--shadow); padding:34px 30px; }
.cols .ch { font-size:38px; font-weight:800; color:var(--accent); letter-spacing:2px; }
.cols .cs { font-size:26px; color:var(--ink2); margin-top:10px; }
.cols ul { margin-top:26px; list-style:none; counter-reset:ci; }
.cols li { counter-increment:ci; font-size:30px; padding:16px 0 16px 52px; border-bottom:2px solid var(--line); }
.cols li:last-child { border-bottom:0; }
.cols li::before { content:counter(ci,decimal-leading-zero); font-size:26px; top:16px; }
.cols .cf { margin-top:22px; padding-top:18px; border-top:2px solid var(--line); font-size:28px; color:var(--ink2); }
.bar { margin-top:60px; background:var(--ink); color:var(--cardbg); border-radius:14px; padding:32px 40px;
  display:flex; justify-content:space-between; align-items:center; gap:30px; box-shadow:10px 10px 0 var(--shadow); }
.bar .bl { font-size:42px; font-weight:700; letter-spacing:1px; }
.bar .bl strong { color:var(--accent); }
.bar .br { font-size:30px; opacity:.85; letter-spacing:1px; }
.cap { position:absolute; bottom:182px; left:80px; right:80px; display:flex; justify-content:center; z-index:5; }  /* 基准=card05 落点 */
.capf { margin-top:40px; display:flex; justify-content:center; }
.cap > div, .capf > div { background:var(--cardbg); border:3px solid var(--ink); border-radius:999px; padding:24px 54px;
  font-size:44px; font-weight:700; box-shadow:10px 10px 0 var(--shadow); max-width:900px; text-align:center; }
table { margin-top:80px; border-collapse:collapse; width:100%; background:var(--cardbg); box-shadow:8px 8px 0 var(--shadow); }
th,td { font-size:40px; padding:26px 24px; text-align:left; border:2px solid var(--line); }
th { background:var(--thbg); color:var(--thfg); font-size:42px; }
td:first-child { color:var(--ink2); width:200px; }
.codebox { margin-top:70px; border:2px solid var(--line); border-radius:12px; overflow:hidden;
  background:__CODEBG__; box-shadow:8px 8px 0 var(--shadow); }
.codehead { display:flex; justify-content:space-between; padding:22px 32px; background:__CODEHD__;
  font-family:'SF Mono',Menlo,monospace; font-size:30px; color:var(--ink2); border-bottom:2px solid var(--line); }
pre { padding:32px 36px; font-family:'SF Mono',Menlo,monospace; font-size:34px; line-height:1.6; color:__CODETX__; white-space:pre-wrap; }
.tcur { color:var(--accent); font-weight:700; }
.flowrow { display:flex; align-items:center; justify-content:flex-start; gap:16px; margin-top:120px; flex-wrap:wrap; }
.chip { border:3px solid var(--ink); border-radius:10px; padding:28px 34px; font-size:46px; font-weight:600;
  background:var(--cardbg); box-shadow:6px 6px 0 var(--shadow); }
.arrow { color:var(--accent); font-size:50px; font-weight:800; }
.cta { display:inline-block; background:var(--accent); color:var(--onaccent); border-radius:14px; padding:36px 70px;
  font-size:60px; font-weight:800; letter-spacing:6px; box-shadow:10px 10px 0 var(--shadow); margin-top:60px; }
.next { font-size:44px; color:var(--ink2); line-height:1.6; margin-top:28px; }
.next strong { color:var(--accent); font-weight:600; }
.gh { margin-top:56px; font-size:38px; color:var(--ink2); letter-spacing:1px; border:2px solid var(--line);
  border-radius:12px; padding:24px 30px; display:inline-block; background:__CODEBG__; }
.gh strong { color:var(--accent); font-size:44px; font-weight:700; }
#caps { position:absolute; left:0; right:0; bottom:40px; text-align:center; z-index:10; }  /* 字幕带(纯文字): 胶囊 bottom:182(底≈1738), 字幕高≈60 → top≈1820, 间距 82px */
.cap-line { position:absolute; left:0; right:0; text-align:center; bottom:0; }
.cap-line span { display:inline-block; background:none; border:0; color:var(--ink);
  font-size:38px; font-weight:700; letter-spacing:2px; padding:4px 10px; /* 降级: 去白胶囊, 纯文字字幕(纸底白晕投影保可读) */
  text-shadow:0 2px 0 rgba(250,246,238,.95), 0 0 14px rgba(250,246,238,.9); }
.cap-line .kw { color:var(--accent); font-weight:800; }
.imgwrap { margin-top:60px; width:880px; height:574px; overflow:hidden; display:flex; flex-direction:column; align-items:center; }
.imgbox { width:880px; height:572px; background:center/contain no-repeat; border-radius:12px; border:2px solid var(--line); transform-origin:center center; margin-bottom:24px; }
.imgcap { font-size:34px; color:var(--ink2); letter-spacing:1px; }
#bar-bg { position:absolute; bottom:0; left:0; right:0; height:10px; background:var(--line); z-index:5; }
#bar { position:absolute; bottom:0; left:0; right:0; height:10px; background:var(--accent); transform-origin:left center; z-index:6; }
"""
CSS = CSS.replace("__BGIMG__", "url('assets/bg-image.jpg') center/cover no-repeat, " if meta.get("bg_image") else "")  # 先替, 防 __BG__ 撞 __BGIMG____BG__ 序列
for _k in sorted(p, key=len, reverse=True):  # 长 key 先替, 防 CODEBG 里藏 BG; token 双下划线与模板 __KEY__ 对齐(旧版单下划线会残留 _ 导致 CSS 失效)
    CSS = CSS.replace("__" + _k.upper() + "__", p[_k])
if meta.get("theme") == "sketch":  # 黑底手绘 demo(11-02): 虚线描边框 + 黄大标题 + 贴纸
    CSS += """
.sketch-override .panel, .sketch-override .gh, .sketch-override .chip, .sketch-override .codebox,
.sketch-override .bar, .sketch-override .cap > div, .sketch-override .cta, .sketch-override table, .sketch-override .cols .col { border-style:dashed; }
.sketch-override h1.hey { color:var(--accent); letter-spacing:4px; }
.sketch-override h1.hey strong { color:var(--accent); }
.stkr { position:absolute; font-size:88px; z-index:4; opacity:.95; filter:drop-shadow(4px 4px 0 rgba(0,0,0,.5)); }
.stkr.a { top:300px; right:110px; transform:rotate(10deg); }
.stkr.b { bottom:330px; left:110px; transform:rotate(-12deg); }
"""

html_out = """<!doctype html>
<html lang="zh">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>%s</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="%.1f" data-width="1080" data-height="1920">
%s
<div id="bar-bg"></div>
<div id="bar"></div>
<div id="caps">%s</div>
<audio id="vo" src="assets/tts.mp3" data-start="0" data-duration="%.1f"></audio>
</div>
<script>
%s
</script>
</body>
</html>
""" % (CSS, total, scenes,
      "\n".join('<div class="cap-line clip" id="cap%d" data-start="%.2f" data-duration="%.2f" data-track-index="2"><span>%s</span></div>' % (k, st, du, cap_span(t)) for k, (t, st, du) in enumerate(cap_items)),
      total, "\n".join(tl))

open(os.path.join(base, "index.html"), "w", encoding="utf-8").write(html_out)
print("index.html ✓ 场景 %d, 总长 %.1fs, starts=%s" % (len(cards), total, [f"{s:.1f}" for s in starts]))
