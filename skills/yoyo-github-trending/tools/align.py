#!/usr/bin/env python3
"""音画对齐:按每张卡的 say(对应口播段)+ boundaries.json 逐字时间戳,
把每张卡的真实起念时刻写回 cards.json 的 duration;随后重渲染重合成。
规则:有 say 的卡=该 say 首字开始被念的时刻;无 say 的卡=前后已知卡之间均分;
末卡长度补到音频末尾(+0.5s 尾垫)。
用法:python3 tools/align.py doc/video01/cards.json
依赖:同目录 tts.mp3/boundaries.json(tools/tts.py 产出)
"""
import json, os, subprocess, sys

def main(path):
    base = os.path.abspath(os.path.dirname(path))
    meta = json.load(open(path, encoding="utf-8"))
    bnd = json.load(open(os.path.join(base, "boundaries.json"), encoding="utf-8"))
    cards = meta["cards"]
    full = "".join(c.get("say", "") for c in cards)

    # 逐字时间映射:character index → 起念时刻(s)
    char_t = [0.0] * max(len(full), 1)
    pos = 0
    for w in bnd:
        idx = full.find(w["text"], pos)
        if idx < 0:
            idx = pos
        t = w["offset_ms"] / 1000.0
        for k in range(idx, min(idx + len(w["text"]), len(full))):
            char_t[k] = t
        pos = idx + len(w["text"])

    audio_end = max((w["offset_ms"] + w["duration_ms"]) / 1000.0 for w in bnd) + 0.5

    # 每卡起念时刻
    starts = [None] * len(cards)
    p = 0
    for i, c in enumerate(cards):
        s = c.get("say", "")
        if s:
            idx = full.find(s, p)
            if idx < 0:
                raise SystemExit(f"卡{i+1} 的 say 在全文中定位失败: {s[:20]}...")
            starts[i] = char_t[idx]
            p = idx + len(s)
    # 无 say 的卡:前后已知卡之间均分
    for i, c in enumerate(cards):
        if starts[i] is None:
            prev = max((j for j in range(i) if starts[j] is not None), default=-1)
            nxt = min((j for j in range(i + 1, len(cards)) if starts[j] is not None), default=-1)
            a = starts[prev] if prev >= 0 else 0.0
            b = starts[nxt] if nxt >= 0 else audio_end
            n_unknown = sum(1 for j in range(prev + 1, nxt if nxt >= 0 else i + 1) if starts[j] is None)
            k = sum(1 for j in range(prev + 1, i + 1) if starts[j] is None)
            starts[i] = a + (b - a) * (k - 1 + 0.5) / n_unknown

    for i, c in enumerate(cards):
        end = starts[i + 1] if i + 1 < len(cards) and starts[i + 1] is not None else audio_end
        c["duration"] = round(max(end - starts[i], 1.0), 1)
    json.dump(meta, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("对齐后时长:", [f"{c['duration']}s" for c in cards], f"(音频 {audio_end:.1f}s)")
    if "--align-only" in sys.argv:
        print("--align-only: 跳过 classic 渲染/合成")
        return
    for cmd in (["cards.py"], ["assemble.py"]):
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", *cmd), path], check=True)

if __name__ == "__main__":
    main(sys.argv[1])
