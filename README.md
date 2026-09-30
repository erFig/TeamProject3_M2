# BudgetWise AI (Team 3, CEN 4930 M2)

**Problem:** People with irregular income, particularly students and part-time workers, can check their balance but cannot tell how much money they can safely spend before their next paycheck.

## What the agent does now
BudgetWise is a single prototype agent which reads fake sample financial data from `data/` and answers questions. It runs on the National Research Platform (NRP)'s `gpt-oss` large language model with a custom Model Context Protocol (MCP) server with multiple tools:

- `get_spending_by_category(days: int = 30)` shows how money was spent over the last N (default: 30) days and flags the top discretionary category.
- `get_safe_to_spend()` calculates balance minus bills due before payday minus a savings buffer, in total and per day.
- `get_income_variability(months: int = 3)` summarizes monthly income swings (default: last 3 months) and provides a conservative planning baseline.

## Intentionally not built yet
Real bank linking, investing or retirement guidance, memory across sessions, multiple agents, a web UI, and any handling of real financial data.

## Setup and run
1. Install Python 3.11.\* or newer (tested on 3.14.7): https://www.python.org/downloads/
2. Download and extract a copy of the TeamProject3_M2 repository:
    1. Git: `git clone https://github.com/erFig/TeamProject3_M2.git`
    2. Github: Go to https://github.com/erFig/TeamProject3_M2/archive/refs/heads/main.zip and unzip the folder to a safe location.
3. Create and activate a virtual environment:
    1. Install `virtualenv`: `python -m pip install virtualenv`
    2. Change command-line directory to repository: `cd /path/to/TeamProject3_M2`
    3. Create a virtual environment: `python -m venv venv`
    4. Activate the virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate`
4. Install required libraries: `python -m pip install -r requirements.txt`
5. Make a copy of `.env.example` named `.env` and paste your NRP token. Optionally, change `NRP_MODEL`. Never commit `.env`.
6. Ask a question: 
    * Example: `python agent.py "How much can I spend per day until payday?"`
    * Run `python agent.py` for chat mode
    * Add `--trace` to see a trace with spans from each model and tool call.

## Known limitations
1. Uses fake sample data with a fixed date (2026-09-28).
2. The safe-to-spend formula is doesn't account for, e.g., irregular expenses and the next paycheck.
3. `gpt-oss` may skip and misuse tool calls or phrase numbers loosely.