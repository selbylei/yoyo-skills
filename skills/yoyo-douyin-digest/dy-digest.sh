#!/usr/bin/env bash
# dy-digest: 抖音视频 URL → 逐字稿笔记,视频文件自动清理
# 用法: dy-digest.sh <URL> [输出目录] [whisper模型]
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
URL="${1:?用法: dy-digest.sh <抖音URL> [输出目录] [模型] (small|medium)}"
OUT_DIR="${2:-$HOME/douyin-digests}"
MODEL="${3:-small}"
export PATH="$HOME/.local/bin:$PATH"

command -v yt-dlp >/dev/null 2>&1 || uv tool install yt-dlp

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT   # 抓一个清一个:视频只活在临时目录里

mkdir -p "$OUT_DIR"

echo "→ 下载(本机 Chrome cookies,最小档位)..."
yt-dlp --cookies-from-browser chrome -f 'w' --no-playlist "$URL" -o "$WORK/video.%(ext)s" --quiet
VIDEO=$(ls "$WORK"/* 2>/dev/null | head -1)
[ -n "$VIDEO" ] || { echo "下载失败:未产出文件(反爬/格式变化,跑 -F 看可用格式)"; exit 1; }

TITLE=$(yt-dlp --cookies-from-browser chrome --print '%(title).40s' --no-playlist "$URL" 2>/dev/null || true)
SLUG=$(printf '%s' "$TITLE" | sed 's#[/\\:*?"<>|]#-#g' | tr -s ' ' '-' | cut -c1-40)
VIDID=$(printf '%s' "$URL" | grep -oE 'video/[0-9]+' | cut -d/ -f2)
[ -n "$VIDID" ] || VIDID=$(date +%s)

echo "→ 转写(模型 $MODEL,CPU;断网时自动用 uv 离线缓存)"
if ! uv run --offline --python 3.12 --with faster-whisper --with av "$SCRIPT_DIR/dy_transcribe.py" "$VIDEO" "$WORK/transcript.txt" "$MODEL"; then
  uv run --python 3.12 --with faster-whisper --with av "$SCRIPT_DIR/dy_transcribe.py" "$VIDEO" "$WORK/transcript.txt" "$MODEL"
fi

OUT_FILE="$OUT_DIR/${VIDID}-${SLUG:-untitled}.md"
{
  echo "# 抖音 ${VIDID} ${SLUG:+— $SLUG}"
  echo
  echo "- URL: $URL"
  echo "- 抓取: $(date +%F) · 模型: $MODEL"
  echo
  cat "$WORK/transcript.txt"
} > "$OUT_FILE"

echo "✓ $OUT_FILE"
echo "✓ 视频已清理(临时目录 $WORK 随退出删除)"
