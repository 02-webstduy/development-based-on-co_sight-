# Copyright 2025 ZTE Corporation.
# All Rights Reserved.

"""Reject weak contest final answers that indicate retrieval failure."""

from __future__ import annotations

import re
from typing import List

INVALID_PATTERNS: List[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"unable to determine",
        r"unknown\s*\(",
        r"not verifiable",
        r"has not occurred",
        r"no such edit",
        r"cannot determine",
        r"could not determine",
        r"com poser",
        r"^\s*0\s*$",  # bare 0 for count questions — flag only when combined with wiki context in caller
    ]
]

REFUSAL_PHRASES = [
    "unable to determine",
    "unknown (not verifiable",
    "has not occurred",
    "no such edit exists",
]


def is_weak_contest_answer(text: str) -> bool:
    if not text or not str(text).strip():
        return True
    lowered = str(text).lower()
    for phrase in REFUSAL_PHRASES:
        if phrase in lowered:
            return True
    if re.search(r"\bcomposer\b", lowered) and "com poser" in lowered:
        return True
    return False


def contest_answer_guard_note() -> str:
    return (
        "If evidence supports a concrete answer, you must output it. "
        "Do not output 'Unable to determine', 'Unknown', 'has not occurred', or 'No such edit exists' "
        "unless the question explicitly allows no answer and all tools failed."
    )
