"""BudgetWise AI - personal finance agent prototype (CEN 4930 M2).

One agent (NRP gpt-oss by default) + one MCP server (mcp_server.py) with three finance tools.

Usage:
    python agent.py "How much can I spend per day until payday?"
    python agent.py --trace "How much can I spend per day until payday?"   # also print trace/spans
    python agent.py                                                         # chat mode ('quit' exits)
"""
import asyncio
import os
import sys
from pathlib import Path

from agents import (
    Agent,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_trace_processors,
    set_tracing_disabled,
)
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from agents.tracing import TracingProcessor
from dotenv import load_dotenv
from openai import AsyncOpenAI

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# --- Model backend (kept separate from the agent logic so it can be swapped) ---
MODEL = os.getenv("NRP_MODEL", "gpt-oss")
SERVER_SCRIPT = ROOT / "mcp_server.py"

# --- Agent persona + core instruction ---
INSTRUCTIONS = """\
You are BudgetWise, a plain-spoken budgeting coach for college students and
working adults with irregular income. Be brief, practical and non-judgmental.

RULES
- You MUST call an MCP tool for every number you report. Never do the math
  yourself and never guess or invent figures.
- Pick the tool that fits the question:
  * get_spending_by_category - where money is going / overspending.
  * get_safe_to_spend - how much can be spent before the next paycheck.
  * get_income_variability - how unpredictable income is / what to plan around.
- Quote the tool's numbers exactly as returned, including cents (say $359.10, not $359
  or "about $360"), then give 1-2 sentences of practical advice.
- The data is FAKE SAMPLE DATA. You are not a licensed financial advisor. If asked
  about investing, taxes or retirement, say that is not supported yet.
"""


class ConsoleTracingProcessor(TracingProcessor):
    """Prints the trace and each span (model call, tool call) to the console, as in the course examples."""

    def on_trace_start(self, trace):
        print(f"\n[trace] '{trace.name}' started")

    def on_trace_end(self, trace):
        print(f"[trace] '{trace.name}' finished")

    def on_span_start(self, span):
        pass

    def on_span_end(self, span):
        data = span.span_data.export()
        line = f"  [span] {data.get('type', 'unknown')}"
        if data.get("name"):
            line += f" - {data['name']}"
        if data.get("usage"):
            line += f" | usage={data['usage']}"
        print(line)

    def shutdown(self):
        pass

    def force_flush(self):
        pass


def _configure(trace: bool) -> None:
    api_key, base_url = os.getenv("NRP_API_KEY"), os.getenv("NRP_BASE_URL")
    if not api_key or not base_url:
        raise RuntimeError(
            "NRP_API_KEY and NRP_BASE_URL must be set. Copy .env.example to .env and fill it in."
        )
    # Point the Agents SDK at the NRP (OpenAI-compatible) endpoint.
    set_default_openai_client(AsyncOpenAI(base_url=base_url, api_key=api_key), use_for_tracing=False)
    set_default_openai_api("chat_completions")
    if trace:
        set_trace_processors([ConsoleTracingProcessor()])  # local console output only
    else:
        set_tracing_disabled(True)  # default SDK tracing would need an OpenAI key


def _tool_names(result) -> list[str]:
    """Names of the tools the agent actually called during this run."""
    return [getattr(i.raw_item, "name", "unknown") for i in result.new_items if i.type == "tool_call_item"]


async def ask(question: str, trace: bool = False) -> tuple[str, list[str]]:
    """Send one question to the agent. Returns (answer, names of tools it called)."""
    _configure(trace)
    async with MCPServerStdio(
        name="BudgetWise Tools",
        params=MCPServerStdioParams(command=sys.executable, args=[str(SERVER_SCRIPT)]),
        client_session_timeout_seconds=120,
    ) as server:
        agent = Agent(name="BudgetWise", instructions=INSTRUCTIONS, mcp_servers=[server], model=MODEL)
        result = await Runner.run(agent, question)
        return str(result.final_output), _tool_names(result)


def _show(question: str, answer: str, tools_called: list[str]) -> None:
    print(f"\nQuestion:     {question}")
    print(f"Tools called: {', '.join(tools_called) or 'none'}")
    print(f"Answer:\n{answer}")


async def main() -> None:
    args = sys.argv[1:]
    trace = "--trace" in args
    args = [a for a in args if a != "--trace"]
    if args:
        question = " ".join(args)
        answer, tools_called = await ask(question, trace)
        _show(question, answer, tools_called)
        return
    print(f"BudgetWise AI (model: {MODEL}). Ask about spending, safe-to-spend, or income. 'quit' exits.")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"quit", "exit", ""}:
            break
        answer, tools_called = await ask(question, trace)
        _show(question, answer, tools_called)


if __name__ == "__main__":
    asyncio.run(main())
