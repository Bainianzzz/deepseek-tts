---
name: deepseek-tts
version: 1.0.0
description: "DeepSeek 语音合成（TTS）：把文字转成语音音频，当用户要朗读/配音/生成语音、把文本或回答转成 mp3/wav/pcm 时使用。"
metadata:
  requires:
    bins: ["curl", "python3"]
  env: ["DEEPSEEK_API_KEY"]
---

# DeepSeek TTS

文字 → 自然语音。语种不用指定，服务端按文本自动识别（普通话、粤语、英语、日语、韩语、马来语、阿拉伯语、印尼语、泰语、越南语）。

## 默认参数（禁止向用户询问，除非用户明确要改）

| 参数 | 默认值 | 备选 |
|------|--------|------|
| `voice_id` | `stella` — 海星，女声 | `tide` — 暗潮，男声 |
| 语言 | 普通话（自动识别，无参数） | — |
| `format` | `wav` | `pcm` — 24 kHz / 16 bit / 单声道裸流 |
| `filter_markdown` | `true`（朗读前自动去掉 Markdown） | `false` |

鉴权一律用环境变量 `DEEPSEEK_API_KEY`，请求头 `Authorization: Bearer $DEEPSEEK_API_KEY`。不要把 key 写进文件或打印出来。

## 步骤

1. **确认文本**：待朗读文本已定稿。回答里的 Markdown 保持原样即可（默认 `filter_markdown=true` 会自动清理），不用自己手洗格式。完成条件：文本非空。
2. **合成**：文本已定稿，跑 `scripts/tts.sh`（见下）整段合成。完成条件：输出文件存在且 > 0 字节。
3. **交付**：给出文件绝对路径；能播放就放一遍（macOS `afplay <file>`）。完成条件：用户拿到了可播放的音频。

## 合成方式

下面的 `<skill-dir>` 是本 SKILL.md 所在目录（路径按 skill 目录解析，不是当前工作目录）。

```bash
bash <skill-dir>/scripts/tts.sh "你好，我是 DeepSeek。" /tmp/speech.wav
bash <skill-dir>/scripts/tts.sh "暗潮男声示例" /tmp/a.wav tide
cat long.md | bash <skill-dir>/scripts/tts.sh - /tmp/long.wav
```

脚本已内置：JSON 转义、默认 `stella`、按后缀选 `wav`/`pcm`、503/504/429 退避重试 3 次、0 字节响应视为失败。

不用脚本时等价的裸调用：

```bash
curl https://api.deepseek.com/v1/tools/tts \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，我是 DeepSeek。", "voice_id": "stella", "format": "wav"}' \
  --output speech.wav
```

单次请求最多 30 分钟音频，最多 10,000 计费字符，请求体 ≤ 64 KiB。超长文本按段落/句切成多段分别合成，再按顺序拼接（`ffmpeg -f concat`）或分段交给用户。不支持语速调节，不支持中断续传。

## 格式转换

```bash
ffmpeg -f s16le -ar 24000 -ac 1 -i speech.pcm speech.wav   # pcm → wav
ffmpeg -i speech.wav -codec:a libmp3lame -q:a 4 speech.mp3 # 用户要 mp3 时
```

## 错误码

| 状态码 / code | 含义 | 处理 |
|---|---|---|
| 400 / `content_filter` | 无可朗读文本，或文本未过内容审核（Content Exists Risk） | 改文本，别重试同样的内容 |
| 429 | 并发超限（每账号同时最多 50 个请求） | 降低并发后重试 |
| 503 / `service_error` | 服务繁忙 | 退避重试 |
| 504 | 合成超时 | 缩短文本后重试 |

音频开始返回后若中途断开，把提前结束的响应**当作失败**丢弃，不要交付半截音频。
