# BudgetWise AI (Team 3, CEN 4930 M2)

**Problem:** People with irregular income, especially students and hourly workers, check their balance but still cannot tell how much they can safely spend before the next paycheck.

## What the agent does now
BudgetWise is a single agent running on NRP `gpt-oss` with a custom MCP server of three tools. It reads FAKE sample data in `data/` and answers plain-English questions:

- `get_spending_by_category` shows where money went over the last N days and flags the top discretionary category.
- `get_safe_to_spend` calculates balance minus bills due before payday minus a savings buffer, in total and per day.
- `get_income_variability` summarizes monthly income swings and a conservative planning baseline.

The agent must call a tool for every number, so the calculations are deterministic and not left to the model.

## Intentionally not built yet
Real bank linking, investing or retirement guidance, memory across sessions, multiple agents, a web UI, and any handling of real financial data.

## Setup and run
1. Install Python 3.11 or 3.12 and Git.
2. `git clone https://github.com/erFig/TeamProject3_M2.git` and `cd TeamProject3_M2`
3. Create and activate a virtual environment: `python -m venv venv`, then `venv\Scripts\activate` (Windows) or `source venv/bin/activate`.
4. `python -m pip install -r requirements.txt` (use `python -m pip` so packages go into the venv)
5. Copy `.env.example` to `.env` and paste your NRP token. Never commit `.env`.
6. Ask a question: `python agent.py "How much can I spend per day until payday?"` (or run `python agent.py` for chat mode). Add `--trace` to also see the trace and spans of each model and tool call.
7. Run checks: `python -m pytest` (no network needed), then `python tests/run_agent_tests.py` (live model; also accepts `--trace`). The three test cases are in `tests/test_cases.md`.

To try another NRP model, set `NRP_MODEL` in `.env`.

## Known limitations
1. Uses fake, static sample data with a fixed "today" (2026-09-28); there is no way to upload real transactions yet.
2. The safe-to-spend formula is simplified: it ignores irregular expenses and does not predict the next paycheck's amount.
3. `gpt-oss` may skip or misuse a tool call, or phrase numbers loosely, so the live test can fail even though the tools themselves are correct.

## Layout
`agent.py` (the agent), `mcp_server.py` (the 3 tools), `data/` (fake sample data), `tests/` (tests and test cases).
