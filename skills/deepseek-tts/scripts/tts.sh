#!/usr/bin/env bash
# DeepSeek TTS 整段合成。用法: tts.sh <文本|-> <输出文件> [voice_id]
# 默认 voice_id=stella（海星，女声）、格式按输出文件后缀推断（.wav 默认，.pcm/.raw 走 pcm）。
# 需要环境变量 DEEPSEEK_API_KEY。文本用 - 表示从 stdin 读取。
set -euo pipefail

text_arg=${1:?用法: tts.sh <文本|-> <输出文件> [voice_id]}
out=${2:?缺少输出文件}
voice=${3:-stella}

case "${out##*.}" in
  pcm|raw) format=pcm ;;
  *)       format=wav ;;
esac

if [ "$text_arg" = "-" ]; then
  text=$(cat)
else
  text=$text_arg
fi
[ -n "${text//[[:space:]]/}" ] || { echo "错误: 文本为空" >&2; exit 2; }

: "${DEEPSEEK_API_KEY:?未设置 DEEPSEEK_API_KEY}"

tmp=$(mktemp); trap 'rm -f "$tmp"' EXIT
body=$(python3 -c 'import json,sys; print(json.dumps({"text": sys.stdin.read(), "voice_id": sys.argv[1], "format": sys.argv[2]}))' "$voice" "$format" <<<"$text")

for attempt in 1 2 3; do
  code=$(curl -sS -o "$tmp" -w '%{http_code}' https://api.deepseek.com/v1/tools/tts \
    -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
    -H 'Content-Type: application/json' \
    -d "$body")
  case $code in
    200) break ;;
    503|504|429)
      if [ "$attempt" = 3 ]; then echo "错误: HTTP $code（已重试 3 次）" >&2; head -c 500 "$tmp" >&2; exit 1; fi
      sleep $((attempt * 2)); continue ;;
    *) echo "错误: HTTP $code" >&2; head -c 500 "$tmp" >&2; echo >&2; exit 1 ;;
  esac
done

[ -s "$tmp" ] || { echo "错误: 返回 0 字节音频（视为失败）" >&2; exit 1; }
mv "$tmp" "$out"
trap - EXIT
echo "已生成: $out ($(wc -c <"$out" | tr -d ' ') 字节, voice=$voice, format=$format)"
