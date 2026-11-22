# hf-env.sh — HyperFrames 本机渲染环境(跨机自适应, 由 yoyo-github-trending skill 携带)
# 用法(git-bash/zsh/bash): source <skill目录>/env/hf-env.sh && cd <期目录>/hyperframes && npx --yes hyperframes@0.8.91 render
# 前置: node ≥18 + Chrome(或 Playwright Chromium/Edge) + pip 装过 imageio-ffmpeg
export HYPERFRAMES_NO_UPDATE_CHECK=1
export HYPERFRAMES_NO_TELEMETRY=1

# 1) 浏览器: 标准 Chrome → Playwright 自带 Chromium(最新版) → Edge
case "$OSTYPE" in
  darwin*)
    _CH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    [ ! -f "$_CH" ] && _CH=$(ls "$HOME/Library/Caches/ms-playwright/chromium-"*/chrome-mac/Chromium.app/Contents/MacOS/Chromium 2>/dev/null | sort -V | tail -1)
    [ -z "$_CH" ] && _CH="/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    ;;
  *)
    _CH=""
    for c in "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
             "C:/Program Files/Google/Chrome/Application/chrome.exe"; do
      [ -f "$c" ] && _CH="$c" && break
    done
    [ -z "$_CH" ] && _CH=$(ls "$HOME"/AppData/Local/ms-playwright/chromium-*/chrome-win64/chrome.exe 2>/dev/null | sort -V | tail -1)
    [ -z "$_CH" ] && _CH="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    ;;
esac
export HYPERFRAMES_BROWSER_PATH="$_CH"

# 2) ffmpeg: 优先 imageio-ffmpeg(pip 自带二进制), 回落 PATH
_FF=$(python -c "import imageio_ffmpeg,sys; sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null \
      || python3 -c "import imageio_ffmpeg,sys; sys.stdout.write(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null \
      || command -v ffmpeg || true)
[ -n "$_FF" ] && export HYPERFRAMES_FFMPEG_PATH="$_FF"

# 3) ffprobe: PATH 优先, 回落各机 skill-lab 的 @ffprobe-installer
_FP=""
for c in "$(command -v ffprobe 2>/dev/null)" \
         "$HOME/Documents/project/ai_ask/skill-lab/node_modules/@ffprobe-installer/darwin-x64/ffprobe" \
         "$HOME/Documents/project/ai_ask/skill-lab/node_modules/@ffprobe-installer/darwin-arm64/ffprobe" \
         "F:/learn/ai_ask/skill-lab/node_modules/@ffprobe-installer/win32-x64/ffprobe.exe"; do
  [ -n "$c" ] && [ -e "$c" ] && _FP="$c" && break
done
[ -n "$_FP" ] && export HYPERFRAMES_FFPROBE_PATH="$_FP"

echo "hf-env: browser=$_CH"
[ -n "$_FF" ] && echo "hf-env: ffmpeg=$_FF" || echo "hf-env: ffmpeg 未找到(装 pip 包 imageio-ffmpeg)"
[ -n "$_FP" ] && echo "hf-env: ffprobe=$_FP" || echo "hf-env: ffprobe 未找到(装 @ffprobe-installer 或系统 ffprobe)"
