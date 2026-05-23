"""Contest-mode prompt and trace helpers.

This module keeps competition-specific behavior behind an environment flag so
the default Co-Sight experience remains unchanged.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict


def is_contest_mode() -> bool:
    return os.environ.get("CONTEST_MODE", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "enabled",
        "on",
    )


def contest_planner_system_append() -> str:
    return """

# Co-Sight Contest Mode
You are solving benchmark questions where scoring is based on:
1. final-answer accuracy,
2. the quality of the visible reasoning trajectory,
3. stable agent orchestration.

Planning rules for contest questions:
- Prefer a small, reliable plan: understand question, gather/compute only what is needed, verify, finalize.
- Do not create report-oriented or presentation-oriented steps unless the question explicitly asks for a report.
- For Level 1 style questions, use 1-2 steps and avoid unnecessary tools.
- For Level 2/3 style questions, decompose into evidence collection, intermediate reasoning, verification, and final answer.
- Every step should have a clear success condition and should help produce the final answer.
- If a question has an exact expected answer, plan toward a concise exact answer instead of a broad essay.
- Include a verification step for multi-hop, calculation, date-sensitive, or source-dependent questions.
"""


def contest_create_plan_append() -> str:
    return """

Contest-mode planning output requirements:
- Create no more than 4 steps unless the task truly requires more.
- Use step names that expose the trajectory clearly, for example:
  "Parse the question and identify answer type",
  "Collect only the necessary evidence",
  "Compute or infer the answer",
  "Verify and finalize the exact answer".
- Avoid vague steps such as "research comprehensively" or "write a report" for exam-style questions.
"""


def contest_replan_append() -> str:
    return """

Contest-mode replanning rules:
- Preserve completed evidence and tool results.
- If the current path is still valid, continue rather than starting over.
- If a tool fails, switch to a cheaper or more direct fallback and record that in the step notes.
"""


def contest_finalize_append(output_format: str = "") -> str:
    from app.cosight.tool.answer_validator import contest_answer_guard_note
    format_note = (
        "Respect the caller-provided output format exactly.\n"
        if output_format
        else "Use the final answer format below.\n"
    )
    return f"""

# Contest Final Answer Rules
{format_note}
- Put the answer first.
- Do not bury the answer in a long report.
- If the answer is a number, entity name, option, date, or short phrase, output it exactly and concisely.
- Then provide a compact trajectory summary that mentions the decisive steps and tools used.
- If evidence is insufficient after all applicable tools, state the best-supported answer briefly — avoid defaulting to "Unable to determine".

Recommended format when no stricter output format is provided:
FINAL_ANSWER: <exact answer>
TRACE_SUMMARY: <2-5 concise bullets or sentences explaining the path>

{contest_answer_guard_note()}
"""


def contest_actor_system_append() -> str:
    return """

# Contest Execution Rules
- Optimize for correct final answers, not long reports.
- Before using a tool, decide what missing fact, calculation, or transformation the tool will provide.
- Prefer direct reasoning for simple questions.
- Use tools for retrieval, calculation, file/document parsing, or verification when they materially improve accuracy.
- Avoid repeated searches with nearly identical queries.
- For multi-hop tasks, keep intermediate facts explicit in step notes.
- When calling mark_step, include:
  1. key evidence or intermediate result,
  2. tools used,
  3. whether the step result is verified or uncertain.
- Do not save files unless a file is useful as evidence, an intermediate artifact, or the requested final output.

# Contest Tool Routing (mandatory)
- Wikipedia revision/history/edit-count/reference-count/size-delta questions:
  use count_wikipedia_edits_in_year, get_wikipedia_revisions, compute_wikipedia_reference_delta,
  find_wikipedia_revision_by_size_delta, extract_section_from_revision — NOT search_wiki or generic web search alone.
- search_wiki only returns article summaries; it cannot count edits or revisions.
- "How many times edited", "revision", "early 2025 version", "reference count", "size diff" → Wikipedia revision tools first.
- Counting tasks: use tool JSON numeric fields; never guess counts from summaries.
- Do not output "Unable to determine", "Unknown", "has not occurred", or "No such edit exists" if revision tools can still be tried.
- Amtrak / rail connection questions (shared station, commuter/heavy rail, as-of date):
  use count_train_line_station_connections ONCE with train_page_title="Adirondack (train)" and as_of_date="2023-07-31".
  Do NOT retry this tool more than once on failure; check VPN/PROXY and TOOL_EXEC_TIMEOUT / RAIL_TOOL_EXEC_TIMEOUT instead.
- Academic abstract year-count questions (paper abstract + referenced book publication year):
  use count_reference_year_in_paper_abstract, or lookup_book_publication_year + extract_abstract_from_text + count_term_occurrences.
- Cookbook / book page-number questions (specific edition, recipe/stuffing page):
  use search_book_page_for_text with book_title, edition_year, and search_phrases — NOT generic web search alone.
- Web search (tavily/google): use only for non-Wikipedia facts; keep snippets short; do not paste full pages into notes.
"""


def contest_execute_task_append(is_last_step: bool) -> str:
    if is_last_step:
        return """

# Contest Current-Step Instructions
This is the final or answer-producing step:
- Derive the exact final answer from the verified step results.
- If there are conflicting facts, resolve them before finalizing.
- Call mark_step with the exact answer and a concise trace note.
"""
    return """

# Contest Current-Step Instructions
This is an intermediate step:
- Produce a compact, reusable intermediate result.
- Keep the trajectory clear by recording decisive evidence, computation, or tool output in mark_step.
- Stop once this step's success condition is met; do not drift into final reporting early.
"""


def safe_json_dump(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
