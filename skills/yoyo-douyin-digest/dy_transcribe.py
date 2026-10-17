import av, numpy as np, sys
from fractions import Fraction
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
model_size = sys.argv[3] if len(sys.argv) > 3 else "small"

# 1) PyAV 解码 → 16k 单声道 float32(不依赖系统 ffmpeg)
c = av.open(src)
audio_stream = c.streams.audio[0]
fr, sr = [], audio_stream.codec_context.sample_rate
for f in c.decode(audio_stream):
    a = f.to_ndarray()
    if a.ndim == 3:
        a = a[0]
    fr.append(a.astype(np.float32))
mono = np.concatenate(fr, axis=1).mean(axis=0)
frame = av.AudioFrame.from_ndarray(mono.reshape(1, -1), format="flt", layout="mono")
frame.rate = sr
frame.pts = 0
frame.time_base = Fraction(1, sr)
res = av.AudioResampler(format="flt", layout="mono", rate=16000)
chunks = []
for x in res.resample(frame):
    if x is not None:
        a = x.to_ndarray()
        chunks.append(a.mean(axis=0) if a.shape[0] > 1 else a[0])
audio16k = np.concatenate(chunks).astype(np.float32) if chunks else np.zeros(0, dtype=np.float32)
print(f"decoded {len(audio16k)/16000:.1f}s audio (src sr={sr})")

# 2) 转写
model = WhisperModel(model_size, device="cpu", compute_type="int8")
segments, info = model.transcribe(audio16k, language="zh", vad_filter=True)
lines = [f"[{s.start:08.2f} → {s.end:08.2f}] {s.text.strip()}" for s in segments]
open(out, "w").write(f"language={info.language}, duration≈{info.duration:.1f}s\n\n" + "\n".join(lines))
print(f"done: {len(lines)} segments -> {out}")
