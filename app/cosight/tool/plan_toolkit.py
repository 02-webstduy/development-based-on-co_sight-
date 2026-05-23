# Copyright 2025 ZTE Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ast
import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from app.cosight.task.plan_report_manager import plan_report_event_manager
from app.cosight.task.todolist import Plan
from app.common.logger_util import logger
from app.cosight.research.research_guard import is_deep_research_enabled

# Keys that belong to search tools, not create_plan — never map these to title/steps.
_CREATE_PLAN_IGNORED_KEYS = frozenset({
    "query", "q", "keyword", "keywords", "search", "prompt", "entity", "website_url",
})


def _step_dict_to_str(step: dict) -> str:
    title = (
        step.get("title")
        or step.get("name")
        or step.get("step")
        or step.get("step_title")
        or ""
    )
    desc = (
        step.get("description")
        or step.get("details")
        or step.get("content")
        or step.get("success_criteria")
        or ""
    )
    tools = step.get("required_tools") or step.get("tools")
    parts = [str(title).strip()] if title else []
    if desc:
        parts.append(str(desc).strip())
    if tools:
        if isinstance(tools, list):
            parts.append("tools: " + ", ".join(str(t) for t in tools))
        else:
            parts.append(f"tools: {tools}")
    text = " — ".join(p for p in parts if p)
    return text or json.dumps(step, ensure_ascii=False)[:300]


def normalize_plan_steps(steps: Any) -> List[str]:
    """Convert LLM step payloads (strings, dicts, JSON text) to Plan step strings."""
    if steps is None:
        return []
    if isinstance(steps, str):
        text = steps.strip()
        if not text:
            return []
        if text.startswith("[") or text.startswith("{"):
            try:
                parsed = json.loads(text)
                return normalize_plan_steps(parsed)
            except json.JSONDecodeError:
                pass
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            line = re.sub(r"^\d+[\.\)]\s*", "", line)
            if line:
                lines.append(line)
        return lines
    if isinstance(steps, dict):
        return [_step_dict_to_str(steps)]
    if isinstance(steps, list):
        out: List[str] = []
        for item in steps:
            if isinstance(item, str):
                s = item.strip()
                if s:
                    out.append(s)
            elif isinstance(item, dict):
                s = _step_dict_to_str(item)
                if s:
                    out.append(s)
            elif item is not None:
                out.append(str(item).strip())
        return out
    return [str(steps).strip()] if str(steps).strip() else []


def resolve_create_plan_args(
    title: Optional[str],
    steps: Any,
    dependencies: Any,
    extra: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[str], Optional[List[str]], Any, Optional[str]]:
    """
    Resolve title/steps from normalized + raw tool args.
    Returns (title, steps, dependencies, error_message). error_message set on invalid input.
    """
    extra = dict(extra or {})
    for key in _CREATE_PLAN_IGNORED_KEYS:
        extra.pop(key, None)

    resolved_title = title or extra.get("title") or extra.get("plan_title") or extra.get("plan_name")
    if not resolved_title:
        for alias in ("name", "task_title", "plan"):
            if extra.get(alias):
                resolved_title = extra.get(alias)
                break

    resolved_steps = steps
    if resolved_steps is None:
        for alias in ("steps", "plan_steps", "step_list", "tasks", "actions", "step_descriptions"):
            if extra.get(alias) is not None:
                resolved_steps = extra.get(alias)
                break

    # Do not treat bare `query` as plan content (common LLM mistake for search tools).
    if resolved_steps is None and any(k in extra for k in _CREATE_PLAN_IGNORED_KEYS):
        return (
            None,
            None,
            dependencies,
            (
                "create_plan argument error: received search-style fields (e.g. 'query') but "
                "create_plan requires title (string) and steps (array of strings or step objects). "
                'Example: create_plan(title="Research ZTE edits", steps=["Collect revisions via API", "Count and verify"]).'
            ),
        )

    normalized_steps = normalize_plan_steps(resolved_steps)

    if not normalized_steps:
        return (
            None,
            None,
            dependencies,
            (
                "create_plan argument error: missing or empty 'steps'. "
                "Pass steps as a non-empty array of strings, e.g. "
                'steps=["Step 1: ...", "Step 2: ..."].'
            ),
        )

    if not resolved_title:
        resolved_title = "Task Plan"

    deps = dependencies if dependencies is not None else extra.get("dependencies")
    return str(resolved_title).strip(), normalized_steps, deps, None


def merge_create_plan_tool_args(
    normalized: Dict[str, Any],
    raw: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge raw LLM args with normalized args before calling PlanToolkit.create_plan."""
    merged: Dict[str, Any] = {}
    if raw:
        merged.update(raw)
    if normalized:
        merged.update(normalized)
    title, steps, deps, err = resolve_create_plan_args(
        merged.get("title"),
        merged.get("steps"),
        merged.get("dependencies"),
        merged,
    )
    out: Dict[str, Any] = {}
    if err:
        out["_plan_tool_error"] = err
        return out
    out["title"] = title
    out["steps"] = steps
    if deps is not None:
        out["dependencies"] = deps
    return out


class PlanToolkit:
    r"""A class representing a toolkit for creating and managing a single plan."""

    def __init__(self, plan: Optional[Plan] = None):
        self.plan = plan

    def create_plan(
        self,
        title: Optional[str] = None,
        steps: Optional[Union[List[str], List[dict], str]] = None,
        dependencies: Optional[Dict[int, List[int]]] = None,
        **kwargs: Any,
    ) -> str:
        r"""Create a new plan with the given title, steps, and dependencies."""
        title, steps, dependencies, err = resolve_create_plan_args(
            title, steps, dependencies, kwargs
        )
        if err:
            logger.warning(err)
            return err

        logger.info(
            f"create plan, title is {title}, steps is {steps}, dependencies({type(dependencies)}) is {dependencies}"
        )

        if dependencies and isinstance(dependencies, str):
            try:
                dependencies = ast.literal_eval(dependencies)
            except Exception as e:
                logger.error(
                    f"Plan Warning: not literal_eval('{dependencies}') to dict, raise error: {str(e)}",
                    exc_info=True,
                )
                dependencies = None

        if dependencies is None and len(steps) > 1:
            dependencies = {i: [i - 1] for i in range(1, len(steps))}

        if is_deep_research_enabled() and (not steps or len(steps) == 0):
            return (
                "InvalidPlan: empty steps rejected in deep research mode. "
                "You must provide at least 2 executable steps with tool-based evidence collection."
            )

        self.plan.update(title, steps, dependencies)
        result = f"Plan created successfully\n\n{self.plan.format()}"
        plan_report_event_manager.publish("plan_created", self.plan)
        logger.info(result)
        return result

    def update_plan(
        self,
        title: Optional[str] = None,
        steps: Optional[List[str]] = None,
        dependencies: Optional[Dict[int, List[int]]] = None,
        **kwargs: Any,
    ) -> str:
        r"""Update the existing plan with new title, steps, or dependencies while preserving completed steps."""
        if self.plan is None:
            return "No plan exists. Create a plan with the 'create' command."

        merged = dict(kwargs)
        if title is not None:
            merged["title"] = title
        if steps is not None:
            merged["steps"] = steps
        if dependencies is not None:
            merged["dependencies"] = dependencies

        resolved_title = merged.get("title")
        resolved_steps = merged.get("steps")
        if resolved_steps is not None:
            resolved_steps = normalize_plan_steps(resolved_steps)
        resolved_deps = merged.get("dependencies")

        logger.info(
            f"update plan, title is {resolved_title}, steps is {resolved_steps}, "
            f"dependencies({type(resolved_deps)}) is {resolved_deps}"
        )

        if resolved_deps and isinstance(resolved_deps, str):
            try:
                resolved_deps = ast.literal_eval(resolved_deps)
            except Exception as e:
                logger.error(
                    f"Plan Warning: not literal_eval('{resolved_deps}') to dict, raise error: {str(e)}",
                    exc_info=True,
                )
                resolved_deps = None

        self.plan.update(resolved_title, resolved_steps, resolved_deps)
        result = f"Plan updated successfully\n\n{self.plan.format()}"
        plan_report_event_manager.publish("plan_updated", self.plan)
        logger.info(f"update result is {result}")
        return result
