#!/usr/bin/env python3
"""成片合成:cards_png/*.png + tts.mp3 → 视频(1080×1920, 30fps)。
用法:python3 tools/assemble.py doc/video01/cards.json
依赖:imageio-ffmpeg(pip --user,无 brew);产物:<同目录>/video_NN.mp4 + segs/
"""
import json, os, subprocess, sys
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()

def main(path):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # GBK 控制台打 ✓ 不崩
    meta = json.load(open(path, encoding="utf-8"))
    base = os.path.abspath(os.path.dirname(path))
    pngs, segs_dir, out = os.path.join(base, "cards_png"), os.path.join(base, "segs"), os.path.join(base, f"video_{meta['episode']}.mp4")
    os.makedirs(segs_dir, exist_ok=True)
    audio = os.path.join(base, "tts.mp3")
    n = len(meta["cards"])
    for i, card in enumerate(meta["cards"], 1):
        seg = os.path.join(segs_dir, f"seg{i:02d}.mp4")
        subprocess.run([FF, "-y", "-loop", "1", "-framerate", "30", "-t", str(card["duration"]),
                        "-i", os.path.join(pngs, f"card{i:02d}.png"),
                        "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "fast", "-crf", "18", seg],
                       check=True, capture_output=True)
    listf = os.path.join(segs_dir, "list.txt")
    open(listf, "w").write("".join(f"file 'seg{i:02d}.mp4'\n" for i in range(1, n + 1)))
    joined = os.path.join(segs_dir, "joined.mp4")
    subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", listf, "-c", "copy", joined], check=True, capture_output=True)

    # 数字人图层(meta.avatar = {"src","mode":"pip"|"full","audio":"tts"|"avatar"})
    av = meta.get("avatar")
    av_path = os.path.join(base, av["src"]) if av else None
    if av and os.path.exists(av_path):
        if av.get("mode", "pip") == "full":
            cmd = [FF, "-y", "-i", av_path, "-vf", "scale=1080:1920", "-c:v", "libx264", "-preset", "fast", "-crf", "20"]
            if av.get("audio", "tts") == "avatar":
                cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
            else:
                cmd += ["-i", audio, "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
            cmd += [out]
        else:  # pip:卡片铺底,数字人右下角 360 宽
            cmd = [FF, "-y", "-i", joined, "-i", av_path,
                   "-filter_complex",
                   ("[1:v]scale=360:-2,format=yuva420p,fade=t=in:st=0:d=0.3:alpha=1[ov];"
                    "[0:v][ov]overlay=W-w-36:H-h-200[v]"),
                   "-map", "[v]"]
            cmd += (["-map", "1:a"] if av.get("audio", "tts") == "avatar" else ["-i", audio, "-map", "2:a"])
            cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-shortest", out]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"{out} ✓(数字人 {av.get('mode','pip')},音频={av.get('audio','tts')})")
        return
    subprocess.run([FF, "-y", "-i", joined, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out], check=True, capture_output=True)
    print(f"{out} ✓")

if __name__ == "__main__":
    main(sys.argv[1])
