#!/usr/bin/env python3
"""TTS 生成 + 逐字时间戳(boundaries.json),供音画对齐。
用法:python3 tools/tts.py doc/video01/tts.txt
产物:<同目录>/tts.mp3 + boundaries.json([{"text","offset_ms","duration_ms"}, ...])
"""
import asyncio, json, os, sys
import edge_tts

DEFAULT_VOICE, DEFAULT_RATE = "zh-CN-YunxiNeural", "+10%"
# flow.json 可覆盖 tts.voice / tts.rate(flows/ 目录)

async def synth(tts_txt, flow=None):
    base = os.path.abspath(os.path.dirname(tts_txt))
    voice, rate = DEFAULT_VOICE, DEFAULT_RATE
    if flow:
        f = json.load(open(flow, encoding="utf-8"))
        voice = f.get("tts", {}).get("voice", voice)
        rate = f.get("tts", {}).get("rate", rate)
    mp3, bnd = os.path.join(base, "tts.mp3"), os.path.join(base, "boundaries.json")
    text = open(tts_txt, encoding="utf-8").read()
    com = edge_tts.Communicate(text, voice=voice, rate=rate, proxy=os.environ.get("TTS_PROXY") or None)  # TTS_PROXY 可切代理出口(直连 403 时)
    words = []
    with open(mp3, "wb") as f:
        async for chunk in com.stream():
            if chunk.get("type") == "audio":
                f.write(chunk["data"])
            else:
                b = chunk if isinstance(chunk, dict) and chunk.get("type") in ("SentenceBoundary", "WordBoundary") else None
                if b and b.get("text"):
                    words.append({"text": b["text"], "offset_ms": b["offset"] / 1e4, "duration_ms": b["duration"] / 1e4})
    json.dump(words, open(bnd, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"tts.mp3 + boundaries.json({len(words)} words) ✓")

if __name__ == "__main__":
    args = sys.argv[1:]
    flow = args[1] if len(args) > 1 else None
    for p in args[:1]:
        asyncio.run(synth(p, flow))
