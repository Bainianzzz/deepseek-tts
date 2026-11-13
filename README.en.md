# deepseek-tts skill

English | [中文](README.md)

An agent skill for [DeepSeek TTS](https://api-docs.deepseek.com/zh-cn/guides/tts): turn text into natural speech. You do not pick a language — the server detects it from the text (Mandarin, Cantonese, English, Japanese, Korean, Malay, Arabic, Indonesian, Thai, Vietnamese).

The skill does one thing: given text, produce an audio file you can play right away. Defaults are `voice_id=stella` (female), `format=wav`, `filter_markdown=true` (Markdown is stripped before reading), so the agent never has to ask the user about parameters.

## Install

If you are using Claude Code, Codex, or another coding agent, send it this message and it will install the skill for you:

```text
Fetch the installation guide and follow it: https://raw.githubusercontent.com/Bainianzzz/deepseek-tts/main/README.en.md
```

For a manual install, the global option is recommended:

```bash
npx skills add Bainianzzz/deepseek-tts -g -y
```

Then provide the API key (through the environment; ask the user for it if it is missing):

```bash
export DEEPSEEK_API_KEY=sk-...      # add to ~/.zshrc or ~/.bashrc
```

Self-check:

```bash
python3 ~/.agents/skills/deepseek-tts/scripts/tts.py "Hello, this is DeepSeek." /tmp/speech.wav
```

To pick up later updates to this skill:

```bash
npx skills update deepseek-tts -g -y
```

## Contents

```text
skills/
└── deepseek-tts/
    ├── SKILL.md
    └── scripts/
        └── tts.py
```

| File             | Purpose                                                                                                                                                                                                                                        |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SKILL.md`       | Entry point: default parameter table, three steps (confirm text / synthesize / deliver, each with a completion criterion), the raw `curl` equivalent, format conversion, error-code handling                                               |
| `scripts/tts.py` | Single-request synthesis script (Python 3 standard library, no third-party deps): `json` encoding instead of hand-written escaping, format picked from the output suffix, backoff retries on 503/504/429, 0-byte and truncated responses treated as failure, atomic write, `-` reads stdin |

## Limitations

- One request covers at most 30 minutes of audio, 10,000 billed characters, and a 64 KiB body; longer text must be split into paragraphs and the segments joined afterwards.
- No speaking-rate control, no resume after interruption.
- Requires `python3` (3.8+, standard library only, no `pip install`); audio post-processing (mp3 conversion, pcm to wav) requires `ffmpeg`.

## License

[MIT License](LICENSE).

Copyright (c) 2026 Bainianzzz
