# Copyright 2025 ZTE Corporation.
# All Rights Reserved.

"""Runtime facts injected into agent prompts (clock, MCP command resolution)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone


def get_time_context_block() -> str:
    """Authoritative current time for LLM reasoning (avoids stale training-year assumptions)."""
    local = datetime.now().astimezone()
    utc_now = datetime.now(timezone.utc)
    return (
        "# Runtime Context (authoritative)\n"
        f"- Current local date-time: {local.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"- Current UTC date-time: {utc_now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"- Calendar year in effect: {local.year}\n"
        "Use the timestamps above for any question about today, the current year, "
        "or whether a future/past event has already happened. "
        "Do not assume the year is 2024 or 2025 unless it matches the date above.\n"
    )


def append_time_context(prompt: str) -> str:
    return prompt.rstrip() + "\n\n" + get_time_context_block()


def resolve_stdio_command(command: str) -> str:
    """Map generic python launchers to the interpreter running Co-Sight (venv-safe)."""
    if not command:
        return sys.executable
    normalized = command.strip()
    if normalized.lower() in ("python", "python3", "py"):
        return sys.executable
    return normalized
