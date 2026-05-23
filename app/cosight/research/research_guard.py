# Copyright 2025 ZTE Corporation.
# All Rights Reserved.

"""Deep-research guardrails: plan validation, tool circuit breaker, evidence table, finalize gate."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.common.logger_util import logger

# --- Limits (env overrides) ---
MAX_TOTAL_TOOL_FAILURES = int(os.environ.get("MAX_TOTAL_TOOL_FAILURES", "6"))
MAX_FAILURES_PER_TOOL = int(os.environ.get("MAX_FAILURES_PER_TOOL", "2"))
MAX_RESEARCH_STEPS = int(os.environ.get("MAX_RESEARCH_STEPS", "8"))
MAX_TOTAL_TOKENS = int(os.environ.get("MAX_TOTAL_TOKENS", "80000"))
MAX_TOTAL_ITERATIONS = int(os.environ.get("MAX_TOTAL_ITERATIONS", "10"))

RETRIEVAL_TOOLS: Set[str] = {
    "search_wiki",
    "search_google",
    "tavily_search",
    "search_baidu",
    "search_duckgo",
    "deep_search",
    "image_search",
    "fetch_website_content",
    "fetch_website_content_with_images",
    "fetch_website_images_only",
    "browser_use",
    "extract_document_content",
    "count_wikipedia_edits_in_year",
    "get_wikipedia_revisions",
    "get_wikipedia_revision_content",
    "get_wikipedia_revision_before_date",
    "count_wikipedia_references",
    "count_references_for_revision",
    "extract_wikipedia_section",
    "extract_section_from_revision",
    "compute_wikipedia_reference_delta",
    "find_wikipedia_revision_by_size_delta",
    "count_train_line_station_connections",
    "lookup_book_publication_year",
    "count_reference_year_in_paper_abstract",
    "search_book_page_for_text",
    "count_term_occurrences",
    "extract_abstract_from_text",
}

FAILURE_MARKERS = (
    "tooltimeouterror",
    "tool `",
    " failed:",
    "network is unreachable",
    "connectionerror",
    "jsondecodeerror",
    "max retries exceeded",
    "do not treat this as evidence",
    '"error":',
    "tool_execution_failed",
)

COUNT_QUESTION_HINTS = (
    r"how many",
    r"count\b",
    r"number of",
    r"increase in",
    r"reference count",
    r"edited\b",
    r"connections to",
    r"page of the",
    r"how many times",
)

EXTERNAL_EVIDENCE_HINTS = (
    "wikipedia",
    "wiki",
    "edited",
    "revision",
    "reference",
    "as of",
    "according to",
    "page",
    "rail",
    "amtrak",
    "abstract",
    "book",
    "edition",
    "youtube",
    "http",
    "website",
    "count",
)


def is_deep_research_enabled() -> bool:
    flag = os.environ.get("DEEP_RESEARCH_ENABLED", "").strip().lower()
    return flag in ("1", "true", "yes", "on", "enabled")


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


class ResearchGuard:
    """Per-plan research session state and policy enforcement."""

    def __init__(self, plan: Any, question: str, enabled: Optional[bool] = None):
        self.plan = plan
        self.question = question or ""
        self.enabled = is_deep_research_enabled() if enabled is None else enabled
        self.run_status: str = "running"  # running | success | partial | failed
        self.terminate_reason: str = ""
        self.total_tool_failures: int = 0
        self.per_tool_failures: Dict[str, int] = {}
        self.per_tool_consecutive_failures: Dict[str, int] = {}
        self.blocked_tools: Set[str] = set()
        self.research_steps_executed: int = 0
        self.total_iterations: int = 0
        self.estimated_tokens: int = 0
        self.successful_retrieval_tools: List[str] = []
        self.failure_records: List[Dict[str, Any]] = []
        self.verified_evidence: List[Dict[str, Any]] = []
        self.unresolved_issues: List[str] = []
        self.evidence_retry_attempted: bool = False
        self.plan_retry_count: int = 0
        self.evidence_table: Dict[str, Any] = self._empty_evidence_table()

    def _empty_evidence_table(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "requires_external_evidence": self.requires_external_evidence(),
            "evidence": [],
            "count_items": [],
            "excluded_items": [],
            "final_count": None,
            "confidence": "low",
        }

    def requires_external_evidence(self) -> bool:
        q = self.question.lower()
        if any(re.search(p, q) for p in COUNT_QUESTION_HINTS):
            return True
        return any(h in q for h in EXTERNAL_EVIDENCE_HINTS)

    def is_count_question(self) -> bool:
        q = self.question.lower()
        return any(re.search(p, q) for p in COUNT_QUESTION_HINTS)

    def is_empty_plan(self) -> bool:
        steps = getattr(self.plan, "steps", None) or []
        return len(steps) == 0

    def record_plan_attempt(self) -> None:
        self.plan_retry_count += 1

    def plan_invalid_after_retries(self, max_retries: int = 2) -> bool:
        return self.enabled and self.is_empty_plan() and self.plan_retry_count >= max_retries

    def increment_research_step(self) -> None:
        self.research_steps_executed += 1

    def record_iteration_tokens(self, messages: List[Dict[str, Any]]) -> None:
        self.total_iterations += 1
        if messages:
            last = messages[-1]
            content = last.get("content") or ""
            self.estimated_tokens += _estimate_tokens(str(content))

    def limits_exceeded(self) -> Tuple[bool, str]:
        if not self.enabled:
            return False, ""
        if self.total_tool_failures >= MAX_TOTAL_TOOL_FAILURES:
            return True, f"total_tool_failures>={MAX_TOTAL_TOOL_FAILURES}"
        if self.research_steps_executed >= MAX_RESEARCH_STEPS:
            return True, f"research_steps>={MAX_RESEARCH_STEPS}"
        if self.total_iterations >= MAX_TOTAL_ITERATIONS:
            return True, f"iterations>={MAX_TOTAL_ITERATIONS}"
        if self.estimated_tokens >= MAX_TOTAL_TOKENS:
            return True, f"tokens>={MAX_TOTAL_TOKENS}"
        return False, ""

    def is_tool_blocked(self, tool_name: str) -> bool:
        return self.enabled and tool_name in self.blocked_tools

    def _classify_error(self, error_text: str) -> str:
        t = (error_text or "").lower()
        if "typeerror" in t:
            return "TypeError"
        if "timeout" in t:
            return "Timeout"
        if "json" in t:
            return "JSONDecodeError"
        if "network" in t or "connection" in t:
            return "NetworkError"
        return "Error"

    def _is_tool_result_failure(self, tool_name: str, result: str) -> bool:
        if not result:
            return True
        lower = str(result).lower()
        if any(m in lower for m in FAILURE_MARKERS):
            return True
        if tool_name in RETRIEVAL_TOOLS:
            try:
                obj = json.loads(result)
                if isinstance(obj, dict) and obj.get("error"):
                    return True
            except json.JSONDecodeError:
                pass
        return False

    def record_tool_outcome(
        self,
        tool_name: str,
        tool_args: str,
        result: str,
        success: bool,
        error_text: str = "",
    ) -> Optional[str]:
        """Record tool result; return early-stop message if circuit opens."""
        if not self.enabled:
            return None

        if success and not self._is_tool_result_failure(tool_name, result):
            self.per_tool_consecutive_failures[tool_name] = 0
            if tool_name in RETRIEVAL_TOOLS:
                self.successful_retrieval_tools.append(tool_name)
                self._ingest_evidence_from_tool(tool_name, tool_args, result)
            return None

        # failure path
        self.total_tool_failures += 1
        self.per_tool_failures[tool_name] = self.per_tool_failures.get(tool_name, 0) + 1
        self.per_tool_consecutive_failures[tool_name] = (
            self.per_tool_consecutive_failures.get(tool_name, 0) + 1
        )

        failure_summary = ""
        try:
            args_obj = json.loads(tool_args) if tool_args else {}
            if isinstance(args_obj, dict):
                if tool_name == "create_plan":
                    failure_summary = str(args_obj.get("title") or args_obj.get("steps", ""))[:200]
                else:
                    failure_summary = str(
                        args_obj.get("query")
                        or args_obj.get("entity")
                        or args_obj.get("title")
                        or args_obj.get("website_url")
                        or ""
                    )[:200]
        except Exception:
            failure_summary = str(tool_args)[:200]

        record: Dict[str, Any] = {
            "tool": tool_name,
            "status": "failed",
            "error_type": self._classify_error(error_text or result),
        }
        if failure_summary:
            record["failure_summary"] = failure_summary
        try:
            parsed = json.loads(result) if result else {}
            if isinstance(parsed, dict) and parsed.get("exception_message"):
                record["exception_message"] = str(parsed["exception_message"])[:800]
                if parsed.get("error_type"):
                    record["error_type"] = parsed["error_type"]
        except json.JSONDecodeError:
            if error_text:
                record["exception_message"] = str(error_text)[:800]
        self.failure_records.append(record)
        if len(self.failure_records) > 12:
            self.failure_records = self.failure_records[-12:]

        if self.per_tool_consecutive_failures[tool_name] >= MAX_FAILURES_PER_TOOL:
            self.blocked_tools.add(tool_name)
            logger.warning(f"ResearchGuard: blocked tool {tool_name} after consecutive failures")

        exceeded, reason = self.limits_exceeded()
        if exceeded:
            self.run_status = "failed"
            self.terminate_reason = reason
            return self._circuit_stop_message(reason)
        return None

    def _ingest_evidence_from_tool(self, tool_name: str, tool_args: str, result: str) -> None:
        claim = f"{tool_name} returned structured data"
        snippet = str(result)[:400]
        entry = {
            "claim": claim,
            "source": snippet,
            "tool": tool_name,
            "status": "verified",
        }
        self.verified_evidence.append(entry)
        self.evidence_table["evidence"].append(entry)

        if tool_name in (
            "count_wikipedia_edits_in_year",
            "compute_wikipedia_reference_delta",
            "count_references_for_revision",
            "count_train_line_station_connections",
            "count_reference_year_in_paper_abstract",
            "search_book_page_for_text",
        ):
            try:
                obj = json.loads(result)
                if isinstance(obj, dict):
                    for key in (
                        "edit_count",
                        "connection_count",
                        "delta",
                        "reference_count",
                        "year_mention_count",
                        "page_number",
                        "final_count",
                    ):
                        if key in obj and obj[key] is not None:
                            self.evidence_table["count_items"].append(
                                {
                                    "item": key,
                                    "included": True,
                                    "reason": f"from {tool_name} JSON field",
                                    "source": str(obj[key]),
                                }
                            )
                            if key in ("edit_count", "connection_count", "delta", "year_mention_count", "page_number"):
                                self.evidence_table["final_count"] = obj[key]
            except json.JSONDecodeError:
                pass

    def has_successful_retrieval(self) -> bool:
        return len(self.successful_retrieval_tools) > 0

    def has_verified_evidence(self) -> bool:
        return len(self.verified_evidence) > 0

    def count_plan_tool_calls(self) -> int:
        total = 0
        stc = getattr(self.plan, "step_tool_calls", {}) or {}
        for step, calls in stc.items():
            if step == "__global_tools__":
                continue
            if isinstance(calls, list):
                total += len(calls)
        return total

    def sync_from_plan(self) -> None:
        """Re-scan plan tool calls for successful retrieval (post-hoc)."""
        stc = getattr(self.plan, "step_tool_calls", {}) or {}
        for _step, calls in stc.items():
            if not isinstance(calls, list):
                continue
            for call in calls:
                name = call.get("tool_name", "")
                result = call.get("tool_result") or ""
                args = call.get("tool_args") or ""
                if name in RETRIEVAL_TOOLS and not self._is_tool_result_failure(name, result):
                    if name not in self.successful_retrieval_tools:
                        self.successful_retrieval_tools.append(name)
                    self._ingest_evidence_from_tool(name, args, result)

    def evidence_retry_prompt(self) -> str:
        return (
            "This task requires external evidence. You must create executable steps and call "
            "retrieval/API tools (e.g. Wikipedia revision tools, search, fetch_website_content). "
            "Do not answer from internal knowledge. Do not output FINAL_ANSWER without tool evidence."
        )

    def build_unable_to_determine(self, reason: str) -> str:
        self.run_status = "failed"
        return (
            f"FINAL_ANSWER: Unable to determine\n"
            f"RUN_STATUS: failed\n"
            f"REASON: {reason}\n"
            f"FAILURE_SUMMARY: {json.dumps(self.failure_records[-6:], ensure_ascii=False)}"
        )

    def build_partial_report(self, reason: str, draft: str = "") -> str:
        self.run_status = "partial"
        body = draft.strip() if draft else "Partial evidence only; cannot assert a verified final answer."
        return (
            f"FINAL_ANSWER: Unable to determine\n"
            f"RUN_STATUS: partial\n"
            f"REASON: {reason}\n"
            f"EVIDENCE_TABLE: {json.dumps(self.evidence_table, ensure_ascii=False)[:3000]}\n"
            f"NOTES: {body[:1500]}"
        )

    def validate_finalize_output(self, llm_output: str) -> str:
        """Post-process planner finalize output; block unverified numeric FINAL_ANSWER."""
        if not self.enabled or not self.requires_external_evidence():
            if self.has_verified_evidence() and self.run_status == "running":
                self.run_status = "success"
            return llm_output

        self.sync_from_plan()

        if self.is_empty_plan():
            return self.build_unable_to_determine(
                "Planner failed to generate executable research steps."
            )

        if not self.has_successful_retrieval() or not self.has_verified_evidence():
            return self.build_unable_to_determine(
                "No successful retrieval/API tool calls with usable evidence."
            )

        text = llm_output or ""
        final_match = re.search(
            r"FINAL_ANSWER:\s*(.+?)(?:\nTRACE|\nRUN_STATUS|\Z)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if final_match:
            answer = final_match.group(1).strip()
            if self.is_count_question() and self._looks_like_guessed_numeric_answer(answer):
                if self.evidence_table.get("final_count") is not None:
                    verified = str(self.evidence_table["final_count"])
                    text = re.sub(
                        r"(FINAL_ANSWER:\s*)(.+?)(?=\nTRACE|\nRUN_STATUS|\Z)",
                        rf"\g<1>{verified}",
                        text,
                        count=1,
                        flags=re.IGNORECASE | re.DOTALL,
                    )
                    self.run_status = "success"
                else:
                    return self.build_unable_to_determine(
                        "Numeric FINAL_ANSWER not backed by evidence table / tool JSON."
                    )
            elif re.search(r"unable to determine", answer, re.I):
                self.run_status = "failed"
            else:
                self.run_status = "success"
        else:
            if self.has_verified_evidence():
                self.run_status = "partial"
            else:
                self.run_status = "failed"

        if "RUN_STATUS:" not in text:
            text += f"\nRUN_STATUS: {self.run_status}\n"
        if self.is_count_question() and "EVIDENCE_TABLE:" not in text:
            text += f"EVIDENCE_TABLE: {json.dumps(self.evidence_table, ensure_ascii=False)[:2000]}\n"
        return text

    def _looks_like_guessed_numeric_answer(self, answer: str) -> bool:
        a = answer.strip().lower()
        if "unable" in a or "unknown" in a or "not verifiable" in a:
            return False
        if re.search(r"\b(best[- ]supported|estimate|likely|probably)\b", a):
            return True
        if self.evidence_table.get("final_count") is not None:
            return str(self.evidence_table["final_count"]) not in answer
        if re.fullmatch(r"\d+", a):
            return True
        return False

    def _circuit_stop_message(self, reason: str) -> str:
        return (
            f"Research circuit breaker open ({reason}). "
            f"Do not retry the same failed tools. "
            f"Failures: {json.dumps(self.failure_records[-4:], ensure_ascii=False)}"
        )

    def compressed_context_block(self) -> str:
        return json.dumps(
            {
                "verified_evidence": self.verified_evidence[-8:],
                "unresolved_issues": self.unresolved_issues[-5:],
                "evidence_table": {
                    "count_items": self.evidence_table.get("count_items"),
                    "final_count": self.evidence_table.get("final_count"),
                    "confidence": self.evidence_table.get("confidence"),
                },
                "tool_failures": self.failure_records[-6:],
                "blocked_tools": sorted(self.blocked_tools),
                "run_status": self.run_status,
            },
            ensure_ascii=False,
        )

    def attach_to_plan(self) -> None:
        if self.plan is not None:
            self.plan.research_guard = self  # type: ignore[attr-defined]
            self.plan.run_status = self.run_status  # type: ignore[attr-defined]
            self.plan.evidence_table = self.evidence_table  # type: ignore[attr-defined]
