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
from datetime import datetime
from app.cosight.agent.actor.instance.actor_agent_instance import create_actor_instance
from llm import llm_for_plan, llm_for_act, llm_for_tool, llm_for_vision
from app.cosight.task.plan_report_manager import plan_report_event_manager


import os
import time
from threading import Thread

from app.cosight.agent.actor.task_actor_agent import TaskActorAgent
from app.cosight.agent.planner.instance.planner_agent_instance import create_planner_instance
from app.cosight.agent.planner.task_plannr_agent import TaskPlannerAgent
from app.cosight.task.task_manager import TaskManager
from app.cosight.task.todolist import Plan
from app.cosight.task.time_record_util import time_record
from app.common.logger_util import logger
from app.cosight.research.research_guard import ResearchGuard, is_deep_research_enabled


class CoSight:
    def __init__(self, plan_llm, act_llm, tool_llm, vision_llm, work_space_path: str = None, message_uuid: str|None = None):
        self.work_space_path = work_space_path or os.getenv("WORKSPACE_PATH") or os.getcwd()
        self.plan_id = message_uuid if message_uuid else f"plan_{int(time.time())}"
        self.plan = Plan()
        TaskManager.set_plan(self.plan_id, self.plan)
        self.research_guard = None
        
        # 设置Langfuse追踪上下文
        plan_llm.set_trace_context(
            trace_id=None,
            session_id=self.plan_id,
            tags=["planning"],
            metadata={"agent_type": "planner", "plan_id": self.plan_id}
        )
        act_llm.set_trace_context(
            trace_id=None,
            session_id=self.plan_id,
            tags=["execution"],
            metadata={"agent_type": "actor", "plan_id": self.plan_id}
        )
        tool_llm.set_trace_context(
            trace_id=None,
            session_id=self.plan_id,
            tags=["tool"],
            metadata={"agent_type": "tool", "plan_id": self.plan_id}
        )
        vision_llm.set_trace_context(
            trace_id=None,
            session_id=self.plan_id,
            tags=["vision"],
            metadata={"agent_type": "vision", "plan_id": self.plan_id}
        )
        
        self.task_planner_agent = TaskPlannerAgent(create_planner_instance("task_planner_agent"), plan_llm,
                                                   self.plan_id)
        self.act_llm = act_llm
        self.tool_llm = tool_llm
        self.vision_llm = vision_llm

    def _init_guard(self, question: str) -> ResearchGuard:
        self.research_guard = ResearchGuard(self.plan, question)
        self.research_guard.attach_to_plan()
        return self.research_guard

    def _create_plan_with_validation(self, question: str, output_format: str, guard: ResearchGuard) -> bool:
        """Return True if a non-empty plan exists after retries."""
        create_task = question
        max_attempts = 2 if guard.enabled else 3
        for attempt in range(max_attempts):
            guard.record_plan_attempt()
            self.task_planner_agent.create_plan(create_task, output_format)
            if not guard.is_empty_plan():
                return True
            logger.warning(f"InvalidPlan: empty steps (attempt {attempt + 1}/{max_attempts})")
            create_task = (
                f"{question}\n\n"
                "InvalidPlan: you MUST call create_plan with at least 2 executable steps "
                "that use retrieval/API tools. Empty plans are rejected."
            )
        return not guard.is_empty_plan()

    def _guard_limits_stop(self, guard: ResearchGuard) -> bool:
        exceeded, reason = guard.limits_exceeded()
        if exceeded:
            guard.run_status = "failed"
            guard.terminate_reason = reason
            logger.warning(f"ResearchGuard stopped execution: {reason}")
            return True
        return False

    @time_record
    def execute(self, question, output_format=""):
        guard = self._init_guard(question)

        task_metadata = {
            "task_question": question[:200] if len(question) > 200 else question,
            "plan_id": self.plan_id,
            "deep_research_enabled": guard.enabled,
        }
        
        for llm in [self.task_planner_agent.llm, self.act_llm, self.tool_llm, self.vision_llm]:
            if hasattr(llm, 'current_metadata'):
                llm.current_metadata.update(task_metadata)

        # A. Empty plan validation (deep research)
        if not self._create_plan_with_validation(question, output_format, guard):
            result = guard.build_unable_to_determine(
                "Planner failed to generate executable research steps."
            )
            self.plan.set_plan_result(result)
            self._set_run_status(guard)
            return self._format_result(question, result, guard)

        active_threads = {}

        while True:
            if self._guard_limits_stop(guard):
                break

            ready_steps = self.plan.get_ready_steps()
            
            for step_index in ready_steps:
                if step_index not in active_threads:
                    if guard.enabled:
                        guard.increment_research_step()
                        if self._guard_limits_stop(guard):
                            break
                    logger.info(f"Starting new step {step_index}")
                    thread = Thread(target=self._execute_single_step, args=(question, step_index, guard))
                    thread.daemon = True
                    thread.start()
                    active_threads[step_index] = thread
            
            completed_steps = []
            for step_index, thread in list(active_threads.items()):
                if not thread.is_alive():
                    completed_steps.append(step_index)
            
            for step_index in completed_steps:
                del active_threads[step_index]
                logger.info(f"Step {step_index} completed and thread removed")
            
            if not active_threads and not ready_steps:
                logger.info("No more ready steps to execute and no active threads")
                break
            
            if self._guard_limits_stop(guard):
                break
            
            time.sleep(0.1)

        # B. Mandatory tool evidence before finalize
        if guard.enabled and guard.requires_external_evidence():
            guard.sync_from_plan()
            if not guard.has_successful_retrieval():
                if not guard.evidence_retry_attempted:
                    guard.evidence_retry_attempted = True
                    logger.warning("No retrieval tools succeeded; running one evidence enforcement step")
                    self._run_evidence_enforcement_step(question, guard)
                    guard.sync_from_plan()

        if guard.enabled and guard.requires_external_evidence() and not guard.has_successful_retrieval():
            result = guard.build_unable_to_determine(
                "No successful retrieval/API tool calls; cannot produce verified FINAL_ANSWER."
            )
            self.plan.set_plan_result(result)
            self._set_run_status(guard)
            return self._format_result(question, result, guard)

        if guard.enabled and guard.terminate_reason and guard.run_status == "failed":
            result = guard.build_partial_report(
                guard.terminate_reason,
                "Research terminated by circuit breaker before finalize.",
            )
            self.plan.set_plan_result(result)
            self._set_run_status(guard)
            return self._format_result(question, result, guard)

        raw_finalize = self.task_planner_agent.finalize_plan(question, output_format, guard)
        result = guard.validate_finalize_output(raw_finalize)
        self.plan.set_plan_result(result)
        self._set_run_status(guard)
        plan_report_event_manager.publish("plan_result", self.plan)
        return self._format_result(question, result, guard)

    def _set_run_status(self, guard: ResearchGuard) -> None:
        self.plan.run_status = guard.run_status  # type: ignore[attr-defined]
        self.plan.evidence_table = guard.evidence_table  # type: ignore[attr-defined]
        guard.attach_to_plan()

    def _format_result(self, question: str, result: str, guard: ResearchGuard) -> str:
        status_line = guard.run_status
        if status_line == "failed":
            status_text = "执行失败"
        elif status_line == "partial":
            status_text = "部分完成（证据不足）"
        elif guard.is_empty_plan():
            status_text = "执行失败"
        else:
            status_text = "执行完成" if guard.has_verified_evidence() or not guard.requires_external_evidence() else "部分完成（证据不足）"

        return f"""
Task:
{question}

Plan Status:
{self.plan.format()}

Run Status: {status_line} ({status_text})

Summary:
{result}
"""

    def _run_evidence_enforcement_step(self, question: str, guard: ResearchGuard) -> None:
        """One extra step forcing tool use when plan completed without retrieval."""
        if guard.is_empty_plan():
            return
        step_index = 0
        try:
            self.plan.mark_step(step_index, step_status="in_progress")
            plan_report_event_manager.publish("plan_process", self.plan)
            task_actor_agent = TaskActorAgent(
                create_actor_instance("actor_evidence_retry", self.work_space_path),
                self.act_llm,
                self.vision_llm,
                self.tool_llm,
                self.plan_id,
                work_space_path=self.work_space_path,
            )
            task_actor_agent.history.append({
                "role": "user",
                "content": guard.evidence_retry_prompt() + f"\n\nTask: {question}",
            })
            task_actor_agent.act(question=question, step_index=step_index)
            self.plan.mark_step(step_index, step_status="completed", step_notes="evidence enforcement pass")
            plan_report_event_manager.publish("plan_process", self.plan)
        except Exception as e:
            logger.error(f"Evidence enforcement step failed: {e}", exc_info=True)
            try:
                self.plan.mark_step(step_index, step_status="blocked", step_notes=str(e))
            except Exception:
                pass

    def _execute_single_step(self, question, step_index, guard: ResearchGuard):
        try:
            logger.info(f"Starting execution of step {step_index}")
            task_actor_agent = TaskActorAgent(
                create_actor_instance(f"actor_for_step_{step_index}", self.work_space_path),
                self.act_llm,
                self.vision_llm,
                self.tool_llm,
                self.plan_id,
                work_space_path=self.work_space_path,
            )
            if guard.enabled and guard.requires_external_evidence():
                task_actor_agent.history.append({
                    "role": "user",
                    "content": (
                        "Deep research mode: use retrieval/API tools for facts and counts. "
                        "Do not answer from internal knowledge alone. "
                        + guard.compressed_context_block()[:2000]
                    ),
                })
            result = task_actor_agent.act(question=question, step_index=step_index)
            logger.info(f"Completed execution of step {step_index} with result: {result}")
        except Exception as e:
            logger.error(f"Error executing step {step_index}: {e}", exc_info=True)

    def execute_steps(self, question, ready_steps):
        from threading import Semaphore
        from queue import Queue

        results = {}
        result_queue = Queue()
        semaphore = Semaphore(min(5, len(ready_steps)))

        def execute_step(step_index):
            semaphore.acquire()
            try:
                logger.info(f"Starting execution of step {step_index}")
                task_actor_agent = TaskActorAgent(
                    create_actor_instance(f"actor_for_step_{step_index}", self.work_space_path),
                    self.act_llm,
                    self.vision_llm,
                    self.tool_llm,
                    self.plan_id,
                    work_space_path=self.work_space_path,
                )
                result = task_actor_agent.act(question=question, step_index=step_index)
                logger.info(f"Completed execution of step {step_index} with result: {result}")
                result_queue.put((step_index, result))
            finally:
                semaphore.release()

        threads = []
        for step_index in ready_steps:
            thread = Thread(target=execute_step, args=(step_index,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        while not result_queue.empty():
            step_index, result = result_queue.get()
            results[step_index] = result

        return results


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    work_space_path = os.path.join(BASE_DIR, 'work_space', f'work_space_{timestamp}')
    os.makedirs(work_space_path, exist_ok=True)

    cosight = CoSight(llm_for_plan, llm_for_act, llm_for_tool, llm_for_vision, work_space_path)

    result = cosight.execute("帮我写一篇中兴通讯的分析报告")
    logger.info(f"final result is {result}")
