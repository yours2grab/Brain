#!/usr/bin/env python3
"""
Daily Digest Hook — appends session summaries to Virgil Brain Daily notes.

Fires on Stop AND PostToolUse (debounced to once per 5 minutes).
Uses Claude CLI (Haiku) to summarize transcripts — no API key needed.

SHORT-TERM MEMORY LAYER:
- Daily notes = ground truth for last 3 days
- Honcho = long-term reasoning
"""

import json
import sys
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

DAILY_DIR = Path(os.path.expanduser("~/My Drive/Virgil Brain/Daily"))
DEBOUNCE_FILE = Path(os.path.expanduser("~/.claude/hooks/.last-digest-ts"))
DEBOUNCE_SECONDS = 300  # 5 minutes
CLAUDE_CLI = "/opt/homebrew/bin/claude"


def read_stdin():
    """Read hook input from stdin."""
    try:
        data = sys.stdin.read().strip()
        if data:
            return json.loads(data)
    except Exception:
        pass
    return {}


def should_run():
    """Check debounce — only run once per 5 minutes."""
    try:
        if DEBOUNCE_FILE.exists():
            last_run = float(DEBOUNCE_FILE.read_text().strip())
            if time.time() - last_run < DEBOUNCE_SECONDS:
                return False
    except Exception:
        pass
    return True


def update_debounce():
    """Record current timestamp for debounce."""
    try:
        DEBOUNCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEBOUNCE_FILE.write_text(str(time.time()))
    except Exception:
        pass


SYSTEM_TAGS = (
    "system-reminder", "local-command-caveat", "command-name",
    "command-message", "command-args", "local-command-stdout",
    "antml_thinking", "antml_function_calls", "antml_invoke",
    "antml_parameter", "function_results", "functions", "function",
)
_SYSTEM_TAG_PATTERN = re.compile(
    r"<(?:" + "|".join(SYSTEM_TAGS) + r")[^>]*>.*?</(?:" + "|".join(SYSTEM_TAGS) + r")>",
    re.DOTALL,
)
_SYSTEM_TAG_ORPHAN = re.compile(
    r"</?(?:" + "|".join(SYSTEM_TAGS) + r")[^>]*>"
)


def strip_system_tags(text: str) -> str:
    """Remove system-injected tags and their content."""
    text = _SYSTEM_TAG_PATTERN.sub("", text)
    text = _SYSTEM_TAG_ORPHAN.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_save_session(path: str) -> bool:
    """Check if the user's last message contains 'save session'."""
    if not path or not os.path.exists(path):
        return False
    try:
        # Read last 5000 chars to find recent user messages
        with open(path) as f:
            content = f.read()
        tail = content[-5000:] if len(content) > 5000 else content
        for line in reversed(tail.split("\n")):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                role = entry.get("type") or entry.get("role")
                if role == "user":
                    msg = entry.get("message", {}).get("content") or entry.get("content", "")
                    if isinstance(msg, list):
                        msg = " ".join(p.get("text", "") for p in msg if p.get("type") == "text")
                    return "save session" in msg.lower()
            except Exception:
                continue
    except Exception:
        pass
    return False


def parse_transcript(path: str) -> str:
    """Extract user and assistant messages from transcript JSONL as plain text."""
    if not path or not os.path.exists(path):
        return ""

    lines = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    role = entry.get("type") or entry.get("role")
                    content = entry.get("message", {}).get("content") or entry.get("content")

                    if not content or role not in ("user", "assistant"):
                        continue

                    if isinstance(content, list):
                        text_parts = [p.get("text", "") for p in content if p.get("type") == "text"]
                        text = "\n".join(text_parts)
                    else:
                        text = content

                    text = strip_system_tags(text)
                    if text and text.strip():
                        lines.append(f"[{role}]: {text.strip()}")
                except Exception:
                    continue
    except Exception:
        pass

    return "\n".join(lines)


def summarize_with_cli(transcript_text: str, cwd: str) -> str | None:
    """Use Claude CLI (Haiku) to summarize the transcript."""
    if not transcript_text or len(transcript_text) < 200:
        return None

    # Truncate to ~8000 chars to stay within reasonable input size
    if len(transcript_text) > 8000:
        transcript_text = transcript_text[-8000:]

    dir_label = os.path.basename(cwd) if cwd else "unknown"
    prompt = f"""Summarize this Claude Code session in exactly 8-10 lines. Format:
- Line 1: **Topics:** comma-separated list
- Line 2: **Asked:** what the user wanted (1 sentence)
- Lines 3-8: **Done:** bullet points of what was accomplished
- Line 9: **Outcome:** final state / what's next
- Line 10: **Pending:** anything unfinished (or "None")

Be specific — include file names, tool names, decisions made. No fluff.

Transcript:
{transcript_text}"""

    try:
        result = subprocess.run(
            [CLAUDE_CLI, "-p", prompt, "--model", "sonnet"],
            capture_output=True,
            text=True,
            timeout=25,
            env={**os.environ, "NO_COLOR": "1"},
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    return None


def fallback_digest(transcript_text: str) -> str | None:
    """Simple fallback if CLI fails — just grab first user message and last assistant message."""
    if not transcript_text:
        return None

    lines = transcript_text.split("\n")
    user_lines = [l for l in lines if l.startswith("[user]:")]
    assistant_lines = [l for l in lines if l.startswith("[assistant]:")]

    if not user_lines or not assistant_lines:
        return None

    asked = user_lines[0].replace("[user]: ", "")[:100]
    outcome = assistant_lines[-1].replace("[assistant]: ", "")[:120]

    return f"**Asked:** {asked}\n**Outcome:** {outcome}"


def ensure_daily_note(date: datetime) -> Path:
    """Create or return the Daily note path for today."""
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    filename = date.strftime("%Y-%m-%d") + ".md"
    filepath = DAILY_DIR / filename

    if not filepath.exists():
        frontmatter = f"""---
type: daily-note
date: {date.strftime('%Y-%m-%d')}
---
# {date.strftime('%Y-%m-%d')}
"""
        filepath.write_text(frontmatter)

    return filepath


def append_digest(filepath: Path, digest: str, dir_label: str):
    """Append digest to the daily note, avoiding duplicates."""
    existing = filepath.read_text() if filepath.exists() else ""

    now = datetime.now()
    header = f"### {now.strftime('%H:%M')} — {dir_label}"

    # Check for duplicate (same HH:MM header already exists)
    if header in existing:
        return False

    entry = f"\n{header}\n{digest}\n"

    with open(filepath, "a") as f:
        f.write(entry)

    return True


def main():
    hook_input = read_stdin()

    # Debounce check — skip if we ran less than 5 min ago
    # Bypass debounce on Stop events and "save session" user messages
    hook_event = hook_input.get("hook_event", "")
    transcript_path = hook_input.get("transcript_path")
    force_run = hook_event == "Stop" or is_save_session(transcript_path)
    if not force_run and not should_run():
        sys.exit(0)

    cwd = (
        hook_input.get("workspace_roots", [None])[0]
        or hook_input.get("cwd")
        or os.getcwd()
    )
    dir_label = os.path.basename(cwd) if cwd else "unknown"

    transcript_text = parse_transcript(transcript_path)
    if not transcript_text or len(transcript_text) < 200:
        sys.exit(0)

    # Try CLI summarization first, fall back to simple extraction
    digest = summarize_with_cli(transcript_text, cwd)
    if not digest:
        digest = fallback_digest(transcript_text)

    if not digest:
        sys.exit(0)

    now = datetime.now()
    daily_path = ensure_daily_note(now)
    appended = append_digest(daily_path, digest, dir_label)

    if appended:
        update_debounce()
        print(f"[daily-digest] Saved to {daily_path.name}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
