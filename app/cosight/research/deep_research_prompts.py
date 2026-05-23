# Copyright 2025 ZTE Corporation.

from app.cosight.research.research_guard import is_deep_research_enabled


def deep_research_planner_append() -> str:
    if not is_deep_research_enabled():
        return ""
    return """

# Deep Research Planning Rules (mandatory)
- NEVER return an empty plan. At least 2 executable steps are required.
- Each step must name a concrete retrieval/API tool (Wikipedia revision tools, search, fetch_website_content, etc.).
- Do not plan essay-only steps without tools for fact/count/date questions.
- Maximum 8 research steps total.
"""


def deep_research_actor_append() -> str:
    if not is_deep_research_enabled():
        return ""
    return """

# Deep Research Execution Rules (mandatory)
- You MUST call retrieval/API tools before stating factual or numeric answers.
- Do NOT answer from internal knowledge when external verification is required.
- If a tool fails twice, do not retry the same tool; try a different source or mark_step blocked.
- For count questions, rely on tool JSON numeric fields (edit_count, delta, connection_count, etc.).
- If evidence is insufficient, mark_step blocked — do not invent FINAL_ANSWER numbers.
- Do not paste full search results into notes; summarize in <=800 tokens.
"""


def deep_research_finalize_append() -> str:
    if not is_deep_research_enabled():
        return ""
    return """

# Deep Research Final Answer Rules (mandatory)
- If no successful tool evidence: FINAL_ANSWER: Unable to determine
- Never output numeric FINAL_ANSWER without tool-backed evidence table.
- Unverified estimates are NOT allowed in FINAL_ANSWER (put them only in NOTES, labeled unverified).
- Include RUN_STATUS: success | partial | failed
- For count tasks include EVIDENCE_TABLE JSON when verified.
"""
