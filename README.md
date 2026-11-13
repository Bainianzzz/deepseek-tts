# deepseek-tts skill

[DeepSeek TTS](https://api-docs.deepseek.com/) 的 Agent Skill：把文字转成自然语音。语种不用指定，服务端按文本自动识别（普通话、粤语、英语、日语、韩语、马来语、阿拉伯语、印尼语、泰语、越南语）。

本 Skill 只做一件事：给定文本，产出一个可直接播放的音频文件。默认 `voice_id=stella`（海星，女声）、`format=wav`、`filter_markdown=true`（朗读前自动去掉 Markdown），不需要向用户询问参数。

## 安装

如果你正在使用 Claude Code、Codex 等 coding agent，直接将下面这段话发给它即可自动完成安装：

```text
Fetch the installation guide and follow it: https://raw.githubusercontent.com/Bainianzzz/deepseek-tts/main/README.md
```

手动安装推荐使用全局安装方式：

```bash
npx skills add Bainianzzz/deepseek-tts -g -y
```

然后准备 API Key（不要写进文件，用环境变量）：

```bash
export DEEPSEEK_API_KEY=sk-...      # 加到 ~/.zshrc 或 ~/.bashrc
```

自检：

```bash
bash ~/.agents/skills/deepseek-tts/scripts/tts.sh "你好，我是 DeepSeek。" /tmp/speech.wav
afplay /tmp/speech.wav              # macOS 播放
```

后续如果本 Skill 有更新，执行：

```bash
npx skills update deepseek-tts -g -y
```

## 内容

```text
skills/
└── deepseek-tts/
    ├── SKILL.md
    └── scripts/
        └── tts.sh
```

| 文件                 | 作用                                                                                                                  |
| -------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `SKILL.md`           | 入口：默认参数表、三段流程（确认文本 / 合成 / 交付，均带完成判据）、裸 `curl` 等价调用、格式转换、错误码处理           |
| `scripts/tts.sh`     | 整段合成脚本：JSON 转义、按输出后缀选 `wav`/`pcm`、503/504/429 退避重试 3 次、0 字节响应视为失败，支持 `-` 读 stdin   |

`SKILL.md` 只保留每次都会用到的流程；细节按需查阅。

## 能力

| 能力                       | 方式                                            | 入口         |
| -------------------------- | ----------------------------------------------- | ------------ |
| 文本 → wav 音频            | `scripts/tts.sh <文本> <out.wav>`               | `SKILL.md`   |
| 长文本（stdin 管道 / Markdown 文件） | `cat long.md \| scripts/tts.sh - out.wav` | `SKILL.md`   |
| 换男声                     | 第三个参数传 `tide`（暗潮，男声）               | `SKILL.md`   |
| 裸流输出                   | 输出文件后缀用 `.pcm` / `.raw`（24 kHz / 16 bit / 单声道） | `SKILL.md` |
| 转 mp3 或 `pcm → wav`      | `ffmpeg` 命令模板                               | `SKILL.md` §格式转换 |
| 失败排查                   | `400` / `429` / `503` / `504` 与中途断流的处理  | `SKILL.md` §错误码 |

## 已知限制

- 单次请求最多 30 分钟音频、10,000 计费字符、请求体 ≤ 64 KiB；超长文本需按段落切分后拼接。
- 不支持语速调节，不支持中断续传。
- 需要 `curl` 与 `python3`；音频后处理（mp3 转换、pcm 转 wav）需要 `ffmpeg`。

## 许可证

[MIT License](LICENSE).

Copyright (c) 2026 Bainianzzz
