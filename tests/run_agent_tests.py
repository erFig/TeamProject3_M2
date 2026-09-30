"""Live end-to-end test: sends the 3 documented questions to the real agent (needs NRP access).

Usage:
    python tests/run_agent_tests.py            # readable pass/fail report
    python tests/run_agent_tests.py --trace    # also show the agent's trace/spans (model + tool calls)

A case PASSES only if the agent (a) called the expected MCP tool and (b) its answer contains the
expected figure(s). Figures are regexes that also accept whole-dollar rounding (e.g. $359 for
$359.10), because LLMs sometimes round. The cases are documented in tests/test_cases.md.
"""
import asyncio
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import MODEL, ask  # noqa: E402

CASES = [
    {
        "id": "TC1",
        "input": "Where am I spending the most money lately?",
        "expected_tool": "get_spending_by_category",
        "expected_text": "dining as the top discretionary category, $359.10",
        "expected_in_answer": [r"dining", r"\b359(\.10?)?\b"],
    },
    {
        "id": "TC2",
        "input": "How much can I safely spend per day until my next paycheck?",
        "expected_tool": "get_safe_to_spend",
        "expected_text": "$39.11 per day, $430.25 total",
        "expected_in_answer": [r"\b39(\.11)?\b", r"\b430(\.25)?\b"],
    },
    {
        "id": "TC3",
        "input": "How unpredictable is my income, and what should I plan around?",
        "expected_tool": "get_income_variability",
        "expected_text": "conservative baseline of $2,610 (the lowest month)",
        "expected_in_answer": [r"\b2610(\.00?)?\b"],
    },
]

LINE = "=" * 72


def _norm(s: str) -> str:
    return s.replace(",", "").replace("$", "").lower()


async def main() -> int:
    trace = "--trace" in sys.argv
    print(f"{LINE}\nBudgetWise AI - live agent tests   (model: {MODEL})\n{LINE}")
    results = []
    for case in CASES:
        print(f"\n--- {case['id']} " + "-" * 60)
        print(f"Input:              {case['input']}")
        print(f"Expected tool:      {case['expected_tool']}")
        print(f"Expected in answer: {case['expected_text']}")
        answer, tools_called = await ask(case["input"], trace)
        tool_ok = case["expected_tool"] in tools_called
        text_ok = all(re.search(p, _norm(answer)) for p in case["expected_in_answer"])
        passed = tool_ok and text_ok
        results.append((case["id"], passed, case["expected_tool"], tools_called))
        print(f"\nTool called:        {', '.join(tools_called) or 'none'}  ->  {'OK' if tool_ok else 'WRONG/MISSING'}")
        print(f"Expected figures:   {'found' if text_ok else 'NOT FOUND'}")
        print("Agent answer:")
        print(textwrap.indent(answer, "    "))
        print(f"\nRESULT: {'PASS' if passed else 'FAIL'}")

    print(f"\n{LINE}\nSUMMARY\n{LINE}")
    for cid, passed, expected, called in results:
        print(f"  {cid}  {'PASS' if passed else 'FAIL'}   expected {expected}, called {', '.join(called) or 'none'}")
    n_pass = sum(1 for r in results if r[1])
    print(f"\n{n_pass}/{len(results)} test cases passed.")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
