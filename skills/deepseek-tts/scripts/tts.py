#!/usr/bin/env python3
"""DeepSeek TTS, single-request synthesis.

Usage: tts.py <text|-> <output file> [voice_id]

- voice_id defaults to stella (female)
- output format inferred from the output suffix: .pcm/.raw -> pcm, otherwise wav
- text "-" means read from stdin
- requires the DEEPSEEK_API_KEY environment variable

Standard library only, Python 3.8+.
"""
from __future__ import annotations

import http.client
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import NoReturn

API_URL = "https://api.deepseek.com/v1/tools/tts"
TIMEOUT = 300  # 秒；长文本合成可能耗时较久
RETRY_CODES = {429, 503, 504}
MAX_ATTEMPTS = 3


def fail(msg: str, code: int = 1) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def error_detail(raw: bytes) -> str:
    """Flatten an error response into one line, preferring error.code / error.message."""
    body = raw[:500].decode("utf-8", "replace").strip()
    try:
        err = json.loads(body).get("error") or {}
    except (ValueError, AttributeError):
        return body
    code = err.get("code") or ""
    msg = err.get("message") or ""
    parts = [p for p in (code, msg) if p]
    return " — ".join(parts) or body


def pick_format(out_path: str) -> str:
    suffix = os.path.splitext(out_path)[1].lower().lstrip(".")
    return "pcm" if suffix in ("pcm", "raw") else "wav"


def read_text(arg: str) -> str:
    return sys.stdin.read() if arg == "-" else arg


def synthesize(text: str, voice: str, fmt: str, api_key: str) -> bytes:
    payload = json.dumps(
        {"text": text, "voice_id": voice, "format": fmt},
        ensure_ascii=False,
    ).encode("utf-8")

    last_err = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        req = urllib.request.Request(
            API_URL,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "audio/wav, audio/pcm, */*",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                audio = resp.read()
        except urllib.error.HTTPError as e:
            detail = error_detail(e.read())
            if e.code in RETRY_CODES and attempt < MAX_ATTEMPTS:
                last_err = f"HTTP {e.code} {detail}".strip()
                print(f"retry {attempt}/{MAX_ATTEMPTS - 1}: {last_err}", file=sys.stderr)
                time.sleep(2 * attempt)
                continue
            if e.code == 400:
                fail(
                    "HTTP 400 request rejected: empty text / failed content moderation / "
                    "invalid parameter; fix the text or voice_id, don't resend as-is\n" + detail
                )
            if e.code in RETRY_CODES:
                fail(f"HTTP {e.code} (retried {MAX_ATTEMPTS} times)\n{detail}")
            fail(f"HTTP {e.code}\n{detail}")
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as e:
            # 连接失败/超时/响应中途断开：整段视为失败，不交付半截音频。
            if attempt < MAX_ATTEMPTS:
                last_err = str(e)
                print(f"retry {attempt}/{MAX_ATTEMPTS - 1}: {last_err}", file=sys.stderr)
                time.sleep(2 * attempt)
                continue
            fail(f"request failed (retried {MAX_ATTEMPTS} times): {e}")

        if not audio:
            last_err = "got 0 bytes of audio"
            if attempt < MAX_ATTEMPTS:
                print(f"retry {attempt}/{MAX_ATTEMPTS - 1}: {last_err}", file=sys.stderr)
                time.sleep(2 * attempt)
                continue
            fail("got 0 bytes of audio (treated as failure)")
        return audio

    fail(f"synthesis failed: {last_err}")
    raise AssertionError("unreachable")


def main(argv: list) -> int:
    if len(argv) < 3:
        print("usage: tts.py <text|-> <output file> [voice_id]", file=sys.stderr)
        return 2

    text_arg, out_path = argv[1], argv[2]
    voice = argv[3] if len(argv) > 3 else "stella"
    fmt = pick_format(out_path)

    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        fail("DEEPSEEK_API_KEY is not set", 2)

    text = read_text(text_arg)
    if not text.strip():
        fail("text is empty", 2)

    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    if not os.path.isdir(out_dir):
        fail(f"output directory does not exist: {out_dir}", 2)
    if os.path.isdir(out_path):
        fail(f"output path is a directory: {out_path}", 2)

    audio = synthesize(text, voice, fmt, api_key)

    # 先写同目录临时文件再原子改名，避免留下半截文件。
    fd, tmp_path = tempfile.mkstemp(dir=out_dir)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(audio)
        # mkstemp 建的是 0600，这里按 umask 放宽到普通文件权限。
        mask = os.umask(0)
        os.umask(mask)
        os.chmod(tmp_path, 0o666 & ~mask)
        os.replace(tmp_path, out_path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    print(f"written: {out_path} ({len(audio)} bytes, voice={voice}, format={fmt})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        raise SystemExit(130)
