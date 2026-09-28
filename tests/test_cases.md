# BudgetWise AI - Test Cases (M2)

All cases use the FAKE sample data in `data/` (as-of date 2026-09-28). The agent must call the
MCP tool for every number. Run the deterministic checks with `pytest`, and the live agent checks
with `python tests/run_agent_tests.py` (needs NRP credentials).

| ID | Input (user question) | Expected tool call | Expected output (must appear in the answer) |
|----|------------------------|--------------------|----------------------------------------------|
| TC1 | "Where am I spending the most money lately?" | `get_spending_by_category` | Dining is the top discretionary category at $359.10 (14.4% of the last 30 days' $2,485.70 spending; rent, a fixed cost, is larger at $1,100). |
| TC2 | "How much can I safely spend per day until my next paycheck?" | `get_safe_to_spend` | $430.25 safe to spend in total = $39.11/day for 11 days ($1,875.25 balance - $1,245.00 bills due before payday - $200 buffer). The $65 internet bill due after payday is excluded. |
| TC3 | "How unpredictable is my income, and what should I plan around?" | `get_income_variability` | Must state the conservative planning baseline of $2,610 (the lowest month, Jun-Aug 2026). The answer may also cite the average $2,960, the $810 swing, or the monthly figures $2,850 / $3,420 / $2,610. |

## Automated coverage
- `tests/test_budgetwise.py` - checks the exact numbers above plus bad-input handling (no LLM), and starts the real MCP server over stdio to call all 3 tools through the protocol.
- `tests/run_agent_tests.py` - sends TC1-TC3 to the live agent and checks the tool called and the figures in the answer.
