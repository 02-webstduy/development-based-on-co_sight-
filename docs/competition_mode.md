# Co-Sight Competition Mode

This mode is designed for contest tasks that score final-answer accuracy,
trajectory quality, and agent orchestration stability.

## Enable

Set the following in `.env`:

```env
CONTEST_MODE=True
TURBO_MODE=False
```

`TURBO_MODE` can be useful for low-cost testing, but contest tasks usually need
better verification, so keep it disabled for final runs unless rate limits are a
serious problem.

## What Changes

When `CONTEST_MODE=True`, Co-Sight keeps the normal UI and API flow, but adds:

- contest-oriented planning rules,
- execution rules that prefer exact answers over long reports,
- explicit verification guidance for multi-hop questions,
- final answer formatting guidance,
- automatic structured trace export.

The default mode is unchanged when `CONTEST_MODE` is off.

## Trace Output

Each task workspace writes:

```text
competition_trace.json
```

It contains:

- plan title and progress,
- step list, status, dependencies, notes, and files,
- tool calls per step,
- global MCP/tool calls,
- final answer text.

This file is intended as support material for automated or manual trajectory
inspection. The UI replay log is still written separately by the existing
Co-Sight flow.

## Recommended Contest Workflow

1. Put all model keys and search keys in `.env`.
2. Set `CONTEST_MODE=True`.
3. Run each of the 10 questions as a separate task.
4. For each task, collect:
   - final answer from the UI or final response,
   - `competition_trace.json`,
   - relevant workspace artifacts.
5. Package the modified source code and the 10 traces.

## Development Priorities

For this scoring rule, prioritize changes in this order:

1. Planner prompts and step granularity.
2. Actor execution prompts and verification rules.
3. Domain-specific tools or MCP integrations.
4. Structured evidence/facts storage.
5. Frontend support for editing/retrying steps.

Adding tools helps, but the largest accuracy gains usually come from better
planning, better answer extraction, and better verification.
